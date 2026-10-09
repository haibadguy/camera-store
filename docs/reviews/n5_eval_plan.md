# Kế hoạch đánh giá nội dung 5 (baseline và cách đo) — đăng ký trước

- Viết ngày 09/10/2026, nhánh `nam/content4`, **trước khi sửa code 05 và trước khi huấn luyện bất kỳ mô hình nào**.
- Mốc thời gian: commit chứa file này. Mọi thay đổi kế hoạch trước khi chạy test ghi vào mục 13 ("Sửa đổi kế hoạch"), commit riêng. Sau khi chạy test thì không sửa kế hoạch nữa.
- 6 câu [HỎI] đã được Nam chốt ngày 09/10/2026 (mục 12); các mục liên quan đã sửa theo (mục 13).
- Số liệu trong file này do 2 script khảo sát sinh ra (chỉ đếm và đo tài nguyên, **không huấn luyện**):

| Script | Log |
|---|---|
| `ai/survey/content5/survey_n5_sets.py` | `ai/data/survey/n5/run_survey_n5_sets_20261009_lan1.log` |
| `ai/survey/content5/probe_gpu.py` (trọng số ngẫu nhiên, không `optimizer.step`) | `ai/data/survey/n5/run_probe_gpu_20261009_lan1.log` |

## 1. Ví dụ trước

Catalog nhỏ có 5 sản phẩm: **A** ống Canon EF, **B** ống Nikon F, **C** thẻ nhớ, **D** thân Canon EOS (ngàm EF-S), **E** chân máy.

Người dùng u1: train = {D}, val = E, test = A. Mô hình cho điểm: B 0,9; C 0,8; A 0,7; E 0,1 (D đã mua nên bị loại khỏi danh sách).

**Xếp hạng toàn bộ (full ranking).** Bỏ sản phẩm đã có trong train (D) và item val E (HỎI 1, Nam chốt 09/10), xếp các sản phẩm còn lại theo điểm: B, C, A. Item test A đứng **hạng 3**.

| Chỉ số | K = 2 | K = 5 | Cách tính |
|---|---|---|---|
| Hit@K | 0 | 1 | A có nằm trong top-K không |
| Recall@K | 0 | 1 | (số item test nằm trong top-K) / (số item test) = 1/1 |
| NDCG@K | 0 | 0,5 | 1 / log2(hạng + 1) = 1 / log2(4) |

**Vì sao Recall@K = Hit@K ở đây:** mỗi người dùng có **đúng 1** item test. Mẫu số của Recall là 1, tử số là 0 hoặc 1, nên Recall@K chính là "có trúng hay không", tức Hit@K. Hai chỉ số chỉ khác nhau khi một người dùng có nhiều item test. Vẫn báo cột Recall@K riêng vì cô yêu cầu, kèm câu giải thích này.

**NDCG với 1 item test:** DCG@K = 1/log2(hạng + 1) nếu hạng ≤ K, còn lại 0. DCG lý tưởng (item test đứng hạng 1) = 1/log2(2) = 1, nên NDCG@K = DCG@K. Hạng 1 → 1; hạng 3 → 0,5; hạng 10 → 0,289.

**CVR@2 (QĐ 4-9).** Top-2 của u1 là B, C. C là phụ kiện → không chấm. B là ống Nikon F, thân duy nhất D là Canon: cặp (D, B) có M = 0, không thuộc "không biết" → **vi phạm**. u1 có 1 vi phạm / 1 ống chấm được.
Thêm u2: top-2 là hai ống, một ống lắp được, một ống cặp "không biết" → chấm được 1 ống, 0 vi phạm. Người dùng u3 không có thân → bỏ.
- Gộp micro (QĐ 4-9): (1 + 0) / (1 + 1) = 0,5; số người dùng được tính = 2.

**Kịch bản "ống cho người đã có thân".** u1 có thân D, item test A là ống trong M, cặp (D, A) M = 1 → u1 thuộc nhóm **lắp được**. Nếu item test là B (Nikon) thì u1 thuộc nhóm **không lắp được**: bộ lọc MountAware loại B khỏi danh sách, nên với người này bộ lọc chắc chắn làm Hit = 0. Đây là cái giá của ràng buộc cứng mà kịch bản muốn đo.

## 2. Lỗi và chỗ phải sửa trong code 05 hiện tại

So với commit `9d97f57` (nhánh `nam/content4`; `common_05.py` đã sửa CVR 08/10, các script 05a/b/c và 05_evaluate còn nguyên bản của Hải). "Đã kiểm" = có số từ log; "đọc code" = suy ra từ đọc code, chưa chạy.

