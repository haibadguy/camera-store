# Skill: Review Code / Fix Bug

## Khi nào sử dụng
- Đánh giá (review) một pull request hoặc đoạn mã nguồn mới.
- Khắc phục (fix) lỗi hoặc sự cố phát sinh trong hệ thống.

## Các bước thực hiện

### 1. Đọc bối cảnh
- Đọc kỹ `docs/coding-style.md` và `docs/architecture.md`.
- Nếu là bug: đọc mô tả lỗi, xác định thông báo exception và cách tái hiện.

### 2. Tiêu chuẩn Review Code
Kiểm tra các vấn đề cốt lõi:
- [ ] Có tuân thủ `docs/coding-style.md` và kiến trúc Modular Monolith không?
- [ ] Có vi phạm anti-pattern (Controller gọi thẳng Repository, logic nghiệp vụ nằm ở Controller) không?
- [ ] Controller có bọc response trong `ApiResponse<T>` không?
- [ ] DTO có đầy đủ Jakarta Bean Validation không?
- [ ] Có nguy cơ lỗi vòng lặp import (circular dependency) không?
- [ ] Nếu là tính năng gợi ý: có xử lý constraint filtering và fallback khi cold-start không?

### 3. Xử lý lỗi (Fix Bug)
- Xác định nguyên nhân gốc rễ (Root Cause).
- Sửa mã nguồn và chạy lại test để đảm bảo không phát sinh lỗi hồi quy (regression).
- Nếu là lỗi đặc biệt hoặc phức tạp: ghi chú bài học vào `docs/lessons.md`.

### 4. Sau khi hoàn thành
- Chạy `cd backend && mvn clean compile` hoặc `cd frontend && npm run build` để kiểm tra tính toàn vẹn.
- Cập nhật checklist tương ứng nếu có.
