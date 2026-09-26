# BÁO CÁO MỤC 2: THU THẬP, LÀM SẠCH & LỌC DỮ LIỆU TƯƠNG TÁC (DATA PREPROCESSING)

**Học phần**: Khóa luận tốt nghiệp / Đề tài Nghiên cứu Hệ thống Gợi ý Thiết bị Nhiếp ảnh  
**Tập dữ liệu nguồn**: Amazon Reviews 2023 (Tập Electronics - McAuley Lab)  
**Thời gian hoàn thành**: Tháng 09/2026  

---

## 1. Mục tiêu & Phương pháp luận

Mục 2 chịu trách nhiệm xử lý từ dữ liệu thô ban đầu thành tập tương tác sạch, phục vụ trực tiếp cho việc huấn luyện mô hình gợi ý và trích xuất tri thức:
1. **Lọc danh mục chuyên biệt (Domain-Specific Camera Filtering)**: Bóc tách chính xác các sản phẩm thuộc nhánh máy ảnh, ống kính và thiết bị quang học từ tập Electronics thô, đồng thời loại trừ triệt để các thiết bị an ninh, giám sát hoặc phụ kiện thiết bị di động.
2. **Giảm độ thưa dữ liệu (Data Sparsity Reduction)**: Áp dụng thuật toán lọc $k$-core lặp đệ quy ($k=5$) đồng thời trên cả hai trục User và Item để đảm bảo mỗi thực thể có đủ tương tác tối thiểu học biểu diễn tiềm ẩn (embeddings).
3. **Quy chuẩn đánh giá chuỗi thời gian (Time-aware Leave-One-Out Protocol)**: Phân tách chuỗi hành vi của từng người dùng theo trục thời gian thực, ngăn chặn hiện tượng rò rỉ dữ liệu (data leakage).

---

## 2. Quy trình Thực thi Kỹ thuật (Implementation Details)

### 2.1. Bộ lọc Domain Camera & Optics
Quá trình lọc dữ liệu từ tập thô Amazon Electronics được thực hiện qua kịch bản `ai/pipeline/01_filter_camera_domain.py`, kết hợp quét trên các trường `categories`, `title` và `main_category` của metadata:
- **Tiêu chí loại trừ trước (Negative Keywords)**: Tự động loại bỏ các thiết bị giám sát hoặc không thuộc thiết bị nhiếp ảnh chuyên dụng:  
  *`security & surveillance`, `surveillance cameras`, `baby monitor`, `trail camera`, `dash cam`, `hunting cameras`, `webcams`, `inspection camera`, `endoscope`, `hidden cameras`, `spy camera`*.
- **Tiêu chí chấp nhận (Positive Keywords)**: Giữ lại các danh mục máy ảnh và quang học:  
  *`camera & photo`, `digital camera`, `digital cameras`, `camera lenses`, `camera lens`, `mirrorless cameras`, `dslr cameras`, `dslr lenses`, `mirrorless lenses`, `slr lenses`, `point & shoot digital cameras`, `camera flashes`, `tripods & monopods`*.

### 2.2. Định nghĩa Tương tác (Interaction Definition) & Phân tích Duplicates
- **Implicit Feedback**: Toàn bộ đánh giá từ 1 đến 5 sao đều được ghi nhận là một tương tác hành vi (user đã mua/trải nghiệm sản phẩm). Rating đóng vai trò metadata và chưa được dùng làm trọng số preference trực tiếp. Phân bố điểm số thực tế:  
  *5 sao (67.2%), 4 sao (16.9%), 3 sao (7.3%), 2 sao (3.8%), 1 sao (4.8%)* — trong đó đánh giá tích cực ($\ge 4$ sao) chiếm **84.1%**.
- **Tương tác lặp (Duplicates) & Kiểm soát Leakage trong Split**:
  - Ghi nhận có **16,195 bản ghi (2.6%)** người dùng tương tác lại với cùng một item ở các thời điểm khác nhau.
  - **Lý do giữ nguyên duplicate**: Việc giữ nguyên các tương tác này phản ánh đúng hành vi mua lặp lại thực tế (repurchase) — đặc biệt phổ biến trong ngành hàng nhiếp ảnh đối với phụ kiện tiêu hao (pin, thẻ nhớ, kính lọc filter, giấy lau lens...).
  - **Đo lường mức độ trùng lặp giữa các tập (Overlap check)**:
    - Users có sản phẩm ở tập Validation từng xuất hiện trong tập Train: **1,290 / 70,424 users (1.83%)**.
    - Users có sản phẩm ở tập Test từng xuất hiện trong tập Train: **1,166 / 70,424 users (1.66%)**.
    - Users có sản phẩm ở tập Test trùng với tập Validation: **2,544 / 70,424 users (3.61%)**.
  - **Diễn giải học thuật**: Tỷ lệ trùng lặp Train–Val (1.83%) và Train–Test (1.66%) đều ở mức thấp (< 2%), xác nhận việc giữ nguyên duplicate không gây nhiễu đáng kể cho giao thức đánh giá. Riêng độ trùng lặp giữa Test và Val đạt 3.61% do đặc thù hai tập này lấy từ 2 vị trí liền kề cuối chuỗi của cùng một user; mức này hoàn toàn chấp nhận được vì Val và Test phục vụ hai mục đích tách biệt (tune hyperparameter vs đánh giá benchmark cuối) và không dùng chung trong cùng một lượt suy luận.

