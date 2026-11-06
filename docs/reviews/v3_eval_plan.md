# Kế hoạch đánh giá v3 (nhận xét cô 06/11, mục A1–A3, A5) — đăng ký trước

**Trạng thái:** **ĐĂNG KÝ TRƯỚC** — Nam chốt 10 câu [HỎI] tối 06/11/2026 (mục 12.1, kèm điều kiện). Từ đây đổi gì
phải ghi ở mục 13 kèm lý do, trước khi xem số mới. [HỎI 11] Nam chốt 06/11 khuya: không dò λ1 cho v2 A (mục 12.1). Đợt dò seed 1
máy nhóm bắt đầu 06/11 (`ai/pipeline/v3_sweep.py --group s1`, mục 6.1).

Nguồn: nhận xét cô `E:\DATN\co\nhan_xet_co_06112026.md` (ngoài repo); kế hoạch cũ `n5_eval_plan.md`,
`cakg_eval_plan.md`, `cakg_v2_plan.md`; `docs/STATUS.md`. Nhánh `nam/v3-plan`.

Mỗi số trong file này ghi nguồn. **[ĐO]** = đọc từ log / `result.json` / output script. **[ƯỚC TÍNH]** = tính từ số
đo theo một giả định ghi rõ, chưa kiểm chứng bằng cách chạy thật.

## 0. Tóm tắt

| Câu hỏi | Trả lời ngắn | Nguồn |
|---|---|---|
| Giờ GPU cho A1–A3 (tính theo tốc độ máy nhóm) [ƯỚC TÍNH] | PA1 (chạy lại hết từ đầu) **229–381 giờ**; PA2 (chạy tiếp `last.pt`, giữ lần đã dừng sớm) **205–357 giờ**; PA3 (tối thiểu) **179–311 giờ** — khoảng = [cận dưới; cận trên]. Trong đó 4 baseline mới chiếm 176 giờ (PA1, PA2) / 151 giờ (PA3) vì chưa có số dừng sớm nên tính đủ 1.000 epoch | mục 8, log `ai/data/survey/v3/run_uoc_tinh_gio_lan1.log` |
| RecBole có tái hiện số LightGCN của nhóm không | **Có.** NDCG@20 val 0,04046 (nhóm 0,04045), test 0,03044 (nhóm 0,03021; TB 3 seed 0,03008 ± 0,00014); cách chấm trùng tới 5·10⁻⁹; hòa điểm không ảnh hưởng | mục 7.3 |
| Kaggle | Đã có gói (2 dataset riêng tư + notebook mẫu), chưa tải lên | mục 9, `kaggle/README.md` |
| Cần Nam quyết | 10 câu [HỎI] | mục 12 |

## 1. Ví dụ trước

**Vì sao "chưa hội tụ" là vấn đề.** LightGCN λ2 = 1e-3, seed 1 (cấu hình đang dùng cho hệ thống cuối) [ĐO,
`results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1/result.json`]: NDCG@20 val ở epoch 10 / 20 / 30 là
0,02172 / 0,02650 / 0,03025; ở epoch 250 … 300 là 0,04017 / 0,04016 / 0,04021 / 0,04034 / 0,04045 / 0,04040. Lần chạy
dừng vì chạm trần 300 epoch, không phải vì dừng sớm; điểm tốt nhất ở epoch 290, tức là đường val **vẫn còn lên**.
CaKG-Rec λ1 = 0,1 cũng vậy (tốt nhất epoch 290: 0,03973), KGAT lr = 1e-4 còn lên rõ ở epoch 300
(0,02017 → 0,02099). Bài gốc LightGCN chạy khoảng 1.000 epoch.

**Dừng sớm làm gì.** Ví dụ một lần chạy mới, trần 1.000 epoch, chấm NDCG@20 val mỗi 10 epoch: nếu điểm tốt nhất ở
epoch 340 và 5 lần chấm sau (350 … 390) đều không cao hơn thì dừng ở epoch 390 và giữ checkpoint epoch 340. Nếu tới
1.000 mà vẫn chưa dừng thì ghi "chưa chắc hội tụ" như trước.

**Chạy tiếp thay vì chạy lại.** Lần chạy cũ seed 1 đã lưu `last.pt` ở epoch 300 (trạng thái mô hình, Adam, mọi bộ sinh
số ngẫu nhiên). Vì lần chạy cũ chưa hề dừng sớm trước epoch 300, chạy tiếp từ `last.pt` tới 1.000 cho **cùng một quá
trình** như chạy mới từ đầu với trần 1.000 (trừ sai lệch không tất định của GPU), mà tiết kiệm 300 epoch.

## 2. Test đã xem — không còn là đánh giá mù (A5)

- Test đã được chấm **hai đợt**: 09/10 (Popularity, MountAware, LightGCN, R-GCN; `05_test_final.py`) và 15/10
  (CaKG-Rec v1, KGAT, LightGCN + mặt nạ, 2 ablation; `06_test_final.py`). Ngày 16/10 chỉ đọc lại mảng test đã lưu
  (giải thích, độ trễ). CaKG-Rec v2 **chưa** chấm test (DỪNG 2).
- Nhóm đã đọc số test, phân tích ca sai, và quyết định v2 / hệ thống cuối sau khi thấy số test lần 1. Vì vậy mọi số
  test từ nay **không còn là đánh giá mù**; báo cáo ghi rõ câu này ở bảng kết quả và ở mục hạn chế.
- Quy tắc v3: mọi lựa chọn (mô hình, siêu tham số, epoch, biến thể) **chỉ dựa trên val**. Test chấm **một lần, ở
  cuối**, cho mọi mô hình v3 × 5 seed, bằng một script, trên cây git sạch, ở máy nhóm; kết quả commit trước khi phân
  tích. Lỗi script phát hiện sau đó: sửa, chạy lại, báo cả hai lần.

## 3. Mô hình và lưới

