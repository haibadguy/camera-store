# CaKG-Rec — Thiết kế mô hình (khung quyển đồ án, mục 2.1–2.6)

- Viết 14/10/2026, nhánh `nam/cakg-rec` (tách từ `nam/khung-co`). **Chỉ là thiết kế: chưa cài mô hình, chưa huấn luyện.** Kế hoạch đánh giá đăng ký trước: `docs/reviews/cakg_eval_plan.md`.
- Khung cô gửi (để ngoài repo) là hướng chính. Tài liệu này dùng ký hiệu của khung; chỗ khác khung ghi **[ĐỀ XUẤT CHO CÔ]**, chỗ cần Nam chốt ghi **[HỎI]**. Tổng hợp ở mục 11.
- **Nam chốt 13 câu [HỎI] ngày 14/10/2026** (mục 11; các khối đã sửa theo). Các mục **[ĐỀ XUẤT CHO CÔ] là ghi chú nội bộ, không gửi cô**; các sửa câu chữ xử lý khi viết báo cáo.
- Mỗi khối: (a) ví dụ nhỏ tính tay, (b) đầu vào / đầu ra, (c) công thức (đánh số), (d) siêu tham số và nguồn, (e) chỗ khác khung / bài gốc.

**Số liệu** trong file chỉ lấy từ 3 script chỉ đọc (`ai/survey/cakg/`, commit `41395a4`, `08c053b`; log ở `ai/data/survey/cakg/`, chạy trên cây sạch):

| Script | Log | sha256 log | Nội dung |
|---|---|---|---|
| `dem_cakg.py` | `run_dem_cakg_20261014_lan1.log` | `9ddf7129…c9c29bcc3` | đếm đồ thị con phần cứng, cặp L_comp, mặt nạ, CVR_relaxed, trần Path Coverage (chỉ dùng **val**, không đọc mảng test) |
| `probe_cakg.py` | `run_probe_cakg_20261014_lan1.log` | `902e20e0…a23ac21e` | VRAM / thời gian bằng **trọng số ngẫu nhiên**, không `optimizer.step` |
| `vidu_tinh_tay.py` | `run_vidu_tinh_tay_20261014_lan2.log` | `7f682759…5667332` | mọi con số của các ví dụ tính tay dưới đây |

Bản nháp (`*_nhap*.log`) cho cùng số (`dem`: trùng từng dòng trừ 2 dòng đầu ghi sha256 script / HEAD); không đưa lên git (log bị `.gitignore`).

**Bài đã đọc toàn văn** (bản HTML trên arXiv / ar5iv, ngày 14/10/2026; PDF không đọc được thành chữ nên không dùng):

| Bài | Bản | Dùng cho |
|---|---|---|
| He et al., LightGCN, SIGIR 2020 | arXiv 2002.02126v4 (đọc 09/10, ghi trong `n5_eval_plan.md`) | khối 1 |
| Busbridge et al., Relational Graph Attention Networks | arXiv 1904.05811v1 (bản duy nhất) | khối 2 |
| Schlichtkrull et al., R-GCN, ESWC 2018 | arXiv 1703.06103v4 (đọc 09/10) | phần tự giữ W_0 (Eq. 2) |
| Wang et al., AM-GCN, KDD 2020 | arXiv 2007.02265v2 | khối 4 (Eq. 7–10) |
| Wang et al., HAN, WWW 2019 | arXiv 1903.07293v2 | khối 4 (so sánh: attention trung bình trên mọi nút) |
| Wu et al., SGL, SIGIR 2021 | arXiv 2010.10783v4 | khối 5, 6 (Eq. 10, 11; lưới τ, λ1) |
| Yu et al., SimGCL, SIGIR 2022 | arXiv 2112.08679v4 | khối 5 (τ = 0,2) |
| van den Oord et al., CPC (InfoNCE) | arXiv 1807.03748v2 | khối 5 (Eq. 4) |
| Balloccu et al., ECIR 2023 | arXiv 2301.05944v1 | khối 8, Path Coverage ("fidelity") |
| Tan et al., CountER, CIKM 2021 | arXiv 2108.10539 (ar5iv, bản mới nhất v3) | khối 8, Faithfulness (PN, PS: Eq. 14, 15) |
| Yuan et al., GNN explainability survey (TPAMI) | arXiv 2012.15445 (ar5iv; abstract khác v3, số phương trình có thể lệch bản TPAMI) | khối 8 (Fidelity+, Eq. 1–2) |
| Xian et al., PGPR, SIGIR 2019 | arXiv 1906.05237v1 | khối 8 (đường ≤ 3 bước) |
| Jain & Wallace, Attention is not Explanation, NAACL 2019 | arXiv 1902.10186v3 | khối 8 (không lấy attention làm bằng chứng) |
| Wang et al., KGAT, KDD 2019 | arXiv 1905.07854 (ar5iv, không ghi bản; có thể v2) + code tác giả `xiangwang1223/knowledge_graph_attention_network` (README, Main.py, KGAT.py, parser.py, loader_kgat.py, helper.py) | khối 9 |

---

## 1. Kiến trúc tổng thể (khung 2.1)

Luồng (mỗi mũi tên là một khối; khối mới in đậm):

```
dữ liệu Amazon (01–02) → M, U (03) → đồ thị G (04)
   → KÊNH HÀNH VI: LightGCN trên user–item train            → e_u, e_i      (khối 1)
   → KÊNH PHẦN CỨNG: RGAT trên đồ thị con phần cứng H       → h_b, h_l      (khối 2, 3)
   → GỘP KÊNH có attention, có cổng                          → z_u, z_i, ŷ   (khối 4)
   → huấn luyện: L_BPR + λ1 L_comp + λ2 ‖Θ‖²                                 (khối 5, 6)
   → MẶT NẠ CỨNG lúc suy luận (QĐ 4-9)                       → top-K         (khối 7)
   → GIẢI THÍCH: đường u → b → l → c, câu tiếng Việt                         (khối 8)
   → FastAPI → Spring Boot → React (nội dung 10)
```

Hình cho chương 2 cô yêu cầu vẽ bằng công cụ vector (draw.io / TikZ); làm khi viết chương, không ở đây.

**Ràng buộc cứng và mềm (nội dung 6; Nam chốt 15/10/2026).** Không làm module ràng buộc mềm riêng:
- **ràng buộc mềm = L_comp** (khối 5): phạt khi biểu diễn thân và ống không lắp được nằm gần nhau, lúc huấn luyện; mô hình vẫn có thể xếp ống vi phạm lên cao (đo bằng CVR trước mặt nạ);
- **ràng buộc cứng = mặt nạ** (khối 7, công thức 15; biến thể ∃b công thức 16): lúc suy luận, gán −∞ cho ống chắc chắn vi phạm, nên CVR sau mặt nạ = 0 do cách dựng.

Ký hiệu chung (theo khung 1.2.1): 𝒰 người dùng, ℐ sản phẩm, ℐ_body / ℐ_lens / ℐ_acc; **B_u** = tập thân trong train của u (khung viết b ∈ ℋ_u); M, U ∈ {0,1}^{537×1.033}; số lớp LightGCN ký hiệu **L** (khung dùng K, trùng với K của top-K — [ĐỀ XUẤT CHO CÔ] đổi ký hiệu, đã nêu ở `khung_co_doi_chieu.md`).

---

## 2. Khối 1 — Kênh hành vi (LightGCN, dùng lại 05b)

**(a) Ví dụ tính tay** (log `run_vidu_tinh_tay`, khối 1). Train có 4 cạnh: u1–A (thân Canon), u1–B (ống EF), u2–B, u2–C (thẻ nhớ). Bậc: u1 2, u2 2, A 1, B 2, C 1. Embedding 1 chiều lớp 0: u1 = 1, u2 = 0, A = 0,5, B = −0,5, C = 1. Một lớp (L = 1):
- e_u1⁽¹⁾ = A/√(2·1) + B/√(2·2) = 0,35355 − 0,25 = **0,10355**; e_u1 = (1 + 0,10355)/2 = **0,55178**.
- e_B⁽¹⁾ = u1/√(2·2) + u2/√(2·2) = 0,5; e_B = (−0,5 + 0,5)/2 = **0**. e_C⁽¹⁾ = u2/√(1·2) = 0; e_C = **0,5**.
- ŷ(u1, B) = 0; ŷ(u1, C) = 0,27589; BPR(u1, B, C) = −ln σ(0 − 0,27589) = **0,84058** (lúc đầu mô hình xếp sai: điểm âm mẫu C cao hơn item đã mua B, nên loss lớn và gradient sẽ kéo B lên).