| # | File, hàm / dòng | Lỗi | Bằng chứng | Sửa |
|---|---|---|---|---|
| L1 | `05c_rgcn_train.py`, lớp `RGCNVariant` (dòng 25, 51–106); `05_evaluate.py` `MODELS` | "R-GCN variant" thật ra là `HeteroConv` + `SAGEConv` cho từng quan hệ, không phải R-GCN (Schlichtkrull et al. 2018) | Đọc code; chính docstring của Hải ghi "không phải implementation Schlichtkrull" (lỗi 1, STATUS mục 4) | Viết lại bằng `RGCNConv` của PyG (mục 6.4), đổi tên trong mọi bảng |
| L2 | `05c_rgcn_train.py`, `get_init_embeddings` (dòng 71–73, 87–94) | Không chạy được với đồ thị mới: `item_proj = Linear(3)` nhưng `item.x` nay 9 chiều; `mount_proj = Linear(8)` nhưng có 23 ngàm; `usecase_proj = Linear(7)` nhưng có 4 nhãn; thiếu 3 loại nút `sensor_format`, `focal_range`, `aperture_class` | Đọc code + in cấu trúc `kg_hetero.pt` (item.x [27.940, 9], mount.x [23, 23], usecase.x [4, 4]). **Chưa chạy** 05c (chạy thì sẽ huấn luyện nếu không lỗi) | Bỏ, thay bằng L1 |
| L3 | `05c` (toàn bộ) | Bỏ qua thuộc tính cạnh (`ngam_khong_chac`, `phia`, `src_phu_kien`, `crop_unknown`). Nam thêm cờ `ngam_khong_chac` để mô hình **không** coi đường thân → ngàm ← ống "không chắc" là lắp được; mô hình hiện tại không thấy cờ này | Đọc code | Nam chốt 09/10 (HỎI 4): giữ 18 quan hệ, bỏ 134 cạnh có cờ `ngam_khong_chac` khỏi đầu vào R-GCN (mục 6.4) |
| L4 | `common_05.sampled_eval`; `05a.run_popularity`, `05b.evaluate`, `05c.evaluate` | Kết quả chính là sampled 1+99, không phải full ranking (lỗi 4) | Đọc code. Âm mẫu của script 02: **86,95% là phụ kiện** (val; test 86,98%), nên chỉ cần xếp ống/thân lên trên phụ kiện là trúng dễ | Thêm `full_rank_eval` (mục 3); sampled chỉ là số phụ |
| L5 | `05b` dòng 222, `05c` dòng 231 | Dừng sớm và chọn checkpoint theo **NDCG@10 sampled** trên val | Đọc code | Chọn theo NDCG@20 full ranking trên val (mục 7) |
| L6 | `05a.run_popularity`, `score_fn_sampled` (dòng 50–59) và `score_fn_full` (dòng 73–80) | Bộ lọc MountAware: (a) người dùng **không có thân** có `valid_lenses` rỗng → **mọi ống** bị đặt −∞; (b) loại cả ống ngoài M (không ngàm, "không chắc") và ống có cặp "không biết". Trái quyết định của Nam 08/10 khuya (chỉ loại ống `judge_lens` = True) | **Đã kiểm** (`run_survey_n5_sets`, mục D): trong 4.618 người dùng có item test là ống, bộ lọc cũ loại mất item test của **3.856** người (3.268 người không có thân + 588 người có thân); bộ lọc mới chỉ loại **282**. Có thể đây là lý do Hit của MountAware thấp hơn Global trong bảng của Hải (dữ liệu cũ, chưa kiểm) | Bộ lọc mới: đặt −∞ đúng các ống `judge_lens(ống, thân, ctx) is True`; người không có thân không bị lọc |
| L7 | `05a.score_fn_full` dòng 78 | Vòng `for iid in range(N_ITEMS)` bằng Python cho từng người dùng: với full ranking 67.661 người là ~1,9 tỷ lần lặp | Đọc code | Tính sẵn mặt nạ "chắc chắn vi phạm" bằng numpy |
| L8 | `common_05.full_catalog_cvr` dòng 265; `_rank_of_pos` | Chưa có quy tắc hòa điểm cho full ranking. `argpartition` xếp các item bằng điểm theo thứ tự tùy ý. Popularity có rất nhiều item cùng số lượt | Đọc code | Quy tắc hòa cố định (mục 3.3), dùng chung cho hạng item test và top-K của CVR |
| L9 | `05b` dòng 29–38 | Siêu tham số không có nguồn: `LR = 2.5e-3`, `BATCH_SIZE = 16384`, `MAX_EPOCH = 30`, `PATIENCE = 4`. Với batch 16.384 mỗi epoch chỉ có ⌈460.193 / 16.384⌉ = 29 bước, cả lần chạy tối đa 870 bước cập nhật; bài LightGCN ghi "1000 epochs" thường đủ để hội tụ với batch 1024–2048 | Đọc code + số cặp train 460.193 (log khảo sát) | Dùng giá trị của bài gốc (mục 7) |
| L10 | `05b` dòng 95–96 | Khởi tạo `normal(std=0.01)`; bài LightGCN dùng Xavier (§4.1.2) | Đọc code | Xavier |
| L11 | `05b` dòng 126, `05c` dòng 129 | `rng = default_rng(SEED)` tạo lại mỗi epoch, nên mỗi epoch áp **cùng một hoán vị** lên thứ tự cũ (không phải xáo ngẫu nhiên mới) | Đọc code | Một `rng` cho cả lần chạy |
| L12 | `05a/b/c` | Chỉ một seed (42), không có trung bình ± độ lệch chuẩn, không có khoảng tin cậy | Đọc code | Mục 8, 9 |
| L13 | `05b` dòng 266 | In cứng "2,488 users" | Đọc code | Bỏ |
| L14 | `05a/b/c`, `05_evaluate` | Ghi đè file kết quả cố định `results/*.json`, `results/*_best.pt`; 5 file `results/*.json` của Hải đang nằm trong git | `git ls-files results/` | Ghi vào thư mục mới theo nhãn lần chạy (mục 11); không đụng file của Hải |
| L15 | `05_evaluate.py` `METRICS` | Không có Recall, không có độ lệch chuẩn hay khoảng tin cậy, không có kịch bản | Đọc code | Viết lại phần tổng hợp |
| L16 | `05c` dòng 104 | ReLU + dropout ở cả lớp cuối, rồi lấy tích vô hướng: điểm luôn ≥ 0 | Đọc code | Bỏ cùng L1 |
| L17 | Lỗi 2 (phần CVR) | Hải báo 2.491 / 2.488 người dùng tính CVR | Theo QĐ 4-9 tập người dùng có thân trong train nay là **10.406** (15,38%); số người **được tính** phụ thuộc K và mô hình (`cvr_n_users@K`). Không tái lập được số cũ (M cũ, dữ liệu trước khi gộp lặp) | Báo số mới, ghi rõ không so được với số cũ |