---

## 3. Kết quả Thực nghiệm & Bảng Thống kê Số liệu

### Bảng 2.1: Biến thiên Quy mô Dữ liệu qua các Bước Tiền xử lý

| Giai đoạn Xử lý | Số Lượng Users ($|\mathcal{U}|$) | Số Lượng Items Metadata ($|\mathcal{I}_{\text{meta}}|$) | Số Items có Tương tác ($|\mathcal{I}_{\text{active}}|$) | Tổng Lượt Tương tác ($|\mathcal{R}|$) | Độ thưa Sparsity (%) | Tương tác TB / User |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Snapshot Amazon Electronics (Raw)** | **18,286,191** | 1,610,012 | — | 43,886,944 | $> 99.999\%$ | 2.40 |
| **2. Sau Domain Filtering (Camera & Optics)** | ~2.1M *(ước tính)* | **253,260** | **72,775** | 4,042,112 | $99.997\%$ | 1.92 |
| **3. Sau Iterative $k$-core ($k=5$) [Chính thức]** | **70,424** | **28,867** | **28,867** | **622,997** | **99.969%** | **8.85** |

*Giải trình số liệu*:
- **Phân định rõ 253,260 vs 72,775 items**: Ở bước lọc domain metadata, có **253,260** sản phẩm camera được trích xuất từ metadata thô. Khi quét giao với bảng lịch sử đánh giá (reviews), có **72,775** sản phẩm phát sinh ít nhất 1 tương tác (các sản phẩm còn lại được niêm yết nhưng chưa có review trong snapshot). Do đó, Vòng 1 của thuật toán $k$-core nhận đúng 72,775 active items này làm đầu vào.
- **Cột Users sau Domain Filtering**: Khoảng 2.1 triệu users có ít nhất 1 tương tác với các sản phẩm Camera trước khi lọc $k$-core. Thuật toán $k$-core sau đó loại bỏ các user vãng lai (< 5 reviews), đưa tập user về trạng thái cô đọng 70,424 users.
- Độ thưa sau $k$-core đạt $99.969\%$, đặc trưng của không gian gợi ý thương mại điện tử lớn. Mỗi người dùng có tối thiểu 5 tương tác (trung vị = 7, trung bình = 8.85), thỏa mãn điều kiện cần để phân chia chuỗi thời gian và huấn luyện mô hình đồ thị.

### Bảng 2.2: Phân bố Tần suất Tương tác trên Mỗi Người Dùng (User Degree Percentiles)

| Chỉ số / Phân vị | Giá trị Tương tác / User | Ý nghĩa kỹ thuật |
| :--- | :--- | :--- |
| **Min** | **5** | Đảm bảo đúng điều kiện biên $k$-core ($k=5$) |
| **Q1 (25%)** | 5.0 | 25% người dùng ở ngưỡng tương tác tối thiểu |
| **Median (50%)** | 7.0 | Trung vị hành vi người dùng trong tập dữ liệu |
| **Mean** | 8.85 | Trung bình 8.85 tương tác / user |
| **Q3 (75%)** | 9.0 | 75% người dùng có $\le 9$ tương tác |
| **P90 (90%)** | 15.0 | Nhóm người dùng hoạt động tích cực |
| **P95 (95%)** | 20.0 | Nhóm người dùng chuyên sâu |
| **Max** | 188 | Người dùng có chuỗi tương tác dài nhất |

### Bảng 2.3: Phân loại Tập Sản phẩm Sau k-core ($|\mathcal{I}| = 28,867$)

