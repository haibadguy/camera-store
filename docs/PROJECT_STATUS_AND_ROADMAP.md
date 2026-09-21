# 🎯 BÁO CÁO TRẠNG THÁI & LỘ TRÌNH THỰC THI DỰ ÁN (PROJECT STATUS & MASTER ROADMAP)

> **Tên dự án:** Camera Store — Monolithic E-Commerce Platform & AI Recommendation System  
> **Mục tiêu tài liệu:** Cung cấp bức tranh toàn cảnh về hiện trạng dự án, kiến trúc, quy tắc phát triển và lộ trình các bước chi tiết để bất kỳ bên thứ 3 (AI assistant/code reviewer) đọc vào đều nắm được chính xác định hướng, tránh đi chệch hướng làm lãng phí thời gian.

---

## 1. 📍 TỔNG QUAN HIỆN TRẠNG DỰ ÁN (CURRENT STATE)

### 1.1. Công nghệ & Hạ tầng (Tech Stack)
- **Backend:** Java 21, Spring Boot 3.4.5 (Modular Monolith), Spring Data JPA, Flyway (Database Migration), Spring Security + JWT, Validation, OpenAPI/Swagger.
- **Frontend:** React 19, TypeScript 5.8, Vite 6, Vanilla CSS (Design System tùy chỉnh, không dùng framework nặng), TanStack Query (React Query).
- **Database & Cache:** PostgreSQL 17 (Cơ sở dữ liệu chính), Redis 7 (Cache kết quả gợi ý AI).
- **Recommendation Engine (AI):** Python 3.11+, Scikit-Learn, Pandas, NumPy (Huấn luyện offline: Content-based filtering qua TF-IDF & Cosine Similarity trên thuộc tính máy ảnh + Behavior user).
- **DevOps & Environment:** Docker Compose (Quản lý PostgreSQL và Redis ở môi trường local).

### 1.2. Những gì ĐÃ HOÀN THÀNH (Done Baseline)
- [x] **Tài liệu dự án đầy đủ (`docs/`):**
  - `AGENTS.md` & `docs/constitution.md`: Nguyên tắc kiến trúc cố định.
  - `docs/architecture.md`: Sơ đồ module và luồng dữ liệu.
  - `docs/coding-style.md`: Quy chuẩn viết code Backend, Frontend & AI.
  - `docs/setup.md`: Hướng dẫn chạy máy local.
  - `docs/plan.md` & `docs/checklist.md`: Kế hoạch và danh sách task từng phase.
- [x] **Khung Backend (Spring Boot Skeleton):**
  - Cấu trúc module rõ ràng (`config/`, `common/`, `modules/`).
  - Cấu hình Flyway migration khởi tạo (`V1__create_products.sql`).
  - File cấu hình `application.yml` kết nối PostgreSQL & Flyway.
- [x] **Khung Frontend (React + Vite Skeleton):**
  - Cài đặt xong `node_modules`, thiết lập cấu hình TypeScript & Vite.
  - Khởi tạo `App.tsx` và hệ thống style `styles.css`.
- [x] **Hạ tầng Docker Local:**
  - File `docker-compose.yml` định nghĩa dịch vụ PostgreSQL 17 và Redis 7.
  - Đã chạy thực nghiệm và kiểm tra kết nối thành công.

---

## 2. 🛡️ CÁC NGUYÊN TẮC VÀNG TRÁNH LỆCH ĐỊNH HƯỚNG (CONSTRAINTS & RULES)

Để tránh lãng phí thời gian vào các abstractions hoặc tái cấu trúc không cần thiết, **BÊN THỨ 3 / AI KHÁC BẮT BUỘC PHẢI TUÂN THỦ:**

