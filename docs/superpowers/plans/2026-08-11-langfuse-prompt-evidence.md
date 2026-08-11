# Langfuse Prompt Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create two real `day13-chat` prompt versions, generate traces for baseline and candidate labels, verify production promotion and rollback, and record non-secret evidence.

**Architecture:** A small CLI module loads `.env`, provisions prompt versions through Langfuse SDK 3.2.1, runs the existing unwrapped agent inside a current Langfuse generation to obtain trace IDs, verifies labels by fetching them back, restores `production` to the baseline version, and writes JSON evidence without credentials.

**Tech Stack:** Python 3.11+, Langfuse SDK 3.2.1, python-dotenv 1.1.0, pytest 8.3.5

## Global Constraints

- Prompt name is exactly `day13-chat`.
- Both versions keep `feature`, `docs`, and `message` variables.
- Real trace metadata must contain `prompt_name`, `prompt_label`, `prompt_version`, and `prompt_source=langfuse`.
- Never print or persist API keys or secret values.
- On 401, 403, network failure, or incompatible API, record the sanitized error and do not fabricate evidence.
- Screenshots must be captured from the authenticated Langfuse UI by a team member.

---

### Task 1: Testable prompt workflow

**Files:**
- Create: `tests/test_langfuse_prompt_evidence.py`
- Create: `scripts/langfuse_prompt_evidence.py`

**Interfaces:**
- Produces: `provision_prompt_versions(client) -> tuple[int, int]`
- Produces: `promote_and_rollback(client, baseline_version: int, candidate_version: int) -> dict[str, int]`

- [ ] **Step 1: Write failing tests with a recording fake client**

Assert that version 1 is created with `baseline` and `production`, version 2 with `candidate`, both prompts retain the required variables, promotion fetches `production` at the candidate version, and rollback fetches it at the baseline version.

- [ ] **Step 2: Run tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_langfuse_prompt_evidence.py -v`

Expected: collection fails because the script module does not exist.

- [ ] **Step 3: Implement prompt provisioning and label transitions**

Use `client.create_prompt(name=..., prompt=..., labels=..., type="text", commit_message=...)`, `client.update_prompt(name=..., version=..., new_labels=...)`, and `client.get_prompt(name, label="production", cache_ttl_seconds=0)` with returned prompt `.version` values. Promotion assigns `candidate,production`; rollback removes production from candidate and assigns `baseline,production` to baseline.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_langfuse_prompt_evidence.py -v`

Expected: all workflow tests pass.

- [ ] **Step 5: Commit workflow code and tests**

```powershell
git add scripts/langfuse_prompt_evidence.py tests/test_langfuse_prompt_evidence.py
git commit -m "feat: automate Langfuse prompt evidence workflow"
```

### Task 2: Real baseline and candidate traces

**Files:**
- Modify: `scripts/langfuse_prompt_evidence.py`
- Create at runtime: `submission/evidence/langfuse/prompt_trace_evidence.json`

**Interfaces:**
- Consumes: versions from `provision_prompt_versions`
- Produces: real trace IDs and verified prompt metadata

- [ ] **Step 1: Add a labeled trace runner**

Load `.env` before importing application modules. For each label, set `LANGFUSE_PROMPT_LABEL`, enter `client.start_as_current_generation(name="lab-agent-evidence", model=agent.model)`, call `LabAgent.run.__wrapped__` with the same fixed input, read `client.get_current_trace_id()`, then flush.

- [ ] **Step 2: Validate remote results before writing evidence**

Require non-empty real trace IDs, distinct baseline/candidate versions, and managed prompt source. Serialize only prompt name, labels, versions, trace IDs, promotion result, rollback result, and trace URLs.

- [ ] **Step 3: Run against the configured project**

Run: `.\.venv\Scripts\python.exe scripts\langfuse_prompt_evidence.py`

Expected: exit 0 and a JSON evidence file. If remote access fails, exit nonzero with a sanitized message and leave no fabricated success file.

- [ ] **Step 4: Commit non-secret machine evidence**

```powershell
git add submission/evidence/langfuse/prompt_trace_evidence.json
git commit -m "docs: record Langfuse prompt trace evidence"
```

### Task 3: Report and screenshots handoff

**Files:**
- Modify: `submission/REPORT.md`
- Create manually: `submission/evidence/langfuse/baseline_trace.png`
- Create manually: `submission/evidence/langfuse/candidate_trace.png`
- Create manually: `submission/evidence/langfuse/production_v2.png`
- Create manually: `submission/evidence/langfuse/production_rollback_v1.png`

**Interfaces:**
- Consumes: machine evidence from Task 2
- Produces: grading-ready prompt evidence references

- [ ] **Step 1: Update report with real values**

Record prompt name, baseline label/version/trace ID, candidate label/version/trace ID, production promotion version, rollback version, and relative evidence paths. Do not add placeholders when a remote value is unavailable; report the sanitized failure instead.

- [ ] **Step 2: Capture authenticated UI screenshots**

A team member opens the trace and prompt pages in the configured Langfuse project and saves the four real screenshots at the paths above. Verify no key or secret appears in any image.

- [ ] **Step 3: Run final checks**

Run `.\.venv\Scripts\python.exe -m pytest -q`, `.\.venv\Scripts\python.exe scripts\validate_logs.py`, and `git diff --check`.

- [ ] **Step 4: Commit report and screenshots after review**

```powershell
git add submission/REPORT.md submission/evidence/langfuse
git commit -m "docs: complete prompt version evidence"
```
