# Alert rules and runbook

Các alert dưới đây dựa trên triệu chứng người dùng/SLO. Luồng điều tra chung là **Metrics → Traces → Logs**; không kết luận nguyên nhân nếu chưa có trace ID hoặc correlation ID làm bằng chứng.

## Alert 1: High Latency P95

- **Severity:** Warning
- **SLI/SLO:** P95 latency ≤ 3000 ms; duy trì vượt ngưỡng trong 3 phút.
- **Ảnh hưởng:** Người dùng phải chờ lâu để nhận phản hồi AI.
- **Kiểm tra đầu tiên:**
  1. Kiểm tra traffic, error rate và thời điểm P95 bắt đầu tăng trên dashboard.
  2. Mở các trace chậm trong cùng cửa sổ và tìm span chiếm nhiều thời gian nhất.
  3. Dùng correlation ID của trace để tìm log tương ứng và xác nhận lỗi/timeout/dependency chậm.
- **Mitigation:** Giảm concurrency hoặc tạm tắt tính năng gây chậm; chuyển sang dependency/model dự phòng nếu có.
- **Owner:** `platform-oncall`

## Alert 2: High Error Rate

- **Severity:** Critical
- **SLI/SLO:** Error rate ≤ 2%; duy trì vượt ngưỡng trong 5 phút.
- **Ảnh hưởng:** Hơn 2% yêu cầu người dùng không nhận được phản hồi thành công.
- **Kiểm tra đầu tiên:**
  1. Xem breakdown `error_type` và xác định feature/model/env bị ảnh hưởng.
  2. Mở trace lỗi đại diện, ghi lại trace ID và span thất bại đầu tiên.
  3. Tra correlation ID trong JSON log để xác nhận exception, status code và dependency liên quan.
- **Mitigation:** Rollback thay đổi gần nhất hoặc chuyển traffic khỏi dependency lỗi; giới hạn request nếu hệ thống quá tải.
- **Owner:** `service-oncall`

## Alert 3: Low Quality Score

- **Severity:** Warning
- **SLI/SLO:** Mean quality score ≥ 0.75; duy trì dưới ngưỡng trong 10 phút.
- **Ảnh hưởng:** Phản hồi vẫn thành công nhưng có thể kém hữu ích hoặc thiếu căn cứ.
- **Kiểm tra đầu tiên:**
  1. Xác định feature/model/prompt label có quality giảm và so sánh với baseline.
  2. Mở trace mẫu, kiểm tra input, retrieved context và metadata prompt version.
  3. Dùng correlation ID để đối chiếu log và loại trừ lỗi dữ liệu/RAG.
- **Mitigation:** Rollback prompt label về version ổn định hoặc tạm tắt feature gây suy giảm chất lượng.
- **Owner:** `ai-oncall`