1. **Chiến lược Vertical Slice:** Làm xong trọn vẹn từng Phase theo luồng: `DB Schema/Migration -> Spring Boot API -> React UI -> Smoke Test` rồi mới chuyển sang Phase tiếp theo. Không phát triển tràn lan UI hay API riêng lẻ.
2. **Ưu tiên sự đơn giản (KISS & DRY):** Không áp dụng Microservices, CQRS, Event Sourcing, DDD phức tạp hay các lớp abstraction chồng chất (Over-engineering). Đây là đồ án E-commerce kết hợp AI Recommendation, trọng tâm nằm ở tính hoàn chỉnh của luồng nghiệp vụ và mô hình Gợi ý.
3. **Nguồn sự thật duy nhất (Source of Truth):**
   - Tài liệu SRS: `Camera Store — Complete Project Specification.md`
   - Kiến trúc cố định: `docs/constitution.md` & `docs/decisions.md`
   - API contract: Kiểm tra Swagger OpenAPI tại Backend (`http://localhost:8080/swagger-ui.html`).
4. **Validation & Kiểm tra nghiêm ngặt:** Giá sản phẩm, tồn kho và tính toán đơn hàng BẮT BUỘC thực hiện ở Server. Không tin tưởng dữ liệu gửi từ Client.

---

## 3. 🚀 LỘ TRÌNH PHÁT TRIỂN CHI TIẾT THEO TỪNG PHASE (MASTER ROADMAP)

Dự án được chia làm **9 Phase (từ Phase 0 đến Phase 8)**. Hiện tại đang hoàn thành **Phase 0**.

```
[Phase 0: Baseline] ✅ -> [Phase 1: Shell & System] ⏳ -> [Phase 2: Catalog Slice] 
                     -> [Phase 3: Auth & Identity] -> [Phase 4: Engagement & Cart] 
                     -> [Phase 5: Commerce Order]  -> [Phase 6: AI Recommendation] 
                     -> [Phase 7: Admin & Metrics]  -> [Phase 8: Polish & Release]
```

### 🔹 Phase 1: Foundation, Global Handler & Design System (ĐANG THỰC HIỆN)
- **Mục tiêu:** Dựng khung xử lý lỗi toàn cục, chuẩn hóa API DTO, Routing frontend và giao diện vỏ (Shell Layout).
- **Tasks Backend:**
  - Xây dựng `GlobalExceptionHandler`, DTO response chuẩn (`ApiResponse<T>`).
  - Cấu hình Spring Security baseline (Cors, Cross-Site, Permitting public endpoints).
  - Cấu hình Swagger OpenAPI documentation.
- **Tasks Frontend:**
  - Xây dựng React Router (`/`, `/catalog`, `/product/:id`, `/cart`, `/checkout`, `/login`, `/admin`).
  - Thiết lập Layout Storefront (Header, Navigation, Footer, Mobile Menu) và Layout Admin.
  - Xây dựng các Shared UI Component (Button, Card, Input, Modal, Badge, Loading Spinner, Empty State).
- **Exit Gate Phase 1:** Build Backend/Frontend thành công, router hoạt động mượt mà.

### 🔹 Phase 2: Catalog Vertical Slice (Danh mục máy ảnh & Specs)
- **Mục tiêu:** Cho phép khách hàng duyệt, tìm kiếm, lọc và xem chi tiết sản phẩm máy ảnh kèm thông số kỹ thuật (Specs).
- **Tasks Backend:**
  - Flyway migration cho `categories`, `brands`, `products`, `product_variants`, `camera_specifications`.
  - API query danh sách sản phẩm (Phân trang, Lọc theo hãng, loại máy ảnh, khoảng giá, sắp xếp).
  - API chi tiết sản phẩm kèm theo thông số chi tiết (Cảm biến, ISO, độ phân giải, ngàm ống kính...).
- **Tasks Frontend:**
  - Trang **Catalog Grid**: Bộ lọc Sidebar, tìm kiếm real-time, thanh sắp xếp, phân trang.
  - Trang **Product Detail**: Carousel ảnh máy ảnh, chọn biến thể (Variant/Màu sắc/Bộ nhớ), hiển thị thông số camera specs, tình trạng còn hàng.
- **Exit Gate Phase 2:** Khách hàng (Guest) thực hiện trọn vẹn luồng: *Trang chủ -> Xem Catalog -> Lọc/Tìm kiếm -> Xem Chi tiết máy ảnh*.

