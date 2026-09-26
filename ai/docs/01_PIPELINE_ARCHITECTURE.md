# BÁO CÁO MỤC 1: PIPELINE TỔNG QUÁT HỆ THỐNG TƯ VẤN THIẾT BỊ NHIẾP ẢNH
*(Phạm vi Giai đoạn 1: Chuẩn bị Dữ liệu, Xây dựng Tri thức & Đo đạc Baseline Benchmark - Từ Mục 1 đến Mục 5)*

---

## 1. Bài toán Nghiên cứu (Problem Statement)

Trong lĩnh vực thương mại điện tử thiết bị nhiếp ảnh, các mô hình gợi ý truyền thống (Collaborative Filtering - CF) chỉ dựa vào lịch sử tương tác giữa người dùng và sản phẩm ($User \times Item$). Cách tiếp cận này gặp phải hạn chế cốt lõi: **Vi phạm ràng buộc tương thích vật lý (Physical Compatibility Violation)**. 

Ví dụ: Hệ thống gợi ý ống kính *Canon RF 50mm* cho người dùng đang sở hữu thân máy *Sony A7 IV (ngàm Sony E)* chỉ vì ống kính này phổ biến. Đây là gợi ý hoàn toàn sai trong thực tế vì hai thiết bị không thể lắp vừa vào nhau.

**Mục tiêu của giai đoạn 1 (Mục 1 đến 5)**:
- Xây dựng đường ống xử lý dữ liệu chuẩn từ tập dữ liệu công khai Amazon Reviews 2023 (Electronics).
- Xây dựng bảng chân lý mặt đất (Ground-truth) về độ tương thích ngàm: Ma trận $M \in \{0, 1\}^{|\mathcal{B}| \times |\mathcal{L}|}$.
- Mô hình hóa mạng lưới quan hệ nhiếp ảnh dưới dạng Đồ thị tri thức đa quan hệ (Heterogeneous Knowledge Graph) trên PyTorch Geometric.
- Huấn luyện 3 mô hình đối chứng (Baselines: Popularity, LightGCN, RGCN) và thiết lập bảng đo Benchmark ban đầu làm cột mốc đối chứng (về độ chính xác NDCG, Recall, Hit và tỷ lệ vi phạm ngàm CVR).

---

## 2. Sơ đồ Pipeline Tổng quát (Mục 1 đến 5)