Chỉ số chọn: **NDCG@20 full ranking trên val, trước mặt nạ, seed 1** (như QĐ 5-6). Lưới mở rộng đúng phía biên.

| Mô hình | Cố định | Lưới cũ (val NDCG@20, seed 1) [ĐO] | Điểm thêm (đề xuất) | Nguồn / lý do |
|---|---|---|---|---|
| LightGCN | d 64, 3 lớp, Adam 1e-3, batch 2048 (như `n5_eval_plan` 7.1) | λ2 1e-5 / 1e-4 / **1e-3**: 0,03769 / 0,03803 / **0,04045** (1e-3 chạm trần) | **3e-3, 1e-2** | biên trên; bài LightGCN §4.1.2 dò {1e-6 … 1e-2}, §4.5 nói λ > 1e-3 giảm nhanh → chỉ cần 2 điểm để thấy đỉnh |
| CaKG-Rec | như `cakg_eval_plan` 4.1 (biến thể: [HỎI 1]) | λ1 0,01 / **0,1** / 1: 0,03948 / **0,03973** / 0,03940 (cả 3 chạm trần) | không thêm; **chạy tiếp cả 3 tới 1.000** rồi chọn lại | λ1 không ở biên; nhưng cả 3 điểm chưa hội tụ nên chọn lại sau khi hội tụ |
| R-GCN | như `n5_eval_plan` 7.1; chấm val mỗi 5 epoch | lr 1e-2 / **1e-3**: 0,01868 / **0,02287** (cả hai dừng sớm ở 30 / 45 epoch) | **3e-4, 1e-4** | biên dưới; lr 1e-3 đạt đỉnh epoch 15–35 rồi giảm |
| KGAT | như `cakg_eval_plan` 4.1 | lr **1e-3** / 1e-4: **0,02629** / 0,02099 (1e-3 dừng sớm ở 80; 1e-4 chạm trần, còn lên) | **3e-3**; **chạy tiếp 1e-4 tới 1.000** | biên trên là 1e-3, nhưng 1e-4 chưa hội tụ nên chưa biết thật sự biên nào |
| BPR-MF | d 64, Adam 1e-3, batch 2048, 1 âm mẫu / cặp | — | λ2 ∈ {1e-5, 1e-4, 1e-3} | như LightGCN để cùng ngân sách; cài đặt: [HỎI 5] |
| ItemKNN | cosine, item-based | — | k ∈ {50, 100, 200}, shrink 0 | k = 100 là mặc định RecBole; tất định, chạy CPU |
| UltraGCN | theo bài / code tác giả | — | 3 cấu hình của trọng số ràng buộc (chốt sau khi đọc bài) | không có trong RecBole / RecBole-GNN [ĐO: danh sách mô hình RecBole 1.2.1 và RecBole-GNN `632ef88`] |
| SimGCL | RecBole-GNN mặc định: 2 lớp, eps 0,1, τ 0,2, reg 1e-4 | — | λ (trọng số tương phản) ∈ {0,005; 0,01; 0,05} | trong khoảng dò của RecBole-GNN (`results/general/ml-1m.md`) |
| KGIN | RecBole mặc định (d 64, 4 ý định, node dropout 0,5) trên cùng KG của KGAT | — | context_hops ∈ {1, 2, 3} | bài KGIN dò số tầng; KG: `to_recbole_kg.py` (98.148 bộ ba, bỏ 134 cạnh "không chắc") |

- Nếu sau khi mở rộng, giá trị tốt nhất **vẫn ở biên mới**: mở rộng **thêm đúng một điểm** theo cùng hướng (một lần),
  rồi dừng và ghi hạn chế [HỎI 3].
- Popularity, MountAware, ItemKNN tất định: không có seed, chạy một lần.
- LightGCN + mặt nạ dùng chính checkpoint LightGCN chốt (không huấn luyện thêm).

## 4. Dừng sớm, đường cong

- Trần **1.000 epoch** cho mọi mô hình học (bản cũ: 300; R-GCN 100). Chấm NDCG@20 val mỗi 10 epoch (R-GCN mỗi 5),
  dừng sau **5 lần chấm** liên tiếp không tăng, giữ checkpoint tốt nhất (như QĐ 5-5). Chạm 1.000 → "chưa chắc hội tụ".
- Lần chạy cũ **đã dừng sớm** dưới trần cũ (LightGCN λ2 1e-5 / 1e-4 ở 180; R-GCN cả 4 lần ở 30–60; KGAT lr 1e-3 cả 3
  seed ở 80–90) cho kết quả **giống hệt** khi trần là 1.000 (quy tắc dừng không đổi) → **giữ, không chạy lại** (PA2, PA3).
- Lần chạy cũ **chạm trần** → chạy tiếp từ `last.pt` (PA2, PA3): cần sửa nhỏ `train_05.run` cho phép tăng
  `max_epoch` khi chạy tiếp (hiện `config.json` phải trùng hoàn toàn), chép thư mục chạy cũ sang `results/v3/…` trước
  khi chạy tiếp (không động vào kết quả cũ đã commit); ghi CHANGELOG khi sửa.
- **Đường cong**: mỗi lần chạy đã ghi loss mỗi epoch và NDCG@20 val mỗi lần chấm (`history` trong `result.json`); vẽ
  bằng script chỉ đọc, mỗi mô hình 5 seed trên một hình, đánh dấu epoch tốt nhất và điểm dừng.

## 5. Seed và cách báo

- Seed **1–5** cho mọi mô hình học và **mọi ablation** (A2). Seed 1 dùng để dò; seed 2–5 chạy cấu hình chốt.
- Báo trung bình ± độ lệch chuẩn mẫu (ddof = 1) qua 5 seed, từng seed ở phụ lục. Bootstrap theo người dùng như cũ
  (B = 2.000), kèm khoảng dao động giữa seed (bootstrap không chứa phần này — hạn chế nội dung 5 điểm 5).
