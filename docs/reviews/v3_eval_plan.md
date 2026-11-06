# Kế hoạch đánh giá v3 (nhận xét cô 06/11, mục A1–A3, A5) — đăng ký trước

**Trạng thái:** bản nháp ngày 06/11/2026, **chờ Nam chốt các câu [HỎI]** (mục 12). Chưa huấn luyện dài; chỉ chạy
RecBole LightGCN để kiểm tái hiện (mục 7) và vài lần đo thời gian ngắn (`--probe-epochs`). Sau khi Nam chốt, bản này
là **đăng ký trước**: đổi gì phải ghi ở mục 13 kèm lý do, trước khi xem số mới.

Nguồn: nhận xét cô `E:\DATN\co\nhan_xet_co_06112026.md` (ngoài repo); kế hoạch cũ `n5_eval_plan.md`,
`cakg_eval_plan.md`, `cakg_v2_plan.md`; `docs/STATUS.md`. Nhánh `nam/v3-plan`.

Mỗi số trong file này ghi nguồn. **[ĐO]** = đọc từ log / `result.json` / output script. **[ƯỚC TÍNH]** = tính từ số
đo theo một giả định ghi rõ, chưa kiểm chứng bằng cách chạy thật.

## 0. Tóm tắt

| Câu hỏi | Trả lời ngắn | Nguồn |
|---|---|---|
| Giờ GPU cho A1–A3 (máy nhóm) | PA1 (chạy lại hết từ đầu) **⟨PA1⟩**; PA2 (chạy tiếp `last.pt`, giữ lần đã dừng sớm) **⟨PA2⟩**; PA3 (tối thiểu) **⟨PA3⟩** — khoảng = [cận dưới; cận trên] | mục 8, log `ai/data/survey/v3/run_uoc_tinh_gio_⟨nhãn⟩.log` |
| RecBole có tái hiện số LightGCN của nhóm không | ⟨chờ lần chạy RecBole⟩ | mục 7 |
| Kaggle | Đã có gói (2 dataset riêng tư + notebook mẫu), chưa tải lên | mục 9, `kaggle/README.md` |
| Cần Nam quyết | 9 câu [HỎI] | mục 12 |

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
| Thời gian | 13,7 s / epoch, chấm val 3,5 s [ĐO] | ⟨s / epoch⟩, chấm valid ⟨s⟩ [ĐO] | RecBole chấm chậm hơn nhiều (mục 7.4) |

### 7.3. Kết quả

⟨chờ lần chạy `results/recbole/repro_lightgcn_20261106/lightgcn_l2-1e-03_s1/`⟩

### 7.4. Hệ quả cho baseline mới

⟨điền sau 7.3⟩

## 8. Ngân sách giờ GPU

### 8.1. Số đo (máy nhóm GTX 1660 Ti) [ĐO]

Script `ai/survey/v3/uoc_tinh_gio_gpu.py` (chỉ đọc `result.json` + log sweep), log ⟨nhãn⟩:

| Mô hình | giây huấn luyện / epoch (trung vị; min–max) | giây / lần chấm val | phần cố định / lần chạy | số epoch đã đo |
|---|---|---|---|---|
⟨bảng⟩

### 8.2. Ba phương án [ƯỚC TÍNH]

Giờ một lần chạy = cố định + E × (giây / epoch) + số lần chấm × (giây / lần chấm). **Cận trên**: mọi lần chạy chưa
có số đo chạy đủ 1.000 epoch. **Cận dưới**: dừng ở mức sớm nhất mà số đo cũ cho phép (lần chạy tiếp: epoch tốt nhất
cũ + 50; seed mới: epoch tốt nhất nhỏ nhất của các seed cũ + 50; điểm lưới mới: số epoch nhỏ nhất đã chạy của mô hình
đó); baseline mới chưa có số nên cận dưới = cận trên.

⟨bảng phương án⟩

### 8.3. Chia việc máy nhóm / Kaggle (đề xuất, [HỎI 7])

⟨điền⟩

## 9. Kaggle

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
5. Gộp 5 seed chạy ở hai loại máy cho cùng một mô hình sẽ trộn sai lệch phần cứng vào độ lệch giữa seed (tránh, mục 5).

## 12. Câu hỏi cho Nam [HỎI]

⟨điền⟩

## 13. Sửa đổi kế hoạch

| Ngày | Sửa gì | Lý do |
|---|---|---|
| 06/11/2026 | Bản đầu | Nhận xét cô 06/11 |
