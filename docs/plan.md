# Kế hoạch & Định hướng Dự án Camera Store

Dự án được triển khai theo chiến lược **Vertical Slice**. Mỗi phase bắt buộc phải hoàn thiện trọn vẹn từ Database/Schema -> Spring Boot API -> React UI -> Smoke Test và đạt Exit Gate trước khi mở rộng sang phase tiếp theo. Module Recommendation được chuẩn bị dữ liệu và hạ tầng từ sớm, không dồn vào cuối.

---

## 1. Định hướng Cấu trúc Toàn bộ File & Submodule trong Project

```
camera-store/
├── AGENTS.md                   # User rules & nguyên tắc phối hợp AI
├── Camera Store — Specification.md # Tài liệu yêu cầu chi tiết (SRS/BRD)
├── README.md                   # Tổng quan dự án & hướng dẫn khởi chạy nhanh
├── docker-compose.yml          # Container orchestration (PostgreSQL, Redis)
│
├── docs/                       # TÀI LIỆU HƯỚNG DẪN & NGUYÊN TẮC THIẾT KẾ
│   ├── constitution.md         # [Source of Truth 1] Nguyên tắc kiến trúc cố định
│   ├── decisions.md            # [Source of Truth 2] Nhật ký quyết định kiến trúc (ADRs)
│   ├── architecture.md         # [Source of Truth 3] Tổng quan kiến trúc & sơ đồ phụ thuộc
│   ├── coding-style.md         # [Source of Truth 4] Quy chuẩn viết code Backend/Frontend/AI
│   ├── workflow.md             # [Source of Truth 5] Quy trình phát triển (Phase Gates)
│   ├── checklist.md            # [Source of Truth 6] Tiến độ thực thi chi tiết
│   ├── plan.md                 # Kế hoạch tổng thể & Định hướng file project (File này)
│   ├── overview.md             # Mục tiêu sản phẩm & bài toán E-commerce + AI Recommendation
│   ├── setup.md                # Hướng dẫn cài đặt môi trường dev local
│   ├── done.md                 # Nhật ký công việc đã hoàn thành
│   └── lessons.md              # Bài học kinh nghiệm & lưu ý debug
│
├── backend/                    # SPRING BOOT MODULAR MONOLITH (JAVA 17+)
│   ├── pom.xml                 # Maven dependencies (Spring Boot, JPA, Flyway, Postgres, JWT, Validation, OpenAPI)
│   ├── Dockerfile              # Container image cho backend
│   └── src/main/java/com/camerastore/
│       ├── config/             # Cấu hình chung (Security, Cors, OpenAPI/Swagger, Redis)
│       ├── common/             # Exceptions, DTO response chuẩn, Utils
│       └── modules/            # CÁC DOMAIN BUSINESS NẰM TRONG CÁC PACKAGE ĐỘC LẬP
│           ├── auth/           # Login, Register, JWT token management, Security Guards
│           ├── users/          # User profile, Address management, Role management
│           ├── products/       # Catalog, Category, Brand, Product Variant, Camera Specifications
│           ├── cart/           # Shopping Cart, CartItems management
│           ├── orders/         # Checkout flow, Order, OrderItem, Transactional Inventory
│           ├── reviews/        # Product rating, Review comments
│           ├── wishlist/       # Favorite products list
│           ├── userbehavior/   # Tracking behavior events (VIEW, ADD_TO_CART, WISHLIST, PURCHASE)
│           └── recommendations/# Core Service phục vụ API gợi ý sản phẩm (Cosine similarity, Cold-start, Fallback)
│       └── resources/
│           ├── application.yml # Backend configuration
│           └── db/migration/   # Flyway SQL migration scripts (V1__, V2__...)
│
├── frontend/                   # REACT + VITE + TYPESCRIPT SPA
│   ├── package.json            # Node dependencies (React, Vite, React Router, TanStack Query, TailwindCSS)
│   ├── vite.config.ts          # Vite build & proxy settings
│   └── src/
│       ├── components/         # Shared UI components (Layouts, Navbar, Footer, Buttons, Cards, Modals)
│       ├── pages/
│       │   ├── storefront/     # Customer Pages (Home, Catalog, ProductDetail, Cart, Checkout, Wishlist, Profile)
│       │   └── admin/          # Admin Pages (Dashboard, Product Admin, Order Admin, Recommendation Metrics)
│       ├── services/           # Axios API Client calls & TanStack Query hooks
│       ├── types/              # TypeScript interfaces/types chuẩn hóa từ Swagger API contract
│       └── utils/              # Helper functions (Currency formatter, Date parser, Storage)
│
└── ai/                         # PYTHON RECOMMENDATION PIPELINE (OFFLINE/BATCH)
    └── recommendation/
        ├── data/               # Raw dataset & Processed feature matrix
        ├── models/             # Exported model artifacts & model versioning
        ├── scripts/
        │   ├── prepare_data.py # Trích xuất & làm sạch camera specs, user behavior
        │   ├── train.py        # Feature engineering (TF-IDF, MinMax Scaler) & Cosine similarity calculation
        │   └── evaluate.py     # Offline evaluation (Precision@K, Recall@K, Hit Rate@K, Coverage, Latency)
        └── README.md           # Hướng dẫn chạy pipeline Python & định dạng artifact xuất cho Spring Boot
```