- GPU không tất định: chạy lại cùng seed có thể lệch nhỏ; máy nhóm và Kaggle cũng lệch → **một mô hình chạy cả 5 seed
  trên cùng một loại máy** (mục 8).

## 6. Chọn trên val

1. Dò (seed 1) → chọn theo NDCG@20 val → ghi `ai/config/v3_final.toml`, **commit trước khi chạy seed 2–5**.
2. Seed 2–5 của cấu hình chốt; ablation 5 seed với đúng cấu hình chốt.
3. So sánh đăng ký trước: giữ nguyên các so sánh S1–S5 (`n5_eval_plan` mục 8) và C1–C9 (`cakg_eval_plan` mục 8),
   thêm: mỗi baseline mới so với LightGCN (Recall@10, NDCG@10, CVR@10, kịch bản nhóm lắp được). Khác 0 hay không:
   bootstrap theo người, kèm dao động giữa 5 seed.
4. Test một lần ở cuối (mục 2).

### 6.1. Thứ tự chạy (thêm 06/11 khi chốt; thứ tự không ảnh hưởng kết quả)

**Máy nhóm, đợt `s1` (dò, seed 1, trần 1.000)** — `ai/pipeline/v3_sweep.py --group s1 --label 20261106`, ghi vào
`results/v3/s1_20261106/<tên>/`:

| # | Lần chạy | Cách | Ước tính giờ [cận dưới; cận trên] (mục 8.2) |
|---|---|---|---|
| 1 | LightGCN λ2 = 1e-3 | chạy tiếp 300 → 1.000 (`last.pt` ĐẠT) | 0,2–2,7 |
| 2 | LightGCN λ2 = 3e-3 | mới | 0,7–3,9 |
| 3 | LightGCN λ2 = 1e-2 | mới | 0,7–3,9 |
| 4 | CaKG-Rec v2 A `lens_gate`, λ1 = 0,1 | chạy tiếp (ĐẠT) | 0,3–4,5 |
| 5 | KGAT lr = 1e-4 | chạy tiếp (ĐẠT) | 0,4–5,4 |
| 6 | KGAT lr = 3e-3 | mới | 0,6–7,7 |
| 7 | R-GCN lr = 3e-4 | mới (chấm mỗi 5 epoch) | 0,25–8,3 |
| 8 | R-GCN lr = 1e-4 | mới | 0,25–8,3 |
| | **Cộng** | | **3,4–44,7 giờ** (cộng tay từ log `lan1`) |

Kiểm `last.pt` (điều kiện của Nam cho PA2): `ai/survey/v3/kiem_last_pt.py` → `results/v3/kiem_last_pt_lan2.json`,
**7/7 ĐẠT** (đủ Adam, RNG numpy / torch / CUDA; code + dữ liệu KG trùng sha256). Sau đợt `s1`: chọn theo NDCG@20 val →
`ai/config/v3_final.toml` (commit) → đợt `s25` (seed 2–5, chạy tiếp seed 2, 3 nếu cấu hình chốt trùng cấu hình cũ) và
đợt `abl` (2 ablation CaKG-Rec v2 A × seed 1–5); nếu giá trị tốt nhất vẫn ở biên mới: thêm đúng 1 điểm (HỎI 3).

**Kaggle, đợt `thu` (chạy thử baseline, seed 1, một cấu hình, HỎI 10; chọn 06/11 trước khi có số nào):** mỗi baseline
lấy điểm **giữa** lưới đã đăng ký ở mục 3 (hoặc cấu hình của tác giả khi chưa có lưới), chỉ chấm val, trần 1.000 epoch,
chấm mỗi 10 epoch, dừng sau 5 lần chấm không tăng:

| Tài khoản (`ACCOUNT`) | Lần chạy (`RUN_LABEL = thu_s1_<tài khoản>`) | Cấu hình |
|---|---|---|
| Nam (`nam`) | `kgin_hops2_s1` | KGIN (RecBole) mặc định, context_hops = 2 (giữa {1, 2, 3}) |
| Hải (`hai`) | `simgcl_lam0.01_s1` | SimGCL (RecBole-GNN `632ef88`) mặc định, λ = 0,01 (giữa {0,005; 0,01; 0,05}) |
| Quyền (`quyen`) | `bprmf_l2-1e-04_s1` | BPR-MF code nhóm (`05d`), λ2 = 1e-4 (giữa {1e-5, 1e-4, 1e-3}) |
| | `ultragcn_electronics_s1` | UltraGCN code nhóm (`05e`) theo file cấu hình Amazon Electronics của tác giả (RecZoo `88fae23`) |
| | `recbole_bpr_s1` | BPR (RecBole) mặc định, để đối chiếu (HỎI 5) |

Baseline RecBole chạy `run_recbole.py --group-eval` (chấm val bằng bộ chấm nhóm, HỎI 6; chạy tiếp được). Notebook tự ngắt
ở mốc 8,5 giờ / phiên (giới hạn phiên 9 hay 12 giờ chưa kiểm, mục 8.3) và chạy tiếp ở phiên bản sau. Chia 3 tài khoản
(HỎI 7). Hướng dẫn từng bước: `kaggle/HUONG_DAN_KAGGLE.md`. Sau đợt này mới quyết lưới / số seed baseline (HỎI 10).

## 7. RecBole: kiểm tái hiện LightGCN (A3 "trước tiên")

### 7.1. Cách làm
- Venv **riêng** `E:\DATN\venvs\recbole` (Python 3.12.10; không đụng `ai/.venv`): torch 2.14.1+cu126 (cùng bản với
  `ai/.venv`), RecBole 1.2.1 cài `--no-deps` (RecBole đòi `ray<=2.6.3`, không có bản cho Python 3.12; `ray` chỉ dùng
  cho dò tham số tự động), numpy 1.26.4, pandas 2.2.3, **scipy 1.11.4** (scipy ≥ 1.12 làm `LightGCN.get_norm_adj_mat`
  của RecBole lỗi `dok_matrix._update` [ĐO, lần chạy thử đầu]). Danh sách đủ: `ai/recbole/requirements-recbole-lock.txt`.
