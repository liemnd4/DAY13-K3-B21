# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: B21
- Repository URL: https://github.com/liemnd4/DAY13-K3-B21
- Commit SHA cuối: (Cập nhật khi commit bài nộp)
- Thành viên và vai trò:
  - Nguyễn Văn Hưng (01251): Vai trò 1 - Logging & PII
  - Nguyễn Đình Liêm (01421): Vai trò 2 - Tracing & Prompt Versioning
  - Đỗ Trung Kiên (01287): Vai trò 3 - Dashboard, SLO & Alert Rules
  - Nguyễn Hồng Yến (01065): Vai trò 4 - Incident Investigation, Report & Demo

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces: 30 traces (bao gồm load-test và prompt-version); evidence: `submission/evidence/langfuse/trace-list.txt`.
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: config/dashboard.yaml

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/validate_logs.txt` và `submission/evidence/validate_logs.png`
- Evidence PII redaction: `submission/evidence/pytest_pii.txt` và `submission/evidence/pii_redaction.png`
- Evidence trace waterfall: `submission/evidence/langfuse/prompt_trace_evidence.json`
- Giải thích một span đáng chú ý: Span `llm_call` nhận prompt template `day13-chat` version 5, thực hiện xử lý trong ~1.2s và tiêu tốn 167 tokens.

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
  - **SLO Latency**: P95 latency <= 3000 ms trong cửa sổ quan sát; mục tiêu tối thiểu 95% request đáp ứng trong 3000 ms.
  - **SLO Error Rate**: Tỷ lệ lỗi toàn hệ thống <= 2%, tương đương tối thiểu 98% request thành công.
- Alert rules và runbook:
  - `HighLatencyP95`: P95 > 3000 ms trong 3 phút, severity warning.
  - `HighErrorRate`: error rate > 2% trong 5 phút, severity critical.
  - `LowQualityScore`: mean quality < 0.75 trong 10 phút, severity warning.
  - Runbook đầy đủ: `docs/alerts.md`, theo luồng Metrics -> Traces -> Logs.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`
- Triệu chứng từ metrics: Latency p95 bị spike tăng vọt lên 5315ms - 13282ms (vượt xa ngưỡng SLO 2000ms) trên feature `refund` khi chạy đồng thời (concurrency 5).
- Trace ID liên quan: `d4f52f190114674baaee39a4a7a726d3`
- Log line/correlation ID liên quan: `req-59be40b6` và `req-cf90b6e6` (ghi nhận latency_ms = 13282.6ms cho feature refund trong `data/logs.jsonl`)
- Root cause: Hàm `retrieve()` trong `app/mock_rag.py` bị nghẽn do cờ sự cố `STATE["rag_slow"] = True` gây trễ 2.5s mỗi lượt truy vấn retrieval.
- Fix action: Tắt cờ sự cố trễ RAG (`python3 scripts/inject_incident.py --disable`) và khôi phục tốc độ phản hồi bình thường (~1.2s).
- Preventive measure: Cấu hình Timeout tối đa 1.0s cho hàm Retrieval RAG, đồng thời thiết lập Alert Rule cảnh báo khi Latency p95 > 2000ms.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Văn Hưng - 01251 | Logging, PII Redaction & Correlation ID | Branch `checkpoint-1-logging-pii` | Biết cách che PII bằng Regex và truyền correlation ID qua structlog |
| Nguyễn Đình Liêm - 01421 | Tracing & Prompt Versioning | Branch `feature/security-prompt-evidence` | Quản lý prompt managed trên Langfuse và thử nghiệm rollback phiên bản |
| Đỗ Trung Kiên - 01287 | Dashboard Contract, SLO & Alerts | Branch `feat-dashboard-slo-alert` | Xây dựng 6 nhóm chỉ số giám sát và thiết lập ngưỡng Alert |
| Nguyễn Hồng Yến - 01065 | Challenge Investigation, Report & Demo | Branch `feature/incident-investigation-report` | Nối mạch suy luận Metrics -> Traces -> Logs để tìm Root Cause |
