# BÁO CÁO MỤC 3: KHỚP NỐI THỰC THỂ & MA TRẬN THAM CHIẾU TƯƠNG THÍCH CỨNG (ENTITY LINKING & HARD COMPATIBILITY REFERENCE MATRIX)

**Học phần**: Khóa luận tốt nghiệp / Đề tài Nghiên cứu Hệ thống Gợi ý Thiết bị Nhiếp ảnh  
**Thời gian hoàn thành**: Tháng 09/2026  
**Trạng thái**: Đã nghiệm thu thực nghiệm & Khóa số liệu  

---

## 1. Mục tiêu & Giới hạn Phạm vi Nghiên cứu (Scope Delimitation)

Trong hệ sinh thái thương mại điện tử thiết bị nhiếp ảnh, các mô hình gợi ý truyền thống (Collaborative Filtering / LightGCN) dựa thuần túy trên hành vi ($User \times Item$) thường mắc lỗi gợi ý các thiết bị không tương thích vật lý (ví dụ: gợi ý ống kính Canon RF cho người dùng đang sở hữu thân máy Sony E). 

**Mục 3 đóng vai trò là "Cầu nối Tri thức Vật lý"**, chịu trách nhiệm:
1. **Entity Linking (Khớp nối thực thể)**: Ánh xạ từ tiêu đề sản phẩm trên Amazon vào danh mục thông số kỹ thuật chuẩn (Canonical Specs), xác định danh tính, phân loại (Body/Lens) và họ ngàm vật lý (Mount Family).
2. **Mount Mapping (Chuẩn hóa ngàm vật lý)**: Định nghĩa quy tắc tương thích vật lý trực tiếp (Native Mount Compatibility).
3. **Hard Compatibility Reference Matrix (Ma trận tham chiếu tương thích cứng $M$)**: Xây dựng ma trận nhị phân tham chiếu đã qua kiểm định:
   $$\mathbf{M} \in \{0, 1\}^{|\mathcal{B}_{\text{linked}}| \times |\mathcal{L}_{\text{linked}}|}$$
   Lưu trữ dưới dạng ma trận thưa **Scipy Sparse CSR** (`compatibility_matrix.npz`) để làm căn cứ đo đạc tỷ lệ vi phạm ràng buộc ngàm (**Known-space CVR@K**) ở Mục 5.

### Giới hạn Phạm vi Đồ án (Delimitation & Assumptions):
- **Khoanh vùng thiết bị đại diện**: Đồ án tập trung xây dựng ma trận ràng buộc cứng trên tập các dòng thân máy và ống kính phổ biến có định danh rõ ràng. Các sản phẩm còn lại (compact, bridge, phụ kiện hoặc mô tả nhiễu) được giữ nguyên trong đồ thị tương tác $User \times Item$ tổng thể để không làm mất dữ liệu hành vi.
- **Tương thích Ngàm trực tiếp (Native Compatibility)**: Ma trận $\mathbf{M}$ chỉ thiết lập giá trị $1$ cho các cặp lắp vừa trực tiếp mà không cần ngàm chuyển đổi (Native Mount). Các trường hợp dùng ngàm chuyển đổi (ví dụ: ống kính Canon EF lắp trên body Canon RF qua ngàm chuyển EF-EOS R) được tách riêng và sẽ được mô hình hóa qua quan hệ `requires_adapter` trong Đồ thị Tri thức ở Mục 4.

---

## 2. Tiến trình Mở rộng Bộ Thông số Chuẩn (Canonical Specs Evolution)