---

## 2. Phương thức Thực thi

- **Mỗi slice gồm 5 bước**:
  1. Contract / DB Schema & Flyway Migration.
  2. Backend DTO, Entity, Service, Controller & Swagger annotation.
  3. Frontend Route, State Handlers (Loading, Empty, Error, Success).
  4. Seed / Demo Data & API Integration.
  5. Focused Testing & Check Exit Gate Evidence.
- **Không polish UI riêng lẻ** khi contract hoặc database backend phía sau chưa sẵn sàng.
- **Phase hiện tại được đánh dấu `ACTIVE`**; chỉ chuyển sang phase kế tiếp sau khi Exit Gate có bằng chứng (evidence) rõ ràng.

---

## 3. Tiến trình & Kế hoạch Chi tiết Các Phase

| Phase | Mục tiêu | Đầu ra chính | Ước lượng | Trạng thái |
|---|---|---|---:|:---:|
| **0** | Khóa Contract & Phục hồi Nền tảng | Schema/API decision, Seed scenarios, Build baseline | 0.5 - 1 ngày | **ACTIVE** |
| **1** | Foundation & UI Shell | Routing, Auth boundaries, Config, Error format, Storefront/Admin shell | 1 - 2 ngày | BLOCKED |
| **2** | Catalog Usable | Product Browse, Search, Filter, Detail, Camera Specs | 2 - 3 ngày | BLOCKED |
| **3** | Customer Identity | Register, Login, JWT, Profile, Address, Role Guard | 1 - 2 ngày | BLOCKED |
| **4** | Engagement Loop | Cart, Wishlist, Product Review, Behavior Tracking (`VIEW`, `ADD_TO_CART`) | 2 - 3 ngày | BLOCKED |
| **5** | Commerce Completion | Checkout transaction, Inventory update, Order management, `PURCHASE` track | 2 - 3 ngày | BLOCKED |
| **6** | Recommendation MVP | Cosine similarity model, Python offline pipeline, Cold-start, API integration | 3 - 5 ngày | BLOCKED |
| **7** | Admin & Recommendation Metrics | CRUD admin, Coupon, Dashboard đo lường CTR, Precision@K, Recall@K | 2 - 4 ngày | BLOCKED |
| **8** | Release & Hardening | Security review, Responsive polish, Docker Compose, Demo script & Report | 2 - 3 ngày | BLOCKED |

---

## 4. Trạng thái & Quyết định Hiện tại (Phase 0)

### Trạng thái
- **Phase 0: ACTIVE** — Kiến trúc Spring Boot + JPA + Flyway + PostgreSQL đã được thống nhất là runtime duy nhất.
- **Phase 1-8: BLOCKED** cho tới khi Java Backend và PostgreSQL Baseline khởi động và build thành công.

### Quyết định kỹ thuật Phase 0
1. **Nguồn sự thật runtime**: Spring Boot modular monolith + JPA/Hibernate + Flyway + PostgreSQL.
2. **Các Slice ưu tiên làm ngay trong Phase 0**:
   - Khởi tạo `backend/pom.xml`, cấu hình Java Application, Flyway Migration & `docker-compose.yml` để 1 backend duy nhất chạy được.
   - Định nghĩa Ranh giới Package/Service DTO cho Java backend.
   - Chốt API contract tiếng Việt cho Catalog trước: `GET /api/products`, `GET /api/products/{id}`, Search, Filter, Pagination và Recommendation metadata.
   - Chốt Seed scenarios: Guest, Cold-start customer, Active customer, Admin.
   - Run clean migration + seed data, kiểm tra Swagger & Frontend/Backend build.

---

## 5. Chi tiết Exit Gate Các Phase

- **Phase 0 Exit Gate**: Migration chạy sạch, Database provider PostgreSQL hoạt động, Swagger contract hoàn chỉnh, không còn code thừa mâu thuẫn.
- **Phase 1 Exit Gate**: Backend & Frontend build pass, Reset DB + Seed pass, Guest truy cập được UI shell của cả Storefront và Admin.
- **Phase 2 Exit Gate**: Guest hoàn thành flow Browse → Search/Filter → Detail; Camera specs sẵn sàng cho recommendation.
- **Phase 3 Exit Gate**: Đăng ký/Đăng nhập thành công, JWT token bảo vệ đúng route Admin, thông tin nhạy cảm không đính kèm log.
- **Phase 4 Exit Gate**: Customer Browse → View → Cart/Wishlist → Review; Behavior tracking ghi nhận đúng thông tin vào DB.
- **Phase 5 Exit Gate**: Order được xử lý nguyên tố (Transactional), không xảy ra oversell, clear cart chuẩn xác, Order History hiển thị đầy đủ.
- **Phase 6 Exit Gate**: API gợi ý sản phẩm trả kết quả tương ứng scenario user, có fallback cold-start, không trả sản phẩm ẩn/hết hàng.
- **Phase 7 Exit Gate**: Admin quản lý được dữ liệu thương mại điện tử và theo dõi chỉ số hiệu năng Recommendation (Precision@K, Recall@K, CTR).
- **Phase 8 Exit Gate**: Build thành công toàn bộ container Docker, chạy lại được demo script từ DB sạch, có báo cáo và video/bằng chứng nghiệm thu.
