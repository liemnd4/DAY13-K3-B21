# Security and Prompt Evidence Design

## Scope

Complete the remaining Security & Compliance work without changing metrics, alerts, or application business logic. The work covers global recursive PII scrubbing, regression tests for all configured PII patterns, and real Langfuse prompt-version trace evidence.

## Global PII scrubbing

Add one recursive value scrubber in `app/pii.py`. It replaces PII in strings, recursively processes dictionary values, lists, and tuples, and leaves other values unchanged. Dictionary keys are preserved because changing keys would break the structured logging contract.

Update `scrub_event` in `app/logging_config.py` to apply this scrubber to the complete Structlog `event_dict` before the JSONL file processor and renderer. This protects top-level custom fields and nested payloads instead of only `event` and first-level payload strings.

The existing patterns remain the source of truth: email, Vietnamese phone, CCCD, credit card, and passport. Redaction markers stay compatible with the current `[REDACTED_<TYPE>]` format.

## Prompt version and trace evidence

Use the configured Langfuse project and the prompt name `day13-chat`.

- Version 1 uses the required `feature`, `docs`, and `message` variables and receives `baseline` and `production` labels.
- Version 2 keeps the same variables, adds only a small answer-format instruction, and receives the `candidate` label.
- Run the same request once with `baseline` and once with `candidate`.
- Record trace identifiers and verify `prompt_name`, `prompt_label`, `prompt_version`, and `prompt_source=langfuse`.
- Move `production` to version 2, verify it, then roll `production` back to version 1.

No API key or secret value may be printed, logged, committed, or included in evidence. If Langfuse rejects remote prompt creation or label updates, stop remote mutation and report the exact non-secret failure; do not fabricate trace IDs or screenshots.

## Tests and verification

Follow red-green-refactor:

1. Add failing unit tests for CCCD, credit card, passport, top-level log fields, and nested dictionary/list/tuple values.
2. Implement the minimal recursive scrubber and logging integration.
3. Run focused PII/logging tests, then the full test suite.
4. Run `scripts/validate_logs.py` and retain the final output.
5. Verify Langfuse prompt and trace metadata using real project responses.

Automated tests prove local behavior. Langfuse trace IDs and web screenshots remain the required evidence for remote prompt versioning and rollback.

## Deliverables

- Updated PII and logging code.
- Regression tests covering every configured PII type and recursive logging structures.
- Final validator output under `submission/evidence/`.
- Langfuse trace IDs and prompt-version details in `submission/REPORT.md`.
- Screenshot placeholders are not acceptable; only real screenshots supplied from the Langfuse UI are referenced.