**(b) Vào / ra.** Vào: 460.193 cặp train. Ra: e_u ∈ ℝ⁶⁴ (67.661 người), e_i ∈ ℝ⁶⁴ (27.940 sản phẩm).

**(c) Công thức** (khung 2.2, LightGCN Eq. 3–4):

  (1) e_u⁽ˡ⁺¹⁾ = Σ_{i∈𝒩_u} e_i⁽ˡ⁾ / √(|𝒩_u| |𝒩_i|),  e_i⁽ˡ⁺¹⁾ = Σ_{u∈𝒩_i} e_u⁽ˡ⁾ / √(|𝒩_i| |𝒩_u|)

  (2) e_u = (1/(L+1)) Σ_{l=0..L} e_u⁽ˡ⁾,  e_i tương tự

**(d) Siêu tham số:** giữ đúng cấu hình chốt của nội dung 5 (`ai/config/n5_final.toml`): d = 64, L = 3, Xavier, Adam lr 0,001, batch 2048, không dropout, λ (L2 trên e⁽⁰⁾) = 1e-3 (dò trên val ở nội dung 5). Nguồn: n5_eval_plan mục 7.1 (LightGCN §4.1.2).

**(e) Ghi chú.** LightGCN ở nội dung 5 cả 3 seed chạm 300 epoch ("chưa chắc hội tụ"); CaKG-Rec dùng cùng ngân sách 300 epoch để so công bằng (kế hoạch đánh giá mục 4). λ = 1e-3 lấy lại, không dò lại: cắt giảm ngân sách, ghi ở kế hoạch đánh giá (mục 3).

---

## 3. Khối 2 — Kênh phần cứng (RGAT trên đồ thị con H)

**(a) Ví dụ tính tay** (log, khối 2). Thân b (EOS 80D, ngàm EF-S) nhận tin từ ống l1 (EF-S 18-55), l2 (EF 50mm) qua quan hệ `rev_compatible_with`, và từ nút ngàm `canon_efs` qua `rev_has_spec_mount`. d = 2; h_b = (0,5; 0,5), h_l1 = (1; 0), h_l2 = (0; 1), h_ngàm = (1; 1); cho W⁽ʳ⁾ = I, W_0 = I, q = (1; 0), k = (0; 1), bias 0.
- q_b = h_b·q = 0,5; k_l1 = 0, k_l2 = 1 → logit LeakyReLU(0,5 + 0) = 0,5 và LeakyReLU(0,5 + 1) = 1,5.
- WIRGAT chuẩn hóa **trong từng quan hệ**: α(b←l1) = 0,2689, α(b←l2) = 0,7311 (softmax của 0,5 và 1,5). Quan hệ ngàm chỉ có 1 hàng xóm nên α = 1.
- Tin từ ống: 0,2689·(1; 0) + 0,7311·(0; 1) = (0,2689; 0,7311). Cộng tin ngàm (1; 1) và phần tự giữ W_0 h_b = (0,5; 0,5): **h_b' = ReLU(1,7689; 2,2311)**.

Ý nghĩa: thân "nghe" ống nào nhiều hơn là do attention học được; nhưng mỗi quan hệ có một phần riêng (ống không lấn được tin của ngàm), đúng tinh thần "bảo toàn cấu trúc ràng buộc" của khung.

**(b) Vào / ra.** Vào: đồ thị con H (dưới), không có nút người dùng, không có cạnh `interacted_with`. Ra: h_v ∈ ℝ⁶⁴ cho mỗi nút của H; dùng h_b (thân), h_l (ống).

**Đồ thị con H (phương án chính H_lõi)** — log `run_dem_cakg`, mục 1; `run_probe_cakg`:

| Loại nút | Số | Ghi chú |
|---|---:|---|
| item (thân 537 + ống 1.251) | 1.788 | ống: 1.033 ống của M + 126 ống "không chắc" (còn cạnh khổ / mục đích) + 113 ống chỉ có `suitable_for` − trùng; 8 ống "không chắc" không còn cạnh nào |
| ngàm / khổ / mục đích | 23 / 7 / 4 | |
| **Tổng** | **1.822** | |

| Quan hệ (cạnh xuôi; mỗi quan hệ có thêm `rev_` cùng số) | Cạnh |
|---|---:|
| `compatible_with` (crop_unknown = 0) | 68.786 |
| `compatible_with_crop_unknown` (cờ QĐ 3-11) | 1.686 |
| `crops_sensor` | 2.248 |
| `requires_adapter` | 16.301 |
| `has_spec_mount` (thân / ống chắc chắn) | 1.570 |
| `has_spec_sensor_format` | 1.498 |
| `suitable_for` | 1.080 |
| **7 quan hệ × 2 chiều = 14 quan hệ, 186.338 cạnh** | |

**Xử lý cờ cạnh** (yêu cầu của hạn chế nội dung 4, điểm 17):
- `ngam_khong_chac` (134 cạnh `has_spec → mount` của ống "không chắc"): **bỏ cạnh** (Nam chốt 14/10, HỎI 3), như QĐ 5-4 của R-GCN. Lý do: nếu giữ, đường thân → ngàm ← ống "không chắc" trông như "lắp được" (QĐ 3-4, 4-5). Ống vẫn giữ cạnh khổ / mục đích.
- `crop_unknown` (1.686 cạnh `compatible_with`): **tách thành quan hệ riêng**, để attention và W⁽ʳ⁾ phân biệt "lắp được, chưa rõ có cắt khung" với "lắp được chắc chắn". Vẫn là M = 1 trong L_comp.
- `src_phu_kien`, `phia` (cạnh ngàm của 954 phụ kiện và 2 × 155 cạnh của ngàm chuyển): chỉ có ở **phương án H_pk** (20 quan hệ: thêm `has_spec_mount_phukien`, `has_spec_mount_phia_ong`, `has_spec_mount_phia_than`). H_lõi không có phụ kiện, theo khung ("Body – Mount – Lens – Sensor Format"). **Nam chốt 14/10 (HỎI 2): dùng H_lõi.** H_pk (thêm biểu diễn cho 1.109 phụ kiện; item val có h: 9,30% → 13,47%; 97 ms so với 95 ms / bước) chỉ là thăm dò nếu còn giờ GPU.
- Không đưa tiêu cự / khẩu độ vào H (khung không nêu; thông tin đó đã nằm trong nhãn `suitable_for`).

**(c) Công thức** (Busbridge et al. 2019, §2.1, Eq. 1, 3, 4, 6, 8; viết lại cho một đầu, D = 1). Với nút i, quan hệ r, hàng xóm 𝒩_i^r (nút j có cạnh j → i loại r):

  (3) g_i⁽ʳ⁾ = W⁽ʳ⁾ h_i⁽ˡ⁾  (W⁽ʳ⁾ ∈ ℝ^{64×64})

  (4) a_ij⁽ʳ⁾ = LeakyReLU( q⁽ʳ⁾ᵀ g_i⁽ʳ⁾ + k⁽ʳ⁾ᵀ g_j⁽ʳ⁾ )  (logit cộng)

  (5) α_ij⁽ʳ⁾ = exp(a_ij⁽ʳ⁾) / Σ_{k∈𝒩_i^r} exp(a_ik⁽ʳ⁾)  (WIRGAT: chuẩn hóa trong từng quan hệ)

  (6) h_i⁽ˡ⁺¹⁾ = σ( Σ_r Σ_{j∈𝒩_i^r} α_ij⁽ʳ⁾ g_j⁽ʳ⁾ + W_0⁽ˡ⁾ h_i⁽ˡ⁾ + b⁽ˡ⁾ ),  σ = ReLU ở lớp 1, không có ở lớp 2

  h_v⁽⁰⁾ là embedding học được của nút v (mỗi nút một vector, như R-GCN baseline). Ra: h_v = h_v⁽²⁾.

