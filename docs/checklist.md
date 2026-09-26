# Development Checklist

> **Trọng tâm đề tài:** **AI Recommendation System** (Tư vấn cá nhân hóa máy ảnh & thiết bị nhiếp ảnh).  
> **Phân nhóm:** Nhóm A (Nền tảng tối thiểu) -> Nhóm B (Trọng tâm AI Core) -> Nhóm C (Phần mở rộng Optional).

---

## 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (Phục vụ thu thập dữ liệu & demo AI)

### Phase 0: Contract & Baseline Lock (DONE)
- [x] Kiến trúc Spring Boot Modular Monolith, PostgreSQL, Docker Compose thống nhất
- [x] JPA entities, Flyway migrations nền tảng đã thiết lập
- [x] Tài liệu kiến trúc và quy chuẩn code đã khóa
- [x] **Gate:** Docker Compose khởi chạy PostgreSQL/Redis thành công, build baseline pass.

### Phase 1: Foundation, Global Error & Design System (ACTIVE)
- [ ] PostgreSQL & Redis chạy bằng Docker Compose
- [ ] Cấu hình `ApiResponse<T>`, `GlobalExceptionHandler` bắt lỗi toàn cục
- [ ] Cấu hình Spring Security baseline (CORS Vite, permit Swagger & public endpoints)
- [ ] Frontend setup: `apiClient.ts` (Axios), TypeScript types khớp Backend DTO
- [ ] Router frontend (`/`, `/catalog`, `/product/:id`, `/recommendations`), layout shell
- [ ] **Gate:** Backend/Frontend build pass, Swagger UI mở được tại `http://localhost:8080/swagger-ui.html`.

### Phase 2: Catalog & Camera Specifications
- [ ] Bảng `categories`, `brands`, `products`, `camera_specifications` qua Flyway
- [ ] API duyệt sản phẩm (lọc brand, category, khoảng giá, phân trang)
- [ ] API chi tiết sản phẩm kèm đầy đủ thông số kỹ thuật (Camera Specs)
- [ ] Frontend trang Catalog & trang Chi tiết máy ảnh (hiển thị bảng thông số)
- [ ] **Gate:** Khách hàng duyệt sản phẩm -> lọc/tìm kiếm -> xem chi tiết máy ảnh kèm thông số specs hoàn chỉnh.

### Phase 3: Identity & Customer Account Cơ Bản
- [ ] Bảng `users`, `roles` qua Flyway
- [ ] Đăng ký, đăng nhập, JWT authentication, mật khẩu băm BCrypt
- [ ] Frontend Modal / Form Đăng nhập, lưu JWT vào Auth State
- [ ] **Gate:** Đăng nhập thành công, nhận JWT token để định danh người dùng phục vụ cá nhân hóa.

### Phase 4: Behavior Tracking (Thu thập dữ liệu hành vi)
- [ ] Bảng `user_behaviors` ghi nhận sự kiện: `VIEW`, `ADD_TO_CART`
- [ ] API nhận sự kiện tracking từ frontend
- [ ] Frontend tự động gửi tracking event khi xem máy ảnh hoặc thêm vào giỏ
- [ ] Giỏ hàng tối giản (lưu local/session)
- [ ] **Gate:** Sự kiện `VIEW` và `ADD_TO_CART` được lưu đúng vào PostgreSQL với `user_id` hoặc `session_id`.

---

## 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (AI RECOMMENDATION CORE - DỒN 60-70% THỜI LƯỢNG)

### Phase 5: Recommendation Engine Core (Constraint + Explainable + Content-Based)
- [ ] Dataset `cameras_seed.csv` chuẩn hóa thông số specs (cảm biến, ngàm lens, megapixel, giá, nhu cầu)
- [ ] **5a. Content-Based Model:** Python script tiền xử lý, TF-IDF vectorizer trên specs, tính ma trận Cosine Similarity
- [ ] **5b. Constraint Filtering (Bắt buộc):** Lọc theo ngân sách (budget), lọc theo tương thích ngàm lens (lens mount), lọc theo tình trạng tồn kho, lọc theo mục đích chụp (chân dung, du lịch, vlog, thể thao)
- [ ] **5c. Explainable Recommendations (Bắt buộc):** Tự động sinh lý do gợi ý ("Phù hợp chụp chân dung nhờ cảm biến Full-frame 33MP", "Tương thích ngàm Canon RF", "Nằm trong ngân sách 50 triệu")
- [ ] Xuất artifact mô hình (`similarity_matrix.json`) sang `ai/recommendation/models/`
- [ ] Backend `RecommendationService` đọc artifact offline, nạp cache Redis và cung cấp API tư vấn
- [ ] Frontend tích hợp giao diện Trợ Lý Tư Vấn AI (Wizard chọn nhu cầu/ngân sách -> hiển thị kết quả kèm lý do)
- [ ] **Gate:** API tư vấn trả về danh sách gợi ý tuân thủ đúng ràng buộc (ngân sách, ngàm) và có lý do giải thích minh bạch.

### Phase 6: Hybrid & Behavior Integration
- [ ] Kết hợp dữ liệu lịch sử `user_behaviors` (`VIEW`, `ADD_TO_CART`) vào thuật toán gợi ý
- [ ] Nâng điểm trọng số cho các sản phẩm/hãng mà người dùng quan tâm gần đây
- [ ] Xử lý Cold-Start Fallback: Gợi ý máy ảnh nổi bật / bán chạy cho người dùng mới
- [ ] **Gate:** Khách hàng đã xem máy ảnh Sony sẽ nhận được danh sách gợi ý ưu tiên dòng máy Sony & Lens ngàm E tương thích.

### Phase 7: Đánh Giá Offline & Recommendation Dashboard
- [ ] Python script đánh giá mô hình offline: Ranking (NDCG@K, Recall@K, Hit@K) và Ràng buộc Ngàm (K-CVR@K, URR@K)
- [ ] Lưu log sự kiện nhấp vào gợi ý để tính toán CTR (Click-Through-Rate)
- [ ] Dashboard quản trị đơn giản hiển thị số liệu đo lường hiệu quả mô hình AI
- [ ] **Gate:** Có bảng số liệu đánh giá offline (NDCG, Recall, K-CVR@K, URR@K) và báo cáo CTR sẵn sàng đưa vào báo cáo đồ án.

### Phase 8: Polish, Demo & Báo Cáo Đồ Án
- [ ] Kiểm thử luồng tư vấn gợi ý hoàn chỉnh từ database sạch
- [ ] Chuẩn bị kịch bản demo (3 kịch bản: khách mới, khách chụp chân dung, khách quay vlog)
- [ ] Hoàn thiện Slide thuyết minh và Báo cáo đồ án (Word/PDF)
- [ ] **Gate:** Demo kịch bản gợi ý mượt mà trước hội đồng, bảo vệ đồ án thành công.

---

## 🎁 PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE - CHỈ LÀM NẾU DƯ THỜI GIAN)
- [ ] Checkout, Order Transactional, trừ kho tự động
- [ ] Lịch sử đơn hàng cá nhân
- [ ] Admin CRUD nâng cao (quản lý sản phẩm, coupon)