- Dữ liệu: `ai/recbole/to_recbole.py` chép **nguyên** `train.txt` / `val.txt` / `test.txt` sang 3 file benchmark
  `camera_loo.{train,valid,test}.inter` (RecBole không tự chia, không lọc). Kiểm [ĐO, `run_to_recbole_20261106_lan2.log`]:
  460.193 cặp train, 67.661 người × 1 item valid, 67.661 × 1 item test, không trùng, 27.940 sản phẩm (71 sản phẩm chỉ
  có ở valid / test).
- Chạy: `ai/recbole/run_recbole.py --model LightGCN --seed 1 --epochs 300` (đúng cấu hình chốt, cùng trần 300 như
  lần của nhóm), rồi `ai/recbole/cross_eval.py` chấm lại embedding RecBole bằng bộ chấm của nhóm để tách lệch do
  **cách chấm** và lệch do **cài đặt huấn luyện**.

### 7.2. Giao thức: chỗ giống và khác (đọc mã nguồn RecBole 1.2.1)

| Điểm | Nhóm (`05b`, `train_05`, `eval_05`) | RecBole 1.2.1 | Ảnh hưởng |
|---|---|---|---|
| Chia dữ liệu | train / val / test của nhóm | cùng 3 file (benchmark) | không |
| Bỏ sản phẩm đã có khi chấm | val: bỏ train; test: bỏ train + item val | sampler cộng dồn theo pha: valid bỏ train, test bỏ train + valid (`sampler.get_used_ids`) | không |
| Xếp hạng | toàn bộ 27.940 sản phẩm | toàn bộ (`mode: full`), cột [PAD] đặt −∞ | không |
| Hòa điểm | hạng = 1 + #cao hơn + #bằng mà π nhỏ hơn (π cố định) | `torch.topk` (thứ tự hòa tùy cài đặt) | chỉ khi điểm bằng nhau đúng từng bit; đo ở 7.3 |
| L2 | λ · ½ Σ‖e⁰‖² / batch | `EmbLoss(require_pow=True)`: Σ‖e⁰‖² / batch / 2 | trùng công thức |
| Khởi tạo | Xavier uniform | Xavier uniform (`xavier_uniform_initialization`) | không |
| Loss BPR | softplus(−Δ) trung bình | −log(1e-10 + σ(Δ)) trung bình | khác ~1e-10 |
| Âm mẫu | 1 âm đều / cặp, ngoài train của người đó | 1 âm đều / cặp, ngoài train | cùng phân phối, khác dãy số ngẫu nhiên |
| Ma trận kề | D^-½ A D^-½, không tự nối | D^-½ A D^-½ (cộng 1e-7 vào bậc), không tự nối | không đáng kể |
| Dừng sớm | dừng khi 5 lần không **tăng** (`>`) | dừng khi số lần "không ≥ tốt nhất" > `stopping_step` = 4 (bằng điểm tốt nhất vẫn tính là tăng) | chỉ khác khi hai lần chấm bằng nhau |
| Seed | `torch.manual_seed`, `numpy default_rng` | `init_seed` (random, numpy, torch, `cudnn.deterministic`) | cùng seed 1 nhưng **khác dãy số** → không mong trùng từng chữ số; so với dao động giữa 3 seed của nhóm |
| Thời gian | 13,7 s / epoch, chấm val 3,5 s [ĐO] | 20,65 s / epoch (19,8–22,0), chấm valid 114–137 s / lần, cả lần chạy 9.772 s ≈ 2,7 giờ cho 300 epoch [ĐO, `result.json`] | RecBole chậm hơn ~1,5× khi học và ~35× khi chấm (mục 7.4) |

### 7.3. Kết quả — **tái hiện được**

Lần chạy: `results/recbole/repro_lightgcn_20261106/lightgcn_l2-1e-03_s1/` (RecBole 1.2.1, seed 1, 300 epoch, chấm mỗi
10, commit `54ef9de` + sửa chưa commit chỉ ở MODEL_CFG của mô hình khác). Chấm chéo: `cross_eval.py`, log
`cross_eval_val_20261106_174143.log`, `cross_eval_test_20261106_174152.log` trong cùng thư mục.

**Ví dụ đọc bảng.** Cùng một mô hình (embedding RecBole), RecBole tự chấm NDCG@20 val = 0,04046022, bộ chấm của nhóm
cho 0,040460225 → lệch 5·10⁻⁹ (chỉ do RecBole làm tròn 8 chữ số). Vậy **cách chấm** hai bên trùng. Còn RecBole học
ra 0,04046 so với nhóm học ra 0,04045 → lệch do **cài đặt huấn luyện** chỉ 1·10⁻⁵.

| NDCG@20 / Recall@20 | val | test |
|---|---|---|
| RecBole tự chấm | 0,040460 / 0,089919 | 0,030436 / 0,066937 |
| Bộ chấm nhóm trên embedding RecBole | 0,040460 / 0,089919 | 0,030436 / 0,066937 |
| → lệch do cách chấm | < 5·10⁻⁹ | < 3·10⁻⁹ |
| Nhóm, LightGCN seed 1 | 0,040447 / 0,089150 | 0,030212 / 0,065739 |
| → lệch do cài đặt (RecBole − nhóm seed 1) | +0,000013 / +0,00077 | +0,00022 / +0,0012 |
| Nhóm, trung bình ± ĐLC 3 seed | 0,040464 ± 0,000070 / 0,08954 ± 0,00057 | 0,030083 ± 0,000136 / 0,06572 ± 0,00043 |