- **Giai đoạn khởi điểm (Mục 2)**: Sử dụng bộ hạt nhân gồm **60 seed specifications** (25 Thân máy, 35 Ống kính) để thăm dò phân bố danh mục.
- **Giai đoạn hoàn thiện (Mục 3)**: Nhận thấy bộ 60 specs chưa đủ để bao phủ các dòng máy DSLR/Mirrorless chủ lực của các hãng lớn trên Amazon, nhóm nghiên cứu đã mở rộng bảng từ điển lên **139 canonical specifications** ([camera_lens_specs.csv](file:///d:/camera-store/ai/data/specs/camera_lens_specs.csv)) bao gồm:
  - **69 Thân máy (Bodies)**: Đầy đủ các thế hệ Sony A6000-series, A7-series; Canon DSLR (Rebel, 70D, 80D, 5D) và Mirrorless (EOS R, RP, R5, R6, R10); Nikon DSLR (D3000/D5000/D7000/D800-series) và Nikon Z (Z5, Z6, Z7, Zfc, Z8); Fujifilm X-series; Panasonic/Olympus Micro Four Thirds.
  - **70 Ống kính (Lenses)**: Bao gồm ống kính chính hãng (Sony FE, Canon EF/RF, Nikkor F/Z, Fujinon XF, M.Zuiko) và các dòng ống kính bên thứ ba phổ biến (Sigma Art/Contemporary, Tamron Di III, Samyang/Rokinon, TTArtisan) với biến thể ngàm xác định rõ ràng.

---

## 3. Kiến trúc Đường ống Entity Linking Đa tầng (Multi-tier Engine)

Nhằm giảm thiểu tối đa hiện tượng dương tính giả (False Positives) do tiêu đề Amazon bị loãng bởi từ khóa marketing hoặc phụ kiện kèm theo, hệ thống áp dụng cơ chế **Short-circuit Cascade** (ưu tiên chính xác cao trước, chỉ fallback khi cần):

```
                   Tiêu đề Sản phẩm Amazon (Title + Brand)
                                     │
      ┌──────────────────────────────┴──────────────────────────────┐
      ▼                                                             ▼
[Ứng viên Thân máy (Bodies)]                                [Ứng viên Ống kính (Lenses)]
  (1,414 sản phẩm)                                            (1,462 sản phẩm)
      │                                                             │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 1: Regex & Hardware Code Extraction (Độ tin cậy cao nhất)                  │
 │ • Quét mã định danh phần cứng: ILCE-7M4, EOS R5, Z6 II, X-T5, DC-S5M2...         │
 │ • Quét thông số quang học: Tiêu cự (\d+mm), khẩu độ (f/\d\.\d), họ ngàm (FE/RF)  │
 └───────────────────────────────────┬─────────────────────────────────────────────┘
                                     │
                     Match chính xác? ──► [CÓ] ──► Chấp nhận (Confidence = 1.0)
                                     │ [KHÔNG]
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 2: Normalized Fuzzy Token Sort Matching                                    │
 │ • Chuẩn hóa chuỗi (bỏ stop-words, lowercase, sort tokens)                       │
 │ • So khớp Token Sort Ratio với Canonical Model Specs (Ngưỡng khắt khe ≥ 82)     │
 └───────────────────────────────────┬─────────────────────────────────────────────┘
                                     │
                          Điểm ≥ 82? ──► [CÓ] ──► Chấp nhận (Confidence = Score/100)
                                     │ [KHÔNG]
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 3: Dense Retrieval qua Sentence-Transformers (Lưới vét ngữ nghĩa)          │
 │ • Model: all-MiniLM-L6-v2 mã hóa vector ngữ nghĩa                               │
 │ • Ngưỡng Cosine Similarity ≥ 0.82                                               │
 │ • Bắt buộc kiểm tra ràng buộc cùng Hãng (Brand-consistency check)               │
 └───────────────────────────────────┬─────────────────────────────────────────────┘
                                     │
                       Cosine ≥ 0.82? ──► [CÓ] ──► Chấp nhận (Confidence = Cosine)
                                     │ [KHÔNG]
                                     ▼
                      Gán nhãn: UNLINKED (mount = UNKNOWN)
                     (Giữ trong Đồ thị KG, loại khỏi Ma trận M)
```

### Giải thích Lựa chọn Ngưỡng (Threshold Selection Rationale):
- **Tầng 2 (Fuzzy Token Sort Ratio $\ge 82$)**: Ngưỡng 82 được xác lập qua khảo sát thực nghiệm nhằm phân biệt các dòng máy có tên gần giống nhau nhưng khác thế hệ (ví dụ: `Canon EOS 5D Mark III` vs `Mark IV`). Nếu đặt $\ge 85$ sẽ bỏ sót nhiều trường hợp tên sản phẩm dài có kèm từ khóa filter/bundle; nếu hạ xuống $\le 80$ sẽ xuất hiện lỗi ghép sai đời máy.
- **Tầng 3 (MiniLM Cosine Similarity $\ge 0.82$ kết hợp Brand-consistency)**: Mức 0.82 đảm bảo các mô tả ống kính có cấu trúc từ ngữ dài vẫn hội tụ về đúng nhóm tiêu cự và khẩu độ, đồng thời ràng buộc cùng hãng ngăn chặn việc vector embedding ghép nhầm giữa các thương hiệu đối thủ.

---

## 4. Bảng Ánh xạ Ngàm Vật lý (Mount Mapping Table)

Quy tắc tương thích ngàm trực tiếp (Native Mount Rules):

| Họ Ngàm Chuẩn | Hãng Sản Xuất Chủ Lực | Thân máy Tiêu Biểu | Ống kính Tiêu Biểu | Quy Tắc Tương Thích Vật Lý Trực Tiếp |
| :--- | :--- | :--- | :--- | :--- |
| **Sony E** | Sony / Tamron / Sigma | A7 IV, A7R V, A6700, ZV-E10 | Sony FE, Sony E, Sigma DG DN (E), Tamron Di III (E) | Lắp vừa trực tiếp tất cả lens Sony E/FE |
| **Canon RF** | Canon | EOS R5, R6 Mark II, R8, R10 | Canon RF, Canon RF-S | Chỉ lắp trực tiếp lens hệ ngàm RF |
| **Canon EF** | Canon (DSLR) | EOS 5D Mark IV, 90D, Rebel | Canon EF, Canon EF-S | Lắp trực tiếp trên body DSLR EF *(Lên RF cần adapter)* |
| **Nikon Z** | Nikon | Z8, Z6 II, Z6 III, Z5, Z50 | NIKKOR Z | Lắp vừa trực tiếp tất cả lens NIKKOR Z |
| **Nikon F** | Nikon (DSLR) | D850, D7500, D5600 | NIKKOR F-mount (AF-S, AF-P) | Lắp trực tiếp trên body DSLR F *(Lên Z cần FTZ)* |
| **Fujifilm X** | Fujifilm | X-T5, X-H2S, X-S20 | Fujinon XF, XC | Lắp vừa trực tiếp tất cả lens ngàm X |
| **Micro Four Thirds (M4/3)** | Olympus / Panasonic | OM-1, Lumix G9 II, GH6 | M.Zuiko, Lumix G | **Liên minh mở**: Body Olympus dùng chung lens Panasonic |
| **L-Mount** | Panasonic / Leica / Sigma | Lumix S5 II, Leica SL2 | Lumix S PRO, Sigma L-mount | Body Lumix S dùng chung lens Sigma L-mount |

---

## 5. Kết quả Thực nghiệm & Số liệu Đo đạc Thực tế (Measured Data)

### 5.1. Thống kê Khớp nối Thực thể (Entity Linking Coverage)
- **Tổng số sản phẩm ứng viên đầu vào (Bodies + Lenses)**: 2,876 items (1,414 Body, 1,462 Lens).
- **Số sản phẩm khớp nối thành công (Specs & Mount Linked)**: **257 items** (106 Bodies, 151 Lenses).
- **Tỷ lệ bao phủ (Coverage Rate)**: **8.94%**.
- **Phân bố theo các Tầng nhận diện**:
  - **Tier 1 (Regex & Model Code Extraction)**: **204 items (79.38%)** — Nhận diện chính xác nhờ mã phần cứng rõ ràng.
  - **Tier 2 (Normalized Fuzzy Token Sort Ratio $\ge 82$)**: **9 items (3.50%)** — Nhận diện các sản phẩm có kèm phụ kiện hoặc biến thể cú pháp nhỏ.
  - **Tier 3 (Dense Retrieval MiniLM Cosine $\ge 0.82$)**: **44 items (17.12%)** — Nhận diện mô tả ngữ nghĩa dài có ràng buộc cùng hãng.
  - **Unlinked (Giữ nguyên trong Đồ thị KG, loại khỏi Ma trận $M$)**: **2,619 items (91.06%)** (gồm 1,308 Body unlinked và 1,311 Lens unlinked).

### 5.2. Cấu trúc Ma trận Tham chiếu Tương thích Cứng $M$
- **Không gian ma trận**: $|\mathcal{B}_{\text{linked}}| \times |\mathcal{L}_{\text{linked}}| = 106 \times 151 = \mathbf{16,006\text{ cặp khả dĩ}}$.
- **Số cặp tương thích vật lý trực tiếp ($M=1$)**: **3,258 cặp (Mật độ 20.35%)**.
- **Số cặp không tương thích vật lý ($M=0$)**: **12,748 cặp (Độ thưa 79.65%)**.
- **Định dạng lưu trữ**: `scipy.sparse.csr_matrix` tại `ai/data/kg/compatibility_matrix.npz` (kèm file chỉ số 2 chiều `body_index.json` và `lens_index.json`).

### 5.3. Bảng Phân bố Ngàm & Số Cặp Tương Thích Thực Tế

| Họ Ngàm Chuẩn (Mount Family) | Hãng Chủ Lực | Số Thân máy ($|\mathcal{B}|$) | Số Ống kính ($|\mathcal{L}|$) | Số Cặp Tương Thích ($M=1$) | Tỷ Lệ Đóng Góp |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Sony E** | Sony / Tamron / Sigma | 31 | 53 | **1,643** | 50.43% |
| **Canon EF** | Canon (DSLR) | 30 | 38 | **1,140** | 34.99% |
| **Nikon F** | Nikon (DSLR) | 12 | 13 | **156** | 4.79% |
| **Canon RF** | Canon (Mirrorless) | 12 | 11 | **132** | 4.05% |
| **Fujifilm X** | Fujifilm | 5 | 15 | **75** | 2.30% |
| **Micro Four Thirds (M4/3)** | Olympus / Panasonic | 4 | 17 | **68** | 2.09% |
| **Nikon Z** | Nikon (Mirrorless) | 11 | 4 | **44** | 1.35% |
| **L-Mount\*** | Panasonic / Leica | 1 | 0 | **0\*** | 0.00% |
| **Tổng cộng** | — | **106** | **151** | **3,258** | **100.00%** |

*\*Ghi chú về L-Mount: Dữ liệu hiện có 1 body L-mount (Panasonic S5) nhưng trong tập catalog Amazon hiện tại chưa có ống kính L-mount độc lập nào đạt ngưỡng tin cậy để link vào ma trận. Hàng L-mount tạm thời có 0 cặp tương thích, hoàn toàn phản ánh trung thực phân bố dữ liệu thực tế (Data-driven).*

---

## 6. Đánh giá Mẫu Kiểm định Thủ công (Empirical Precision Validation)

Trên mẫu ngẫu nhiên **50 sản phẩm đã link** ([validation_samples_50.csv](file:///d:/camera-store/ai/data/kg/validation_samples_50.csv)):
- **Độ chính xác xác định Ngàm quan sát được (Mount Precision)**: **47 / 50 mẫu đúng ngàm = 94.0%**.
- **Độ chính xác chi tiết Model (Model Precision)**: **44 / 50 mẫu đúng phiên bản = 88.0%**.
- **Phân tích lỗi (Error Analysis)**:
  - *Tier 1 (Regex)*: Đạt độ chính xác ngàm **100%** trên mẫu kiểm định.
  - *Tier 2 (Fuzzy)*: Xuất hiện 3 trường hợp bị lệch do tên combo quá dài (ví dụ: `Canon EOS-1D X Mark II` bị kéo điểm vào `Canon EOS R6 Mark II` do chuỗi `Mark II`), dẫn đến nhầm ngàm EF sang RF. Đây là nguyên nhân chính dẫn đến 3 lỗi ngàm trong mẫu kiểm định.
  - *Tier 3 (Semantic)*: Đạt độ chính xác ngàm **100%** nhờ bộ lọc `brand-consistency check`. Dù có trường hợp match lệch tiêu cự giữa hai ống kính cùng hãng (như `XF150-600mm` match vào `XF 70-300mm`), nhưng **thuộc tính Mount (Fujifilm X) vẫn chính xác tuyệt đối**.

---

## 7. Audit Nhóm Sản Phẩm Chưa Khớp Nối (UNLINKED Audit — n=50)

Để trả lời khách quan câu hỏi *"Tại sao có 2,619 sản phẩm bị UNLINKED?"*, nhóm đã rút ngẫu nhiên mẫu **50 sản phẩm** từ tập 2,619 items UNLINKED ([unlinked_audit_samples_50.csv](file:///d:/camera-store/ai/data/kg/unlinked_audit_samples_50.csv)) để kiểm tra bản chất:

| Nhóm Nguyên Nhân | Số Lượng (n=50) | Tỷ Lệ | Bản Chất & Ví Dụ Thực Tế |
| :--- | :---: | :---: | :--- |
| **1. Thiết bị liền khối / Không có ngàm tháo rời** | **18** | **36.0%** | Máy ảnh Compact du lịch, bridge zoom liền (Nikon Coolpix S8000/S6200, Canon PowerShot A720IS, Casio Exilim, Sony CyberShot RX100/RX10, Olympus Camedia...). Nhóm này không có ngàm lens tháo rời, việc loại khỏi ma trận $M$ là hoàn toàn chính xác. |
| **2. Phụ kiện quang học / Adapter / Teleconverter** | **8** | **16.0%** | Ống nối macro (Polaroid Extension Tube), Teleconverter (Nikon TC-17E II), Loa che sáng (Tamron/Canon Lens Hood), Filter mắt cá phụ trợ (Opteka Fisheye screw-on). Đây là phụ kiện bị phân loại nhầm thành Lens ở bước trích xuất từ khóa. |
| **3. Hệ máy hiếm / Ngoại vi phạm vi 8 ngàm chính** | **6** | **12.0%** | Ngàm Pentax K (K20D, K-5 IIs, K-1 II), Nikon 1 mirrorless 1-inch (Nikon 1 S1, J2), Sony A-mount DSLR (SAL-24F20Z). Nằm ngoài phạm vi 8 họ ngàm phổ biến của đồ án. |
| **4. Thiếu mã trong từ điển Specs 139 dòng** | **13** | **26.0%** | Ống kính hãng thứ 3 hoặc ống kính dòng phụ (TTArtisan 35mm f/1.4, Sigma 20mm f/1.8, Zeiss 25mm f/2.0, Voigtlander 42.5mm f/0.95, Panasonic 14-140mm...). Có thể tăng coverage nếu mở rộng specs trong tương lai. |
| **5. Tiêu đề bundle quá dài / Filter từ ngữ chặt** | **5** | **10.0%** | Tiêu đề chứa quá nhiều phụ kiện (pin, thẻ nhớ, túi) làm loãng điểm similarity dưới ngưỡng 0.82 (ví dụ: Sony A6100 Bundle, Nikon D3300 Renewed Bundle...). |
| **Tổng cộng** | **50** | **100.0%** | — |

> **Kết luận từ Audit**: Có tới **64.0%** (Nhóm 1 + 2 + 3) các sản phẩm UNLINKED bản chất không thể hoặc không nên đưa vào ma trận ngàm tháo rời trực tiếp. Chỉ có khoảng **36.0%** (Nhóm 4 + 5) là thiết bị thật bị bỏ sót do giới hạn từ điển. Quyết định không cố ép link nhóm này giúp bảo vệ tối đa độ tin cậy của ma trận tham chiếu $M$.

---

## 8. Khả Thi Thống Kê & Giao Thức Đánh Giá CVR@K ở Mục 5 (Evaluation Protocol)

### 8.1. Kiểm chứng Tính Khả thi Thống kê (Statistical Feasibility Check)
Nghiên cứu đã kiểm tra trực tiếp số lượng tương tác của người dùng trên tập 257 thiết bị đã link:
- **Tập Train (70,424 users)**: Có **2,491 người dùng** sở hữu thân máy đã xác định ngàm (tạo ra 2,798 tương tác thân máy và 8,215 tương tác ống kính).
- **Quy mô tập đánh giá CVR**: **2,491 users** sở hữu thân máy đã biết ngàm trong lịch sử là một kích thước mẫu **đủ lớn về mặt thống kê** để đo lường độ vi phạm ràng buộc ngàm của các thuật toán gợi ý.

### 8.2. Giao thức Đánh giá 2 Tầng (Two-tier Evaluation Protocol)
Tại Mục 5, hệ thống sẽ báo cáo song song 2 nhóm chỉ số:
1. **Chỉ số Xếp hạng Tổng thể (System-wide Ranking Metrics)**:
   - Đo trên **toàn bộ 28,867 items** trong đồ thị $User \times Item$: **NDCG@{5,10,20}**, **Recall@{5,10,20}**, **Hit Rate@{5,10,20}**.
2. **Chỉ số Ràng buộc Ngàm (Constraint Metrics)** trên tập 2,491 người dùng sở hữu thân máy:
   - **K-CVR@K (Known-space Constraint Violation Rate)**:
     $$\text{K-CVR@K} = \frac{\sum_{u} \sum_{l \in \text{Top-K}_u \cap \mathcal{L}_{\text{linked}}} \mathbb{I}\Big(\mathbf{M}_{\text{body}(u), l} = 0\Big)}{\sum_{u} |\text{Top-K}_u \cap \mathcal{L}_{\text{linked}}|}$$
     *Ý nghĩa: Đo chính xác tỷ lệ thuật toán gợi ý ống kính sai ngàm trên không gian tri thức đã kiểm chứng.*
   - **URR@K (Unknown Recommendation Rate)**:
     $$\text{URR@K} = \frac{\sum_{u} |\text{Top-K}_u \setminus \mathcal{I}_{\text{linked}}|}{K \times |\mathcal{U}_{\text{eval}}|}$$
     *Ý nghĩa: Đo lường mức độ thuật toán đưa ra các gợi ý nằm ngoài vùng tri thức đã kiểm định (độ không chắc chắn).*

---

## 9. Danh mục Sản phẩm Bàn giao Mục 3 (Deliverables)

1. [03_entity_linking_matrix.py](file:///d:/camera-store/ai/pipeline/03_entity_linking_matrix.py): Pipeline hoàn chỉnh từ trích xuất, liên kết đa tầng đến xuất ma trận.
2. [camera_lens_specs.csv](file:///d:/camera-store/ai/data/specs/camera_lens_specs.csv): Từ điển 139 canonical specs đã mở rộng.
3. [linked_products.csv](file:///d:/camera-store/ai/data/kg/linked_products.csv): Bảng 257 sản phẩm đã gán Specs, Mount và Confidence.
4. [unlinked_audit_samples_50.csv](file:///d:/camera-store/ai/data/kg/unlinked_audit_samples_50.csv): Mẫu kiểm định 50 sản phẩm unlinked phục vụ biện minh học thuật.
5. [mount_mapping.json](file:///d:/camera-store/ai/data/kg/mount_mapping.json): Quy tắc định nghĩa 8 họ ngàm vật lý.
6. [compatibility_matrix.npz](file:///d:/camera-store/ai/data/kg/compatibility_matrix.npz): Ma trận tham chiếu tương thích thưa CSR ($106 \times 151$).
7. [body_index.json](file:///d:/camera-store/ai/data/kg/body_index.json) & [lens_index.json](file:///d:/camera-store/ai/data/kg/lens_index.json): Bảng tra cứu 2 chiều giữa index ma trận $\leftrightarrow$ ASIN.
8. [compatibility_stats.json](file:///d:/camera-store/ai/data/kg/compatibility_stats.json): Báo cáo thống kê số lượng định lượng.
9. [validation_samples_50.csv](file:///d:/camera-store/ai/data/kg/validation_samples_50.csv): File 50 mẫu kiểm định ngẫu nhiên đối chứng.
10. [03_ENTITY_LINKING_MATRIX.md](file:///d:/camera-store/ai/docs/03_ENTITY_LINKING_MATRIX.md): Bản báo cáo kỹ thuật hoàn chỉnh đã chuẩn hóa.