**Điểm đã kiểm là đúng (giữ):**
- `common_05.judge_lens` / `full_catalog_cvr`: CVR theo QĐ 4-9, gộp micro, bỏ người dùng không có ống chấm được (`test_cvr.py` 26/26, log `run_c4_test_cvr_20261008_vidumoi.log`).
- Âm mẫu 1+99 của script 02: 99 âm mẫu / người, không trùng train, val, test (log khảo sát mục E).
- `compute_hit_ndcg`: công thức NDCG với 1 item test đúng (IDCG = 1).

## 3. Kết quả chính: xếp hạng toàn bộ

### 3.1. Đối tượng được đo

| Thành phần | Phiên bản | sha256 |
|---|---|---|
| train / val / test | `ai/data/processed/` (nội dung 2, sau khi gộp lặp): 67.661 người dùng, 460.193 cặp train, mỗi người 1 item val và 1 item test | train `ebd29b03…ca06a5c5`, val `e8a47d06…85a3a900`, test `410fc46c…6e4da8ea` |
| Âm mẫu 1+99 (chỉ cho số phụ) | `val_negatives.json`, `test_negatives.json` (script 02, seed 42) | `f6ad945f…9e5a277f`, `8c408f53…1293b205` |
| Loại sản phẩm | `ai/data/kg/item_attributes.csv` | `3b05f535…4cc7b621` |
| Đồ thị | `ai/data/kg/kg_hetero.pt` (bản có cờ `ngam_khong_chac`) | `abf149b5…c69fce4b` |
| M, "không biết" | `kg_edges_compatible_with.csv`, `kg_edges_crops_sensor.csv`, `unknown_mask.npz`, `body_index.json`, `lens_index.json` | `77c8d5c8…`, `a2a052a5…`, `c9ae5c10…`, `dfffbc20…`, `f774c8e5…` |
| CVR | `ai/pipeline/common_05.py` ở `9d97f57` | `dd79d6bc…7315a020` |

### 3.2. Tập ứng viên
- **Ứng viên** của người dùng u = toàn bộ **27.940** sản phẩm, trừ các sản phẩm u đã có trong train.
- **Khi chấm test, bỏ thêm item val** của u khỏi ứng viên (**Nam chốt 09/10, HỎI 1**). Lý do: lúc gợi ý cho lần mua test, hệ thống đã biết u mua item val; gợi ý lại nó là vô ích, mà nó chiếm một chỗ trong top-K. Mô hình vẫn chỉ học trên train (không học lại trên train + val), để đồ thị và mọi mô hình dùng đúng một tập cạnh. Khi chấm **val**: chỉ bỏ train.
- Popularity đếm lượt trên **train**.

### 3.3. Hạng và quy tắc hòa điểm
- Hạng của item test p: hạng(p) = 1 + #{j: s_j > s_p} + #{j: s_j = s_p và π(j) < π(p)}, j chạy trên ứng viên.
- π là một hoán vị ngẫu nhiên cố định của 27.940 sản phẩm (seed `20261009`), **dùng chung cho mọi mô hình**. Top-K (cho CVR) xếp theo (điểm giảm dần, π tăng dần), nên cùng quy tắc với hạng.
- Với mô hình học (điểm số thực) hòa điểm gần như không xảy ra; script đếm và in số ca hòa ở item test.

### 3.4. Chỉ số
- Recall@K, NDCG@K, Hit@K, K ∈ {5, 10, 20}, trung bình trên **67.661** người dùng (mọi người dùng đều có 1 item test).
- Công thức như mục 1. Recall@K = Hit@K (giải thích ở mục 1); vẫn in cả hai cột, script kiểm hai cột bằng nhau.
- Báo thêm: số ống / thân / phụ kiện / máy "khác" trung bình trong top-10 (để thấy mô hình gợi ý loại gì).

### 3.5. Số phụ: sampled 1+99
- Dùng nguyên âm mẫu của script 02, cùng quy tắc hòa của Hải (âm mẫu bằng điểm thì xếp trên item test). Báo Hit@K, NDCG@K, K ∈ {5, 10, 20}.
- Chỉ để đặt cạnh bảng của Hải. **Không so trực tiếp được với số của Hải**: dữ liệu đã đổi (gộp lặp: 70.424 → 67.661 người dùng), M đổi, bộ lọc MountAware đổi.
- Ghi trong báo cáo: Krichene & Rendle (KDD 2020, "On Sampled Metrics for Item Recommendation") chỉ ra chỉ số lấy mẫu có thể đảo thứ tự các mô hình so với xếp hạng toàn bộ; ở dữ liệu này, 87% âm mẫu là phụ kiện (mục 2, L4).

## 4. CVR@K (QĐ 4-9)

