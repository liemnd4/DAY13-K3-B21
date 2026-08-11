# Recursive PII Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redact every configured PII value anywhere in a structured log before it is persisted or rendered.

**Architecture:** `scrub_value(value)` recursively preserves containers and non-string values while applying the existing `scrub_text()` to strings. Structlog's `scrub_event` applies it once to the complete event dictionary before `JsonlFileProcessor` and `JSONRenderer`.

**Tech Stack:** Python 3.11+, Structlog 25.4.0, pytest 8.3.5

## Global Constraints

- Preserve dictionary keys and all non-string values.
- Preserve list and tuple container types.
- Treat `PII_PATTERNS` as the single source of truth.
- Redact before any persistence or rendering processor.
- Validator acceptance is at least 80/100; target is 100/100.

---

### Task 1: Recursive PII value scrubber

**Files:**
- Modify: `tests/test_pii.py`
- Modify: `app/pii.py`

**Interfaces:**
- Consumes: `scrub_text(text: str) -> str`
- Produces: `scrub_value(value: Any) -> Any`

- [ ] **Step 1: Write failing recursive structure and pattern tests**

Add tests that assert the exact transformed fixture containing email, phone, CCCD, credit card, passport, nested dictionaries, a list, a tuple, integers, booleans, and an email-shaped dictionary key. Import `scrub_value`; assert the key and non-string values are unchanged.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_pii.py -v`

Expected: collection fails because `scrub_value` is not defined.

- [ ] **Step 3: Implement the minimal recursive scrubber**

Implement in `app/pii.py`:

```python
from typing import Any

def scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, dict):
        return {key: scrub_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_value(item) for item in value)
    return value
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_pii.py -v`

Expected: all PII tests pass.

- [ ] **Step 5: Commit the unit**

```powershell
git add app/pii.py tests/test_pii.py
git commit -m "feat: recursively scrub structured PII values"
```

### Task 2: Global Structlog integration

**Files:**
- Create: `tests/test_logging_security.py`
- Modify: `app/logging_config.py`

**Interfaces:**
- Consumes: `scrub_value(value: Any) -> Any`
- Produces: `scrub_event(logger, method_name, event_dict) -> dict[str, Any]`

- [ ] **Step 1: Write a failing JSONL integration test**

Configure logging against `tmp_path / "logs.jsonl"`, emit a real event with `custom_email="abc@gmail.com"` and nested phone/card values, read the JSONL record, and assert raw values are absent while redaction markers are present.

- [ ] **Step 2: Run the integration test and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_logging_security.py -v`

Expected: FAIL because the current processor leaves top-level and nested PII unchanged.

- [ ] **Step 3: Apply the recursive scrubber to the entire event**

Replace the field-specific implementation with:

```python
def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    return scrub_value(event_dict)
```

Keep `scrub_event` before `JsonlFileProcessor()` and the final `JSONRenderer()` in `configure_logging()`.

- [ ] **Step 4: Run integration and unit tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_logging_security.py tests/test_pii.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the integration**

```powershell
git add app/logging_config.py tests/test_logging_security.py
git commit -m "test: enforce PII scrubbing before log persistence"
```

### Task 3: Repository verification evidence

**Files:**
- Create or update: `submission/evidence/pytest_pii.txt`
- Create or update: `submission/evidence/pytest_full.txt`
- Create or update: `submission/evidence/validate_logs.txt`

**Interfaces:**
- Consumes: completed Tasks 1-2
- Produces: reviewable test and validator evidence

- [ ] **Step 1: Run focused, full, and validator commands**

Run the focused tests, `python -m pytest -q`, and `python scripts/validate_logs.py` using `.venv\Scripts\python.exe`.

- [ ] **Step 2: Verify outputs**

Expected: focused and full tests have zero failures; validator is at least 80/100 with zero PII leaks.

- [ ] **Step 3: Save exact non-secret outputs**

Store the three command outputs at the evidence paths above and run `git diff --check`.

- [ ] **Step 4: Commit evidence**

```powershell
git add submission/evidence/pytest_pii.txt submission/evidence/pytest_full.txt submission/evidence/validate_logs.txt
git commit -m "docs: record security verification evidence"
```
