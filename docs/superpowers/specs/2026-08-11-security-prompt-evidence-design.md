# Security and Prompt Evidence Design

## Scope

Complete the remaining Security & Compliance work without changing metrics, alerts, or application business logic. The work covers global recursive PII scrubbing, regression tests for all configured PII patterns, and real Langfuse prompt-version trace evidence.

## Global PII scrubbing

Add one recursive value scrubber in `app/pii.py`. It replaces PII in strings, recursively processes dictionary values, lists, and tuples, and leaves other values unchanged. Dictionary keys are preserved because changing keys would break the structured logging contract.

Update `scrub_event` in `app/logging_config.py` to apply this scrubber to the complete Structlog `event_dict` before the JSONL file processor and renderer. This protects top-level custom fields and nested payloads instead of only `event` and first-level payload strings.

`PII_PATTERNS` is the single source of truth. The current repository already configures email, Vietnamese phone, CCCD, credit card, and passport, so tests cover all five. Passport is additional coverage beyond the four detector groups enforced by `scripts/validate_logs.py`. Redaction markers stay compatible with the current `[REDACTED_<TYPE>]` format.

The acceptance fixture includes nested dictionaries, lists, and tuples containing all configured PII types plus integers and booleans. The expected result preserves dictionary keys, container types, integer values, and boolean values while replacing every PII-bearing string.

`scrub_event` must execute before `JsonlFileProcessor`, `JSONRenderer`, or any future processor that persists or renders the event. Redaction after persistence is not acceptable.

## Prompt version and trace evidence

Use the configured Langfuse project and the prompt name `day13-chat`.

- Version 1 uses the required `feature`, `docs`, and `message` variables and receives `baseline` and `production` labels.
- Version 2 keeps the same variables, adds only a small answer-format instruction, and receives the `candidate` label.
- Run the same request once with `baseline` and once with `candidate`.
- Record trace identifiers and verify `prompt_name`, `prompt_label`, `prompt_version`, and `prompt_source=langfuse`.
- Move `production` to version 2, verify it, then roll `production` back to version 1.

Every recorded trace must contain the following metadata:

| Field | Expected value |
|---|---|
| `prompt_name` | `day13-chat` |
| `prompt_label` | `baseline`, `candidate`, or `production` for the corresponding run |
| `prompt_version` | The real version returned by Langfuse |
| `prompt_source` | `langfuse` |

Correlation-ID linkage between Structlog and Langfuse is not part of this change because the current application does not propagate the Structlog context value into Langfuse trace metadata. It can be added as a separate observability enhancement.

No API key or secret value may be printed, logged, committed, or included in evidence. If Langfuse rejects remote prompt creation or label updates, stop remote mutation and report the exact non-secret failure; do not fabricate trace IDs or screenshots.

## Tests and verification

Follow red-green-refactor:

1. Add failing unit tests for CCCD, credit card, passport, top-level log fields, nested dictionary/list/tuple values, preserved dictionary keys, and preserved non-string types.
2. Implement the minimal recursive scrubber and logging integration.
3. Add an integration test that emits a real Structlog event containing top-level and nested PII, reads the JSONL output, and proves raw values were not persisted.
4. Run focused PII/logging tests, then the full test suite.
5. Run `scripts/validate_logs.py` and retain the final output. A score below 80/100 fails the acceptance gate; the target is the current 100/100 baseline.
6. Verify Langfuse prompt and trace metadata using real project responses.

Automated tests prove local behavior. Langfuse trace IDs and web screenshots remain the required evidence for remote prompt versioning and rollback.

## Deliverables

- Updated PII and logging code.
- Regression tests covering every configured PII type and recursive logging structures.
- `submission/evidence/validate_logs.txt` containing the final validator output.
- `submission/evidence/pytest_pii.txt` containing focused PII/logging test output.
- `submission/evidence/pytest_full.txt` containing full-suite output.
- Langfuse trace IDs and prompt-version details in `submission/REPORT.md`.
- Real Langfuse screenshots under `submission/evidence/langfuse/` for baseline trace, candidate trace, production promotion, and production rollback.
- Screenshot placeholders are not acceptable; only real screenshots supplied from the Langfuse UI are referenced.