(Đủ 4 chỉ số @10 / @20 ở hai file log trên.) [ĐO, `cross_eval.py`]

- **Hòa điểm**: có 14 người (val) / 13 người (test) mà item đúng bị hòa điểm với đúng 1 item khác; cận trên = cận dưới
  tới 9 chữ số → quy tắc hòa (π của nhóm so với `topk`) **không ảnh hưởng** số liệu.
- **Đường cong val**: tốt nhất cùng ở epoch 290 (nhóm 0,04045, RecBole 0,04046), chạm trần 300 như nhau; lệch lớn nhất
  giữa hai đường qua 30 lần chấm 0,00037 (epoch 100: 0,03721 so với 0,03687), trung bình −0,00007 (RecBole hơi chậm hơn
  ở giữa, bắt kịp ở cuối).
- **Mức lệch so với dao động seed**: val nằm trong ±1 ĐLC giữa 3 seed của nhóm. Test NDCG@20 lệch +0,00035 so với
  trung bình 3 seed (~2,6 ĐLC), Recall@20 +0,0012 (~2,8 ĐLC); ĐLC chỉ từ 3 seed nên chưa đáng tin, và một lần chạy
  RecBole cũng là một mẫu → coi là **cùng cỡ dao động giữa seed**, không phải lỗi. Kiểm chặt hơn cần RecBole nhiều seed
  (không đề xuất: tốn ~2,7 giờ / seed).
- Kết luận: LightGCN của nhóm và của RecBole cho cùng kết quả trong giới hạn dao động ngẫu nhiên; bộ chấm của nhóm trùng
  RecBole tới làm tròn.

### 7.4. Hệ quả cho baseline mới

- Bộ chấm và cách chia của nhóm đã được kiểm độc lập bằng RecBole → baseline lấy từ RecBole / RecBole-GNN (BPR, KGIN,
  SimGCL) dùng được trên cùng dữ liệu, cùng giao thức; số cuối vẫn chấm bằng bộ chấm nhóm cho đồng nhất.
- RecBole tự chấm valid mất 114–137 s / lần (so với 3,5 s của nhóm): với trần 1.000 epoch, chấm mỗi 10 epoch là 100 lần
  ≈ 3,3–3,8 giờ chỉ để chấm → [HỎI 6].

### 7.5. Sửa để chạy được KGIN / SimGCL (đo ngắn 06/11)

| Lỗi [ĐO] | Nguyên nhân (đọc mã nguồn) | Sửa |
|---|---|---|
| KGIN: `KeyError: 'mount_14'` trong `_merge_item_and_entity` (`probe_20261106_lan2`, `lan3`) | KG chỉ phủ **2.972 / 27.940** sản phẩm; `.link` cũ ghi cả 27.940. Ở chế độ benchmark RecBole **bỏ qua** `_data_filtering` (nên cũng không lọc `.link`), mà phép gộp mã đòi mọi thực thể trong `.link` có mặt trong `.kg` | `to_recbole_kg.py`: `.link` chỉ ghi item có trong `.kg` (2.972 dòng; log `run_to_recbole_kg_20261106_lan3.log`; `.kg` không đổi, sha256 `ba9a9611…`). Item ngoài KG vẫn có mã thực thể, không có cạnh — như code KGIN gốc. Kiểm: không mất tương tác nào (460.193 / 67.661 / 67.661, assert trong `run_recbole.py`) |
| KGIN: dataloader KG không có thuộc tính `dataset` (`lan4`) | lỗi của `run_recbole.py` (đếm số dòng train) | đếm bằng `train_data._dataset` |
| KGIN: thiếu `torch_scatter` (`lan5`); SimGCL: thiếu `torch_sparse` (`lan2`) | không có bản dựng sẵn cho torch 2.14.1 (`pip install --only-binary` từ `data.pyg.org/whl/torch-2.14.0+cu126` báo không có bản nào) | `scatter_mean` thay bằng `torch_geometric.utils.scatter(reduce="mean")` (kiểm trên dữ liệu nhỏ: lệch 0,0); `torch_sparse` thay bằng module giả chỉ để import qua — RecBole-GNN tự dùng `edge_index` thường khi thiếu `torch_sparse` (`recbole_gnn/data/dataset.py`), `matmul` giả mà bị gọi thì báo lỗi ngay. Ghi trong `config_used.json` → `patches` |

Lưu ý: log `run_to_recbole_kg_20261106_lan2.log` là lần chạy lại **code cũ** do sửa hỏng (cho đúng kết quả `lan1`);
bản đúng là `lan3`. Loss SimGCL lớn (~1,2·10⁶ / epoch) vì RecBole-GNN cộng InfoNCE theo **tổng** trên batch
(`simgcl.py`, `calculate_cl_loss` trả `.sum()`), không phải lỗi.

## 8. Ngân sách giờ GPU

### 8.1. Số đo (máy nhóm GTX 1660 Ti) [ĐO]

Script `ai/survey/v3/uoc_tinh_gio_gpu.py` (chỉ đọc `result.json` + log sweep), log
`ai/data/survey/v3/run_uoc_tinh_gio_lan1.log` (các log `thu1`–`thu5` là bản chạy thử script, trước khi có số RecBole):

| Mô hình | giây huấn luyện / epoch (trung vị; min–max) | giây / lần chấm val | phần cố định / lần chạy | số epoch đã đo |
|---|---|---|---|---|
| LightGCN (nhóm) | 13,74 (12,32–15,94) | 3,46 (mỗi 10 epoch) | 20,0 | 1.260 (5 lần chạy) |
| R-GCN (nhóm) | 29,02 (27,21–29,87) | 3,59 (mỗi 5 epoch) | 30,7 | 175 (4) |
| CaKG-Rec (nhóm, v1 + v2) | 22,20 (19,19–26,51) | 7,18 | 35,2 | 3.600 (12) |
| KGAT (nhóm) | 27,31 (25,67–29,74) | 3,69 | 23,7 | 550 (4) |
| LightGCN (RecBole, lần tái hiện) | 20,65 (19,80–21,99) | 119,2 (RecBole tự chấm) | — | 300 |
| BPR (RecBole) | 1,42 | 101,5 | — | 2 (đo ngắn) |
| ItemKNN (RecBole) | 1,32 (một lần "fit", không cần GPU) | 130,5 | — | 1 |
| SimGCL (RecBole-GNN) | 32,77 | 106,2 | — | 2 (đo ngắn) |
| KGIN (RecBole) | 41,27 | 105,7 | — | 2 (đo ngắn) |