- Tập người dùng: có ít nhất một thân trong train: **10.406 / 67.661 = 15,38%** (10.359 có ít nhất một thân trong M).
- Top-K lấy từ đúng danh sách xếp hạng của mục 3 (cùng tập ứng viên, cùng quy tắc hòa). Mỗi ống trong top-K được `judge_lens` phán: vi phạm / không vi phạm / không chấm được. Phụ kiện, thân, máy "khác", ống ngoài M không chấm.
- CVR@K = (tổng vi phạm) / (tổng ống chấm được), gộp micro trên mọi người dùng. Người dùng không có ống nào chấm được trong top-K thì bỏ.
- Báo kèm cho mỗi K: số người dùng được tính, số ống chấm được, số vi phạm. CVR là "nan" nếu không có ống chấm được (ghi rõ, không đổi thành 0).
- CVR của Popularity-MountAware **phải bằng 0** theo cách dựng bộ lọc. Đây là phép kiểm tra code: khác 0 là có lỗi.
- CVR dùng top-K trên **test** (cùng lần chạy test). Trên val chỉ in để theo dõi, không dùng để chọn mô hình.

## 5. Kịch bản "gợi ý ống kính cho người đã có thân máy"

### 5.1. Định nghĩa
- Người dùng u thuộc kịch bản khi: (1) u có ít nhất một thân trong train; (2) item test của u là **ống trong M** (có 1 ngàm, không "không chắc").
- Chia nhóm bằng `judge_lens(item test, thân của u)`:
  - **lắp được**: có ít nhất một thân M = 1 với ống test (trả False);
  - **không lắp được**: mọi thân M = 0 và không cặp nào "không biết" (trả True). Gồm cả cặp `requires_adapter` (M = 0 theo QĐ 3-2), đếm riêng;
  - **không phán được**: còn lại (trả None). Báo số người, không đưa vào so sánh hai nhóm.
- Gọi "lắp được / không lắp được" thay cho "cùng ngàm / khác ngàm": so chuỗi ngàm thì sai, vì ống EF lắp được trên thân EF-S (khác chuỗi ngàm nhưng M = 1). Trong báo cáo ghi "lắp được trực tiếp (M = 1)" và "không lắp được trực tiếp (M = 0)".
- Hạn chế (QĐ 3-5): chỉ biết thân mà người dùng có viết đánh giá; nhóm "không lắp được" có thể là người đã mua thân mới mà không đánh giá.

### 5.2. Số người dùng (log khảo sát, mục C)

| Tập | Trong kịch bản | Lắp được | Không lắp được (trong đó có `requires_adapter`) | Không phán được |
|---|---:|---:|---:|---:|
| val | 1.152 | 904 (78,47%) | 236 (20,49%; 18) | 12 (1,04%) |
| **test** | **1.060** | **762 (71,89%)** | **282 (26,60%; 11)** | **16 (1,51%)** |

Thêm 290 người có thân và item test là ống **ngoài** M (không ngàm hoặc "không chắc"): ngoài kịch bản, chỉ báo số.

### 5.3. Cách đo
- Tập ứng viên của kịch bản (**Nam chốt 09/10, HỎI 2**):
  - **số chính: chỉ ống** (1.339 sản phẩm có `item_type = ong`, trừ ống đã có trong train và item val), vì kịch bản là "khung gợi ý ống kính";
  - **số phụ:** toàn bộ 27.940 sản phẩm như mục 3 (chỉ lọc người dùng).
- Báo Recall@K, NDCG@K, K ∈ {5, 10, 20}, và CVR@K, **tách theo nhóm** lắp được / không lắp được, cho cả 4 mô hình.
- Nhóm "không lắp được" chỉ có 282 người, nên khoảng tin cậy sẽ rộng; ghi rõ.
- Dự kiến (chưa kiểm chứng): bộ lọc MountAware cho Hit = 0 ở **mọi** người nhóm "không lắp được" (vì item test bị lọc), và có thể tăng Hit ở nhóm "lắp được".

## 6. Bốn baseline

### 6.1. Popularity (Global)
Điểm của sản phẩm = số người dùng có sản phẩm đó trong train. Giống nhau cho mọi người dùng. Không có siêu tham số, không có seed (trừ hoán vị hòa π).

### 6.2. Popularity-MountAware (theo quy tắc)
- Lấy điểm của Popularity, rồi với người dùng có thân trong train: ống mà `judge_lens` = True ("chắc chắn vi phạm") bị đặt điểm −∞.
- Ống `judge_lens` = None (ngoài M, "không chắc", có cặp "không biết") và mọi sản phẩm không phải ống: **giữ nguyên**. Người dùng không có thân: không lọc gì (Nam chốt 08/10 khuya; sửa lỗi L6).
- Bộ lọc này là module ràng buộc cứng đơn giản nhất. Áp cùng bộ lọc lên LightGCN / R-GCN là việc của nội dung 6, không làm ở đây.

### 6.3. LightGCN (He et al., SIGIR 2020)
- Đồ thị: chỉ cạnh user–item của train (460.193), ma trận kề chuẩn hóa D^(−1/2) A D^(−1/2).
- K = 3 lớp, gộp lớp với α_k = 1/(K+1); điểm ŷ_ui = e_uᵀ e_i; loss BPR + λ‖E⁽⁰⁾‖² (chỉ embedding lớp 0, Eq. 15).
- Mỗi cặp train lấy 1 âm mẫu ngẫu nhiên đều trong các sản phẩm u **chưa có trong train** (viết lại `OnlineNegSampler` bằng numpy, không dùng vòng Python).

### 6.4. R-GCN thật (Schlichtkrull et al., ESWC 2018) trên đồ thị nội dung 4
**Ví dụ trước.** Ống EF 70-200 nhận thông tin từ: người đã mua nó (`rev_interacted_with`), các thân nối tới nó (`rev_compatible_with`), nút ngàm `canon_ef` (`rev_has_spec`), nút "thể thao/chim" (`rev_suitable_for`)… Mỗi loại quan hệ r có ma trận W_r riêng; tin nhắn từ hàng xóm loại r được nhân W_r rồi lấy trung bình trong loại đó; cộng tất cả các loại với phần tự giữ W_0 h_i.

