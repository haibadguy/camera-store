# 🎯 BÁO CÁO TRẠNG THÁI & LỘ TRÌNH THỰC THI DỰ ÁN (PROJECT STATUS & MASTER ROADMAP)

> **Tên đề tài đồ án:** *"Xây dựng hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh (Camera Store & AI Recommendation System)"*  
> **TRỌNG TÂM ĐỒ ÁN:** **AI Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)**. Giao diện E-commerce chỉ đóng vai trò **nền tảng tối thiểu** để thu thập dữ liệu và demo luồng tư vấn.  
> **Mục tiêu tài liệu:** Cung cấp bức tranh toàn cảnh về hiện trạng dự án, kiến trúc, quy tắc phát triển và lộ trình tập trung đúng trọng tâm để bất kỳ bên thứ 3 (AI assistant/code reviewer) đọc vào đều bám sát yêu cầu của giảng viên, tránh làm tràn lan các tính năng web thương mại điện tử gây mất thời gian.

---

## 1. 📍 TỔNG QUAN HIỆN TRẠNG DỰ ÁN (CURRENT STATE)

### 1.1. Công nghệ & Hạ tầng (Tech Stack)
- **Backend:** Java 21, Spring Boot 3.4.5 (Modular Monolith), Spring Data JPA, Flyway (Database Migration), Spring Security + JWT, Validation, OpenAPI/Swagger.
- **Frontend:** React 19, TypeScript 5.8, Vite 6, Vanilla CSS (Design System tùy chỉnh, tối giản).
- **Database & Cache:** PostgreSQL 17 (Cơ sở dữ liệu chính), Redis 7 (Cache kết quả gợi ý AI).
- **Recommendation Engine (AI Core):** Python 3.11+, Scikit-Learn, Pandas, NumPy (Huấn luyện Content-based, Constraint Filtering, Hybrid & Explainable Recommendation).
- **DevOps & Environment:** Docker Compose (Chạy PostgreSQL và Redis local).

### 1.2. Những gì ĐÃ HOÀN THÀNH (Done Baseline - Phase 0)
- [x] **Tài liệu dự án đầy đủ (`docs/`):** `AGENTS.md`, `constitution.md`, `architecture.md`, `coding-style.md`, `setup.md`, `plan.md`, `checklist.md`.
- [x] **Khung Backend (Spring Boot Skeleton):** Cấu trúc module (`config/`, `common/`, `modules/`), Flyway migration khởi tạo (`V1__create_products.sql`), `application.yml`.
- [x] **Khung Frontend (React + Vite Skeleton):** `App.tsx`, `styles.css`, TypeScript & Vite config.
- [x] **Hạ tầng Docker Local:** `docker-compose.yml` khởi chạy thành công PostgreSQL 17 & Redis 7.

---

## 2. 🛡️ CÁC NGUYÊN TẮC VÀNG CHỐNG LỆCH TRỌNG TÂM (CONSTRAINTS & RULES)

1. **TRỌNG TÂM LÀ AI RECOMMENDATION SYSTEM:** E-commerce web chỉ là vỏ nền tảng để hiển thị và thu thập hành vi. Mọi quyết định kỹ thuật phải ưu tiên cho chất lượng gợi ý (Constraint filtering + Explainable reasons) hơn là phát triển quá nhiều tính năng thương mại điện tử phức tạp.
2. **Chiến lược Vertical Slice & Nhóm ưu tiên:** Hoàn thành nhanh Nhóm Nền Tảng Tối Thiểu để dành tối đa thời gian cho Nhóm Trọng Tâm AI.
3. **Không Over-Engineering:** Không chia Microservices, không dùng CQRS/Event Sourcing. Giữ vững Modular Monolith trên Spring Boot 3 + React + Python ML offline.
4. **Nguồn sự thật duy nhất:** 
   - Đề xuất đề tài gửi giảng viên hướng dẫn.
   - `docs/PROJECT_STATUS_AND_ROADMAP.md` (File này).
   - Swagger OpenAPI tại Backend (`http://localhost:8080/swagger-ui.html`).

---

## 3. 🚀 LỘ TRÌNH PHÁT TRIỂN TINH GỌN (MASTER ROADMAP)

Lộ trình được chia thành **2 Nhóm chính** và **1 Nhóm mở rộng** để đảm bảo tiến độ đồ án (10-12 tuần):