### 🔹 Phase 3: Identity & Customer Account (Xác thực & Tài khoản)
- **Mục tiêu:** Quản lý đăng ký, đăng nhập, bảo mật JWT và thông tin người dùng.
- **Tasks Backend:**
  - Bảng `users`, `addresses`, `roles` (ADMIN, CUSTOMER).
  - Service Hash mật khẩu (BCrypt), Đăng ký, Đăng nhập xuất JWT Access Token.
  - Spring Security Guard (Phân quyền API cho Customer và Admin).
  - API quản lý Profile và Danh sách địa chỉ giao hàng.
- **Tasks Frontend:**
  - Giao diện Modal/Trang Đăng nhập, Đăng ký (Validate form client-side).
  - Auth Store / Context lưu trữ JWT và thông tin User đăng nhập.
  - Trang Quản lý tài khoản & Danh sách địa chỉ.
- **Exit Gate Phase 3:** User đăng nhập nhận token thành công; Admin API bị chặn nếu dùng tài khoản Customer.

### 🔹 Phase 4: Engagement & User Behavior Tracking (Giỏ hàng, Wishlist, Đánh giá, Tracking)
- **Mục tiêu:** Cho phép khách hàng thêm giỏ hàng, lưu yêu thích, đánh giá và **ghi lại lịch sử hành vi (User Behavior Tracking)** phục vụ AI.
- **Tasks Backend:**
  - API Giỏ hàng (`cart`, `cart_items`): Thêm, sửa số lượng, xóa, xóa sạch.
  - API Wishlist (`wishlist`): Thêm/Xóa sản phẩm yêu thích.
  - API Review (`reviews`): Đánh giá sao, bình luận (Ràng buộc: Chỉ người đã mua mới được review).
  - **Behavior Tracking Module:** Ghi nhận sự kiện `user_behaviors` (`VIEW`, `ADD_TO_CART`, `WISHLIST`, `PURCHASE`).
- **Tasks Frontend:**
  - Mini Cart Sidebar & Trang chi tiết Giỏ hàng.
  - Nút thả tim (Wishlist) trên Card sản phẩm.
  - Form gửi Đánh giá trên trang Chi tiết sản phẩm.
  - Tự động gọi API tracking khi người dùng xem sản phẩm hoặc bấm thêm giỏ hàng.
- **Exit Gate Phase 4:** Mọi hành vi `VIEW`, `ADD_TO_CART` đều lưu chính xác vào Database Postgres.

### 🔹 Phase 5: Commerce & Order Operations (Thanh toán & Đơn hàng)
- **Mục tiêu:** Luồng Đặt hàng (Checkout), trừ kho transactional và quản lý đơn hàng.
- **Tasks Backend:**
  - Bảng `orders`, `order_items`, `shipments`.
  - Service Checkout sử dụng `@Transactional`: Kiểm tra kho khả dụng -> Khởi tạo Đơn hàng -> Trừ kho tương ứng -> Ghi sự kiện `PURCHASE` -> Xóa giỏ hàng.
  - API xem Lịch sử đơn hàng của Customer & API Cập nhật trạng thái đơn hàng của Admin.
- **Tasks Frontend:**
  - Trang Checkout: Chọn địa chỉ, chọn phương thức thanh toán giả lập (COD / Banking QR), tóm tắt đơn hàng.
  - Trang Thông báo Đặt hàng thành công & Trang Lịch sử đơn hàng.
- **Exit Gate Phase 5:** Đặt hàng thành công, kho trừ chuẩn xác, không bị race-condition hay oversell.