**Công thức (Eq. 2 của bài):** h_i^(l+1) = σ( Σ_r Σ_{j∈N_i^r} (1/c_{i,r}) W_r^(l) h_j^(l) + W_0^(l) h_i^(l) ).

**Cài đặt:**
- `torch_geometric.nn.RGCNConv`, đồ thị nội dung 4 chuyển sang dạng đồng nhất: 95.646 nút, 1.116.950 cạnh (cả chiều `rev_`), **chỉ cạnh train** cho user–item; val / test không bao giờ vào đồ thị.
- **Số quan hệ (Nam chốt 09/10, HỎI 4): 18 quan hệ** như `kg_hetero.pt`, và **bỏ 134 cạnh `has_spec → mount` có cờ `ngam_khong_chac` = 1** (cùng 134 cạnh `rev_has_spec` tương ứng) khỏi đồ thị đầu vào của R-GCN. Đồ thị đầu vào còn 1.116.950 − 268 = 1.116.682 cạnh.
  - **Lý do:** `RGCNConv` không đọc thuộc tính cạnh. Nếu giữ 134 cạnh này mà không tách quan hệ, mô hình thấy đường thân Canon → nút `canon_ef` ← ống "không chắc" y như đường của một ống chắc chắn ngàm EF, tức coi ống "không chắc" là lắp được — đúng điều cờ `ngam_khong_chac` muốn tránh (QĐ 3-4, 4-5). Bỏ cạnh thì ống "không chắc" không có đường nào qua nút ngàm; ống vẫn giữ các cạnh khác (người mua, tiêu cự, khẩu độ, khổ, mục đích).
  - Các thuộc tính cạnh khác (`src_phu_kien`, `phia`, `crop_unknown`) bị bỏ qua: cạnh phụ kiện / ngàm chuyển / "chưa rõ có cắt khung" được xử lý như cạnh thường cùng quan hệ. Ghi là hạn chế.
  - Phương án không chọn: tách thành 28 quan hệ theo cờ cạnh (đã đo thời gian ở mục 9).
  - `kg_hetero.pt` không sửa; script 05c bỏ cạnh khi nạp và in số cạnh bị bỏ (phải đúng 134 mỗi chiều).
- Nút không có đặc trưng đầu vào: mỗi nút một embedding học được (bài §2.2: one-hot cho mỗi nút khi không có đặc trưng, qua một phép biến đổi tuyến tính — tương đương một bảng embedding). Không dùng `item.x` ở baseline này (để dành nội dung 7).
- 2 lớp, d = 64, ReLU giữa hai lớp (không ở lớp cuối), `root_weight = True` (W_0), `aggr = "mean"` (c_{i,r} = |N_i^r|).
- **Chấm điểm user–item:** DistMult (bài Eq. 6) cho đúng quan hệ `interacted_with`: f(u, i) = e_uᵀ diag(r) e_i, với r ∈ ℝ^64 học được. Đây là tích vô hướng có trọng số theo từng chiều.
- **Hàm loss: BPR (Nam chốt 09/10, HỎI 3)**, giống LightGCN: −ln σ(f(u, i) − f(u, j)), j là 1 âm mẫu đều trong các sản phẩm u chưa có trong train. Lý do: khác biệt giữa R-GCN và LightGCN khi đó chỉ đến từ bộ mã hóa và đồ thị, không đến từ hàm loss. Sai khác so với bài gốc: bài dùng cross-entropy nhị phân với ω = 1 âm mẫu cho mỗi cạnh dương (Eq. 7).
- Mỗi bước: mã hóa toàn đồ thị một lần (như LightGCN lan truyền lại mỗi batch), lấy embedding của batch cặp BPR.

**Chỗ lệch so với bài gốc (ghi trong báo cáo):**
- d = 64 (bài: 200 hoặc 500) — để bằng LightGCN, như LightGCN cố định d = 64 cho mọi mô hình (§4.1.2);
- chuẩn hóa c_{i,r} = |N_i^r| (công thức Eq. 2, ví dụ của chính bài); phần dự đoán liên kết của bài dùng c_i = Σ_r |N_i^r| (§5.2), `RGCNConv` không hỗ trợ trọng số cạnh nên không làm đúng được nếu không viết lớp riêng;
- edge dropout: bài dùng 0,2 cho tự nối và 0,4 cho cạnh khác; PyG không có cạnh tự nối (W_0 là phần riêng), nên chỉ áp **0,4 cho cạnh** (`dropout_edge`), không dropout phần W_0;
- mini-batch BPR thay cho full-batch (bài §5.2: full-batch) — xem mục 9 về thời gian;
- loss BPR thay cho cross-entropy (HỎI 3);
- tối đa 100 epoch (mục 7.1, HỎI 5).

## 7. Siêu tham số

### 7.1. Giá trị mặc định và nguồn