```
┌────────────────────────────────────────────────────────────────────────┐
│ NHÓM A: NỀN TẢNG TỐI THIỂU (Phải có để thu thập dữ liệu & demo AI)     │
│ Phase 0 (Done) ──> Phase 1 (Shell) ──> Phase 2 (Catalog & Specs)       │
│                ──> Phase 3 (Auth cơ bản) ──> Phase 4 (Tracking)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ NHÓM B: TRỌNG TÂM ĐỒ ÁN (Tập trung dồn sức 60-70% thời lượng)           │
│ Phase 5 (Recommendation Core: Content-Based + Constraint + Explain)   │
│ Phase 6 (Hybrid & Behavior Integration)                                │
│ Phase 7 (Offline Evaluation: Precision@K... & Dashboard Metrics CTR)   │
│ Phase 8 (Polish, Demo & Báo cáo đồ án)                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Nếu còn thừa thời gian)
┌───────────────────────────────────▼────────────────────────────────────┐
│ PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE)                                 │
│ Order / Checkout đầy đủ, Admin CRUD nâng cao, Coupon, Bundles           │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (TỐC ĐỘ CAO)

#### 🔹 Phase 1: Shell, Global Exception Handler & Design System (ĐANG THỰC HIỆN)
- **Backend:** `GlobalExceptionHandler`, wrapper `ApiResponse<T>`, Spring Security baseline (Cors, public endpoints), Swagger OpenAPI docs.
- **Frontend:** React Router (`/`, `/catalog`, `/product/:id`, `/recommendations`), Shell Layout (Header, Navigation, Footer), Bộ Shared Components cơ bản (Button, Card, Input, Modal, Badge, Spinner).
- **Exit Gate Phase 1:** Build Backend/Frontend thành công, router mượt mà.

#### 🔹 Phase 2: Catalog & Camera Specifications (Rút gọn)
- **Backend:** Schema Flyway (`categories`, `brands`, `products`, `camera_specifications`). API Query sản phẩm (Lọc theo brand, category, khoảng giá) & API Chi tiết máy ảnh kèm Camera Specs.
- **Frontend:** Trang Catalog Grid (Bộ lọc, Tìm kiếm, Sắp xếp, Phân trang) & Trang Chi tiết máy ảnh (Hiển thị đầy đủ thông số kỹ thuật cảm biến, ngàm lens, ISO...).
- **Exit Gate Phase 2:** Hiển thị danh sách và chi tiết máy ảnh kèm đầy đủ bộ Camera Specs phục vụ AI.

#### 🔹 Phase 3: Auth & Account Cơ Bản
- **Backend:** Schema `users`, `roles`. API Đăng ký, Đăng nhập (JWT), Spring Security Guard.
- **Frontend:** Modal / Trang Đăng nhập, Đăng ký. Auth Context lưu JWT.
- **Exit Gate Phase 3:** Đăng nhập thành công, lưu thông tin User ID để phục vụ gợi ý cá nhân hóa.

#### 🔹 Phase 4: Behavior Tracking (Thu thập dữ liệu hành vi)
- **Backend:** Schema `user_behaviors`. API ghi nhận sự kiện: `VIEW` (xem chi tiết) và `ADD_TO_CART` (thêm vào giỏ).
- **Frontend:** Tự động phát sự kiện tracking khi người dùng xem sản phẩm hoặc tương tác.
- **Exit Gate Phase 4:** Hành vi của user được lưu chính xác vào Database Postgres.

---

### 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (RECOMMENDATION ENGINE - DỒN SỨC CHÍNH)

#### 🔹 Phase 5: Recommendation Engine CORE (Constraint + Explainable + Content-Based)
*Đây là module quan trọng nhất của đồ án, bao gồm 3 thành phần cốt lõi:*

- **5a. Content-Based Recommendation Engine:**
  - Python Script: Biến đổi thuộc tính máy ảnh (Camera Specs) qua TF-IDF Vectorizer + Scaler.
  - Tính toán ma trận độ tương đồng Cosine (Cosine Similarity Matrix).
  - Cold-start fallback: Gợi ý sản phẩm nổi bật / bán chạy cho khách hàng mới.
- **5b. Constraint Filtering (Lọc Ràng Buộc - BẮT BUỘC):**
  - Lọc theo **Ngân sách** (Budget constraint).
  - Lọc theo **Tương thích thiết bị** (Ngàm Lens vs Thân máy camera mount compatibility).
  - Lọc theo **Tồn kho & Trạng thái kinh doanh**.
  - Lọc theo **Loại thiết bị / Nhu cầu sử dụng** (Chụp chân dung, Phượt/Du lịch, Quay vlogging).
- **5c. Explainable Recommendation (Giải Thích Lý Do Gợi Ý - BẮT BUỘC):**
  - Sinh lý do gợi ý tự động cho từng sản phẩm:
    - *"Phù hợp chụp chân dung nhờ cảm biến Full-frame và khẩu độ lớn."*
    - *"Nằm trong ngân sách 15 - 20 triệu đồng bạn lựa chọn."*
    - *"Tương thích hoàn toàn với ngàm Canon RF hiện có của bạn."*
- **Exit Gate Phase 5:** API `/api/v1/recommendations/consult` trả về danh sách gợi ý kèm lý do giải thích (Explainable Reasons) và tuân thủ đúng các ràng buộc (Constraints).

#### 🔹 Phase 6: Hybrid & Behavior Integration
- Kết hợp mô hình Content-based specs với dữ liệu lịch sử hành vi `user_behaviors` (`VIEW`, `ADD_TO_CART`).
- Cập nhật điểm trọng số (Scoring & Ranking) cho sản phẩm gợi ý dựa trên mức độ quan tâm thực tế của khách hàng.
- **Exit Gate Phase 6:** Người dùng có lịch sử xem máy ảnh DSLR sẽ nhận được danh sách gợi ý nâng cao thiên về DSLR & Lens tương thích.

#### 🔹 Phase 7: Đánh Giá Mô Hình Offline & Recommendation Metrics Dashboard
- **Đánh giá Offline (Python):** Tính toán và báo cáo các chỉ số toán học:
  - **Precision@K, Recall@K, Hit Rate@K, Coverage, Latency**.
- **Admin Metrics Dashboard (Spring Boot + React):**
  - Giao diện đo lường tỷ lệ nhấp vào gợi ý (**CTR - Click Through Rate**).
  - Thống kê hiệu quả tư vấn của hệ thống AI.
- **Exit Gate Phase 7:** Có báo cáo metric offline đầy đủ + Dashboard đo lường CTR sẵn sàng đưa vào báo cáo đồ án.

#### 🔹 Phase 8: Polish, Demo & Báo Cáo Đồ Án
- Kiểm thử toàn diện khép kín từ Database sạch.
- Chuẩn bị Kịch bản Demo chi tiết thể hiện rõ bài toán tư vấn gợi ý.
- Hoàn thiện Báo cáo đồ án (Word/PDF) và Slide thuyết minh bảo vệ trước hội đồng.
- **Exit Gate Phase 8:** Thuyết minh bảo vệ thành công đồ án với điểm số tối đa.

---

### 🎁 PHẦN MỞ RỘNG (OPTIONAL - CHỈ LÀM NẾU DƯ THỜI GIAN)
- Đơn hàng & Payment Checkout đầy đủ.
- Admin CRUD quản lý sản phẩm nâng cao.
- Mã giảm giá (Coupon), Combo sản phẩm (Bundles).

---

## 4. 📝 HƯỚNG DẪN DÀNH CHO AI BÊN THỨ 3 (INSTRUCTIONS FOR 3RD PARTY AI)

Nếu bạn đưa file này cho bất kỳ công cụ AI nào khác (ChatGPT, Claude, Cursor, Copilot...):
> ⚠️ **LƯU Ý NGHÊM NGẶT:** Trọng tâm của đồ án này là **Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)**, KHÔNG PHẢI E-commerce platform thông thường.  
> 1. Mọi đề xuất mã nguồn hay kiến trúc phải tập trung giải quyết bài toán AI Recommendation (Content-based, Constraint filtering, Explainable reasons, Offline evaluation).  
> 2. Không sa đà xây dựng các tính năng thương mại điện tử phức tạp ở Nhóm A làm lãng phí thời gian.  
> 3. Tuân thủ chiến lược Vertical Slice và cây thư mục quy định tại Phần 1.

---
*Tài liệu này được cập nhật theo đúng yêu cầu trọng tâm đồ án tại: `docs/PROJECT_STATUS_AND_ROADMAP.md`*