Ghi chú cài đặt: trong `RGATConv` của PyG, q và k dùng chung cho mọi quan hệ (q ∈ ℝ^{64×1}), chỉ W⁽ʳ⁾ riêng; bài gốc Eq. 3 cho Q⁽ʳ⁾, K⁽ʳ⁾ riêng từng quan hệ. **Nam chốt 14/10 (HỎI 5): q⁽ʳ⁾, k⁽ʳ⁾ riêng từng quan hệ như bài** (thêm khoảng 3.300 tham số cho 2 lớp). Lớp tự cài trong probe dùng q, k chung để kiểm trùng PyG; bản cài thật kiểm trùng bằng cách đặt mọi q⁽ʳ⁾, k⁽ʳ⁾ bằng nhau.

**Kiểm `RGATConv` trong PyG 2.8.0.post1:** **có** (`torch_geometric.nn.RGATConv`, có `attention_mechanism="within-relation"`, `return_attention_weights`). Nhưng nó nhân ma trận W⁽ʳ⁾ riêng cho **từng cạnh** (tạo tensor [số cạnh, 64, 64]): một lớp forward + backward trên H_lõi **đỉnh 8.985 MiB** (> 6 GB của GTX 1660 Ti, tràn sang bộ nhớ chung, 1.302 ms) (log `run_probe_cakg`). Vì vậy **cài lại lớp `RGATLayer`** cùng công thức: tính g⁽ʳ⁾ = W⁽ʳ⁾h cho mọi nút một lần ([14, 1.822, 64]) rồi mới lấy theo cạnh. Kiểm trùng với `RGATConv` (cùng trọng số, 20.000 cạnh ngẫu nhiên): lệch đầu ra tối đa **1,91e-06**, lệch α tối đa **3,58e-07**; tổng α theo (nút đích, quan hệ) = 1,0000 ở mọi nhóm. Cả mô hình một bước: 95 ms, đỉnh 600 MiB (khối 6).

**(d) Siêu tham số**

| Tham số | Giá trị | Nguồn |
|---|---|---|
| số lớp | 2 | Busbridge §2.2: kiến trúc phân loại nút = 2 lớp RGAT (như R-GCN). 2 lớp đủ để thân → ngàm → ống |
| cơ chế | WIRGAT + logit cộng | Busbridge §4: "WIRGAT đi với logit cộng" làm nhỉnh hơn ở bài toán transductive |
| số đầu | 1 | Busbridge Bảng 4: dò {1, 2, 4}, không công bố giá trị chọn → **quyết định nhóm** |
| d | 64 | bằng LightGCN để gộp kênh |
| phân rã cơ sở | không | Busbridge dò {Full, 5, 10, 20, 30}; 14 quan hệ ít, W đầy đủ chỉ 2 × 14 × 64 × 64 = 114.688 tham số |
| LeakyReLU | độ dốc 0,2 | mặc định PyG; bài không ghi ("not found") |
| dropout | không | bài dò Uniform(0; 0,8), không công bố giá trị chọn → **quyết định nhóm** (giữ ít tham số dò) |
| phần tự giữ W_0 | có | **khác bài RGAT** (Eq. 8 không có W_0 h_i); lấy theo R-GCN Eq. 2. Lý do: nút ngàm / khổ có rất nhiều hàng xóm, và hai thân cùng ngàm có tập hàng xóm gần như trùng nhau, nên cần giữ phần riêng của chính nút |
| đầu vào | embedding theo mã nút | Busbridge §3.3.2 (đầu vào one-hot), R-GCN §2.2 |

Bài RGAT kết luận RGAT **không chắc hơn R-GCN** ("perform competitively or poorly", không trường hợp nào chắc chắn hơn R-GCN có ý nghĩa). Vì vậy không được viết "RGAT tốt hơn R-GCN" khi chưa có ablation; ablation "kênh phần cứng dùng R-GCN thay RGAT" là **thăm dò**, không đăng ký (kế hoạch mục 6).

**(e) Khác khung.** Khung viết RGAT "cô lập hoàn toàn nhiễu từ hành vi mua sắm". Đúng ở chỗ H không có người dùng; nhưng biểu diễn phần cứng của người dùng h_u (khối 4) lấy từ các thân họ đã đánh giá, tức vẫn dùng hành vi. **[ĐỀ XUẤT CHO CÔ]** sửa câu thành "đồ thị con không chứa cạnh hành vi".

---

## 4. Khối 3 — Sản phẩm không có cạnh tri thức (khoảng 87–91%)

**(a) Ví dụ tính tay** (log, khối 3–4). Thẻ nhớ C không có nút trong H. Người u2 không có thân. Với e_u2 = (0,1; 0,3), e_C = (0,3; 0,2): **ŷ(u2, C) = e_u2 · e_C = 0,09**, đúng bằng điểm LightGCN.

**Số thật** (log `run_dem_cakg`, mục 1–2; số item test lấy từ `khung_co_doi_chieu.md` mục 3c):
- H_lõi có 1.788 sản phẩm (6,4% catalog). **Item val có h: 6.291 / 67.661 = 9,30%**, tức **90,70% item val không có biểu diễn phần cứng**. (Khung nói ~87%: đó là 86,98% item test không có **bất kỳ** cạnh tri thức nào; tính theo H_lõi thì phần không có h còn lớn hơn.)
- Người có h_u (có thân trong H): **10.359 / 67.661 = 15,3%**. 47 người còn lại trong 10.406 người có thân chỉ có thân ngoài M.
- 14.249 người không có thân nhưng có ống trong H. **Nam chốt 14/10 (HỎI 4): h_u chỉ lấy từ thân**, nên những người này không có h_u.

**Cách xử lý (phương án chính): kênh vắng mặt, không gán vector giả.**
- Sản phẩm i không có nút trong H: **không có h_i** (cờ has_h(i) = 0). Không dùng vector 0 hay một vector "rỗng" học được, vì vector học được dùng chung sẽ cộng cùng một lượng cho mọi sản phẩm không có tri thức, không mang thông tin gì.
- Người dùng u không có thân trong H: không có h_u.
- **Cổng theo cặp** (khối 4, công thức 9): kênh phần cứng chỉ tham gia khi **cả** u lẫn i có h. Mọi cặp còn lại dùng đúng điểm hành vi e_uᵀe_i.

**Hệ quả phải nói rõ — [ĐỀ XUẤT CHO CÔ].** Với phương án này, CaKG-Rec **chỉ khác LightGCN** trên vùng (15,3% người có thân) × (9,30% sản phẩm có h). Ngoài vùng đó, điểm có cùng dạng với LightGCN (embedding vẫn khác vì huấn luyện chung). Vì vậy:
- trên toàn bộ người dùng, khác biệt Recall / NDCG với LightGCN có thể rất nhỏ; câu "vượt LightGCN về Recall/NDCG" (khung 2.6) **không thể hứa trước**;
- tác dụng phải được đo ở **người có thân** và **kịch bản ống cho người có thân** (1.060 người test), đúng chỗ khung đặt trọng tâm (2.5).

---

## 5. Khối 4 — Gộp hai kênh bằng attention (Adaptive Channel Fusion)

**(a) Ví dụ tính tay** (log, khối 3–4). Cho W = I, b = 0, q = (1; 1).
- Ống l2: e = (0,2; 0,4), h = (0,6; 0). ω_e = tanh 0,2 + tanh 0,4 = 0,57732; ω_h = tanh 0,6 + tanh 0 = 0,53705. β = softmax(ω_e, ω_h) = (0,51007; 0,48993). z_l2 = (0,10201; 0,20403; 0,29396; 0).
- Người u1 (có thân b): e = (0,5; 0,1), h_u1 = (0,4; 0,2) → β = (0,49612; 0,50388), z_u1 = (0,24806; 0,04961; 0,20155; 0,10078).
- **ŷ(u1, l2) = z_u1 · z_l2 = 0,09468 = phần hành vi 0,03543 + phần phần cứng 0,05925.**
- Cặp có một phía thiếu h dùng cổng: ŷ(u1, C) = e_u1·e_C = 0,17; ŷ(u2, l2) = e_u2·e_l2 = 0,14. Nếu **không** có cổng (gộp thẳng z_u·z_i) thì ŷ(u2, l2) = β_e(l2)·e_u2·e_l2 = 0,07141: điểm hành vi của mọi ống bị co lại ~một nửa với **mọi** người dùng, kể cả 84,7% người không có h_u. Đó là lý do chọn cổng.

