# Coding Style

## Nguyên tắc chung
- Dùng `camelCase` cho biến và phương thức.
- Dùng `PascalCase` cho class, component, và model.
- Dùng `kebab-case` cho tên thư mục và file (trừ khi framework yêu cầu khác).

## Xử lý lỗi
- Ưu tiên domain-specific exceptions thay vì generic `Error`.
- Validate input ở tầng DTO bằng Jakarta Bean Validation trước khi vào service.
- Bắt lỗi tập trung tại `GlobalExceptionHandler`, không nuốt ngoại lệ mà không xử lý.

## Tổ chức module (Backend Spring Boot)
- Mỗi module có thư mục riêng dưới `backend/src/main/java/com/camerastore/modules/`.
- Phân định rõ: `controllers`, `services`, `dto`, `entities`, `repositories`.
- Không truy cập database trực tiếp từ controller – luôn qua service.
- Controller luôn trả về response bọc trong `ApiResponse<T>`.

## Logging
- Dùng logger chuẩn của framework (SLF4J/Logback).
- Log ở mức INFO cho các hoạt động bình thường, ERROR cho ngoại lệ.
- Tuyệt đối không log password, token, hoặc thông tin cá nhân nhạy cảm.

## Database & Persistence
- Dùng Spring Data JPA repository để truy vấn.
- Mọi thay đổi schema bảng bắt buộc phải tạo file Flyway migration mới trong `db/migration/`.
- Với các thao tác ghi nhiều bảng, sử dụng `@Transactional`.

## Module và phụ thuộc
- Tránh vòng lặp import (circular dependency).
- Tách logic dùng chung vào module `common`.

## Anti-patterns cần tránh
- ❌ Truy cập repository trực tiếp trong Controller khi có business logic.
- ❌ Import vòng tròn giữa các service.
- ❌ Ném ngoại lệ chung chung (generic `RuntimeException` không rõ lý do).
- ❌ DTO chứa logic nghiệp vụ.
- ❌ Controller quá dày (nên mỏng, chỉ nhận request, validate và gọi service).