Đo ngắn: `results/recbole/probe_20261106*/` (`--probe-epochs 2`, mặc định RecBole / RecBole-GNN, seed 1). Chạy được
KGIN / SimGCL cần 3 sửa nhỏ, ghi ở mục 7.5. UltraGCN chưa có cài đặt → tạm lấy bằng LightGCN [ƯỚC TÍNH].

### 8.2. Ba phương án [ƯỚC TÍNH]

Giờ một lần chạy = cố định + E × (giây / epoch) + số lần chấm × (giây / lần chấm). **Cận trên**: mọi lần chạy chưa
có số đo chạy đủ 1.000 epoch. **Cận dưới**: dừng ở mức sớm nhất mà số đo cũ cho phép (lần chạy tiếp: epoch tốt nhất
cũ + 50; seed mới: epoch tốt nhất nhỏ nhất của các seed cũ + 50; điểm lưới mới: số epoch nhỏ nhất đã chạy của mô hình
đó); baseline mới chưa có số nên cận dưới = cận trên. Baseline mới giả định chấm val bằng bộ chấm nhóm (3,46 s / lần,
[HỎI 6]); nếu để RecBole tự chấm (~119 s / lần, 100 lần / 1.000 epoch) thì mỗi lần chạy thêm ~3,3 giờ, tức thêm
~70 giờ cho BPR + SimGCL + KGIN (3 × 7 lần chạy).

| Khối | PA1: chạy lại từ đầu | PA2: chạy tiếp `last.pt` + giữ lần đã dừng sớm | PA3: tối thiểu (1 điểm / biên, không dò lại λ1, baseline 2 cấu hình) |
|---|---|---|---|
| LightGCN | 9,2–28,8 | 4,3–23,9 | 3,6–20,0 |
| CaKG-Rec + 2 ablation | 34,9–108,4 | 21,5–95,0 | 21,0–86,1 |
| R-GCN | 2,5–34,6 | 1,0–33,1 | 0,8–24,8 |
| KGAT | 6,5–32,7 | 2,3–28,5 | 2,3–28,5 |
| *Cộng 4 mô hình cũ (máy nhóm)* | *53,1–204,5* | *29,1–180,5* | *27,7–159,4* |
| BPR-MF | 3,5 | 3,5 | 3,0 |
| UltraGCN [ƯỚC TÍNH = LightGCN] | 27,4 | 27,4 | 23,5 |
| SimGCL | 64,4 | 64,4 | 55,2 |
| KGIN | 81,0 | 81,0 | 69,4 |
| *Cộng 4 baseline mới (Kaggle, mục 8.3)* | *176,3* | *176,3* | *151,1* |
| **Tổng (giờ GPU, tốc độ GTX 1660 Ti)** | **229,4–380,8** | **205,3–356,8** | **178,7–310,5** |

Phát sinh nếu cấu hình chốt khác cấu hình cũ: LightGCN +2,4 giờ, CaKG-Rec +7,7 giờ, KGAT +15,4 giờ (cận trên).
ItemKNN chạy CPU, không tính. Số từng khối và dòng tổng lấy từ log; các dòng "cộng" do Claude cộng lại từ số trong log (lệch 0,1 so với tổng của log do làm tròn).

**Đọc bảng.** Phần máy nhóm của PA2 là 29–181 giờ (khoảng 1,2–7,5 ngày chạy liền). Phần baseline mới 151–176 giờ là
cận trên (1.000 epoch không dừng sớm); với hạn mức Kaggle ~30 giờ / tuần (mục 8.3) là ~5–6 tuần nếu chạy hết trên
Kaggle → đây là điểm nghẽn, xem [HỎI 7], [HỎI 10].

### 8.3. Chia việc máy nhóm / Kaggle (đề xuất, [HỎI 7])

| Máy | Việc | Lý do |
|---|---|---|
| Máy nhóm (GTX 1660 Ti) | LightGCN, CaKG-Rec + 2 ablation, R-GCN, KGAT (dò + seed 1–5); ItemKNN (CPU); **chấm test cuối** | `last.pt` và các lần chạy cũ nằm ở máy này; mỗi mô hình đủ 5 seed trên một loại máy; test chỉ chấm ở máy nhóm |
| Kaggle (GPU T4) | BPR-MF, UltraGCN, SimGCL, KGIN (dò + seed 1–5) | khối độc lập, không cần `last.pt`; là notebook gửi cô |

