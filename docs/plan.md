# Kế hoạch & Định hướng Dự án Camera Store

Dự án được triển khai theo chiến lược **Vertical Slice**. Mỗi phase bắt buộc phải hoàn thiện trọn vẹn từ `Database/Schema -> Spring Boot API -> React UI -> Smoke Test` và đạt Exit Gate trước khi mở rộng sang phase tiếp theo.

> ⚠️ **TÔN CHỈ DỰ ÁN:** **Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)** là TRỌNG TÂM DUY NHẤT của đồ án. Giao diện E-commerce chỉ đóng vai trò nền tảng tối thiểu để thu thập dữ liệu và demo luồng tư vấn.

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
│   ├── PROJECT_STATUS_AND_ROADMAP.md # [Source of Truth Bổ Sung] Báo cáo lộ trình trọng tâm AI
│   ├── constitution.md         # [Source of Truth 1] Nguyên tắc kiến trúc cố định
│   ├── decisions.md            # [Source of Truth 2] Nhật ký quyết định kiến trúc (ADRs)
│   ├── architecture.md         # [Source of Truth 3] Tổng quan kiến trúc & sơ đồ phụ thuộc
│   ├── coding-style.md         # [Source of Truth 4] Quy chuẩn viết code Backend/Frontend/AI
│   ├── workflow.md             # [Source of Truth 5] Quy trình phát triển (Phase Gates)
│   ├── checklist.md            # [Source of Truth 6] Tiến độ thực thi chi tiết
│   ├── plan.md                 # Kế hoạch tổng thể chia Phase (File này)
│   ├── overview.md             # Mục tiêu sản phẩm & bài toán E-commerce + AI Recommendation
│   ├── setup.md                # Hướng dẫn cài đặt môi trường dev local
│   ├── done.md                 # Nhật ký công việc đã hoàn thành
│   └── lessons.md              # Bài học kinh nghiệm & lưu ý debug
│
├── backend/                    # SPRING BOOT MODULAR MONOLITH (JAVA 21)
│   ├── pom.xml                 # Maven dependencies (Spring Boot 3.4.5, JPA, Flyway, Postgres, JWT, Validation, OpenAPI)
│   ├── Dockerfile              # Container image cho backend
│   └── src/main/java/com/camerastore/
│       ├── config/             # Cấu hình chung (Security, Cors, OpenAPI/Swagger, Redis)
│       ├── common/             # Exceptions, DTO response chuẩn (ApiResponse<T>), Utils
│       └── modules/            # CÁC DOMAIN BUSINESS NẰM TRONG CÁC PACKAGE ĐỘC LẬP
│           ├── auth/           # Login, Register, JWT token management, Security Guards
│           ├── users/          # User profile, Address management, Role management
│           ├── products/       # Catalog, Category, Brand, Product Variant, Camera Specifications
│           ├── cart/           # Shopping Cart, CartItems management (Tối giản)
│           ├── userbehavior/   # Tracking behavior events (VIEW, ADD_TO_CART)
│           └── recommendations/# CORE AI MODULE: Recommendation Service (Content-based, Constraint filtering, Explainable reasons)
│       └── resources/
│           ├── application.yml # Backend configuration
│           └── db/migration/   # Flyway SQL migration scripts (V1__, V2__...)
│
├── frontend/                   # REACT + VITE + TYPESCRIPT SPA
│   ├── package.json            # Node dependencies (React 19, Vite 6, TypeScript, TanStack Query)
│   ├── vite.config.ts          # Vite build & proxy settings
│   └── src/
│       ├── components/         # Shared UI components (Layouts, Navbar, Footer, Buttons, Cards, Modals)
│       ├── pages/
│       │   ├── storefront/     # Customer Pages (Home, Catalog, ProductDetail, Recommendations, Profile)
│       │   └── admin/          # Admin Pages (Recommendation Metrics Dashboard, Catalog Manage)
│       ├── services/           # Axios API Client calls & TanStack Query hooks
│       ├── types/              # TypeScript interfaces/types chuẩn hóa từ Swagger API contract
│       └── utils/              # Helper functions (Currency formatter, Date parser, Storage)
│
└── ai/                         # PYTHON RECOMMENDATION PIPELINE (OFFLINE/BATCH)
    └── recommendation/
        ├── data/               # Raw dataset & Processed feature matrix
        ├── models/             # Exported model artifacts (.pkl, .json)
        ├── scripts/
        │   ├── prepare_data.py # Trích xuất & làm sạch camera specs, user behavior
        │   ├── train.py        # Feature engineering (TF-IDF, MinMax Scaler) & Cosine similarity calculation
        │   └── evaluate.py     # Offline evaluation (Precision@K, Recall@K, Hit Rate@K, Coverage, Latency)
        └── README.md           # Hướng dẫn chạy pipeline Python & định dạng artifact xuất cho Spring Boot