| Nhóm danh mục | Số lượng sản phẩm | Tỷ lệ (%) | Vai trò trong hệ thống |
| :--- | :--- | :--- | :--- |
| **Thân máy (Camera Bodies)** | 1,414 | 4.9% | Tập ứng viên Thân máy ($\mathcal{B}$) trong ma trận $M$ |
| **Ống kính (Camera Lenses)** | 1,462 | 5.1% | Tập ứng viên Ống kính ($\mathcal{L}$) trong ma trận $M$ |
| **Tổng ứng viên Thân máy & Ống kính** | **2,876** | **10.0%** | Tập đối tượng cốt lõi cần Entity Linking ở Mục 3 |
| **Phụ kiện & Thiết bị hỗ trợ khác** | 25,991 | 90.0% | Đỉnh Item tương tác phụ trợ trong Đồ thị Tri thức |

---

## 4. Phân chia Tập Dữ liệu & Giao thức Đánh giá

Kịch bản `ai/pipeline/02_split_time_aware.py` phân chia chuỗi tương tác tăng dần theo thời gian $\mathcal{S}_u = ((i_1, t_1), (i_2, t_2), \dots, (i_n, t_n))$:
- **Tập Huấn luyện (Train)**: $(i_1, \dots, i_{n-2})$ gồm **482,149** tương tác (lưu tại `train.txt`, định dạng `uid item1 item2 ...`).
- **Tập Kiểm định (Validation)**: Tương tác kế cuối $(i_{n-1}, t_{n-1})$ gồm **70,424** tương tác (lưu tại `val.txt`, định dạng `uid item`).
- **Tập Thử nghiệm (Test)**: Tương tác cuối cùng $(i_n, t_n)$ gồm **70,424** tương tác (lưu tại `test.txt`, định dạng `uid item`).
- **Giao thức Đánh giá Sampled Ranking**:
  - Mỗi tương tác Val và Test được ghép với 99 negative items ngẫu nhiên từ tập $\mathcal{I} \setminus \mathcal{H}_u$ (loại trừ tuyệt đối toàn bộ item user từng tương tác trong quá khứ và tương lai).
  - Cố định `random.seed(42)` đảm bảo tính tái lập.
  - *Ghi nhận học thuật*: Giao thức $1 \text{ positive} + 99 \text{ negatives}$ tương thích với chuẩn thực nghiệm phổ biến (RecBole/Elliot). Nhóm ghi nhận hạn chế đã được phân tích bởi Krichene & Rendle (2020) để thận trọng khi diễn giải kết quả so sánh giữa các baseline ở Mục 5.

---

## 5. Dữ liệu Thông số Kỹ thuật Chuẩn (Specs) & Đánh giá Sơ bộ cho Mục 3

- **Tập Specs hạt nhân (`camera_lens_specs.csv`)**: Đã chuẩn hóa 60 dòng thông số kỹ thuật chuẩn cho các dòng thiết bị tiêu biểu:
  - **Nguồn trích xuất**: Thu thập từ Kaggle và đối chiếu đặc tả ngàm/cảm biến trên Wikidata (thực hiện tháng 09/2026).
  - **25 Thân máy (Body)**: Sony (7), Canon (7), Nikon (6), Fujifilm (3), Panasonic (1), OM System (1).
  - **35 Ống kính (Lens)**: Canon (9), Sony (8), Nikon (6), Fujifilm (5), Olympus (2), Panasonic (2), Sigma (2), Tamron (1).
  - **Phân bố họ ngàm**: Sony E (18), Canon RF (11), Nikon Z (11), Fujifilm X (8), Canon EF (5), Micro Four Thirds (4), L-Mount (2), Nikon F (1).
- **Thực nghiệm Pilot Heuristic Matching (Khảo sát sơ bộ, chưa phải Entity Linking chính thức)**:
  - Chạy thử nghiệm heuristic token matching trên đúng **2,876 sản phẩm ứng viên Body & Lens**:
  - **Kết quả thô**: 1,435 / 2,876 sản phẩm (~49.9%) chứa từ khóa trùng khớp với tên dòng máy trong bộ 60 specs.
  - **Khảo sát chất lượng nhanh trên mẫu nhỏ ($n=20$)**: Nhận thấy tỷ lệ *False Positive* ở mức cao (khoảng 35–40%) do cách match chuỗi lỏng (ví dụ: chuỗi *"Canon EOS 6D"* bị match nhầm vào spec *"Canon EOS R5"* vì cùng token *"EOS"* và *"Canon"*). Khảo sát này mang tính cảnh báo sơ bộ nhằm định lượng rủi ro của phương pháp rule-based đơn giản.
  - **Ước tính Tham chiếu cho Mục 3 (Rough Anchor Point)**: Sau khi loại trừ ước tính False Positive, số lượng sản phẩm match tin cậy sơ bộ nằm trong khoảng **~860 – 930 items** (~30 – 32% trên tổng số 2,876 Body/Lens). Con số này chỉ mang tính tham khảo thô do suy ra từ khảo sát mẫu nhỏ ($n=20$), đóng vai trò điểm neo đối chiếu (anchor point) chứ không phải chỉ tiêu ràng buộc, bởi đường ống Multi-tier ở Mục 3 với Semantic Matching có thể phát hiện thêm nhiều biến thể mà rule đơn giản bỏ sót.
  - **Kết luận kiến trúc cho Mục 3**: Bắt buộc phải áp dụng kiến trúc Entity Linking đa tầng:
    1. Regex nhận dạng chính xác Model Code / Mount code.
    2. Fuzzy Matching chuẩn hóa theo Token Sort Ratio.
    3. Sentence-Transformers (`all-MiniLM-L6-v2`) với ngưỡng Cosine Similarity cao ($\ge 0.80$) kết hợp validation sample thủ công để loại bỏ hoàn toàn các trường hợp match sai trước khi tạo Ma trận Tương thích Cứng $M$.