**(b) Vào / ra.** Vào: e_u, e_i (khối 1), h_v (khối 2). Ra: z_u, z_i ∈ ℝ¹²⁸, điểm ŷ_ui.

**(c) Công thức.** Biểu diễn phần cứng của người dùng (quan hệ "owns", khối 8):

  (7) h_u = (1/|B_u^H|) Σ_{b∈B_u^H} h_b,  B_u^H = thân trong train của u có nút trong H

Attention theo từng nút (AM-GCN Eq. 8–9), tham số riêng cho phía người và phía sản phẩm:

  (8) ω_{v,c} = qᵀ tanh(W x_{v,c} + b),  c ∈ {e, h}, x_{v,e} = e_v, x_{v,h} = h_v;  β_v = softmax_c(ω_{v,c}) trên các kênh **có mặt** (thiếu h thì β_v = (1; 0))

  (9) z_v = [ β_{v,e} e_v ; β_{v,h} h_v ] ∈ ℝ¹²⁸ (ghép, không cộng);  ŷ_ui = z_uᵀ z_i nếu has_h(u)·has_h(i) = 1, ngược lại ŷ_ui = e_uᵀ e_i

  Khai triển: ŷ_ui = β_{u,e}β_{i,e} e_uᵀe_i + β_{u,h}β_{i,h} h_uᵀh_i — hai phần tách bạch, dùng lại ở khối 8.

**(d) Siêu tham số.** W ∈ ℝ^{64×64}, b, q ∈ ℝ⁶⁴ (h' = 64, **quyết định nhóm**: AM-GCN không ghi h'; HAN §5.3 chọn 128 cho q). Không dò.

**(e) Khác bài gốc / khung.**
- AM-GCN Eq. 10 **cộng** các kênh (Z = Σ α_c Z_c); ở đây **ghép** (9). Lý do: e và h học trong hai không gian khác nhau; cộng thì tích vô hướng sinh các số hạng chéo e_uᵀh_i không có nghĩa. Ghép cho điểm tách đúng thành phần hành vi + phần phần cứng (dùng để giải thích, khối 8).
- HAN (Eq. 7) lấy trung bình attention trên mọi nút → một trọng số chung cho cả đồ thị; AM-GCN giữ trọng số **theo từng nút** — chọn theo AM-GCN vì độ tin của kênh phần cứng khác nhau giữa các ống.
- Cổng theo cặp (9) là thêm của nhóm, không có trong khung → **[ĐỀ XUẤT CHO CÔ]** (khối 3).
- Rủi ro đã biết: với người có thân, điểm của sản phẩm có h (dạng z) và không có h (dạng e) có thang khác nhau; mô hình phải tự học độ lớn. Kế hoạch đánh giá in tỉ lệ loại sản phẩm trong top-10 để thấy nếu bị lệch.

---

## 6. Khối 5 — L_comp (InfoNCE theo M)

**(a) Ví dụ tính tay** (log, khối 5). Thân b = Canon 5D (FF, ngàm EF). Cosine: l1 EF 50mm (M = 1) 0,8; l2 EF-S 18-55 (M = 0) 0,3; l3 Nikon DX 35mm (M = 0) −0,2; l4 Sigma 17-50 DC "for Canon" (U = 1, QĐ 3-8) 0,6. τ = 0,2:
- sim/τ: dương 4; âm 1,5 và −1; **l4 không vào mẫu số**.
- ℓ(b, l1) = −log( e⁴ / (e⁴ + e^1,5 + e⁻¹) ) = log(1 + e^−2,5 + e⁻⁵) = **0,08510**.
- Nếu lỡ đưa l4 vào mẫu số: 0,37618, tức phạt mô hình vì để b gần một ống mà chính nhóm **không biết** có lắp được không.

**(b) Vào / ra.** Vào: h_b (537 thân), h_l (1.033 ống) của M; M, U. Ra: một số vô hướng L_comp.

**Số cặp** (log `run_dem_cakg`, mục 3):
- **Dương M = 1: 72.720** (= `compatible_with` 70.472 + `crops_sensor` 2.248).
- **Âm M = 0 ∧ U = 0: 476.155** (= `requires_adapter` 16.301 + incompatible 459.854). **Bỏ U = 1: 5.846.** Tổng 554.721 = 537 × 1.033.
- Dương mỗi thân: trung vị 103, TB 135,4, max 286. **34 thân không có cặp dương nào** (18 máy phim) → không làm "neo". 9 ống không có cặp dương.
- Âm mỗi thân (thân có dương): min 747, trung vị 843. Không cặp âm nào cùng chuỗi ngàm với thân (EF-S và EF là hai chuỗi khác nhau).
- Dương lệch theo ngàm: `canon_efs` 27.742, `nikon_f` 17.301, `sony_e` 10.830, `mft` 7.313, `canon_ef` 4.300 (5 ngàm nhiều nhất).

**`crops_sensor` và `requires_adapter` tính là gì:** `crops_sensor` (lắp trực tiếp, ảnh bị cắt) là **dương** vì M = 1 (QĐ 3-2). `requires_adapter` là **âm** vì M = 0 và không thuộc U (**Nam chốt 14/10, HỎI 6**). Hệ quả, **ghi vào hạn chế**: L_comp đẩy xa (EOS M, ống EF) dù người có ngàm chuyển dùng được — khớp với CVR_strict và mặt nạ, ngược với CVR_relaxed (khối 7).

**(c) Công thức** (khung 1.2.1 / 2.4; SGL Eq. 10; CPC Eq. 4):

  (10) s(b, l) = cos(h_b, h_l) / τ

  (11) 𝒩⁻(b) = { l : M_bl = 0 ∧ U_bl = 0 }

  (12) ℒ_comp = (1/|𝒫|) Σ_{(b,l⁺)∈𝒫} −log [ exp s(b,l⁺) / ( exp s(b,l⁺) + Σ_{l⁻∈𝒩⁻(b)} exp s(b,l⁻) ) ],  𝒫 = { (b,l) : M_bl = 1 }

**Cách lấy mẫu âm: không lấy mẫu — dùng toàn bộ 𝒩⁻(b).** Ma trận s chỉ có 537 × 1.033 ô nên tính hết mỗi bước được (RGAT + L_comp: 19,9 ms / bước, log `run_probe_cakg`). Không có nhiễu do lấy mẫu, dễ giải thích. Theo SGL Eq. 10 (dùng mọi nút khác làm âm, §3.5 nói in-batch chỉ để giảm chi phí).

**(d) Siêu tham số**

| Tham số | Giá trị | Nguồn |
|---|---|---|
| sim | cosine | SGL: "s(·) is set as cosine similarity function"; SimGCL chuẩn hóa L2 rồi tích vô hướng (tương đương) |
| τ | 0,2, không dò | SimGCL §4.1: "empirically let τ = 0.2" cho cả SimGCL và SGL. SGL dò {0,1; 0,2; 0,5; 1,0} (§4.1.2), không ghi giá trị chọn; §4.4.1: τ lớn (1,0) kém và chậm hội tụ, τ quá nhỏ (0,1) để vài âm mẫu lấn át |
| λ1 | dò trên val {0,01; 0,1; 1,0} | tập con của lưới SGL {0,005; 0,01; 0,05; 0,1; 0,5; 1,0} (§4.1.2); SGL không ghi giá trị chọn |

**(e) Khác khung.** Khung viết Σ (tổng) trên mọi cặp dương; ở đây lấy **trung bình** (chia |𝒫| = 72.720) để λ1 không phụ thuộc số cặp, như SGL và SimGCL tính trên batch → [ĐỀ XUẤT CHO CÔ] (chỉ đổi thang của λ1). Thêm định nghĩa rõ 𝒩⁻(b) bỏ cặp U (khung chỉ ghi "cặp vi phạm M = 0").

---

## 7. Khối 6 — L_total, λ1, λ2

