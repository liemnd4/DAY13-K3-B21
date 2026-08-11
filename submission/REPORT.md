# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

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