Hạn mức Kaggle (chưa kiểm trên tài khoản Nam): trang hướng dẫn GPU của Kaggle ghi tối đa **30 giờ GPU / tuần**;
bài thông báo "floating GPU quota" nói có thể hơn 30 giờ tùy tuần; giờ tối đa mỗi phiên các nguồn ghi 9 hoặc 12 giờ
(https://www.kaggle.com/docs/efficient-gpu-usage, https://www.kaggle.com/product-feedback/173129). Nam xem số đúng ở
trang tài khoản trước khi lập lịch.

## 9. Kaggle

Cập nhật 06/11 khuya: gói thêm file RecBole (`ai/data/recbole/camera_loo/`, trùng sha256 với lần đối chiếu ở máy nhóm)
và bundle RecBole-GNN; notebook thêm môi trường `recbole` (venv `--system-site-packages`, dùng torch của python chính),
bộ việc theo tài khoản, ngắt theo mốc giờ, chạy tiếp từ output phiên bản trước. Đã **mô phỏng trên máy** (đường dẫn
giả `/kaggle`, CPU, 1 việc BPR-MF 20 epoch): giải nén zip, clone bundle đúng commit, kiểm sha256 30 file, ngắt ở mốc giờ
còn `last.pt`, phiên bản sau chạy tiếp đến xong. Môi trường `recbole` và cài thư viện trên Kaggle **chưa kiểm chứng**.

Gói: `kaggle/build_kaggle_package.py` (đã thử trên máy, chưa tải lên), hướng dẫn `kaggle/README.md`. Tóm tắt: dataset
riêng tư `camera-store-v3-code` (git bundle, notebook checkout đúng commit) + `camera-store-v3-data` (129,2 MiB, 23
file, kiểm sha256 từng file; `user_map.json` thay mã người dùng Amazon bằng `u0…`) + notebook mẫu `v3_runner.ipynb`
(môi trường → code → thư viện đúng phiên bản → dữ liệu → chạy tiếp tùy chọn → chạy việc → gom kết quả + sha256).
**Chưa kiểm chứng**: Python / torch trên ảnh Kaggle, hạn mức GPU / tuần và giờ / phiên, tốc độ T4 so với GTX 1660 Ti.
Trước khi chạy thật: một phiên bản ngắn (1 việc `--max-epoch 20`) để đo giây / epoch trên T4 và kiểm notebook.

## 10. Đầu ra và log

- Lần chạy mới: `results/v3/<đợt>/<tên>/` (máy nhóm) hoặc `results/kaggle/<RUN_LABEL>/<tên>/` (Kaggle, tải về giữ
  nguyên tên). Log không ghi đè (tên có thời điểm). Bảng lần chạy (ngày, máy, commit, phiên bản notebook Kaggle) ghi ở
  mục 13 khi chạy.
- `result.json` giữ đủ `history` để vẽ đường cong; checkpoint không lên git (như cũ).

## 11. Chưa kiểm chứng / rủi ro

1. Cận trên 1.000 epoch có thể vẫn chưa hội tụ với lr 1e-3 (chưa biết).
2. Tốc độ và hạn mức Kaggle (mục 9).
3. UltraGCN phải tự cài; chưa đo thời gian (tạm lấy bằng LightGCN).
4. KGIN / SimGCL: số giây / epoch từ lần đo ngắn (2 epoch) với siêu tham số mặc định; cấu hình khác (số tầng) đổi tốc độ.
   Hai thư viện `torch_scatter` / `torch_sparse` được thay (mục 7.5); KGIN trên KG chỉ phủ 2.972 sản phẩm (10,6 %).
6. Tái hiện RecBole mới là **một seed**; lệch test (+0,00035 NDCG@20 so với TB 3 seed nhóm) coi là dao động seed dựa
   trên ĐLC của chỉ 3 seed.
5. Gộp 5 seed chạy ở hai loại máy cho cùng một mô hình sẽ trộn sai lệch phần cứng vào độ lệch giữa seed (tránh, mục 5).

## 12. Câu hỏi cho Nam [HỎI]

| # | Câu hỏi | Lựa chọn | Đề xuất (Claude) |
|---|---|---|---|
| HỎI 1 | "CaKG-Rec" trong v3 là bản nào? | (a) v1, λ1 = 0,1 (đã chấm test 15/10); (b) v2 A `lens_gate` (chọn trên val 16/10, DỪNG 2 không đạt, chưa chấm test); (c) cả hai | (b) nếu theo đúng "chọn chỉ trên val" (v2 A có NDCG@20 val seed 1 cao hơn v1: 0,04063 so với 0,03973); ablation λ1 = 0 / bỏ `suitable_for` làm trên bản đã chọn. Bản chưa chọn không chạy thêm; chọn (c) thì gần gấp đôi khối CaKG-Rec, thêm ~21,5–95,0 giờ (PA2, mục 8.2) |
| HỎI 2 | Phương án ngân sách | PA1 / PA2 / PA3 (mục 8.2) | PA2 |
| HỎI 3 | Lưới mở rộng (mục 3) và quy tắc "vẫn ở biên thì mở thêm đúng 1 điểm, một lần" | đồng ý / sửa điểm | đồng ý |
| HỎI 4 | Sửa `train_05.run` để chạy tiếp `last.pt` với `max_epoch` lớn hơn (cần cho PA2 / PA3; ghi CHANGELOG) | có / không (thì PA1) | có |
| HỎI 5 | BPR-MF cài ở đâu | (a) code nhóm: `05b` với 0 lớp (e = e⁰), cùng L2 λ2 và vòng huấn luyện — trùng giao thức tuyệt đối; (b) `BPR` của RecBole (không có L2, chỉ dò lr) | (a), chạy thêm `BPR` RecBole seed 1 để đối chiếu |
| HỎI 6 | Chấm val trong vòng huấn luyện của RecBole | (a) để RecBole tự chấm (~108–137 s / lần, mục 7.2); (b) thay bằng bộ chấm nhóm (cùng giao thức, ~3,5 s / lần), kiểm bằng `cross_eval.py` trên một checkpoint | (b); số cuối luôn chấm bằng bộ chấm nhóm |
| HỎI 7 | Chia máy nhóm / Kaggle (mục 8.3) | đồng ý / sửa | đồng ý |
| HỎI 8 | Kaggle: tải 2 dataset **riêng tư** lên tài khoản của Nam; `user_map.json` ẩn mã; bật Internet để cài đúng torch / PyG như file lock (không bật thì dùng torch sẵn của Kaggle và ghi phiên bản) | đồng ý / sửa | đồng ý; Nam tự chạy lệnh tải lên |
| HỎI 9 | Báo số test | (a) bảng chính = test v3 (5 seed), số test cũ (3 seed, 300 epoch) ở phụ lục kèm câu "test đã xem"; (b) chỉ báo test v3 | (a) |
| HỎI 10 | Baseline mới 151–176 giờ (cận trên, mục 8.2) vượt xa hạn mức Kaggle ~30 giờ / tuần. Giảm thế nào? | (a) giữ trần 1.000 + dừng sớm, chạy song song Kaggle và máy nhóm khi rảnh, chấp nhận ~4–6 tuần; (b) dò chỉ seed 1 ở trần 1.000, seed 2–5 dùng trần = epoch tốt nhất của seed 1 + 100; (c) bớt lưới baseline xuống 2 điểm (PA3) và bỏ UltraGCN (phải tự cài, không có trong RecBole) | chưa đề xuất được: số dừng sớm thật của baseline chưa có; nên chạy seed 1 một cấu hình mỗi baseline trước (~0,5 giờ BPR, ~9–12 giờ SimGCL / KGIN mỗi lần, tính từ mục 8.1) rồi quyết |

### 12.1. Quyết định của Nam (06/11/2026, tối)

Nam: "Chốt 10 câu [HỎI] theo đúng đề xuất, kèm điều kiện":

| # | Quyết định | Điều kiện / ghi chú của Nam |
|---|---|---|
| HỎI 1 | (b) CaKG-Rec bản chính = **v2 A `lens_gate`** | ablation làm trên v2 A; **v1 không chạy lại** |
| HỎI 2 | **PA2** | chỉ khi `last.pt` đủ trạng thái Adam và RNG; kiểm trước, thiếu thì lần đó chạy lại từ đầu → đã kiểm: 7/7 ĐẠT (mục 6.1) |
| HỎI 3 | đồng ý lưới mục 3 + "vẫn ở biên thì thêm đúng 1 điểm, một lần" | |
| HỎI 4 | có, sửa `train_05.run` | cùng điều kiện HỎI 2; đã sửa, CHANGELOG 06/11 tối |
| HỎI 5 | (a) BPR-MF bằng **code nhóm** là số chính | chạy thêm `BPR` RecBole seed 1 để đối chiếu |
| HỎI 6 | (b) chấm val của RecBole bằng bộ chấm nhóm | |
| HỎI 7 | đồng ý chia máy | phần Kaggle chia cho **3 tài khoản** (Nam, Hải, Quyền); vẫn giữ "một mô hình cả 5 seed trên cùng loại GPU" (mục 5) |
| HỎI 8 | dataset **riêng tư**, ẩn mã người dùng | **notebook phải chia sẻ được cho cô xem** |
| HỎI 9 | (a) bảng chính test v3, test cũ ở phụ lục | |
| HỎI 10 | **chạy thử mỗi baseline seed 1, một cấu hình trước**, rồi mới quyết lưới / trần | |

Hệ quả Claude rút ra (ghi lại để Nam kiểm):
- HỎI 1 + "v1 không chạy lại" → bỏ dòng "chạy tiếp cả 3 λ1 của v1" ở mục 3; CaKG-Rec chỉ chạy tiếp **v2 A λ1 = 0,1**
  (seed 1–3 có `last.pt`), ablation λ1 = 0 / bỏ `suitable_for` dựng mới trên v2 A × seed 1–5.
- **[HỎI 11] (mới, không chặn):** v2 A chỉ có một giá trị λ1 = 0,1 (lấy từ lúc dò v1). Có dò λ1 cho v2 A không
  (vd {0,01; 1}, như lưới v1, mỗi điểm ~0,7–6,4 giờ)? Chưa dò thì báo cáo ghi "λ1 lấy từ v1, không dò lại cho v2".
  Đợt `s1` chưa có các lần này; thêm vào cuối đợt nếu Nam đồng ý.
  **Nam chốt 06/11 (khuya, sau): KHÔNG dò λ1 cho v2 A, giữ λ1 = 0,1.** Lý do của Nam: 0,1 không ở biên lưới v1
  {0,01; 0,1; 1}, và lần dò v1 các điểm chênh nhau nhỏ — val NDCG@20 seed 1 0,03948 / **0,03973** / 0,03940 [ĐO, mục 3],
  tức 0,1 hơn 0,01 là 0,00025 và hơn 1 là 0,00033 (≤ 0,00033). Báo cáo ghi: "λ1 = 0,1 chọn khi dò CaKG-Rec v1 (cả 3 điểm
  chạm trần 300 epoch); không dò lại cho v2 A". Hệ quả: CaKG-Rec v2 A không có điểm lưới nào khác → không áp quy tắc
  "ở biên thêm 1 điểm" cho CaKG-Rec.

## 13. Sửa đổi kế hoạch

| Ngày | Sửa gì | Lý do |
|---|---|---|
| 06/11/2026 | Bản đầu | Nhận xét cô 06/11 |
| 06/11/2026 (tối) | Điền kết quả tái hiện RecBole (mục 7.3–7.5), số đo BPR / ItemKNN / KGIN / SimGCL, bảng giờ GPU (log `lan1`); thêm HỎI 10 | Lần chạy RecBole LightGCN và đo ngắn xong; chưa có số nào của mô hình v3 |
| 06/11/2026 (khuya) | Nam chốt 10 câu (mục 12.1); thêm thứ tự chạy (mục 6.1), HỎI 11; CaKG-Rec chỉ v2 A | Quyết định của Nam; **trước khi có số v3 nào** (chỉ có smoke 1 lần chấm sau mốc 300, `results/v3/smoke_s1_thu1/`, không dùng để chọn) |
| 06/11/2026 (khuya, sau) | Cấu hình đợt Kaggle `thu` (mục 6.1: điểm giữa lưới; UltraGCN theo cấu hình Electronics của tác giả); cập nhật mục 9 | Chuẩn bị gói Kaggle; chưa có số baseline nào |
