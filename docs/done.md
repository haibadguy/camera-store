# Definition of Done (Tiêu Chuẩn Nghiệm Thu)

## Mọi task
- [ ] Mã nguồn nằm đúng thư mục/module và không làm phát sinh file thừa ngoài phạm vi yêu cầu.
- [ ] Dữ liệu đầu vào được kiểm tra hợp lệ (validation) và xử lý ngoại lệ tập trung.
- [ ] Không phá vỡ phân quyền bảo mật, quyền sở hữu dữ liệu hoặc API hiện có.
- [ ] Backend build thành công (`mvn clean package`) nếu có thay đổi backend.
- [ ] Frontend build thành công (`npm run build`) nếu có thay đổi giao diện.
- [ ] Kiểm tra thực tế (smoke test) chạy ổn định, không có lỗi runtime.
- [ ] Tài liệu/checklist được cập nhật tương ứng nếu có thay đổi hợp đồng API hoặc tiến độ.

## API task (Backend)
- [ ] DTO và Jakarta Bean Validation đầy đủ.
- [ ] Response được bọc đúng chuẩn `ApiResponse<T>`.
- [ ] Swagger/OpenAPI phản ánh chính xác request, response và mã lỗi.
- [ ] Controller mỏng, không chứa business logic hay gọi trực tiếp Repository (phải qua Service).

## Database task
- [ ] Quan hệ schema, chỉ mục (index), tính duy nhất (uniqueness) và ràng buộc khóa ngoại đã được kiểm tra kỹ.
- [ ] Script migration Flyway chạy thành công trên cơ sở dữ liệu sạch (`mvn flyway:info`).
- [ ] Dữ liệu seed chạy tốt và không sinh dữ liệu mâu thuẫn.
- [ ] Thao tác ghi nhiều bảng sử dụng `@Transactional`.

## Recommendation task (AI)
- [ ] Thuộc tính máy ảnh (Camera specs) và sự kiện hành vi có nguồn dữ liệu chuẩn hóa, khớp với Database.
- [ ] Có thuật toán lọc ràng buộc (Constraint filtering) loại bỏ sản phẩm hết hàng hoặc vượt ngân sách.
- [ ] Có giải thích lý do gợi ý tự động (Explainable reasons).
- [ ] Có cơ chế Fallback xử lý trường hợp người dùng mới (Cold-start).
- [ ] Có chỉ số đánh giá offline (Precision@K, Recall@K, Coverage) trước khi xuất bản model artifact mới.

## Phase completion (Nghiệm thu phase)
- [ ] Đạt toàn bộ tiêu chí Exit Gate tương ứng trong `docs/checklist.md`.
- [ ] Có bằng chứng rõ ràng (lệnh build pass, API trả về đúng kết quả, luồng UI hoạt động mượt mà).
