from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


PROMPT_NAME = "day13-chat"
REQUIRED_VARIABLES = ("{{feature}}", "{{docs}}", "{{message}}")
BASELINE_PROMPT = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
CANDIDATE_PROMPT = (
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}\n"
    "Answer in a concise format with the main conclusion first."
)
REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = REPO_ROOT / "submission" / "evidence" / "langfuse" / "prompt_trace_evidence.json"


def provision_prompt_versions(client: Any) -> tuple[int, int]:
    baseline = client.create_prompt(
        name=PROMPT_NAME,
        prompt=BASELINE_PROMPT,
        labels=["baseline", "production"],
        type="text",
        commit_message="Day 13 baseline prompt",
    )
    candidate = client.create_prompt(
        name=PROMPT_NAME,
        prompt=CANDIDATE_PROMPT,
        labels=["candidate"],
        type="text",
        commit_message="Day 13 concise candidate prompt",
    )
    return int(baseline.version), int(candidate.version)


def promote_prompt(client: Any, candidate_version: int) -> int:
    client.update_prompt(
        name=PROMPT_NAME,
        version=candidate_version,
        new_labels=["candidate", "production"],
    )
    promoted = client.get_prompt(
        PROMPT_NAME,
        label="production",
        type="text",
        cache_ttl_seconds=0,
    )
    if int(promoted.version) != candidate_version:
        raise RuntimeError("Langfuse production promotion verification failed")
    return int(promoted.version)


def rollback_prompt(client: Any, baseline_version: int, candidate_version: int) -> int:
    client.update_prompt(
        name=PROMPT_NAME,
        version=candidate_version,
        new_labels=["candidate"],
    )
    client.update_prompt(
        name=PROMPT_NAME,
        version=baseline_version,
        new_labels=["baseline", "production"],
    )
    rolled_back = client.get_prompt(
        PROMPT_NAME,
        label="production",
        type="text",
        cache_ttl_seconds=0,
    )
    if int(rolled_back.version) != baseline_version:
        raise RuntimeError("Langfuse production rollback verification failed")
    return int(rolled_back.version)


def promote_and_rollback(
    client: Any, baseline_version: int, candidate_version: int
) -> dict[str, int]:
    promoted_version = promote_prompt(client, candidate_version)
    rollback_version = rollback_prompt(client, baseline_version, candidate_version)

    return {
        "promoted_version": promoted_version,
        "rollback_version": rollback_version,
    }


def run_labeled_trace(
    client: Any,
    *,
    label: str,
    model: str,
    run_agent: Callable[[], Any],
) -> dict[str, Any]:
    managed_prompt = client.get_prompt(
        PROMPT_NAME,
        label=label,
        type="text",
        cache_ttl_seconds=0,
    )
    if getattr(managed_prompt, "is_fallback", False):
        raise RuntimeError(f"Langfuse returned a fallback prompt for label {label}")

    previous_label = os.environ.get("LANGFUSE_PROMPT_LABEL")
    os.environ["LANGFUSE_PROMPT_LABEL"] = label
    try:
        with client.start_as_current_generation(
            name="lab-agent-evidence",
            model=model,
            prompt=managed_prompt,
        ):
            run_agent()
            trace_id = client.get_current_trace_id()
    finally:
        if previous_label is None:
            os.environ.pop("LANGFUSE_PROMPT_LABEL", None)
        else:
            os.environ["LANGFUSE_PROMPT_LABEL"] = previous_label

    if not trace_id:
        raise RuntimeError(f"Langfuse did not return a trace ID for label {label}")
    client.flush()
    return {
        "prompt_name": PROMPT_NAME,
        "prompt_label": label,
        "prompt_version": int(managed_prompt.version),
        "prompt_source": "langfuse",
        "trace_id": trace_id,
        "trace_url": client.get_trace_url(trace_id=trace_id) or "",
    }


def execute_workflow(
    client: Any,
    *,
    model: str,
    run_agent: Callable[[], Any],
) -> dict[str, Any]:
    baseline_version, candidate_version = provision_prompt_versions(client)
    if baseline_version == candidate_version:
        raise RuntimeError("Langfuse returned the same version for baseline and candidate")

    baseline_trace = run_labeled_trace(
        client, label="baseline", model=model, run_agent=run_agent
    )
    candidate_trace = run_labeled_trace(
        client, label="candidate", model=model, run_agent=run_agent
    )
    promoted_version = promote_prompt(client, candidate_version)
    try:
        production_trace = run_labeled_trace(
            client, label="production", model=model, run_agent=run_agent
        )
    finally:
        rollback_version = rollback_prompt(client, baseline_version, candidate_version)

    trace_ids = {
        baseline_trace["trace_id"],
        candidate_trace["trace_id"],
        production_trace["trace_id"],
    }
    if len(trace_ids) != 3:
        raise RuntimeError("Langfuse returned duplicate trace IDs")

    return {
        "prompt_name": PROMPT_NAME,
        "versions": {
            "baseline": baseline_version,
            "candidate": candidate_version,
        },
        "traces": {
            "baseline": baseline_trace,
            "candidate": candidate_trace,
            "production_v2": production_trace,
        },
        "promotion": {"promoted_version": promoted_version},
        "rollback": {"rollback_version": rollback_version},
    }


def _safe_error(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    suffix = f" (HTTP {status_code})" if status_code is not None else ""
    return f"{type(exc).__name__}{suffix}"


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
    required_env = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        print(f"Remote prompt mutation: FAILED ({', '.join(missing)} not configured)")
        return 1

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    try:
        from langfuse import get_client

        from app.agent import LabAgent

        client = get_client()
        if not client.auth_check():
            raise RuntimeError("Langfuse authentication check failed")

        agent = LabAgent()

        def run_agent() -> Any:
            return LabAgent.run.__wrapped__(
                agent,
                user_id="security-evidence-user",
                feature="qa",
                session_id="security-prompt-evidence",
                message="Explain how traces help investigate an AI incident.",
            )

        evidence = execute_workflow(
            client,
            model=agent.model,
            run_agent=run_agent,
        )
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Prompt evidence written: {EVIDENCE_PATH.relative_to(REPO_ROOT)}")
        for name, trace in evidence["traces"].items():
            print(
                f"{name}: version={trace['prompt_version']} "
                f"trace_id={trace['trace_id']}"
            )
        print(f"production rollback: version={evidence['rollback']['rollback_version']}")
        return 0
    except Exception as exc:
        print(f"Remote prompt mutation: FAILED ({_safe_error(exc)}). Secrets redacted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
