# AGENTS.md

## Role
Bạn là AI assistant cho Camera Store - một dự án đồ án thương mại điện tử chuyên về máy ảnh, tích hợp hệ thống tư vấn & gợi ý cá nhân hóa (Recommendation System). Trọng tâm đồ án là Recommendation System. Sử dụng kiến trúc Modular Monolith với Spring Boot 3, JPA/Hibernate + Flyway, PostgreSQL 17 và React 19.

## Commands
- Backend dev: `cd backend && mvn spring-boot:run` (Port: 8080)
- Frontend dev: `cd frontend && npm run dev` (Port: 5173)
- Migration: Flyway tự động chạy khi Spring Boot khởi động; kiểm tra: `cd backend && mvn flyway:info`
- Backend build: `cd backend && mvn clean package`
- Frontend build: `cd frontend && npm run build`

## Source of Truth (Thứ tự ưu tiên khi có mâu thuẫn thông tin)
1. `docs/FOUNDATION_BASELINE.md` – Bản móng kỹ thuật & ranh giới 3 thành viên
2. `docs/PROJECT_STATUS_AND_ROADMAP.md` – Lộ trình trọng tâm AI & phân nhóm A/B
3. `docs/constitution.md` – Nguyên tắc kiến trúc bất biến
4. `docs/decisions.md` – Quyết định kiến trúc đã được chấp nhận (ADRs)
5. `docs/architecture.md` – Kiến trúc tổng thể và ranh giới module
6. `docs/coding-style.md` – Quy tắc code chuẩn
7. `docs/plan.md` – Kế hoạch phase
8. `docs/checklist.md` – Danh sách kiểm tra tiến độ

## Scope & Constraints
- Đồ án tập trung vào hệ thống tư vấn gợi ý thiết bị nhiếp ảnh (Content-based, Constraint filtering, Explainable reasons).
- Giao diện E-commerce chỉ là nền tảng tối thiểu để hiển thị và thu thập hành vi (`user_behaviors`).
- Ưu tiên giải pháp đơn giản, dễ bảo trì, dễ demo.
- Không giới thiệu các mẫu kiến trúc phức tạp (Microservices, CQRS, Event Sourcing, DDD đầy đủ, Hexagonal).
- Tránh tạo abstraction không cần thiết.

## AI Skills
- Implement feature: tham khảo `.ai/skills/implement-feature/SKILL.md`
- Review code / fix bug: tham khảo `.ai/skills/review-code/SKILL.md`

## Workflow
Thực hiện theo chiến lược Vertical Slice: `DB Migration -> Spring Boot API -> React UI -> Smoke Test`.

## API Reference
Swagger/OpenAPI tại `http://localhost:8080/swagger-ui.html` là nguồn sự thật duy nhất cho API contracts. Mọi response đều bọc trong `ApiResponse<T>`.