```

---

## 2. Phương thức Thực thi (Vertical Slice)

- **Mỗi slice gồm 5 bước**:
  1. Contract / DB Schema & Flyway Migration.
  2. Backend DTO (`ApiResponse<T>`), Entity, Service, Controller & Swagger annotation.
  3. Frontend Route, State Handlers (Loading, Empty, Error, Success).
  4. Seed / Demo Data & API Integration.
  5. Focused Testing & Check Exit Gate Evidence.
- **Không polish UI E-commerce rườm rà** làm lệch tiến độ phần AI Recommendation.

---

## 3. Phân Chia Phase Chi Tiết (Grouped Phases Roadmap)

### 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (Phải có để thu thập dữ liệu & hiển thị)

| Phase | Mục tiêu chính | Đầu ra chính | Trạng thái |
|---|---|---|:---:|
| **Phase 0** | Baseline Setup | Schema, Docker Compose, Spring Boot & React Skeleton | **DONE** |
| **Phase 1** | Shell, Global Error & Design System | Router, GlobalExceptionHandler, ApiResponse<T>, Swagger, UI Shell | **ACTIVE** |
| **Phase 2** | Catalog & Camera Specs | API Product/Specs, Filter/Search, Detail Page với thông số máy ảnh | BLOCKED |
| **Phase 3** | Auth & User Identity | Login, Register, JWT Auth, User Context | BLOCKED |
| **Phase 4** | Behavior Tracking | Tracking `VIEW` & `ADD_TO_CART`, Giỏ hàng tối giản | BLOCKED |

### 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (AI RECOMMENDATION CORE - DỒN 60-70% SỨC CỰC)

| Phase | Mục tiêu chính | Đầu ra chính | Trạng thái |
|---|---|---|:---:|
| **Phase 5** | AI Recommendation Core (Constraint + Explainable + Content) | Content-based TF-IDF/Cosine, Constraint filtering (Ngân sách, Ngàm lens, Loại máy), Explainable reasons ("Phù hợp chụp chân dung...") | BLOCKED |
| **Phase 6** | Hybrid & Behavior Integration | Kết hợp dữ liệu lịch sử `user_behaviors` vào mô hình gợi ý cá nhân hóa | BLOCKED |
| **Phase 7** | Offline Evaluation & Admin Metrics Dashboard | Đánh giá Offline (Precision@K, Recall@K, Coverage) & Dashboard đo lường CTR | BLOCKED |
| **Phase 8** | Release, Demo & Báo cáo Đồ án | Smoke test toàn hệ thống, Kịch bản Demo bài toán tư vấn, Báo cáo đồ án | BLOCKED |

### 🎁 PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE)
- Checkout & Order Management đầy đủ.
- Admin CRUD Quản lý sản phẩm nâng cao.
- Coupon & Bundles.

---

## 4. Chi tiết Exit Gate Các Phase

- **Phase 0 Exit Gate (DONE)**: Migration chạy sạch, PostgreSQL & Redis container hoạt động, Swagger contract sẵn sàng.
- **Phase 1 Exit Gate**: Backend & Frontend build pass, Router mượt mà, `GlobalExceptionHandler` format lỗi chuẩn.
- **Phase 2 Exit Gate**: Hiển thị danh sách và chi tiết máy ảnh kèm đầy đủ bộ Camera Specs phục vụ AI.
- **Phase 3 Exit Gate**: Đăng nhập/Đăng ký thành công, JWT token bảo vệ đúng endpoint.
- **Phase 4 Exit Gate**: Sự kiện `VIEW` và `ADD_TO_CART` được ghi lại chuẩn xác vào Database Postgres.
- **Phase 5 Exit Gate (RẤT QUAN TRỌNG)**: API tư vấn gợi ý trả về danh sách sản phẩm tuân thủ ràng buộc (Constraint: budget, lens mount) và có lý do giải thích sinh tự động (Explainable reasons).
- **Phase 6 Exit Gate**: User có lịch sử xem máy ảnh DSLR nhận danh sách gợi ý cá nhân hóa tương ứng.
- **Phase 7 Exit Gate**: Có báo cáo metric offline (Precision@K, Recall@K...) + Dashboard đo lường CTR cho Admin.
- **Phase 8 Exit Gate**: Demo bài toán tư vấn gợi ý thành công từ DB sạch, sẵn sàng nộp và bảo vệ đồ án.