```mermaid
flowchart TD
    %% Khối 1: Dữ liệu
    subgraph K1 ["Khối 1: Thu thập & Làm sạch Dữ liệu (Mục 2)"]
        A1["Amazon Reviews 2023<br/>(Electronics - Raw)"] -->|1. Lọc Taxonomy Camera| A2["Camera Interactions<br/>(User, ASIN, Rating, Time)"]
        A2 -->|2. Lọc k-core lặp (k=5)| A3["Dense Interactions"]
        A3 -->|3. Time-aware Leave-One-Out| A4["train.txt, val.txt, test.txt"]
        
        B1["Specs Camera & Lens<br/>(Kaggle / Wikidata)"] -->|Chuẩn hóa thuộc tính| B2["Bảng Specs Chuẩn<br/>(Brand, Model, Mount, Sensor)"]
    end

    %% Khối 2: Entity Linking & Ma trận M
    subgraph K2 ["Khối 2: Entity Linking & Ma trận Ràng buộc Cứng (Mục 3)"]
        A3 -.->|ASIN Title & Brand| C1["Multi-tier Entity Linking Engine<br/>1. Regex/Rule → 2. Fuzzy → 3. Sentence-Transformers"]
        B2 -.->|Canonical Model| C1
        C1 -->|Threshold Tuning & Validation Sample| C2["Tập Sản phẩm đã gán Specs<br/>Body (B) và Lens (L)"]
        C2 --> C3["Mount Mapping Engine<br/>(Sony E/FE, Canon RF, Nikon Z, M4/3...)"]
        C3 --> C4[/"Ma trận Tương thích Cứng M (Ground-truth)<br/>M ∈ {0, 1}^(|B| × |L|) (Lưu file .npz)"/]
    end

    %% Khối 3: Knowledge Graph
    subgraph K3 ["Khối 3: Xây dựng Đồ thị Tri thức KG (Mục 4)"]
        C2 & A4 --> D1["Knowledge Graph Builder<br/>(PyTorch Geometric HeteroData)"]
        D1 --> D2[/"Đồ thị Tri thức Đa quan hệ G = (V, E, R)<br/>• Đỉnh V: User, Body, Lens, Mount, Sensor, UseCase<br/>• Cạnh R: interacted_with, has_spec, compatible_with, suitable_for<br/>(Lưu file kg_data.pt)"/]
    end

    %% Khối 4: Baselines & Benchmark
    subgraph K4 ["Khối 4: Huấn luyện Baselines & Benchmark Đối chứng (Mục 5)"]
        A4 & D2 --> E1["Baseline 1: Popularity (Rule-based Mount-filtered)"]
        A4 --> E2["Baseline 2: LightGCN (CF thuần túy trên User-Item Graph)"]
        D2 & A4 --> E3["Baseline 3: RGCN (Relational GNN trên Đồ thị Tri thức G)"]
        
        E1 & E2 & E3 --> F1["Đo Độ chính xác Xếp hạng:<br/>NDCG@{5,10,20}, Recall@{5,10,20}, Hit@{5,10,20}<br/>(Protocol: 1 positive + N sampled negatives)"]
        E1 & E2 & E3 --> F2["Đo Tỷ lệ Vi phạm Ràng buộc Ngàm:<br/>CVR@{5,10,20} (trên tập user sở hữu body)"]
        F1 & F2 --> F3[/"Bảng Kết quả Benchmark Đối chứng<br/>(Markdown / Excel)"/]
    end

    style C4 fill:#ffeaa7,stroke:#fdcb6e,stroke-width:2px
    style D2 fill:#dfe6e9,stroke:#b2bec3,stroke-width:2px
    style F3 fill:#55efc4,stroke:#00b894,stroke-width:2px
```

---

## 3. Nội dung Chi tiết Từng Bước Thực hiện

### Bước 2: Thu thập, Làm sạch & Lọc Dữ liệu Tương tác
1. **Lọc Domain Camera**:
   - Trích xuất từ tập `Amazon Reviews 2023 (Electronics)` các sản phẩm thuộc nhánh máy ảnh, ống kính và phụ kiện quang học theo Category Taxonomy và từ khóa danh mục.
2. **Lọc $k$-core lặp ($k=5$)**:
   - Loại bỏ các user có $<5$ lượt đánh giá và các item có $<5$ lượt đánh giá để giải quyết hiện tượng dữ liệu thưa (Sparsity). Thuật toán chạy đệ quy đến khi hội tụ.
3. **Phân chia tập dữ liệu (Time-aware Leave-One-Out Protocol)**:
   - Sắp xếp tương tác của mỗi user theo mốc thời gian tăng dần:
     - **Tập Test**: Tương tác gần nhất (cuối cùng) của user.
     - **Tập Validation**: Tương tác kế cuối.
     - **Tập Train**: Toàn bộ các tương tác trước đó.
   - Xuất ra 3 file: `train.txt`, `val.txt`, `test.txt`.

### Bước 3: Khớp nối Thực thể (Entity Linking) & Ma trận Tương thích Cứng
1. **Entity Linking Đa tầng (Multi-tier Strategy)**:
   - Kết nối tên sản phẩm Amazon thô với bảng thông số kỹ thuật chuẩn:
     - *Tầng 1*: Quét Regex trích xuất Brand và Model Code (VD: `Sony`, `ILCE-7M4 / A7 IV`, `Canon`, `RF 50mm`). Match chính xác $\rightarrow$ Chấp nhận.
     - *Tầng 2*: Fuzzy String Matching (Token Sort Ratio) cho các tên có biến thể ký tự nhẹ.
     - *Tầng 3 (Fallback)*: Với các trường hợp không bóc tách được rõ ràng, sử dụng `Sentence-Transformers (all-MiniLM-L6-v2)` tính Cosine Similarity. Thực nghiệm khảo sát các ngưỡng $\{0.75, 0.80, 0.85\}$ để cân bằng giữa Precision và Match Rate.
   - *Đánh giá thủ công (Validation Sample)*: Rút ngẫu nhiên một tập mẫu 100-200 sản phẩm đã link để kiểm tra thủ công, báo cáo tỷ lệ gán nhãn chính xác (Precision) trước khi tạo ma trận $M$.