**(a) Ví dụ** (log, khối 6): L_BPR = 0,6; L_comp = 0,08510; ‖Θ_batch‖² = 2,5; λ1 = 0,1; λ2 = 1e-3 → L_total = 0,6 + 0,00851 + 0,0025 = **0,61101**.

**(b), (c)** (khung 2.4; SGL Eq. 11 cùng dạng):

  (13) ℒ_BPR = (1/|ℬ|) Σ_{(u,i,j)∈ℬ} −ln σ(ŷ_ui − ŷ_uj),  j lấy đều trong sản phẩm u chưa có trong train (như 05b)

  (14) ℒ_total = ℒ_BPR + λ1 ℒ_comp + λ2 · ½(‖e_u⁽⁰⁾‖² + ‖e_i⁽⁰⁾‖² + ‖e_j⁽⁰⁾‖²)/|ℬ|

**(d)** λ2 = 1e-3, theo cấu hình LightGCN đã chốt (cùng cách tính L2 như 05b, theo code tác giả LightGCN); chỉ phạt embedding lớp 0 của kênh hành vi, không phạt tham số RGAT và gộp kênh (như SGL: Θ chỉ là tham số của L_main). λ1 dò ở khối 5. Mỗi bước: một batch BPR 2048 cặp + L_comp trên toàn bộ M; một bộ tối ưu Adam lr 0,001 cho mọi tham số.

**(e)** Khung viết λ2‖Θ‖² chung; ở đây Θ chỉ là e⁽⁰⁾ → ghi rõ trong chương 2 (không phải khác ý khung).

---

## 8. Khối 7 — Mặt nạ cứng, CVR trước / sau mặt nạ, CVR_relaxed

**(a) Ví dụ tính tay** (log, khối 7; ví dụ dựa trên người dùng thật uid 378 ở `khung_co_doi_chieu.md` mục 3a). Người có Sony a7 (`sony_e`) và Nikon D750 (`nikon_f`). Top-4 trước mặt nạ: Nikon 200-500 (D750: M = 1), Canon EF 70-200 (cả hai thân M = 0), thẻ nhớ, Sony FE 50 (a7: M = 1).
- **CVR trước mặt nạ @4** = 1 vi phạm / 3 ống chấm được = 0,3333.
- **QĐ 4-9:** chặn Canon EF (mọi thân M = 0); giữ Nikon 200-500 và Sony FE 50 → CVR sau mặt nạ = 0.
- **Biến thể ∃b của khung:** chặn Canon EF, **và cả** Nikon 200-500 (vì a7 M = 0) **và** Sony FE 50 (vì D750 M = 0). Người dùng hai hệ máy không được gợi ý ống nào cho cả hai thân.

**(b) Vào / ra.** Vào: điểm ŷ_u· (27.940), B_u, M, U. Ra: điểm sau mặt nạ, top-K.

**(c) Công thức.** ℐ_M = 1.033 ống của M; ℬ_M = 537 thân của M.

  (15) Cách chính (QĐ 4-9): 𝓜(u,l) = −∞ nếu l ∈ ℐ_M, B_u ≠ ∅, B_u ⊆ ℬ_M và ∀b ∈ B_u: M_bl = 0 ∧ U_bl = 0; ngược lại 0

  (16) Biến thể khung: 𝓜_∃(u,l) = −∞ nếu l ∈ ℐ_M và ∃b ∈ B_u ∩ ℬ_M: M_bl = 0 ∧ U_bl = 0; ngược lại 0

  (17) ŷ'_ul = ŷ_ul + 𝓜(u,l)

Điều kiện B_u ⊆ ℬ_M ở (15) khớp code `eval_05.certain_violation_mask` (người có một thân ngoài M không bị chặn ống nào, vì không phán chắc được). Sản phẩm không phải ống không bao giờ bị chặn.

**Số thật trên VAL** (log `run_dem_cakg`, mục 4):

| | QĐ 4-9 (15) | ∃b (16) |
|---|---:|---:|
| cặp (người có thân, ống trong M) bị chặn | 8.557.447 | 8.904.038 |
| kịch bản val "lắp được" (904 người): item val bị chặn | **0** | **109** |
| "không lắp được" (236): item val bị chặn | 236 | 236 |
| "không phán được" (12) | 0 | 0 |

(Trên test, cùng phép đếm ở `khung_co_doi_chieu.md`: 0 / 93 người nhóm lắp được.) **Nam chốt 14/10 (HỎI 1): (15) là cách chính; (16) của khung chạy và báo song song** (mọi chỉ số, cùng lần chấm test; không thuộc so sánh đăng ký).

**CVR trước và sau mặt nạ.** CVR_strict@K theo QĐ 4-9 (`eval_05.cvr_from_top`):

  (18) CVR_strict@K = Σ_u V_u@K / Σ_u N_u@K,  N_u@K = số ống chấm được trong top-K của u, V_u@K = số ống vi phạm; chỉ người có thân, bỏ người có N_u@K = 0

