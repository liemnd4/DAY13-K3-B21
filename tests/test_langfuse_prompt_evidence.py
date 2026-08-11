from __future__ import annotations

from dataclasses import dataclass

from scripts.langfuse_prompt_evidence import (
    CANDIDATE_PROMPT,
    REQUIRED_VARIABLES,
    execute_workflow,
    promote_prompt,
    promote_and_rollback,
    provision_prompt_versions,
    rollback_prompt,
    run_labeled_trace,
)


@dataclass
class FakePrompt:
    version: int


class StatefulPromptClient:
    def __init__(self) -> None:
        self.versions: dict[int, dict] = {}
        self.next_version = 1

    def create_prompt(self, **kwargs) -> FakePrompt:
        version = self.next_version
        self.next_version += 1
        self.versions[version] = {
            "prompt": kwargs["prompt"],
            "labels": list(kwargs["labels"]),
        }
        return FakePrompt(version=version)

    def update_prompt(self, *, name: str, version: int, new_labels: list[str]):
        for existing in self.versions.values():
            existing["labels"] = [
                label for label in existing["labels"] if label not in new_labels
            ]
        self.versions[version]["labels"] = list(new_labels)

    def get_prompt(self, name: str, *, label: str, **kwargs) -> FakePrompt:
        version = next(
            version
            for version, data in self.versions.items()
            if label in data["labels"]
        )
        return FakePrompt(version=version)


class FakeGenerationContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class TracePromptClient(StatefulPromptClient):
    def __init__(self) -> None:
        super().__init__()
        self.flushed = False

    def start_as_current_generation(self, **kwargs) -> FakeGenerationContext:
        return FakeGenerationContext()

    def get_current_trace_id(self) -> str:
        return "trace-real-123"

    def get_trace_url(self, *, trace_id: str) -> str:
        return f"https://langfuse.example/trace/{trace_id}"

    def flush(self) -> None:
        self.flushed = True


class WorkflowPromptClient(TracePromptClient):
    def __init__(self) -> None:
        super().__init__()
        self.trace_number = 0

    def start_as_current_generation(self, **kwargs) -> FakeGenerationContext:
        self.trace_number += 1
        return FakeGenerationContext()

    def get_current_trace_id(self) -> str:
        return f"trace-{self.trace_number}"

def test_provision_prompt_versions_keeps_contract_and_assigns_initial_labels() -> None:
    client = StatefulPromptClient()

    baseline_version, candidate_version = provision_prompt_versions(client)

    assert (baseline_version, candidate_version) == (1, 2)
    assert client.versions[1]["labels"] == ["baseline", "production"]
    assert client.versions[2]["labels"] == ["candidate"]
    assert all(variable in client.versions[1]["prompt"] for variable in REQUIRED_VARIABLES)
    assert all(variable in CANDIDATE_PROMPT for variable in REQUIRED_VARIABLES)


def test_promote_and_rollback_verifies_production_then_restores_baseline() -> None:
    client = StatefulPromptClient()
    baseline_version, candidate_version = provision_prompt_versions(client)

    result = promote_and_rollback(client, baseline_version, candidate_version)

    assert result == {"promoted_version": 2, "rollback_version": 1}
    assert client.versions[1]["labels"] == ["baseline", "production"]
    assert client.versions[2]["labels"] == ["candidate"]


def test_promotion_and_rollback_can_be_verified_as_separate_steps() -> None:
    client = StatefulPromptClient()
    baseline_version, candidate_version = provision_prompt_versions(client)

    assert promote_prompt(client, candidate_version) == 2
    assert "production" in client.versions[2]["labels"]
    assert rollback_prompt(client, baseline_version, candidate_version) == 1
    assert client.versions[1]["labels"] == ["baseline", "production"]
    assert client.versions[2]["labels"] == ["candidate"]


def test_labeled_trace_returns_non_secret_prompt_and_trace_evidence(monkeypatch) -> None:
    client = TracePromptClient()
    baseline_version, _ = provision_prompt_versions(client)
    observed_labels: list[str | None] = []

    result = run_labeled_trace(
        client,
        label="baseline",
        model="fake-model",
        run_agent=lambda: observed_labels.append(
            __import__("os").environ.get("LANGFUSE_PROMPT_LABEL")
        ),
    )

    assert observed_labels == ["baseline"]
    assert result == {
        "prompt_name": "day13-chat",
        "prompt_label": "baseline",
        "prompt_version": baseline_version,
        "prompt_source": "langfuse",
        "trace_id": "trace-real-123",
        "trace_url": "https://langfuse.example/trace/trace-real-123",
    }
    assert client.flushed is True


def test_execute_workflow_runs_same_agent_for_labels_and_always_rolls_back() -> None:
    client = WorkflowPromptClient()
    observed_labels: list[str | None] = []

    evidence = execute_workflow(
        client,
        model="fake-model",
        run_agent=lambda: observed_labels.append(
            __import__("os").environ.get("LANGFUSE_PROMPT_LABEL")
        ),
    )

    assert observed_labels == ["baseline", "candidate", "production"]
    assert evidence["traces"]["baseline"]["trace_id"] == "trace-1"
    assert evidence["traces"]["candidate"]["trace_id"] == "trace-2"
    assert evidence["traces"]["production_v2"]["trace_id"] == "trace-3"
    assert evidence["promotion"]["promoted_version"] == 2
    assert evidence["rollback"]["rollback_version"] == 1
    assert client.versions[1]["labels"] == ["baseline", "production"]
    assert client.versions[2]["labels"] == ["candidate"]
