# Project Constitution

## Vai trò file này
File cố định. Đây là bộ quy tắc làm việc không nên thay đổi trong suốt dự án trừ khi có quyết định kiến trúc lớn.

## 1. Architecture rules
- Ưu tiên modular monolith thay vì microservices.
- Giữ các domain tách biệt theo Spring Boot packages/modules.
- Tránh over-engineering trừ khi yêu cầu nghiệp vụ thực sự đòi hỏi.

## 2. Development rules
- Xây dựng tính năng theo từng lát cắt hoàn chỉnh (Vertical Slice).
- Giữ code rõ ràng, nhất quán và có kiểm thử.
- Sử dụng JPA entities và Flyway migrations làm nguồn sự thật duy nhất cho database modeling.
- Không tự ý thêm dịch vụ hoặc abstraction không cần thiết.

## 3. Recommendation rules
- Logic recommendation nằm độc lập trong module `recommendations`.
- Bắt đầu với Content-based filtering kết hợp Constraint filtering và Explainable reasons.
- Tích hợp đơn giản: Spring Boot đọc model artifact từ Python (file JSON/PKL) và nạp cache Redis.
- Không phức tạp hóa phiên bản đầu tiên.

## 4. Documentation rules
- Cập nhật tài liệu mỗi khi có thay đổi kiến trúc hoặc hợp đồng API.
- Giữ các ghi chú kiến trúc và tài liệu triển khai luôn đồng bộ.

## 5. Quality rules
- Luôn kiểm tra build backend (`mvn clean package`) và frontend (`npm run build`) trước khi hoàn thành task.
- Đảm bảo các luồng cốt lõi hoạt động: duyệt danh mục, thông số máy ảnh, tư vấn gợi ý AI.
- Giữ dự án luôn ở trạng thái sẵn sàng demo và báo cáo trước hội đồng.