- **Báo cả hai:** CVR **trước** mặt nạ (top-K của ŷ) đo tác dụng của kênh phần cứng + L_comp; CVR **sau** mặt nạ (top-K của ŷ') **= 0 do cách dựng** (mặt nạ (15) chặn đúng các ống mà CVR đếm là vi phạm; mặt nạ (16) chặn nhiều hơn nên cũng = 0). Không được trình bày "CVR = 0" là kết quả học (giống MountAware, hạn chế nội dung 5 điểm 6).

**CVR_relaxed.** Nới cho ngàm chuyển **người dùng đã có trong train**:

  (19) 𝒜_u = { (m_ống, m_thân) : u có phụ kiện ngàm chuyển dạng "m_ống>m_thân" }

  (20) R1: ống l vi phạm strict được nới nếu ∃b ∈ B_u: (mount(l), mount(b)) ∈ 𝒜_u

  (21) R2 = R1, thêm: ∃b ∈ B_u: (b, l) ∈ `requires_adapter` và u có phụ kiện **một ngàm** có chữ "adapter" trong tiêu đề, ngàm = mount(b)

  (22) CVR_relaxed@K = Σ_u (V_u@K − số ống được nới) / Σ_u N_u@K  (mẫu số giữ như (18))

- **Ca uid 2465** (STATUS hạn chế nội dung 5, điểm 12): hai thân EOS M (`canon_efm`), có "Canon EOS M Mount Adapter" (iid 7524) mà nội dung 3 xếp là phụ kiện **một ngàm** `canon_efm` (bỏ sót phía EF). Top-10 **val** của LightGCN s1 có ống iid 19161 (`canon_ef`): strict = vi phạm; R1 **không** nới được (không có dạng a>b); **R2 nới được** (cặp `requires_adapter`, phụ kiện "adapter" cùng ngàm thân).
- **Số trên top-10 VAL của LightGCN s1** (log mục 5): 23.441 ống chấm được, 3.005 vi phạm → **CVR_strict@10 = 0,1282**; R1 nới 61 → **0,1256**; R2 nới 109 → **0,1235** (50 người được nới). 637 người có thân có ngàm chuyển a>b; 746 có phụ kiện một ngàm chữ "adapter".
- **Nam chốt 14/10 (HỎI 7): CVR_strict là số chính. CVR_relaxed báo cả R1 lẫn R2: R1 là số relaxed chính** (hướng ngàm chuyển đọc được từ tiêu đề dạng a>b); **R2 là số phụ** vì dựa vào chữ "adapter" trong tiêu đề, chưa đo độ đúng. Ca uid 2465 chỉ R2 nới được → ghi rõ khi trình bày. Cả hai đều là **cận dưới** (chỉ biết ngàm chuyển người dùng có đánh giá).
- CVR_relaxed sau mặt nạ (15) cũng = 0 (relaxed ≤ strict). Mặt nạ "mềm" (không chặn ống lắp được qua ngàm chuyển người đó có) **không làm** (Nam chốt 15/10: ràng buộc mềm là L_comp, xem mục 1).

---

## 9. Khối 8 — Giải thích: đường u → b → l → c, Path Coverage, Faithfulness

**"owns" = cạnh `interacted_with` tới sản phẩm loại thân** (13.495 cạnh của 10.406 người, `khung_co_doi_chieu.md` 3b). Nghĩa thật: người dùng **đã viết đánh giá** thân trong train (QĐ 3-5), không xác nhận đang sở hữu → **[ĐỀ XUẤT CHO CÔ]** ghi trong luận văn là "owns (suy ra từ đánh giá)" hoặc đổi tên `reviewed_body`.

**Đường giải thích** (khung 2.4; đường dài ở khung 1.2.1 u → b → mount → l → spec → c **không đi được** vì đồ thị không có cạnh spec → usecase, `khung_co_doi_chieu.md` 3b):

  (23) 𝒫_{u→l} = ( u –owns→ b* –ρ→ l –suitable_for→ c* ),  ρ ∈ {compatible_with, crops_sensor}

Thêm nhánh `crops_sensor` (khung chỉ có `compatible_with`) → **[ĐỀ XUẤT CHO CÔ]**: trên top-10 val của LightGCN, 639 ống chỉ nối với thân người dùng bằng `crops_sensor` (log mục 6); trên test, 7 người kịch bản chỉ nối bằng `crops_sensor`.

**(a) Ví dụ tính tay** (log, khối 8). Người có D750 và D500 (cùng ngàm Nikon F, cả hai M = 1 với ống l). β_h(u) = 0,4, β_h(l) = 0,5; h_D750 = (0,9; 0,1), h_D500 = (0,3; 0,5), h_l = (0,8; 0,2). Theo (7), h_u là trung bình nên phần phần cứng của ŷ_ul **tách đúng** thành đóng góp từng thân:
- c(D750) = 0,4 · 0,5 · ⟨h_D750, h_l⟩ / 2 = **0,0740**; c(D500) = **0,0340**; tổng 0,1080 = β_h(u)β_h(l)⟨h_u, h_l⟩. → **b* = D750**.

**"Trọng số liên kết cao nhất" lấy từ đâu:**
- **b\***: thân có đóng góp lớn nhất vào phần phần cứng của điểm, trong các thân có M_bl = 1:

  (24) c_u(b, l) = β_{u,h} β_{l,h} h_bᵀ h_l / |B_u^H|,  b* = argmax_{b∈B_u^H, M_bl=1} c_u(b, l)

  Đây là phân rã **chính xác** của điểm (từ (7), (9)), không phải attention. Lý do không dùng attention của RGAT cho b*: Jain & Wallace (2019) cho thấy trọng số attention tương quan yếu với độ quan trọng thật, và attention khác hẳn vẫn cho cùng dự đoán.
- **c\***: nhãn mục đích của l có hệ số attention α lớn nhất ở lớp RGAT thứ 2 trên quan hệ `rev_suitable_for` (tin từ nút mục đích về ống, công thức (5)). Phần lớn ống có 1 nhãn (980 ống có 1.080 cạnh `suitable_for`) nên α = 1. Đây là chỗ duy nhất dùng attention; kiểm bằng Faithfulness.
- Nam đồng ý cách chọn b*, c* này (14/10, HỎI 8).

**Mẫu câu tiếng Việt** (mọi chỗ trong ngoặc nhọn đều lấy từ đồ thị, không sinh tự do → không có chi tiết ngoài đồ thị):
- `compatible_with`: "Gợi ý **{l}** vì ống này lắp trực tiếp được trên **{b\*}** bạn đã mua (ngàm **{mount}**), và phù hợp chụp **{c\*}** (tiêu cự {f} mm, khẩu độ tối đa f/{a})."
- `crops_sensor`: "… lắp trực tiếp được trên **{b\*}**, nhưng ống thiết kế cho cảm biến nhỏ hơn nên ảnh sẽ bị cắt khung …"
- cạnh có `crop_unknown`: "… lắp được trên {b\*}; chưa rõ máy có tự cắt khung với ống này không …"
- ống không có `suitable_for`: dùng đường ngắn u → b* → l, bỏ vế mục đích.
- Thân máy phim: không viết "cảm biến full-frame" (hạn chế nội dung 4, điểm 16).

**Path Coverage.** Nguồn: Balloccu et al. (ECIR 2023, §2.3, Bảng 3) định nghĩa *fidelity* = "tỉ lệ sản phẩm được gợi ý giải thích được" (không có phương trình đánh số; trích lại Peake & Wang, KDD 2018); Tan et al. (CIKM 2021, Bảng 2, §6.4) báo cùng đại lượng. Định nghĩa đo offline cho CaKG-Rec:

  (25) PC@K = #{(u, l) : u ∈ 𝒰_B, l ∈ top-K'(u), l là ống, có đường (23) đủ 3 bước} / #{(u, l) : u ∈ 𝒰_B, l ∈ top-K'(u), l là ống}

  𝒰_B = người có thân; top-K' = top-K **sau mặt nạ**. Báo thêm PC_ngắn@K (đường u → b → l) và PC_mọi_sp@K (mẫu số là mọi sản phẩm trong top-K, đúng định nghĩa fidelity của Balloccu).
- Chú ý **do cách dựng**: sau mặt nạ (15), mọi ống **chấm được** trong top-K đều có ít nhất một thân M = 1, nên đường ngắn luôn có với các ống đó. Mẫu số của (25) gồm cả ống **không chấm được** (ống "không chắc", ống ngoài M, ống có cặp U), nên PC không tự bằng 1.
- **Trần thô** trên top-10 val của LightGCN s1 (chưa mặt nạ; log mục 6): trong 23.441 ống chấm được, 20.436 (87,2%) có đường ngắn; **9.095 (38,8%) có đủ đường** (44,5% số ống lắp được). Chỉ 787 / 1.033 ống của M có `suitable_for` — đây là giới hạn chính của PC.

**Faithfulness (độ trung thực).** Nguồn: PN (Probability of Necessity) của Tan et al. (CIKM 2021, §5.2, Eq. 14): bỏ phần được nêu trong lời giải thích, xếp hạng lại, xem sản phẩm có rơi khỏi top-K không; Fidelity+ của Yuan et al. (survey, §VII-B1, Eq. 1–2): bỏ phần "quan trọng" rồi đo độ tụt của dự đoán. Định nghĩa đo offline:
- Với mỗi cặp (u, l) có đường (23): tạo đồ thị phản thực tế bằng cách **bỏ đúng các cạnh của đường**: b* khỏi B_u^H (tính lại h_u theo (7)); cạnh (b*, l) loại ρ và (l, c*) `suitable_for` khỏi H (chạy lại RGAT). Giữ nguyên kênh hành vi. Chấm lại mọi ứng viên của u, xếp lại, áp mặt nạ.

  (26) FS_PN@K = (1/|𝒮|) Σ_{(u,l)∈𝒮} 𝟙[ l ∉ top-K'_cf(u) ],  ΔS = (1/|𝒮|) Σ (ŷ'_ul − ŷ'^{cf}_ul)

  𝒮 = các cặp có đường giải thích trong top-K' trên test (mẫu ngẫu nhiên tối đa 2.000 cặp, seed cố định, vì mỗi cặp phải chạy lại RGAT: 28 ms một lần tính biểu diễn, log `run_probe_cakg`).
- **Đối chứng:** cùng phép bỏ nhưng với một đường **ngẫu nhiên** cùng dạng (thân khác của u có M = 1 với l nếu có; nhãn mục đích ngẫu nhiên của l). Lời giải thích được coi là trung thực hơn ngẫu nhiên khi FS_PN(giải thích) − FS_PN(ngẫu nhiên) có khoảng 95% không chứa 0. Với người chỉ có 1 thân phù hợp, không có đối chứng thân → báo riêng.
- **Làm rõ 15/10/2026 (Nam xác nhận; kế hoạch mục 14):** bỏ cạnh là bỏ cả hai chiều (r, rev_r); 𝒮 chỉ gồm đường đủ 3 bước; nhãn đối chứng **khác c\*** (ống chỉ có một nhãn: không có đối chứng nhãn, đếm và báo). Cài thành hai đối chứng, mỗi cái thay một thành phần: đối chứng thân (b', l, c\*) cho C9; đối chứng nhãn (b\*, l, c'). Dưới 30 cặp có đối chứng thân trên test thì C9 chỉ báo mô tả.
- Ý nghĩa và giới hạn: FS thấp không có nghĩa câu giải thích **sai sự kiện** (mọi cạnh đều có thật, script kiểm), mà nghĩa là gợi ý chủ yếu đến từ kênh hành vi; đó chính là thông tin cần báo. PS (Eq. 15 của Tan) không đo (phải bỏ mọi thứ **ngoài** đường, kể cả kênh hành vi: không có nghĩa với mô hình này) → ghi hạn chế.

**[ĐỀ XUẤT CHO CÔ]**: khung viết "triệt tiêu hoàn toàn ảo giác", "độ trung thực cao". Chỉ cam kết được: (i) câu giải thích chỉ chứa sự kiện có trong đồ thị (đúng do cách dựng, có kiểm thử); (ii) Faithfulness là số đo được, chưa biết cao hay thấp.

---

## 10. Khối 9 — Baseline KGAT

**(a) Ví dụ tính tay** (log, khối 9). Nút h (ống) có 2 hàng xóm t1 = (1; 0), t2 = (0; 1) cùng quan hệ r; e_h = (0,5; 0,5), e_r = (0,1; 0), W_r = I. tanh(e_h + e_r) = (0,53705; 0,46212); π thô = 0,53705 và 0,46212; sau softmax **0,51872 và 0,48128**.

**(b) Vào / ra.** Vào: đồ thị cộng tác = toàn bộ `kg_hetero.pt` (18 quan hệ; `interacted_with` đóng vai "Interact" của bài), bỏ 134 cạnh `ngam_khong_chac` mỗi chiều như R-GCN (QĐ 5-4): 95.646 nút, 1.116.682 cạnh. Ra: e*_u, e*_i ∈ ℝ¹⁷⁶, ŷ.

**(c) Công thức theo bài** (KGAT §3.1–3.4):

  (27) g(h,r,t) = ‖W_r e_h + e_r − W_r e_t‖²₂  (TransR, Eq. 1);  ℒ_KG = Σ −ln σ( g(h,r,t') − g(h,r,t) )  (Eq. 2)

  (28) π(h,r,t) = (W_r e_t)ᵀ tanh(W_r e_h + e_r)  (Eq. 4), softmax trên mọi bộ ba có đầu h (Eq. 5);  e_{𝒩_h} = Σ π(h,r,t) e_t  (Eq. 3)

  (29) e_h⁽ˡ⁾ = LeakyReLU( W_1 (e_h⁽ˡ⁻¹⁾ + e_{𝒩_h}⁽ˡ⁻¹⁾) ) + LeakyReLU( W_2 (e_h⁽ˡ⁻¹⁾ ⊙ e_{𝒩_h}⁽ˡ⁻¹⁾) )  (Bi-Interaction, Eq. 8, mặc định của bài)

  (30) e*_u = e_u⁽⁰⁾ ‖ … ‖ e_u⁽ᴸ⁾ (Eq. 11);  ŷ(u,i) = e*_uᵀ e*_i (Eq. 12);  ℒ_KGAT = ℒ_KG + ℒ_CF + λ‖Θ‖² (Eq. 14), ℒ_CF là BPR (Eq. 13); tối ưu xen kẽ ℒ_KG và ℒ_CF (§3.4.1)

**(d) Siêu tham số và chỗ khác bài gốc**

| Mục | Bài / code tác giả | Ở đây | Lý do |
|---|---|---|---|
| d, lớp | 64; L = 3, [64, 32, 16] (bài §4.2.3) | như bài | — |
| tác tử gộp | Bi-Interaction | như bài | — |
| batch CF / KG | 1024 (bài); KG 2048 (mặc định code) | 1024 / 2048 | — |
| lr | bài dò {0,05; 0,01; 0,005; 0,001}, không ghi giá trị chọn; lệnh README dùng 0,0001 | **dò {1e-3, 1e-4} trên val** | 1e-3 thuộc lưới bài, 1e-4 là lệnh README; cắt lưới vì ngân sách |
| L2 | bài dò {1e-5 … 1e2}; README `regs [1e-5, 1e-5]` | 1e-5 | README |
| message dropout | bài dò {0 … 0,8}; README 0,1 mỗi lớp | 0,1 | README |
| node dropout | bài có dò; trong code dòng dùng nó bị chú thích (không dùng) | không | theo code |
| attention | bài không nói cách cập nhật; code tác giả **tính lại một lần mỗi epoch, không có gradient** (`update_attentive_A`) | **như code: một lần / epoch** (Nam chốt 14/10, HỎI 9) | (a) có gradient mỗi bước: 1,2 phút / epoch, 3.284 MiB; (b) một lần / epoch: 0,5 phút / epoch, 1.347 MiB (log `run_probe_cakg`). Đã kiểm 14/10: trong code tác giả ma trận attention mới **không** được dùng trong lan truyền (mục "Kiểm code tác giả" dưới bảng) — ở đây cài cho nó được dùng thật |
| ℒ_KG gồm gì | code: mọi cạnh kể cả Interact và chiều ngược, đuôi âm lấy đều trên mọi nút | như code (546 bước KG / epoch, 3,3 s) | — |
| khởi tạo | Xavier (bài); README khuyên khởi tạo từ BPR-MF đã huấn luyện | Xavier, không pretrain | để so công bằng với LightGCN / CaKG-Rec (cũng từ đầu) → ghi sai khác |
| cờ cạnh | — | bỏ 134 cạnh `ngam_khong_chac`; các cờ khác bỏ qua | như R-GCN (QĐ 5-4) |
| dừng sớm | bài: recall@20 val không tăng 50 epoch; code: 10 lần chấm × 10 epoch | NDCG@20 val mỗi 10 epoch, dừng sau 5 lần không tăng, tối đa 300 epoch | như QĐ 5-5 / LightGCN; sai khác so với bài (README chạy 1000 epoch) |
| tập đo | bài: 80/20 ngẫu nhiên, all-ranking | chia theo thời gian, full ranking (nội dung 2, 5) | — |

**Kiểm code tác giả: ma trận attention mới có được dùng trong lan truyền không** (Nam yêu cầu trước khi cài, HỎI 9; đọc 14/10/2026 nhánh `master` của `xiangwang1223/knowledge_graph_attention_network`: `Model/KGAT.py`, `Model/Main.py`, `Model/utility/loader_kgat.py`, `Model/utility/batch_test.py`). **Kết quả: không.**
- Lan truyền (`_create_bi_interaction_embed`, cùng `_create_gcn_embed`, `_create_graphsage_embed`) đọc `A = self.A_in`, cắt bằng `_split_A_hat`, đổi sang `tf.SparseTensor` bằng `_convert_sp_mat_to_sp_tensor` với giá trị là mảng numpy → **hằng số trong đồ thị TF**, tạo **một lần** khi dựng mô hình (`__init__` → `_build_model_phase_I`). Không dùng placeholder.
- `update_attentive_A` tính điểm attention, chạy softmax (`self.A_out`, placeholder `A_values` chỉ dùng ở đây) rồi chỉ **gán lại thuộc tính Python** `self.A_in = sp.coo_matrix(...)`. Không có dòng nào dựng lại đồ thị hay tạo lại các tensor thưa.
- Feed dict của bước CF (`generate_train_feed_dict`) và lúc chấm (`generate_test_feed_dict`) chỉ có người dùng, item, dropout — không có giá trị attention.
- Hệ quả: trong code tác giả, mọi epoch lan truyền trên Laplacian **ban đầu** `sum(data_generator.lap_list)` (chuẩn hóa D⁻¹A, `adj_type = 'si'`); tri thức chỉ tác động qua embedding chung do bước TransR cập nhật. Attention tính mỗi epoch rồi bỏ.
- **Cách cài ở đây** (đúng mô tả của bài §3.2 Eq. 4–5, theo lịch cập nhật của code): sau mỗi epoch tính lại π theo (28) **không gradient**, và **dùng π mới cho lan truyền ở epoch sau**; epoch đầu dùng π tính từ embedding khởi tạo. Đây là sai khác so với code tác giả (code không dùng π), ghi trong báo cáo. Nếu Nam muốn chép đúng hành vi code (bỏ attention khỏi lan truyền) thì phải đổi kế hoạch, hỏi lại trước.

---

## 11. Tổng hợp [ĐỀ XUẤT CHO CÔ] và [HỎI]

**[ĐỀ XUẤT CHO CÔ]** (chỗ khác khung, kèm lý do và số). **Ghi chú nội bộ, không gửi cô** (Nam chốt 14/10); các sửa câu chữ xử lý khi viết báo cáo:

| # | Khung | Đề xuất | Số / lý do |
|---|---|---|---|
| Đ1 | Mặt nạ chặn khi ∃b có M = 0 ∧ U = 0 | Dùng QĐ 4-9 (mọi thân M = 0, không cặp U); ∃b chỉ là biến thể | val: ∃b chặn item val của 109 / 904 người "lắp được" (test 93 / 762); người hai hệ máy bị chặn cả ống cho thân kia (khối 7) |
| Đ2 | CVR → 0 là kết quả | Báo CVR **trước** mặt nạ (kết quả học) và sau (= 0 do cách dựng) | khối 7 |
| Đ3 | Đường u → b → mount → l → spec → c | Dùng đường u → b → l → c của khung 2.4, thêm nhánh `crops_sensor` | đồ thị không có cạnh spec → usecase; 639 ống top-10 val chỉ qua `crops_sensor` |
| Đ4 | "owns" | "owns (suy ra từ đánh giá thân)" | cạnh thật là đã viết đánh giá (QĐ 3-5) |
| Đ5 | Kênh phần cứng "cô lập hoàn toàn" nhiễu hành vi | "đồ thị con không có cạnh hành vi" | h_u lấy từ thân người dùng đã đánh giá |
| Đ6 | ~87% sản phẩm không có tri thức: khung không nói xử lý | Kênh vắng mặt + cổng theo cặp; CaKG-Rec chỉ khác LightGCN trên 15,3% người × 9,30% sản phẩm | khối 3; không hứa trước "vượt LightGCN" trên toàn bộ người dùng |
| Đ7 | L_comp dạng tổng | Lấy trung bình trên 72.720 cặp dương; tập âm bỏ cặp U | khối 5; thang của λ1 không phụ thuộc số cặp |
| Đ8 | "triệt tiêu hoàn toàn ảo giác", "độ trung thực cao" | Chỉ cam kết câu chỉ chứa sự kiện có trong đồ thị; Faithfulness là số đo, chưa biết | khối 8 |
| Đ9 | Ký hiệu K cho số lớp LightGCN | Đổi thành L | trùng K của top-K |
| Đ10 | Baseline: không có "LightGCN + mặt nạ" | Thêm LightGCN + mặt nạ (15) (không huấn luyện thêm) | để tách tác dụng của kênh phần cứng khỏi tác dụng của mặt nạ (kế hoạch, so sánh C2) |
| Đ11 | 2.3 "18 loại quan hệ" | Kênh phần cứng dùng 14 quan hệ (7 × 2 chiều), tách cờ `crop_unknown` | khối 2 |

**Quyết định của Nam (14/10/2026)** cho các câu [HỎI] của thiết kế (HỎI 10–13 ở kế hoạch đánh giá, mục 13):

| # | Câu hỏi | Đề xuất của Claude | **Nam chốt 14/10/2026** |
|---|---|---|---|
| HỎI 1 | Mặt nạ chính: QĐ 4-9 hay ∃b? | QĐ 4-9 | **QĐ 4-9 là cách chính; ∃b của khung chạy và báo song song** |
| HỎI 2 | H_lõi hay H_pk? | H_lõi | **H_lõi** |
| HỎI 3 | 134 cạnh ngàm của ống "không chắc"? | Bỏ | **Bỏ** |
| HỎI 4 | h_u chỉ từ thân hay cả ống? | Chỉ thân | **Chỉ thân** |
| HỎI 5 | q, k của RGAT chung hay riêng từng quan hệ? | Riêng | **Riêng từng quan hệ, như bài** |
| HỎI 6 | `requires_adapter` là cặp âm trong L_comp? | Có | **Có; ghi vào hạn chế** |
| HỎI 7 | CVR_relaxed: R1 hay R2 làm số chính? | R2 | **CVR_strict vẫn là số chính. CVR_relaxed báo cả R1 lẫn R2; R1 là số relaxed chính, R2 là số phụ (dựa vào chữ "adapter", chưa đo)** |
| HỎI 8 | b* theo đóng góp (24), c* theo attention RGAT? | Đồng ý | **Đồng ý** |
| HỎI 9 | Attention KGAT một lần / epoch hay mỗi bước? | Một lần / epoch | **Như code tác giả (một lần / epoch). Trước khi cài, kiểm "ma trận attention mới có được dùng trong lan truyền không" và ghi kết quả** (khối 9, mục "Kiểm code tác giả") |

**Hạn chế phát sinh từ các chốt** (đưa vào mục hạn chế khi viết báo cáo): `requires_adapter` là cặp âm của L_comp (HỎI 6); R2 dựa vào chữ "adapter" chưa đo độ đúng (HỎI 7); ablation chỉ 1 seed (kế hoạch HỎI 11).

---|---|---|
| HỎI 1 | Mặt nạ chính: QĐ 4-9 hay ∃b? (đã treo trong STATUS) | QĐ 4-9, báo cô (Đ1) |
| HỎI 2 | Đồ thị con: H_lõi (thân, ống) hay H_pk (thêm 1.109 phụ kiện có ngàm)? | H_lõi (đúng khung); H_pk là thăm dò nếu còn giờ GPU |
| HỎI 3 | 134 cạnh ngàm của ống "không chắc": bỏ (như QĐ 5-4) hay quan hệ riêng? | Bỏ |
| HỎI 4 | h_u chỉ từ thân (đúng "owns"), hay cả ống người dùng có (thêm 14.249 người có h_u)? | Chỉ thân (đường giải thích cần thân); cả ống là thăm dò |
| HỎI 5 | q, k của RGAT: dùng chung mọi quan hệ (như PyG) hay riêng từng quan hệ (như bài Eq. 3)? | Riêng từng quan hệ (đúng bài; thêm khoảng 3.300 tham số cho 2 lớp); kiểm trùng PyG bằng cách đặt mọi q⁽ʳ⁾, k⁽ʳ⁾ bằng nhau |
| HỎI 6 | `requires_adapter` là cặp âm trong L_comp? | Có (M = 0, khớp mặt nạ và CVR_strict) |
| HỎI 7 | CVR_relaxed: R1 hay R2 làm số chính? | R2 chính (bắt được uid 2465), R1 báo kèm |
| HỎI 8 | Giải thích: b* theo đóng góp chính xác (24), c* theo attention RGAT? | Đồng ý |
| HỎI 9 | KGAT: attention một lần / epoch (code tác giả) hay mỗi bước có gradient (đúng chữ của bài hơn, chậm 2,4 lần)? | Một lần / epoch |
| HỎI 10–12 | Ngân sách và cắt giảm | Ở kế hoạch đánh giá, mục 9 |

---

## 12. Việc khi cài (sau khi Nam chốt; chưa làm)

- `ai/pipeline/06_cakg_train.py` (mô hình, dùng lại `train_05.run`, `eval_05`), `ai/pipeline/rgat_layer.py` (lớp `RGATLayer`, chép từ `probe_cakg.py` kèm kiểm trùng PyG), `ai/pipeline/07_kgat_train.py`.
- `eval_05.py`: thêm chấm **trước / sau mặt nạ**, CVR_relaxed (R1, R2), mặt nạ ∃b (biến thể); `train_05.py`: ghi `torch.cuda.max_memory_allocated` vào `result.json` (hiện chưa ghi, `khung_co_doi_chieu.md` 3d).
- `ai/pipeline/08_explain.py`: đường (23), câu tiếng Việt, PC (25), FS (26).
- Kiểm thử dựng tay: mọi ví dụ ở file này (số trong `run_vidu_tinh_tay_20261014_lan2.log`) chạy qua code thật phải ra đúng số.
- Sửa `eval_05.py`, `train_05.py` là sửa code nội dung 5 (của nhóm, không phải của Hải từ `62abf54`) — vẫn ghi CHANGELOG khi sửa.
