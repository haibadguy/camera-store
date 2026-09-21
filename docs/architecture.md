# Architecture Notes

## Overall Architecture
Dự án sử dụng kiến trúc Modular Monolith - một ứng dụng Spring Boot duy nhất, các package tách biệt rõ ràng theo business domain.

Docker Compose là môi trường chạy và chuẩn hóa local/deployment (PostgreSQL 17, Redis 7), không phải ranh giới microservice. `backend` vẫn là một Spring Boot application/deployment duy nhất.

## Module Boundaries
- `auth`: Authentication & Authorization (Spring Security, JWT)
- `users`: User profile & account
- `products`: Catalog, categories, brands, camera specifications
- `cart`: Shopping cart tối giản
- `userbehavior`: Tracking hành vi người dùng (`VIEW`, `ADD_TO_CART`) cho recommendation
- `recommendations`: Recommendation engine (Content-based, Constraint filtering, Explainable reasons)

## Business Context
**Actors:**
- **Guest (Khách vãng lai)**: Xem danh mục, lọc theo ngân sách/thông số, nhận tư vấn AI.
- **User (Đã đăng ký)**: Lưu thông tin, theo dõi hành vi để nhận gợi ý cá nhân hóa.
- **Admin**: Quản lý sản phẩm, xem dashboard đo lường CTR và metrics recommendation.

**Core Workflows:**
1. Duyệt danh mục sản phẩm -> Xem chi tiết thông số máy ảnh (Camera Specs).
2. Sử dụng Trợ lý Tư vấn AI (Wizard 3 bước: nhu cầu, ngân sách, ngàm lens) -> Nhận danh sách gợi ý kèm lý do minh bạch.
3. Ghi nhận hành vi tương tác (`VIEW`, `ADD_TO_CART`) phục vụ thuật toán Hybrid.
4. Đánh giá mô hình offline (Precision@K, Recall@K, Coverage) và đo lường CTR trên Dashboard.

## Data Layer
- **PostgreSQL 17**: Main relational database store.
- **JPA/Hibernate + Flyway**: Persistence và migration source of truth.
- **Redis 7**: Cache layer cho ma trận tương đồng Cosine và kết quả gợi ý cá nhân hóa (TTL: 1 giờ).

## Recommendation Boundary
Logic recommendation nằm trong service/module Spring Boot riêng. Python ở `ai/recommendation/` phụ trách dataset preparation, training, offline evaluation và batch inference; không chạy như một Python microservice riêng biệt. Artifact mô hình (`similarity_matrix.json` hoặc `.pkl`) được Spring Boot đọc để phục vụ REST API.
