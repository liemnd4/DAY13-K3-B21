from __future__ import annotations

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


def promote_and_rollback(
    client: Any, baseline_version: int, candidate_version: int
) -> dict[str, int]:
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

    return {
        "promoted_version": int(promoted.version),
        "rollback_version": int(rolled_back.version),
    }
