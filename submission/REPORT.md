# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: 13 traces mới trong lần chạy CP2 gần nhất (10 load-test và 3 prompt-version); evidence: `submission/evidence/langfuse/trace-list.txt`.
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/validate_logs.txt` (10 correlation IDs duy nhất)
- Evidence PII redaction: `submission/evidence/pytest_pii.txt` và `submission/evidence/validate_logs.txt`
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 5, labels `baseline` và `production` sau rollback
- Version/label candidate: version 6, label `candidate`
- Trace ID của mỗi version:
  - baseline/v5: `1711969e11f142e8cc7b1beb72de8a23`
  - candidate/v6: `c5845f99ff771be61e7c302335ec5c9a`
  - production/v6 trước rollback: `1bc0ba2bebf726cedc5c162902fbe625`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/langfuse/prompt_trace_evidence.json`; production được promote sang v6 và rollback về v5, đã xác minh lại từ Langfuse.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract. Evidence: `submission/evidence/dashboard-validator.txt`.
- Evidence dashboard: `submission/evidence/dashboard.png` (chụp sau khi chạy load test; không tạo evidence giả).
- SLO đã chọn và lý do:
  - **SLO Latency**: P95 latency ≤ 3000 ms trong cửa sổ quan sát; mục tiêu tối thiểu 95% request đáp ứng trong 3000 ms.
  - **SLO Error Rate**: Tỷ lệ lỗi toàn hệ thống ≤ 2%, tương đương tối thiểu 98% request thành công.
- Alert rules và runbook:
  - `HighLatencyP95`: P95 > 3000 ms trong 3 phút, severity warning.
  - `HighErrorRate`: error rate > 2% trong 5 phút, severity critical.
  - `LowQualityScore`: mean quality < 0.75 trong 10 phút, severity warning.
  - Runbook đầy đủ: `docs/alerts.md`, theo luồng Metrics → Traces → Logs.

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