| Mô hình | Siêu tham số | Giá trị | Nguồn |
|---|---|---|---|
| LightGCN | d | 64 | He et al. 2020 §4.1.2 |
| | số lớp K | 3 | §4.1.2 ("satisfactory performance can be achieved when K equals to 3") |
| | α_k | 1/(K+1) | §4.1.2 |
| | khởi tạo | Xavier | §4.1.2 |
| | tối ưu, lr | Adam, 0,001 | §4.1.2 |
| | batch | 2048 | §4.1.2 (1024; 2048 cho Amazon-Book "for speed") |
| | λ (L2 trên E⁽⁰⁾) | dò trên val trong {1e−5, 1e−4, 1e−3} | §4.1.2: dò {1e−6…1e−2}, "in most cases the optimal value is 1e−4"; §4.5: λ > 1e−3 làm kết quả giảm nhanh |
| | dropout | không | §3.3 |
| | số epoch tối đa | **300** (Nam chốt 09/10, HỎI 5) | **Sai khác so với bài gốc**: §4.1.2 ghi "Typically, 1000 epochs are sufficient". Giảm vì ngân sách GPU |
| R-GCN | lớp, phân rã | 2 lớp, phân rã cơ sở B = 2 | Schlichtkrull et al. 2018 §5.2 (FB15k/WN18: B = 2, 1 lớp; FB15k-237: 2 lớp, khối 5×5). Chọn 2 lớp để thông tin đi được user → item → thân/ngàm → ống |
| | tối ưu, lr | Adam, dò {0,01; 0,001} | §5.2: Adam lr 0,01. Thêm 0,001 (lr của LightGCN) vì đổi sang mini-batch |
| | L2 | 0,01 trên bộ giải mã (r) | §5.2 |
| | edge dropout | 0,4 | §5.2 (xem chỗ lệch ở 6.4) |
| | d, batch | 64, 2048 | theo LightGCN để so công bằng |
| | số epoch tối đa | **100** (Nam chốt 09/10, HỎI 5) | Bài R-GCN không ghi số epoch cho dự đoán liên kết; **sai khác** so với mức ~1000 epoch của LightGCN. Giảm vì một epoch R-GCN chậm gấp ~2,2 lần LightGCN (mục 9) |
| Chung | dừng sớm | chấm NDCG@20 val **mỗi 10 epoch (LightGCN) / mỗi 5 epoch (R-GCN)**; dừng khi **5 lần chấm liên tiếp** không tăng (LightGCN 50 epoch, R-GCN 25 epoch); giữ checkpoint tốt nhất (Nam chốt 09/10, HỎI 5) | **Quyết định nhóm**: LightGCN nói theo NGCF mà không ghi patience; R-GCN không ghi số epoch |
| | chạm giới hạn epoch | lần chạy nào chạy hết 300 / 100 epoch mà chưa dừng sớm thì ghi **"chưa chắc hội tụ"** ở bảng kết quả và ở mục hạn chế (Nam chốt 09/10) | — |
| | chỉ số chọn | NDCG@20, full ranking, trên val | Quyết định nhóm; @20 theo LightGCN (recall@20, ndcg@20, all-ranking) |

### 7.2. Quy trình
1. Sửa code, viết kiểm thử dựng tay (mục 10), commit.
2. **Dò trên val, seed 1**: LightGCN 3 cấu hình (λ), R-GCN 2 cấu hình (lr). Chọn cấu hình có NDCG@20 val cao nhất. Popularity không có gì để dò.
3. Ghi cấu hình chốt vào `ai/config/n5_final.toml`, **commit trước khi chạy test**.
4. Chạy cấu hình chốt với seed 2 và 3 (seed 1 dùng lại lần chạy ở bước 2; chọn cấu hình chỉ dựa trên val nên dùng lại không làm lộ test).
5. **Test chạy một lần** cho cả 4 mô hình × mọi seed, bằng một script; script ghi commit hash và sha256 của `n5_final.toml` vào log, dừng nếu cây git không sạch.
6. Ghi số vào CHANGELOG / STATUS và commit **trước** khi phân tích ca sai hay chạy phân tích thêm.
7. Nếu sau khi chạy test phát hiện lỗi script: sửa, chạy lại, **báo cả hai** lần và lý do, không giấu lần đầu.

### 7.3. Seed
- 3 seed {1, 2, 3} cho LightGCN và R-GCN. Seed điều khiển khởi tạo, âm mẫu, xáo dữ liệu, edge dropout.
- Báo **trung bình ± độ lệch chuẩn mẫu** (ddof = 1) qua 3 seed, kèm từng seed trong phụ lục.
- Hạn chế: phép cộng của phép nhân ma trận thưa / gom tin nhắn trên GPU không tất định, nên chạy lại cùng seed có thể lệch nhỏ. Không cam kết sha256 trùng như các bước trước; ghi đây là hạn chế.

## 8. Khoảng tin cậy và so sánh giữa mô hình

- **Bootstrap theo người dùng, có ghép cặp:** lấy lại 67.661 người dùng có hoàn lại, B = 2.000 lần, seed `20261009`. Mỗi lần tính chỉ số của mọi mô hình trên **cùng** mẫu người dùng, nên được cả khoảng tin cậy của từng mô hình lẫn của hiệu hai mô hình. Khoảng 95% theo phân vị (2,5% – 97,5%).
- Chỉ số theo từng người (Hit, Recall, NDCG) của mô hình học = trung bình qua 3 seed của người đó. Độ lệch giữa các seed báo riêng (mục 7.3), vì bootstrap theo người không chứa phần dao động do seed.
- CVR là tỷ số micro: mỗi lần bootstrap tính lại (tổng vi phạm) / (tổng ống chấm được) trên mẫu người dùng. Với mô hình học, mỗi seed cho một CVR; khoảng tin cậy tính trên tổng vi phạm và tổng ống chấm được cộng qua 3 seed.
- Kịch bản (mục 5): bootstrap riêng trong từng nhóm.
- **So sánh đăng ký trước** (K = 10; các K khác chỉ mô tả):

  | # | So sánh | Chỉ số | Tập |
  |---|---|---|---|
  | S1 | LightGCN − Popularity | Recall@10, NDCG@10 | mọi người dùng |
  | S2 | R-GCN − LightGCN | Recall@10, NDCG@10 | mọi người dùng |
  | S3 | MountAware − Popularity | CVR@10, Recall@10 | người có thân / mọi người dùng |
  | S4 | R-GCN − LightGCN | CVR@10 | người có thân |
  | S5 | MountAware − Popularity | Recall@10 | kịch bản, từng nhóm |

  Hiệu được coi là khác 0 khi khoảng 95% không chứa 0. Không hiệu chỉnh đa so sánh; mọi so sánh ngoài bảng này ghi là "thăm dò".