2. **Bảng Ánh xạ Ngàm (Mount Mapping)**:
   - Ánh xạ từng Body và Lens vào các họ ngàm chuẩn: `Sony E/FE`, `Canon RF`, `Canon EF`, `Nikon Z`, `Fujifilm X`, `Micro Four Thirds (M4/3)`.
   - *Giả định phạm vi nghiên cứu Giai đoạn 1*: Ma trận $M$ tập trung định nghĩa **tương thích ngàm vật lý trực tiếp (Native Mount Compatibility)**. Các trường hợp sử dụng ngàm chuyển đổi (như lens Canon EF lắp trên body Canon RF qua EF-EOS R Adapter) được coi là tương thích có điều kiện và sẽ được mô hình hóa qua cạnh quan hệ `requires_adapter` trong đồ thị tri thức ở các bước mở rộng sau.
3. **Tạo Ma trận Nhị phân Tương thích Cứng $M$ (Ground-truth)**:
   - Ma trận nhị phân giữa tập Thân máy $\mathcal{B}$ và tập Ống kính $\mathcal{L}$:
     $$M \in \{0, 1\}^{|\mathcal{B}| \times |\mathcal{L}|}$$
     $$M_{b, l} = \begin{cases} 
     1 & \text{nếu thân máy } b \text{ và ống kính } l \text{ cùng hệ ngàm (lắp vừa trực tiếp)} \\
     0 & \text{nếu khác hệ ngàm (không thể lắp vừa trực tiếp)}
     \end{cases}$$
   - Lưu dưới dạng ma trận thưa **Scipy Sparse CSR Matrix** thành file `compatibility_matrix.npz` để tối ưu bộ nhớ RAM và tăng tốc độ truy vấn slicing theo hàng.
   - Xuất file báo cáo thống kê số lượng Body, Lens, số cặp tương thích ($M=1$) và số cặp không tương thích ($M=0$).

### Bước 4: Xây dựng Đồ thị Tri thức $G = (V, E, R)$
Mô hình hóa dữ liệu trên `PyTorch Geometric (torch_geometric.data.HeteroData)`:
- **Tập thực thể ($V$)**:
  - Người dùng ($User$)
  - Thân máy ($Body$)
  - Ống kính ($Lens$)
  - Ngàm ống kính ($Mount$)
  - Cảm biến ($Sensor$)
  - Nhu cầu chụp ảnh ($UseCase$: Chân dung, Phong cảnh, Thể thao/Động vật, Vlog).
- **Tập quan hệ ($R$)**:
  - `(user, interacted_with, item)`: Hành vi người dùng đã mua/đánh giá sản phẩm.
  - `(item, has_spec, mount/sensor)`: Thuộc tính kỹ thuật của thiết bị.
  - `(body, compatible_with, lens)`: Cạnh tương thích vật lý (sinh từ $M_{b,l} = 1$).
  - `(item, suitable_for, usecase)`: Thiết bị phù hợp nhu cầu, gán theo **Quy tắc Nhiếp ảnh Cụ thể (Domain Rules)**:
    - *Chân dung (Portrait)*: Tiêu cự $85\text{--}135mm$, khẩu độ lớn $f \le 2.0$.
    - *Phong cảnh (Landscape)*: Tiêu cự góc rộng $16\text{--}35mm$.
    - *Thể thao / Động vật hoang dã (Sports/Wildlife)*: Tiêu cự Tele $70\text{--}200mm \ (f/2.8)$ hoặc $\ge 200mm$.
    - *Quay Vlog (Vlog)*: Tiêu cự góc rộng nhẹ nhàng ($16\text{--}35mm$) kết hợp thân máy có màn hình xoay lật (flip screen) và trọng lượng $< 500g$.
- Lưu kết quả thành file `kg_data.pt`.