### 🔹 Phase 6: AI Recommendation Engine (Hệ thống Gợi ý Máy ảnh)
- **Mục tiêu:** Xây dựng mô hình AI gợi ý sản phẩm cá nhân hóa & tương tự dựa trên thông số máy ảnh và hành vi người dùng.
- **Tasks AI Pipeline (Python):**
  - Script trích xuất và tiền xử lý dữ liệu (`camera_specifications` + `user_behaviors`).
  - Biến đổi đặc trưng máy ảnh (TF-IDF vectorizer cho specs + MinMax Scaler cho giá/độ phân giải).
  - Tính toán Ma trận tương đồng Cosine (Cosine Similarity Matrix).
  - Đánh giá mô hình bằng chỉ số offline: **Precision@K, Recall@K, Hit Rate@K, Coverage**.
  - Xuất artifact mô hình (file `.pkl` / `.json`).
- **Tasks Backend Integration:**
  - Module `recommendations`: Đọc artifact mô hình AI.
  - API Gợi ý sản phẩm tương tự (`GET /api/v1/recommendations/similar/{productId}`).
  - API Gợi ý cá nhân hóa cho User (`GET /api/v1/recommendations/personalized`).
  - Chiến lược Cold-Start Fallback (Gợi ý máy ảnh nổi bật/bán chạy cho người dùng mới).
- **Tasks Frontend Integration:**
  - Section "Máy ảnh tương tự" ở trang Product Detail.
  - Section "Gợi ý dành riêng cho bạn" ở Trang chủ & Giỏ hàng.
- **Exit Gate Phase 6:** Test 3 kịch bản user (Mới hoàn toàn, xem nhiều máy Canon, đã mua Sony) trả về 3 danh sách gợi ý hoàn toàn khác nhau.

### 🔹 Phase 7: Admin Operations & Recommendation Metrics (Quản trị & Đo lường AI)
- **Mục tiêu:** Giao diện Quản trị viên và Dashboard đo lường hiệu quả mô hình AI.
- **Tasks Backend & Frontend:**
  - Trang Admin CRUD Sản phẩm, Danh mục, Hãng, Biến thể, Số lượng tồn kho.
  - Quản lý mã giảm giá (Coupon cơ bản).
  - **Dashboard Recommendation Metrics:** Ghi nhận và hiển thị CTR (Click-Through-Rate) của các sản phẩm được gợi ý bởi AI.
- **Exit Gate Phase 7:** Admin quản lý toàn bộ sản phẩm và theo dõi được chỉ số CTR gợi ý.

### 🔹 Phase 8: Release & Polish (Kiểm thử, Đóng gói & Báo cáo)
- **Mục tiêu:** Hoàn thiện giao diện, kiểm thử bảo mật, đóng gói Docker và chuẩn bị báo cáo/slide demo.
- **Tasks:**
  - Security Review: Kiểm tra phân quyền API, băm mật khẩu, validate dữ liệu đầu vào.
  - Polish UI: Responsive trên Mobile/Tablet, hiệu ứng loading, empty states mượt mà.
  - Kiểm thử khép kín từ Database sạch.
  - Chuẩn bị Kịch bản Demo, Slide thuyết minh và Báo cáo đồ án.
- **Exit Gate Phase 8:** Hệ thống hoạt động mượt mà, không lỗi nghiêm trọng, sẵn sàng bảo vệ đồ án.

---

## 4. 📝 HƯỚNG DẪN DÀNH CHO AI BÊN THỨ 3 (INSTRUCTIONS FOR 3RD PARTY AI)

Nếu bạn đưa file này cho bất kỳ công cụ AI nào khác (ChatGPT, Claude, Cursor, Copilot...):
1. **Hãy yêu cầu AI đọc thuộc file này** trước khi đưa ra bất kỳ lời khuyên hay đoạn code nào.
2. Yêu cầu AI kiểm tra xem task cần làm thuộc **Phase mấy** trong Lộ trình trên.
3. **Tuyệt đối không để AI tự ý thay đổi kiến trúc** (Ví dụ: đề xuất chia Microservices, cài thêm thư viện UI nặng, hoặc bỏ qua bước Flyway migration).
4. Mọi đoạn code sinh ra phải tuân thủ đúng vị trí cây thư mục đã quy định tại Phần 1.

---
*Tài liệu này được khởi tạo và lưu tại: `docs/PROJECT_STATUS_AND_ROADMAP.md`*