---

## 6. Danh mục Sản phẩm Bàn giao (Deliverables)

1. `ai/data/processed/camera_interactions_k5.csv`: Dữ liệu 622,997 tương tác sạch sau k-core.
2. `ai/data/processed/train.txt`, `val.txt`, `test.txt`: Dữ liệu phân chia Leave-One-Out (70,424 dòng mỗi file val/test; 482,149 tương tác train).
3. `ai/data/processed/val_negatives.json`, `test_negatives.json`: 99 negative samples/user (seed=42).
4. `ai/data/processed/user_map.json`, `item_map.json`: Bảng ánh xạ ID nguyên (0-indexed).
5. `ai/data/processed/camera_items_meta.jsonl`: Metadata của 28,867 sản phẩm còn lại sau k-core.
6. `ai/data/specs/camera_lens_specs.csv`: Bảng thông số chuẩn 60 thiết bị hạt nhân.
7. `ai/data/processed/filtering_stats.json`: Bảng vết tham số tự động.

---

## Phụ lục A: Quá trình Hội tụ Thuật toán Lọc $k$-core ($k=5$)

Thuật toán lọc lặp đệ quy trên tập 72,775 items và 4,042,112 tương tác đạt hội tụ tuyệt đối sau 14 vòng:
```text
Vòng 1:  826,275 tương tác | 99,317 users | 72,775 items
Vòng 2:  705,951 tương tác | 88,402 users | 33,549 items
Vòng 3:  647,400 tương tác | 73,723 users | 31,952 items
Vòng 4:  634,527 tương tác | 72,728 users | 29,495 items
Vòng 5:  626,566 tương tác | 70,900 users | 29,294 items
Vòng 6:  624,703 tương tác | 70,761 users | 28,959 items
Vòng 7:  623,564 tương tác | 70,500 users | 28,934 items
Vòng 8:  623,303 tương tác | 70,484 users | 28,884 items
Vòng 9:  623,116 tương tác | 70,440 users | 28,881 items
Vòng 10: 623,068 tương tác | 70,439 users | 28,870 items
Vòng 11: 623,013 tương tác | 70,426 users | 28,869 items
Vòng 12: 623,001 tương tác | 70,425 users | 28,867 items
Vòng 13: 622,997 tương tác | 70,424 users | 28,867 items
Vòng 14: 622,997 tương tác | 70,424 users | 28,867 items (Hội tụ hoàn toàn)
```
*Ghi chú cơ chế hội tụ*: Ở mỗi vòng lặp, thuật toán áp dụng **đồng thời** cả hai điều kiện: `user_counts[u] >= 5 AND item_counts[i] >= 5`. Tại Vòng 1, số lượng tương tác giảm mạnh từ 4,042,112 xuống 826,275 và người dùng giảm từ ~2.1M xuống 99,317 do phần lớn người dùng vãng lai (< 5 tương tác) bị loại bỏ, trong khi toàn bộ 72,775 items tạm thời đều thỏa mãn bậc ban đầu. Việc loại bỏ các tương tác ở Vòng 1 làm suy giảm bậc của các items ở các vòng tiếp theo, kích hoạt quá trình cắt tỉa dây chuyền cho tới khi toàn bộ đồ thị nhị phân User–Item cùng thỏa mãn điều kiện $k$-core tại Vòng 14.

## Phụ lục B: Trích dẫn Tài liệu Nguồn
> Hou, Y., Mu, J., Bao, K., Zheng, C., Tang, X., Zhang, H., ... & McAuley, J. (2024). *Bridging Language and Items for Retrieval and Recommendation*. arXiv preprint arXiv:2403.03952 (Amazon Reviews 2023 Dataset).
