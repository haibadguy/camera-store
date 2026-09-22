# GVHD Roadmap

> Source of truth: Mail ngày 22/09/2026.  
> Ưu tiên hoàn thành nội dung 1–5 sớm nhất có thể, mục tiêu rong 1 tuần.  
> Nếu có vướng mắc kỹ thuật hoặc dữ liệu, sử dụng tuần thứ 2 làm thời gian dự phòng.

## Giai đoạn hiện tại: Nội dung 1–5

### 1. Xây dựng Pipeline tổng quát
Xây dựng luồng xử lý tổng thể của bài toán tư vấn dựa trên:
- Ràng buộc tương thích
- Khả năng giải thích được

### 2. Thu thập, làm sạch & lọc dữ liệu
- Tải Amazon Reviews: Camera and Photo hoặc Electronics.
- Lọc k-core với k = 5 hoặc k = 10.
- Thu thập thông số kỹ thuật Camera/Lens từ các nguồn public.
- Chia dữ liệu theo Time-aware Split / Leave-one-out.

Output:
- `train.txt`
- `val.txt`
- `test.txt`

### 3. Entity Linking & Ma trận Ràng buộc Cứng
- Khớp sản phẩm Amazon với bảng thông số kỹ thuật bằng Sentence-Transformers + Regex.
- Xây dựng Mount Mapping Table.
- Tạo ma trận nhị phân tương thích và lưu dạng Sparse Matrix.

Output:
- `compatibility_matrix.npz`
- Thống kê số cặp tương thích / không tương thích.

### 4. Xây dựng Knowledge Graph
Xây dựng đồ thị tri thức `G = (V, E, R)`.

Thực thể gồm:
- User
- Product: Body, Lens, Tripod...
- Thuộc tính kỹ thuật
- Mục đích sử dụng

Quan hệ gồm:
- `interacted_with`
- `has_spec`
- `compatible_with`
- `requires_adapter`
- `crops_sensor`

Output:
- Knowledge Graph dưới dạng DGL hoặc PyTorch Geometric.

### 5. Chạy Baseline
Chạy và ghi nhận ít nhất 3 baseline:
- LightGCN
- KGAT hoặc RGCN
- Rule-based / Popularity

Metrics:
- NDCG@K
- Recall@K
- Hit@K

Với:
- K = 5, 10, 20

Output:
- Bảng benchmark ban đầu bằng Excel hoặc Markdown.

---

## Giai đoạn sau: Nội dung 6–10

6. Constraint Module  
7. Bundle / Complementary Recommendation  
8. Explainability Engine  
9. Benchmark, Ablation Study & User Study  
10. Demo Web/App & dữ liệu thực tế

---

## Yêu cầu của GVHD

Trong quá trình thực hiện:
- Viết rõ pipeline xử lý.
- Mô tả chi tiết từng khối.
- Có công thức.
- Có ví dụ minh họa từng bước.
- Có demo.
- Đẩy các version lên GitHub.
- Làm tới đâu phải hiểu và chỉn chu tới đó.
- Không lạm dụng AI mà không hiểu.
- Kết quả làm tới đâu đưa dần vào báo cáo tới đó.