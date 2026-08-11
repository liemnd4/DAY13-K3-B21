from __future__ import annotations

from dataclasses import dataclass

from scripts.langfuse_prompt_evidence import (
    CANDIDATE_PROMPT,
    REQUIRED_VARIABLES,
    promote_and_rollback,
    provision_prompt_versions,
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