### Bước 5: Chạy Thử nghiệm 3 Baselines & Đo đạc Benchmark Đối chứng
1. **Cài đặt 3 mô hình Baseline**:
   - **Baseline 1: Popularity (Rule-based Mount-filtered)**:
     - Gợi ý ống kính phổ biến nhất hệ thống nhưng **có lọc theo các hệ ngàm mà người dùng sở hữu**:
       $$\mathcal{M}_u = \bigcup_{b \in \mathcal{B}_u} \text{mount}(b)$$
       $$\hat{y}_{u, l} = \text{Count}(l) \cdot \mathbb{I}\Big(\text{mount}(l) \in \mathcal{M}_u\Big)$$
     - Nếu người dùng sở hữu nhiều body khác ngàm (VD: vừa có Sony vừa có Canon), hệ thống sẽ xét hợp các ngàm hợp lệ $\mathcal{M}_u$.
   - **Baseline 2: LightGCN (Collaborative Filtering thuần túy)**:
     - Mô hình GNN tiêu chuẩn State-of-the-Art trên đồ thị 2 phía $User-Item$, bỏ qua thông tin kỹ thuật và ngàm. Huấn luyện bằng hàm mất mát **Bayesian Personalized Ranking (BPR Loss)**.
   - **Baseline 3: RGCN (Relational Graph Convolutional Network - KG/Relational Baseline)**:
     - Mô hình học biểu diễn trên đồ thị đa quan hệ $G=(V, E, R)$ (gồm cả quan hệ tương tác người dùng lẫn quan hệ tri thức thiết bị). Sử dụng cơ chế truyền thông điệp có trọng số theo từng loại quan hệ $r \in \mathcal{R}$, tối ưu hóa bằng **BPR Link Prediction Loss** trên tập tương tác người dùng.

2. **Giao thức Đánh giá (Evaluation Protocol)**:
   - **Sampled Ranking Evaluation**: Ghép mỗi positive test item với $N$ negative items chưa từng tương tác (mặc định $N=99$ theo chuẩn benchmark của thư viện RecBole/Elliot). Giao thức Full-ranking có thể mở rộng chạy đối chứng khi cần.
   - **Bộ chỉ số đo lường độ chính xác xếp hạng**: NDCG@K, Recall@K, Hit@K với $K \in \{5, 10, 20\}$.
   - **Tỷ lệ Vi phạm Ràng buộc Ngàm (Constraint Violation Rate - CVR@K)**:
     Chỉ số CVR đo lường tỷ lệ ống kính được gợi ý trong Top-K không tương thích với bất kỳ thân máy nào mà người dùng đang sở hữu. Chỉ số này chỉ tính trên tập người dùng đã sở hữu ít nhất một thân máy ($\mathcal{U}^* = \{u \in \mathcal{U} : \mathcal{B}_u \neq \emptyset\}$), nhằm đảm bảo tính logic và tránh lỗi tập rỗng (vacuous truth):
     $$\text{CVR@K} = \frac{1}{|\mathcal{U}^*|} \sum_{u \in \mathcal{U}^*} \frac{1}{K} \sum_{l \in \text{Top-K}(u) \cap \mathcal{L}} \mathbb{I}\Big( \forall b \in \mathcal{B}_u, M_{b, l} = 0 \Big)$$
     *(Nếu toàn bộ lens gợi ý đều khớp với ít nhất một body của user thì $\text{CVR@K} = 0\%$. CVR càng cao chứng tỏ mô hình càng vi phạm tương thích vật lý nghiêm trọng).*

3. **Sản phẩm đầu ra Mục 5**: Bảng kết quả benchmark ban đầu (Markdown / Excel) làm mốc đối chứng khoa học vững chắc.

---

## 4. Danh sách Sản phẩm Bàn giao Mục 1-5 (Deliverables)

1. Tài liệu kiến trúc luồng xử lý chi tiết (File này).
2. Tệp dữ liệu tương tác sạch: `train.txt`, `val.txt`, `test.txt`.
3. Bảng ánh xạ ngàm & Ma trận tương thích: `compatibility_matrix.npz` kèm báo cáo thống kê số cặp tương thích.
4. Đồ thị tri thức hoàn chỉnh PyTorch Geometric: `kg_data.pt`.
5. Bảng kết quả thực nghiệm benchmark đối chứng ban đầu (Baseline Benchmark Table).
