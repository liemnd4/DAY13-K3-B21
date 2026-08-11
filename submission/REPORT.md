# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/validate_logs.txt` (10 correlation IDs duy nhất)
- Evidence PII redaction: `submission/evidence/pytest_pii.txt` và `submission/evidence/validate_logs.txt`
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 1, labels `baseline` và `production` sau rollback
- Version/label candidate: version 2, label `candidate`
- Trace ID của mỗi version:
  - baseline/v1: `e3cdf055b491c9a3725692ce77668935`
  - candidate/v2: `f2e50462fb347c80f9507dc73a5872a4`
  - production/v2 trước rollback: `bd0bb609190de1dc69413125dc1b6975`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/langfuse/prompt_trace_evidence.json`; production được promote sang v2 và rollback về v1, đã xác minh lại từ Langfuse.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
