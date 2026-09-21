# Camera Store Project Overview

## Mục tiêu sản phẩm
Xây dựng một hệ thống thương mại điện tử chuyên biệt về thiết bị nhiếp ảnh (máy ảnh, ống kính, phụ kiện) tích hợp **Hệ Thống Gợi Ý & Tư Vấn Cá Nhân Hóa (Recommendation System)**.

## Định vị trọng tâm
Khác với các website e-commerce thông thường:
1. **Recommendation System là TRỌNG TÂM HỌC THUẬT CỐT LÕI (chiếm 60-70% nỗ lực)**:
   - Thuật toán Content-based filtering phân tích sâu thông số kỹ thuật máy ảnh (Camera Specs: cảm biến, ngàm lens, megapixel, video, trọng lượng).
   - Lọc ràng buộc khắt khe (Constraint Filtering: ngân sách, tương thích ngàm lens, tình trạng tồn kho, mục đích sử dụng).
   - Sinh lý do gợi ý tự động, minh bạch bằng ngôn ngữ tự nhiên (Explainable Recommendations).
   - Tích hợp dữ liệu hành vi người dùng (`VIEW`, `ADD_TO_CART`) để nâng cấp mô hình Hybrid.
   - Đánh giá chất lượng mô hình offline bằng các chỉ số toán học: Precision@K, Recall@K, Hit Rate@K, Coverage.
2. **E-commerce đóng vai trò NỀN TẢNG TỐI THIỂU**:
   - Cung cấp giao diện duyệt sản phẩm, xem chi tiết và giỏ hàng để thu thập dữ liệu hành vi người dùng thực tế và làm môi trường demo sống động cho hệ thống gợi ý AI.

## Công nghệ sử dụng
- **Frontend**: React 19, Vite 6, TypeScript, TanStack Query, Vanilla CSS (Design System phẳng, thực tế).
- **Backend**: Spring Boot 3.4.5, Java 21, REST API, Swagger OpenAPI 3, Spring Security, JWT.
- **Database & Cache**: PostgreSQL 17 (dữ liệu quan hệ chính), Redis 7 (cache kết quả tính toán recommendation).
- **AI Recommendation**: Python 3.11, Pandas, NumPy, Scikit-learn (TF-IDF, Cosine Similarity, Constraint rules).
- **Hạ tầng**: Docker Compose quản lý PostgreSQL và Redis local.

## Kiến trúc hệ thống
Sử dụng kiến trúc **Modular Monolith**. Toàn bộ logic nghiệp vụ backend nằm trong các package riêng biệt của một ứng dụng Spring Boot duy nhất, kết nối một cơ sở dữ liệu PostgreSQL duy nhất. Không phân chia microservices phức tạp để đảm bảo tính ổn định, dễ bảo trì và dễ demo.