- Bộ nhớ: ma trận chỉ số lấy mẫu 2.000 × 67.661 số int64 ≈ 1 GB, nên tạo theo từng khối 100 lần lấy mẫu.

## 9. Thời gian và bộ nhớ trên GTX 1660 Ti 6 GB

Đo bằng `probe_gpu.py` (trọng số ngẫu nhiên, forward + backward, không cập nhật; log `run_probe_gpu_20261009_lan1.log`). Lúc đo RAM trống 4.059 MiB; tiến trình dùng khoảng 1.444 MiB RAM.

| Phần | Cấu hình | ms / bước | s / epoch | Đỉnh GPU |
|---|---|---:|---:|---:|
| LightGCN | batch 2048 (225 bước) | 56 | 12,5 | 367 MiB |
| LightGCN | batch 16384 (29 bước) | 52 | 1,5 | 367 MiB |
| R-GCN 18 quan hệ | batch 2048 | 124 | 27,9 | 1.090 MiB |
| R-GCN 18 quan hệ | batch 16384 | 126 | 3,6 | 1.090 MiB |
| R-GCN 28 quan hệ | batch 2048 | 177 | 39,9 | 1.576 MiB |
| R-GCN 28 quan hệ | batch 16384 | 175 | 5,1 | 1.576 MiB |
| Xếp hạng toàn bộ 67.661 × 27.940 | lô 1024 người | — | 0,82 s / lần chấm | 404 MiB |

- Phân rã cơ sở (đo với B = 4; kế hoạch dùng B = 2) so với không phân rã: thời gian và bộ nhớ gần như bằng nhau (tham số chủ yếu là 95.646 × 64 embedding nút).
- **Vừa bộ nhớ:** đỉnh GPU cao nhất ~1,6 GB / 6 GB; RAM ~1,5 GB. Không cần giảm.
- Chưa tính: lấy âm mẫu (sẽ viết bằng numpy), chấm val mỗi 10 epoch (~1 s).
- **Ngân sách đã chốt (Nam, 09/10, HỎI 5):** batch 2048; LightGCN tối đa 300 epoch, R-GCN (18 quan hệ) tối đa 100 epoch; dò trên val với 1 seed, cấu hình chốt chạy 3 seed.
- **Thời gian xấu nhất** (mọi lần chạy hết giới hạn epoch, tính từ bảng trên): LightGCN 300 × 12,5 s ≈ 62 phút / lần; R-GCN 100 × 27,9 s ≈ 47 phút / lần (bỏ 268 cạnh không đổi đáng kể). Số lần chạy: LightGCN 3 cấu hình + 2 seed thêm = 5 lần ≈ 5,2 giờ; R-GCN 2 + 2 = 4 lần ≈ 3,1 giờ; **tổng ≈ 8,3 giờ**, chưa tính lấy âm mẫu và chấm val (~1 s mỗi lần chấm).
- *(Ước lượng ban đầu với 1000 epoch: xấu nhất ≈ 17,5 + 44 giờ; đã thay bằng ngân sách trên.)*
- **Chưa kiểm chứng** 300 / 100 epoch có đủ để hội tụ không; đây là lý do có nhãn "chưa chắc hội tụ" (mục 7.1).

## 10. Kiểm thử trước khi chạy (dựng tay, như `test_cvr.py`)
- Hạng / Recall / NDCG / Hit trên ví dụ mục 1 (hạng 3 → NDCG@5 = 0,5).
- Quy tắc hòa: 3 sản phẩm cùng điểm, hạng theo π.
- Item train và (khi chấm test) item val không bao giờ vào top-K.
- Bộ lọc MountAware mới: người không có thân không bị lọc; ống `judge_lens` = None không bị lọc; CVR@K của MountAware = 0 trên dữ liệu thật.
- Recall@K = Hit@K từng người.
- Popularity chấm bằng full ranking cho kết quả giống hệt khi chạy 2 lần (sha256 file kết quả theo người).
- Bootstrap: với hai "mô hình" giống hệt nhau, hiệu luôn bằng 0.

## 11. Đầu ra và log
- Mọi kết quả ghi vào `results/n5/<nhãn lần chạy>/` (vd `results/n5/val_lightgcn_l2-1e-4_s1_20261010/`), log tên mới kèm ngày và nhãn. Không ghi đè; 5 file `results/*.json` của Hải giữ nguyên.
- Mỗi lần chạy lưu: cấu hình, commit hash, sha256 đầu vào, đường học (loss, NDCG@20 val theo epoch), checkpoint tốt nhất, và **hạng của item test cho từng người dùng** (để bootstrap và kiểm lại không cần chạy lại mô hình).

## 12. Quyết định của Nam (09/10/2026)

