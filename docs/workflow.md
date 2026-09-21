# Agent Workflow and Phase Gates

## 1. Xác định nguồn sự thật (Source of Truth)
Đọc tài liệu theo đúng thứ tự ưu tiên:

1. `docs/FOUNDATION_BASELINE.md` – Bản móng kỹ thuật & ranh giới 3 thành viên
2. `docs/PROJECT_STATUS_AND_ROADMAP.md` – Lộ trình trọng tâm AI & phân nhóm A/B
3. `docs/constitution.md` – Nguyên tắc kiến trúc bất biến
4. `docs/decisions.md` – Quyết định kiến trúc đã được chấp nhận
5. `docs/architecture.md` – Kiến trúc tổng thể và ranh giới module
6. `docs/coding-style.md` – Quy tắc code chuẩn
7. `docs/plan.md` – Kế hoạch phase
8. `docs/checklist.md` – Danh sách kiểm tra tiến độ

Swagger/OpenAPI tại `http://localhost:8080/swagger-ui.html` là nguồn sự thật duy nhất cho API contracts.

## 2. Chọn đúng phase và vertical slice
- Mỗi task phải ghi rõ phase, module, API/UI surface và acceptance criteria.
- Không bắt đầu phase mới khi gate của phase trước chưa đạt.
- Ưu tiên flow hoàn chỉnh theo lát cắt: Database Migration → Spring Boot API → React UI → Smoke Test.
- Không ôm đồm task quá lớn dàn trải toàn bộ project.

## 3. Trước khi code
- Xác định entity, DTO, validation, error cases và API response (`ApiResponse<T>`).
- Nếu đổi schema, tạo file Flyway migration mới trước khi viết code Java.
- Nếu đổi recommendation, xác định feature source, constraint và explainable reason bị ảnh hưởng.
- Giới hạn file được phép thay đổi trong scope task.

## 4. Trong khi code
- Tuân theo `docs/coding-style.md`.
- Controller mỏng; business logic nằm trong service.
- Dùng DTO validation cho input.
- Không tin giá, role hoặc stock do frontend gửi lên (luôn kiểm tra tại server).
- Không log password, token hoặc dữ liệu nhạy cảm.
- Cập nhật Swagger khi API thay đổi.

## 5. Sau mỗi task
Chạy kiểm tra nhỏ nhất phù hợp:

1. Typecheck/build của phần vừa sửa (`mvn clean package` hoặc `npm run build`).
2. Unit/service test cho logic mới.
3. API smoke test cho endpoint quan trọng qua Swagger.
4. Frontend flow test nếu sửa UI.
5. Flyway migration check nếu sửa schema.

## 6. Gate của phase
Chỉ tick checklist khi có bằng chứng (evidence):
- Command đã chạy và kết quả pass;
- Endpoint/UI flow đã được kiểm tra thực tế;
- Lỗi chính và boundary cases đã được xử lý;
- Swagger, schema hoặc docs đã đồng bộ.

## 7. Kết thúc task
- Kiểm tra `docs/done.md`.
- Cập nhật `docs/checklist.md` đúng mục, không tick thay cho phase khác.
- Cập nhật `docs/lessons.md` khi có lỗi bất thường hoặc quyết định mới.