| # | Câu hỏi | Đề xuất của Claude | **Nam chốt 09/10/2026** |
|---|---|---|---|
| HỎI 1 | Khi chấm test, bỏ item val khỏi ứng viên? | Có | **Có** (mục 3.2) |
| HỎI 2 | Ứng viên của kịch bản "ống cho người có thân": chỉ ống, hay toàn bộ catalog? | Chỉ ống là số chính, toàn bộ là số phụ | **Như đề xuất** (mục 5.3) |
| HỎI 3 | Loss của R-GCN: BPR (giống LightGCN) hay cross-entropy ω = 1 (bài gốc)? | BPR | **BPR** (mục 6.4) |
| HỎI 4 | R-GCN dùng 18 quan hệ, hay tách theo cờ cạnh thành 28? | 28 | **18 quan hệ; bỏ 134 cạnh `has_spec → mount` có cờ `ngam_khong_chac` (và 134 cạnh ngược) khỏi đồ thị đầu vào của R-GCN.** Lý do ở mục 6.4 |
| HỎI 5 | Ngân sách thời gian GPU | Batch 2048, tối đa 1000 epoch | **LightGCN tối đa 300 epoch, R-GCN tối đa 100 epoch; dừng sớm theo NDCG@20 val, chấm mỗi 10 epoch (LightGCN) / 5 epoch (R-GCN), patience 5 lần chấm; dò trên val 1 seed, cấu hình chốt chạy 3 seed; chạm giới hạn epoch thì ghi "chưa chắc hội tụ" ở kết quả và hạn chế; ghi là sai khác so với bài gốc (~1000 epoch)** (mục 7.1, 9) |
| HỎI 6 | Chỉ số chọn mô hình = NDCG@20 full ranking trên val, và 5 so sánh đăng ký trước ở mục 8? | Đồng ý | **Đồng ý** |

## 13. Sửa đổi kế hoạch

| Ngày | Sửa | Lý do |
|---|---|---|
| 09/10/2026 | Ghi 6 quyết định của mục 12 vào các mục 3.2, 5.3, 6.4, 7.1, 9; R-GCN đổi từ đề xuất 28 quan hệ sang 18 quan hệ + bỏ 134 cạnh "không chắc"; giới hạn epoch 1000 → 300 (LightGCN) / 100 (R-GCN), R-GCN chấm val mỗi 5 epoch | Nam chốt, trước khi sửa code 05 và trước khi chạy bất kỳ mô hình nào |
| 09/10/2026 | **Làm rõ cài đặt, không đổi quyết định** (code `f21ced4`, trước khi dò trên val và trước khi chạy test). (1) LightGCN: hạng L2 = λ · ½(‖e_u⁰‖² + ‖e_i⁰‖² + ‖e_j⁰‖²) / số cặp trong batch, theo code của tác giả (kuandeng/LightGCN, gusye1234/LightGCN-PyTorch); giữ Xavier như mục 7.1 dù code tác giả khởi tạo normal (std 0,01 / 0,1). (2) R-GCN: r của DistMult khởi tạo glorot; L2 bộ giải mã = 0,01·‖r‖² mỗi bước; không L2 trên embedding nút; `RGCNConv` có bias; edge dropout lấy lại mỗi bước, cạnh xuôi và ngược độc lập. (3) Sampled 1+99: quy tắc hòa của Hải viết dạng tất định, hạng = 1 + #(âm mẫu có điểm ≥ điểm item). (4) Script `05a/05b/05c` chỉ nhận val; test chấm bằng một script riêng (mục 7.2 bước 5) | Kế hoạch chưa ghi các chi tiết này; ghi lại để thấy được chọn trước khi xem bất kỳ số nào của mô hình học (chỉ có số Popularity trên val và 1–3 epoch chạy thử) |
| 09/10/2026 | **Sai khác sau khi dò val, trước khi chạy test** (cấu hình chốt `ai/config/n5_final.toml`; dò val `results/n5/val_sweep_20261010/summary_20261009_053905.json`, seed 2–3 ở `results/n5/final_20261009/`, cả 6 lần chạy cùng commit `595bc70`, dirty = False). (1) **LightGCN λ = 1e-3 "chưa chắc hội tụ"**: cả 3 seed chạy hết 300 epoch mà không dừng sớm (epoch tốt nhất 290 / 260 / 300); NDCG@20 val còn nhích ở các lần chấm cuối (seed 1: 0,04001 ở epoch 230 → 0,04045 ở epoch 290). (2) **Cấu hình tốt nhất nằm ở biên lưới dò**: λ = 1e-3 là giá trị lớn nhất của {1e-5, 1e-4, 1e-3}; lr = 0,001 là giá trị nhỏ nhất của {0,01; 0,001}. Chưa biết giá trị ngoài lưới có tốt hơn không; **không mở rộng lưới** (lưới đã đăng ký trước, ngân sách GPU QĐ 5-5). Với λ, bài LightGCN §4.5 ghi λ > 1e-3 làm kết quả giảm nhanh. (3) Cách tổng hợp của script chạy test `05_test_final.py` (chưa ghi rõ ở mục 8): bảng chính báo CVR mô hình học = trung bình ± độ lệch chuẩn CVR từng seed, còn khoảng tin cậy dùng CVR gộp 3 seed (mục 8); mỗi tập bootstrap (mọi người dùng / người có thân / từng nhóm kịch bản) lấy mẫu riêng với cùng seed 20261009; S5 dùng số chính "chỉ ống"; khoảng của từng mô hình và các chỉ số @20 chỉ để mô tả | (1), (2): kết quả dò val, ghi theo QĐ 5-5 trước khi chạy test; cũng ghi ở hạn chế nội dung 5 (STATUS). (3): làm rõ cài đặt, chọn trước khi xem số test |
