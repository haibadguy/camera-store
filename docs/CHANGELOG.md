# Nhật ký thay đổi so với bản của Hải

Bản gốc để so sánh: commit `62abf54` (Hải, 28/09/2026).
File này ghi lại mọi chỗ Nam sửa trong code hoặc dữ liệu của Hải. Mỗi mục gồm: **sửa gì**, **vì sao**, **ảnh hưởng thế nào** (số cũ → số mới).
Mục mới nhất nằm trên cùng.

---

## 09/10/2026: nội dung 5 — sửa code 05 theo kế hoạch đăng ký trước; chạy Popularity / MountAware trên val; chạy thử LightGCN, R-GCN. Nhánh `nam/content4`, code ở commit `f21ced4`

Theo `docs/reviews/n5_eval_plan.md` (mục 2: lỗi L1–L17; QĐ 5-1 .. 5-6). **Không huấn luyện dài, không chấm test.**

**Ví dụ trước.** Người dùng u có thân Canon EOS (EF-S) trong train, item val là một ống Nikon F.
- Bản của Hải (05a): MountAware loại **mọi** ống ngoài tập M = 1 của u. Người **không có thân** cũng bị loại hết ống, vì tập đó rỗng.
- Bản mới: chỉ loại ống mà `judge_lens` = True ("chắc chắn vi phạm", như ống Nikon F với thân Canon). Ống không phán được (ngoài M, "không chắc", có cặp "không biết") được giữ. Người không có thân không bị lọc gì.
- Ở u, ống Nikon F bị loại nên Hit của u chắc chắn = 0. Đó là cái giá của ràng buộc cứng mà kịch bản "ống cho người đã có thân" muốn đo.

**Sửa gì**
1. **`ai/pipeline/eval_05.py` (mới)**: phần chấm chung (L4, L7, L8, L15 một phần, L17).
   - Xếp hạng toàn bộ 27.940 sản phẩm. Bỏ item train; khi chấm test bỏ thêm item val (QĐ 5-1).
   - Quy tắc hòa: hạng = 1 + #(điểm lớn hơn) + #(bằng điểm và π nhỏ hơn). π là hoán vị cố định, seed 20261009, dùng chung mọi mô hình. Top-K xếp theo (điểm giảm, π tăng) trên đúng tập ứng viên.
   - Script tự kiểm cho **mọi** người dùng: "hạng ≤ K ⇔ item nằm trong top-K"; Recall@K (tính từ top-K) = Hit@K (tính từ hạng); top-K không chứa sản phẩm bị loại.
   - CVR@K lấy từ top-K này, dùng `common_05.judge_lens` (QĐ 4-9).
   - Kịch bản "ống cho người đã có thân" (mục 5): nhóm lắp được / không lắp được / không phán được. Số chính xếp hạng chỉ trong 1.339 ống; số phụ trên toàn catalog.
   - Sampled 1+99 là số phụ, giữ quy tắc hòa của Hải ở dạng tất định: âm mẫu bằng điểm xếp trên.
   - Bootstrap ghép cặp theo người dùng.
   - Mỗi lần chấm lưu mảng hạng / top-20 từng người dùng (`.npy`, ghi sha256 vào `result.json`).
2. **`05a_popularity.py` viết lại**:
   - bộ lọc MountAware mới (L6), mặt nạ numpy thay vòng Python (L7);
   - chỉ nhận `--split val`;
   - ghi vào thư mục mới, đã có thì DỪNG (L14);
   - DỪNG nếu CVR của MountAware khác 0.
3. **`05b_lightgcn_train.py` viết lại** (L9, L10, L11, L5, L13):
   - Xavier, Adam lr 0,001, batch 2048; λ là tham số dò;
   - tối đa 300 epoch, chấm NDCG@20 full ranking trên val mỗi 10 epoch, dừng sau 5 lần chấm không tăng;
   - hạng L2 viết theo code của tác giả (kuandeng/LightGCN `create_bpr_loss`; gusye1234/LightGCN-PyTorch `bpr_loss`, đọc ngày 09/10): λ · ½(‖e_u⁰‖² + ‖e_i⁰‖² + ‖e_j⁰‖²) / số cặp trong batch, chỉ embedding lớp 0.
4. **`05c_rgcn_train.py` viết lại: R-GCN thật** (L1, L2, L3, L16), đúng mục 6.4:
   - `RGCNConv` của PyG; 18 quan hệ; bỏ 134 + 134 cạnh có cờ `ngam_khong_chac` (script DỪNG nếu số cạnh bỏ khác 134);
   - kiểm cạnh user–item của `kg_hetero.pt` trùng `train.txt`;
   - mỗi nút một embedding; 2 lớp, d 64, B = 2, aggr mean, root_weight, ReLU chỉ giữa hai lớp, edge dropout 0,4;
   - bộ giải mã DistMult; loss BPR + 0,01·‖r‖²; lr là tham số dò; tối đa 100 epoch, chấm val mỗi 5 epoch.
5. **`train_05.py` (mới)**: vòng huấn luyện chung.
   - Âm mẫu lấy bằng numpy (không vòng Python). Một bộ sinh số cho cả lần chạy (L11).
   - Ở mỗi lần chấm val lưu `last.pt` (mô hình, Adam, trạng thái mọi bộ sinh số) → **chạy tiếp được** khi bị ngắt; xong thì ghi `result.json`, gõ lại lệnh sẽ bỏ qua.
   - Mỗi lần gọi ghi log tên mới `train_<thời điểm>.log`.
   - Hết giới hạn epoch mà chưa dừng sớm thì ghi `chua_chac_hoi_tu = true`.
6. **`05_val_sweep.py` (mới)**: dò trên val, seed 1, gồm 5 lần chạy (LightGCN λ ∈ {1e-5, 1e-4, 1e-3}, R-GCN lr ∈ {0,01; 0,001}).
   - Mỗi lần chạy là một tiến trình con, có log riêng. Chạy tiếp được.
   - DỪNG nếu cây git bẩn hoặc không có GPU.
   - Cuối cùng in bảng NDCG@20 val.
7. `05_evaluate.py`: chỉ thêm ghi chú "bản cũ, đọc kết quả cũ". Bảng tổng hợp mới (bootstrap, S1–S5) chưa viết; sẽ viết cùng script chạy test.
8. `.gitignore`: bỏ `results/n5/**/*.pt`, `*.npy`, `results/n5/smoke_*/`. 5 file `results/*.json` của Hải **không đụng tới**.
9. Kiểm thử: `ai/survey/content5/test_eval_05.py`.

**Vì sao:** kế hoạch mục 2.
- R-GCN cũ không phải R-GCN và không chạy được với đồ thị mới.
- Sampled 1+99 dễ trúng vì 87% âm mẫu là phụ kiện.
- Bộ lọc MountAware cũ loại mất item test của 3.856 người (khảo sát 09/10).
- Không có quy tắc hòa điểm (Popularity hòa rất nhiều).
- Siêu tham số không có nguồn.
- Kết quả ghi đè file cố định.

**Kiểm thử**
- `test_eval_05.py` **ĐẠT CẢ**: chạy trên commit `f21ced4`, log `ai/data/survey/n5/run_test_eval_05_20261009_lan2_f21ced4.log` (lần 1 trước commit: `run_test_eval_05_20261009_lan1.log`, cũng đạt cả). Gồm:
  - ví dụ mục 1 (hạng 3, Hit@2 = 0, NDCG@3 = 0,5; chấm test bỏ cả D lẫn E);
  - quy tắc hòa theo π;
  - train / val không vào top-K; ống bị lọc −∞ vẫn xếp trước sản phẩm không phải ứng viên;
  - Recall = Hit (cố ý làm sai thì báo lỗi);
  - CVR từ top-K = `full_catalog_cvr` cũ trên ví dụ dựng tay;
  - nhóm kịch bản; sampled hòa điểm; bootstrap hai mô hình giống hệt → hiệu (0, 0, 0).
- **Bộ lọc MountAware trên dữ liệu thật:** mặt nạ = `judge_lens is True` ở mọi ô của 10.406 người có thân × 1.033 ống (0 ô lệch; 8.557.447 cặp chắc chắn vi phạm). Người không có thân: 0 ống bị lọc.
- **CVR của MountAware = 0** ở K = 5, 10, 20, cả toàn catalog lẫn kịch bản chỉ ống (script tự kiểm).
- **Tái lập Popularity:** chạy 3 lần (lan1 trước commit, lan2, lan3 trên `f21ced4`). 14/14 mảng từng người dùng của mỗi mô hình trùng sha256, số liệu trùng hết (`ai/data/survey/n5/run_sha256_popularity_val_20261009.log`).
- **Chạy thử mỗi mô hình 3 epoch** trên dữ liệu thật, chấm val mỗi epoch (`results/n5/smoke_20261009/`, không lên git):
  - dừng giả lập sau 2 epoch rồi gõ lại lệnh → chạy tiếp từ epoch 3 đúng; gõ lại lần nữa → bỏ qua;
  - `05_val_sweep.py --smoke` (1 epoch mỗi lần chạy, `results/n5/smoke_val_sweep_20261009/`): chạy đủ 5 lần chạy, gõ lại thì bỏ qua cả 5.
  - Lần chạy thử đầu phát hiện lỗi chạy tiếp (trạng thái bộ sinh số CPU bị nạp lên GPU), đã sửa trước commit.

**Ảnh hưởng: số mới trên val** (log `results/n5/val_popularity_20261009_lan2/run_20261009_010620.log`, `result.json`; 67.661 người dùng; chỉ bỏ item train)

| Full ranking, val | Recall@5 | Recall@10 | Recall@20 | NDCG@10 | NDCG@20 |
|---|---:|---:|---:|---:|---:|
| Popularity | 0,0136 | 0,0228 | 0,0380 | 0,0114 | 0,0152 |
| Popularity-MountAware | 0,0136 | 0,0229 | 0,0382 | 0,0114 | 0,0153 |

- Hit@K = Recall@K (đã kiểm từng người).
- Item val hòa điểm với ít nhất một ứng viên: 61.465 người (Popularity) / 61.460 người (MountAware). Vì thế quy tắc hòa π ảnh hưởng thật tới số của Popularity.
- Top-10 trung bình: Popularity 0,99 ống + 9,01 phụ kiện; MountAware 0,89 ống + 9,11 phụ kiện. Top-10 chung của mọi người gần như chỉ có **một** ống, nên CVR@10 của Popularity gần như là phán trên đúng ống đó.

| CVR (val, người có thân trong train: 10.406) | @5 | @10 | @20 |
|---|---:|---:|---:|
| Popularity: CVR (vi phạm / ống chấm được; số người được tính) | 0,5625 (9/16; 16) | 0,6759 (6.789/10.045; 10.032) | 0,7003 (14.070/20.092; 10.346) |
| Popularity-MountAware | 0 (0/7; 7) | 0 (0/3.268; 3.268) | 0 (0/6.028; 5.922) |

| Kịch bản (val), chỉ ống | số người | Pop Recall@10 | MA Recall@10 | Pop CVR@10 | MA CVR@10 |
|---|---:|---:|---:|---:|---:|
| lắp được | 904 | 0,1471 | 0,2179 | 0,6967 | 0 |
| không lắp được (có cặp `requires_adapter`: 18) | 236 | 0,0551 | **0** | 0,7789 | 0 |
| không phán được | 12 | 0,4167 | 0,4167 | 0,7750 | 0 |

- Đúng như kế hoạch dự kiến: MountAware cho Recall = 0 ở **mọi** người nhóm "không lắp được" (236/236 item val bị lọc), và tăng Recall ở nhóm "lắp được".
- Sampled 1+99 (số phụ), Popularity / MountAware: Hit@10 0,4605 / 0,4603; NDCG@10 0,2845 / 0,2847.
- **Đặt cạnh số cũ của Hải (không so trực tiếp được).** Số cũ là sampled trên **test**, dữ liệu trước khi gộp lặp, M cũ, bộ lọc cũ, CVR cũ chia cho K:
  - Popularity Hit@10 0,4188 / MountAware 0,4112; CVR@10 0,0577 / 0.
  - Ở số cũ, MountAware thấp hơn Global; ở số mới (val), hai bên gần bằng nhau. Điều này khớp với việc bộ lọc cũ loại nhầm item cần đoán (L6), nhưng chưa tách được bao nhiêu là do bộ lọc, bao nhiêu do dữ liệu / M đổi.

**Thời gian thật mỗi epoch** (GTX 1660 Ti, batch 2048, các lần chạy thử ở trên)

| | Huấn luyện / epoch | Một lần chấm val (full ranking) | Đỉnh GPU (khảo sát 09/10) |
|---|---:|---:|---:|
| LightGCN | 12,5–14,0 s | 3,4–3,6 s | 367 MiB |
| R-GCN (18 quan hệ, bỏ 268 cạnh) | 27,4–28,9 s | 3,5–3,6 s | 1.090 MiB |

Lấy âm mẫu + xáo: 0,03–0,04 s / epoch. Chấm đầy đủ cuối mỗi lần chạy (full, CVR, kịch bản, sampled): khoảng 15 s.

**Phát hiện, chưa chắc**
1. **R-GCN không tất định trên GPU.** Cùng cấu hình lr 0,01, seed 1:
   - lần chạy thử đầu: epoch 1 loss 0,37824, NDCG@20 val 0,01229;
   - lần chạy qua `05_val_sweep --smoke`: loss 0,37846, NDCG@20 val 0,01360.

   LightGCN hai lần cho cùng số (loss 0,57152, NDCG@20 0,01601). Kế hoạch mục 7.3 đã ghi đây là hạn chế. Mức lệch thật sau khi hội tụ chưa biết.
2. **Bài LightGCN ghi Xavier, nhưng code của tác giả khởi tạo normal** (std 0,01 ở bản TF; std 0,1 ở bản PyTorch; dòng Xavier bị comment). Giữ Xavier theo kế hoạch đã chốt (L10). Ghi là sai khác so với code gốc.
3. **Chi tiết cài R-GCN kế hoạch chưa ghi, nay là quyết định cài đặt (chưa có nguồn):**
   - vector r của DistMult khởi tạo glorot, giống mọi tham số của `RGCNConv` (`reset_parameters` dùng glorot);
   - L2 = 0,01·‖r‖², tính mỗi bước, không chia batch;
   - không có L2 trên embedding nút;
   - `RGCNConv` có bias (mặc định của PyG);
   - edge dropout lấy mẫu lại mỗi bước, cạnh xuôi và cạnh ngược bị bỏ độc lập với nhau.

   Đã ghi vào kế hoạch mục 13.
4. Kết quả lần chạy thử (smoke) **không dùng để chọn mô hình**: chỉ 1–3 epoch.

**Phía sau phải làm**
- Nam chạy `05_val_sweep.py` qua đêm, rồi chốt `ai/config/n5_final.toml` (kế hoạch 7.2 bước 3) và commit.
- Seed 2, 3 cho cấu hình chốt.
- Viết script chạy test một lần (kế hoạch 7.2 bước 5): 4 mô hình × mọi seed, bootstrap, S1–S5, bảng tổng hợp thay `05_evaluate.py`.

## 08/10/2026 (khuya, tiếp 3): cờ `ngam_khong_chac` trong đồ thị; sửa ví dụ QĐ 4-9. Nhánh `nam/content4`

Nam chốt các câu treo của mục trước.

**Sửa gì**
1. **`04_build_knowledge_graph.py`:** cạnh `has_spec → mount` có thêm thuộc tính `ngam_khong_chac` (int8; 1 = cạnh của ống "không chắc" theo QĐ 3-4). Cột mới cùng tên trong `kg_edges_has_spec_mount.csv`, số đếm `has_spec_mount_ngam_khong_chac` trong `kg_stats.json`.
   - Kiểm tra 6A (5) có thêm một điều kiện: 134 cạnh có cờ, đúng bằng 134 ống "không chắc", mỗi ống 1 cạnh, mọi cạnh khác cờ 0.
   - Mục 6B in thêm 10 cạnh có cờ.
2. **Ví dụ QĐ 4-9:** sửa trong `test_cvr.py`, docstring `common_05.judge_lens`, STATUS, `content4_design`. Logic CVR không đổi.
   - Rebel T6s + FM-10, ống Nikon DX → không chấm được.
   - D3200 + FM-10, ống Canon EF → vi phạm.

**Vì sao**
- Cờ: không có cờ thì mô hình có thể suy "lắp được" qua đường thân → ngàm ← ống "không chắc", trái QĐ 4-5.
- Ví dụ cũ (D3500 + FM, Canon EF → không chấm được) viết khi QĐ 3-16 còn xếp mọi cặp có thân phim là "không biết". Sau Red Team T4, cặp (FM-10, Canon EF) là "không lắp được".

**Ảnh hưởng** (sao lưu bản trước ở `ai/data/kg_c8eb613/`, chạy lại với `--overwrite`)
- Số nút, số cạnh: **không đổi** (95.646 nút; 558.475 cạnh xuôi).
- So sha256 với bản trước: chỉ 3 file đổi (`kg_hetero.pt`, `kg_stats.json`, `kg_edges_has_spec_mount.csv`); 9 file còn lại giống hệt.
- Log mới khác log cũ đúng 3 chỗ: dòng đếm cờ, kiểm tra 5 mới, 10 dòng ví dụ cạnh có cờ.
- Kiểm tra 6A (1)–(7) ĐẠT cả (log `ai/data/kg/kg_validation_log_20261008_khongchac_lan1.txt`).
- Kiểm tra 8: chạy 2 lần (lần 2 vào thư mục tạm ngoài repo), 13/13 file trùng sha256 (`ai/data/kg/kg_sha256_khongchac_lan1_vs_lan2_20261008.txt`).
- `test_cvr.py` 26/26 ĐẠT (log `ai/data/survey/run_c4_test_cvr_20261008_vidumoi.log`). Cả hai ví dụ mới cũng đúng trên dữ liệu thật:
  - (T6s, AF-S DX 35mm) không có M = 1, không "không biết" → chắc chắn không lắp;
  - (FM-10, DX 35mm) "không biết";
  - (D3200, EF 50mm STM) và (FM-10, EF 50mm STM): không có M = 1, không "không biết".

**Phía sau phải sửa theo**
- Nội dung 5: bộ lọc Popularity MountAware chỉ được loại ống "chắc chắn vi phạm" (`judge_lens` trả True), giữ ống không chấm được (Nam chốt). **Chưa sửa** `05a_popularity.py`.
- Mô hình ở nội dung 7 phải đọc thuộc tính `ngam_khong_chac` (và `src_phu_kien`, `phia`) của cạnh `has_spec → mount`.

**Dọn dẹp:** đã xóa `ai/data/kg_draft_c4/`, `kg_draft_c4_lan2/`, `kg_draft_rt1b/`, `kg_draft_rt1b_lan2/`, `kg_draft_rt1b_lan2_final/` (theo yêu cầu của Nam).

---

## 08/10/2026 (khuya, tiếp 2): nội dung 4, việc 3–4 — viết lại `04_build_knowledge_graph.py`, sửa `common_05.py` (CVR theo QĐ 4-9). Nhánh `nam/content4`

Theo `docs/content4_design.md` mục 2, 5, 6, 7, 9. **Không sửa** `05a/05b/05c` và `05_evaluate.py` (nội dung 5).

**Sửa gì**
1. **`ai/pipeline/04_build_knowledge_graph.py`: viết lại toàn bộ.** Bản của Hải đọc `linked_products.csv` + bảng 139 dòng (đã gỡ khỏi git ở QĐ 3-14), `assert` cứng 257 / 106 / 151, nên không chạy được với đầu ra nội dung 3 mới.
   - Đầu vào: `item_attributes.csv`, `compat_pairs.csv`, `compatibility_matrix.npz`, `unknown_mask.npz`, `body_index.json`, `lens_index.json` (nội dung 3); `train/val/test.txt`; `mount_rules.toml`, `usecase_rules.toml`. Không đọc CSV của script khảo sát.
   - Nút (7 loại): `user`, `item` (vector 9 chiều: one-hot 4 loại + tiêu cự min/max, khẩu độ min/max, cờ "có số"), `mount`, `sensor_format`, `focal_range`, `aperture_class`, `usecase`.
   - Cạnh (9 loại xuôi): `interacted_with`; `compatible_with`, `crops_sensor`, `requires_adapter` (bỏ mức `unknown` và ống "không chắc", QĐ 4-5); `has_spec` tới 4 loại nút thuộc tính; `suitable_for`.
   - `has_spec → mount` có 2 thuộc tính cạnh (QĐ 4-10): `src_phu_kien` (1 = nguồn là phụ kiện) và `phia` (0 không phải ngàm chuyển, 1 phía ống, 2 phía thân). Ngàm chuyển `"A>B"` → 2 cạnh: A là phía ống, B là phía thân (vd `leica_m>mft` "Leica M to Micro 4/3").
   - `compatible_with` mang thêm thuộc tính `crop_unknown` (cờ QĐ 3-11, lấy nguyên từ `compat_pairs.csv`).
   - Khổ cảm biến: khung `ff` / `apsc` giữ nguyên; khung `khac` tra theo ngàm: `mft`, `four_thirds` → four_thirds; `nikon_1` → one_inch; `fuji_g` → medium; `pentax_q` → small; `canon_ef` (EOS-1D) và `leica_m` (M8) → aps_h. Ngàm `khac` ngoài bảng này thì script DỪNG.
   - Cạnh ngược: `ToUndirected(merge=False)`. Lý do: với cạnh item → item, `ToUndirected()` mặc định **gộp** cạnh ngược vào chính quan hệ đó (thành vô hướng, số cạnh nhân đôi), không tạo `rev_*` như thiết kế mục 5 viết. `merge=False` tạo `rev_*` cho mọi quan hệ.
   - Mọi danh sách cạnh được sắp xếp → đầu ra tái lập được.
   - Kiểm tra mục 6A (1)–(7) chạy trong script; sai một điều kiện thì DỪNG (mã thoát 2) và không ghi đầu ra. Mục 6B in vào log.
   - Log tên mới theo `--run-label` (`kg_validation_log_<nhãn>.txt`); đã có thì DỪNG. Các file đầu ra khác cần `--overwrite` mới ghi đè.
2. **`ai/pipeline/usecase_labels.py` (mới):** chép nguyên hàm `crops`, `labels_at`, `label` của `ai/survey/content4/count_usecase.py`, để script 04 gắn nhãn mục đích từ `usecase_rules.toml` + `lens_specs.read_title`. Việc kiểm nguồn / câu trích vẫn do `count_usecase.py` làm.
3. **`ai/pipeline/common_05.py`** (content4_design mục 7, QĐ 4-9):
   - `load_item_type()` đọc `item_attributes.csv`, 4 mã: 0 thân, 1 ống, 2 phụ kiện, **3 khác** (trước: `argmax` của `kg_hetero.pt`, 3 mã, máy ống liền bị gộp vào phụ kiện);
   - `load_body_to_lenses()` đọc `kg_edges_compatible_with.csv` + `kg_edges_crops_sensor.csv` (tức M = 1; trước: `compatible_item_edges.csv` của Hải);
   - **`build_train_bodies()`: lấy mọi thân trong train** (trước: chỉ thân có ít nhất một ống M = 1). Lý do: QĐ 4-9 "xét các thân người dùng có trong train"; nếu bỏ thân máy phim thì cặp "không biết" của nó không còn chặn được phán "vi phạm". Giữ nguyên chữ ký hàm;
   - **CVR mới** (`judge_lens`, `full_catalog_cvr`): ống chấm được khi nằm trong M, không "không chắc", và (a) có thân M = 1 → không vi phạm, hoặc (b) mọi thân M = 0 và không cặp nào "không biết" → vi phạm; còn lại không chấm được. Thân nằm ngoài M (không xác định được ngàm) không có giá trị M, nên không bao giờ cho (b). Gộp **micro**; người dùng không có ống chấm được trong top-K bị bỏ. Trả kèm `cvr_n_users@K`, `cvr_n_lenses@K`, `cvr_n_violations@K`, `cvr_n_users_with_body`; `cvr@K = nan` khi không có ống nào chấm được. Trước: vi phạm = mọi ống không thuộc tập hợp lệ, chia K, người dùng không có ống thì CVR = 0;
   - bỏ `import torch`, `pandas` (không còn dùng).
4. **Kiểm thử, đối chiếu:** `ai/survey/content4/test_cvr.py` (dựng tay + tra dữ liệu thật), `check_suitable_for_vs_survey.py`.
5. `.gitignore`: đưa `kg_hetero.pt` lên git (19,2 MB); không đưa `kg_edges_interacted_with.csv` (chính là `train.txt`, vốn không lên git).

**Vì sao**
- Script 04 cũ không chạy được, và đồ thị cũ gần như rỗng: 99,11% sản phẩm không có cạnh tri thức nào.
- CVR cũ tính ống "không chắc" và cặp "không biết" là vi phạm, trái QĐ 3-4, 3-8, 3-16 (QĐ 4-6).

**Ảnh hưởng: đồ thị cũ (Hải, `kg_v62abf54/kg_stats.json`) → mới (`ai/data/kg/kg_stats.json`, log `ai/data/kg/kg_validation_log_20261008_lan1.txt`)**

| | Cũ | Mới |
|---|---:|---:|
| Nút `user` / `item` | 70.424 / 28.867 | 67.661 / 27.940 (dữ liệu sau gộp lặp) |
| Loại nút thuộc tính | `mount` 8, `usecase` 7 | `mount` 23, `sensor_format` 7, `focal_range` 6, `aperture_class` 5, `usecase` 4 |
| Tổng số nút | 99.306 | **95.646** |
| `interacted_with` | 482.149 | **460.193** |
| `compatible_with` (thân → ống) | 3.258 | **70.472** |
| `crops_sensor` | — | **2.248** |
| `requires_adapter` | — (ghi "ngoài phạm vi") | **16.301** |
| `has_spec → mount` (cũ: `has_mount`) | 257 | **2.968** (thân 537, ống 1.167, phụ kiện 954, ngàm chuyển 155 × 2) |
| `has_spec → sensor_format` | — | **1.498** (ff 575, apsc 681, four_thirds 212, one_inch 17, aps_h 6, small 4, medium 3) |
| `has_spec → focal_range` | — | **2.427** |
| `has_spec → aperture_class` | — | **1.288** |
| `suitable_for` | 441 | **1.080** (phong cảnh 560, thể thao/chim 287, chân dung 147, macro 86) |
| Sản phẩm có ít nhất một cạnh tri thức | 257 (0,89%) | **2.974 (10,64%)** |

Số mới khớp các số dự kiến trong `content4_design` mục 3.2, 5 (từ `count_spec_nodes.py`, `count_usecase.py`, `mount_compat_stats.json`). Tổng nút dự kiến "khoảng 95.650" → thật 95.646.

**Kiểm tra mục 6A** (log `kg_validation_log_20261008_lan1.txt`): cả 8 ĐẠT.
1. Chỉ số nút trong khoảng, không cạnh lặp, ở cả 18 loại cạnh (kể cả `rev_*`); ba quan hệ thân–ống đều đi từ thân tới ống.
2. `interacted_with` = đúng tập cặp `train.txt`, 460.193; giao val = 0, giao test = 0.
3. `compatible_with` 70.472 + `crops_sensor` 2.248 = 72.720 = nnz(M), trùng từng cặp với M; `requires_adapter` 16.301 = số dòng tương ứng của `compat_pairs.csv`; ba quan hệ không trùng cặp; 0 cặp thuộc `unknown_mask`; 0 cạnh tới 134 ống "không chắc".
4. Mọi cạnh có `rule_id` đúng mức và khớp ngàm hai đầu theo `mount_rules.toml` (sai 0). `crops_sensor`: 2.248/2.248 cùng ngàm; `requires_adapter`: 0/16.301 cùng ngàm, đúng 10 cặp ngàm có ngàm chuyển trong bảng luật.
5. 1.704 thân + ống có 1 ngàm: đúng 1 cạnh, trùng cột `mount`; 954 phụ kiện: 1 cạnh có cờ; 155 ngàm chuyển: 2 cạnh (phía ống, phía thân); tổng 2.968 = 1.704 + 954 + 2 × 155.
6. 18 thân máy phim: 0 cạnh thân–ống.
7. `torch.load` đọc lại khớp từng tensor; đồ thị đồng nhất 95.646 nút, 1.116.950 cạnh, 18 quan hệ; 1 lớp `RGCNConv` chạy trên GTX 1660 Ti, ra (95.646, 16), hữu hạn.
8. Chạy 2 lần (lần 2 vào `ai/data/kg_draft_c4_lan2/`, nay đã xóa): **13/13 file trùng sha256**, kể cả nội dung log (`ai/data/kg/kg_sha256_lan1_vs_lan2_20261008.txt`).

**Đã kiểm chứng thêm**
- Nhãn mục đích của pipeline trùng từng ống với bảng của `count_usecase.py` (1.080 cạnh, 980 ống, 0 ống lệch; log `ai/data/survey/run_c4_suitable_for_vs_survey_20261008.log`).
- Kiểm thử CVR (`test_cvr.py`, log `ai/data/survey/run_c4_test_cvr_20261008_lan2.log`; `_lan1` có một dòng đếm ghi nhãn sai "thân máy phim", đã sửa nhãn, các số khác giống hệt): 20/20 ca dựng tay đúng, gồm ví dụ QĐ 4-9 (D3500 + FM, ống Canon EF, giả định cặp (FM, EF) "không biết") → không chấm được; gộp micro 2/3 khác macro 0,5; người dùng không có ống chấm được bị bỏ; không ai chấm được → `nan`.
- Trên dữ liệu thật: 10.406 người dùng có thân trong train (quy tắc cũ của `build_train_bodies` trên cùng dữ liệu: 10.226); 71 người có thân ngoài M; 108 người có thân máy phim; 216 người có thân trong M mà không có ống M = 1 nào (34 thân như vậy, 18 là máy phim).

**Phát hiện: ví dụ của QĐ 4-9 không còn đúng với dữ liệu hiện tại.** QĐ 4-9 ghi cặp (FM, Canon EF) là "không biết" theo QĐ 16 bản đầu. Nhưng QĐ 16 đã sửa theo Red Team T4: cặp mà luật thường cho "không lắp được" (khác ngàm) giữ "không lắp được". Tra dữ liệu thật: (FM-10, Canon EF 50mm f/1.8 STM) không có M = 1, cũng không thuộc "không biết". Vì vậy người dùng có D3200 + FM-10 mà top-K có ống Canon EF thì ống đó **bị tính vi phạm** (không có D3500 trong dữ liệu nên dùng D3200). Code làm đúng định nghĩa "chấm được"; chỉ có câu ví dụ là cũ. Chờ Nam xác nhận (STATUS mục 6).

**Phía sau phải chạy lại / sửa theo**
- `05c_rgcn_train.py` **không chạy được** với đồ thị mới: code này ghi cứng nút `mount` (8) / `usecase` (7), `Linear(3, ...)` cho `item.x` (nay 9 chiều), quan hệ `has_mount`. Thuộc nội dung 5 / 7 (lỗi 1), không sửa ở đây.
- `05a_popularity.py` (MountAware) lọc theo `cvr_users`: do `build_train_bodies` nay lấy mọi thân, người dùng chỉ có thân không có ống M = 1 nào (máy phim, thân ngoài M…) bị lọc **mọi** ống. Trước đây những người này không bị lọc gì. Cần xem lại khi chạy lại nội dung 5.
- Kết quả CVR của mọi mô hình phải tính lại; số cũ (vd 2.491 / 2.488 người dùng) không còn so được. `05_evaluate.py` chỉ đọc `cvr@K`, các khóa mới không làm hỏng bảng.
- Chưa chạy lại bất kỳ script 05 nào.

---

## 08/10/2026 (khuya, tiếp): nội dung 4, việc 2 — đo bước đọc tiêu cự / khẩu độ từ tiêu đề ống (đăng ký trước). Nhánh `nam/content4`

Theo kế hoạch `docs/reviews/n4_focal_aperture_plan.md` (commit `c14300e`; sửa đổi mục 9 ở commit `e47e941`, **trước khi chạy holdout**). Không sửa code của Hải; mọi file dưới đây là file mới của nội dung 4.

**Sửa gì**
1. **Bộ đọc riêng cho đồ thị:** `ai/pipeline/lens_specs.py`.
   - v0 chép nguyên `head_main` + `lens_sig` từ `eval_external.py`, để sửa ở đây không làm đổi bộ đánh giá của nội dung 3.
   - v1 sửa 3 chỗ:
     - S1: dải "f/1.8-22" là dải từ mở lớn nhất tới khép nhỏ nhất → bỏ số 22; dải toàn ≥ 11 như "f/22-32" → bỏ, đọc khẩu độ kế tiếp;
     - S2: "12mm - 24mm";
     - S3: khẩu độ đứng ngay sau "with".
   - Có thêm hàm khoảng nút (`focal_nodes`, `aperture_node`).
2. **Đáp án ngoài khớp không dùng thuộc tính cần đo:** `fa_match.py`. Kèm `fetch_wikidata_focal.py` (tải Wikidata P2151, 821 item, sha256 `42feaf8d…`).
3. **Đo, đếm phân loại, kiểm:** `fa_eval.py`, `fa_errors.py`, `fa_reader_diff.py`, `test_lens_specs.py` (38/38 đúng).

**Holdout: chạy một lần** (log `ai/data/survey/n4_fa/run_fa_eval_holdout_20261008.log`, file `fa_holdout_20261008.csv`). 325 ống, 570 ô. Khoảng tin cậy 95%: bootstrap theo cụm (mục nguồn), B = 10.000, seed 20261009. Không thấy lỗi script; không chạy lại. Số ghi ở đây **trước khi mở file ca lệch của holdout**.

| Chỉ số (bộ đọc mới v1) | Lensfun | Wikidata | Theo ống |
|---|---|---|---|
| T1 tiêu cự đúng mm | 162/202 = 80,2% [70,4–89,7] | 108/140 = 77,1% [68,5–85,2] | 200/270 = 74,1% [65,9–81,9] |
| **T2 tiêu cự đúng khoảng nút** | 165/202 = 81,7% [71,7–91,2] | 116/140 = 82,9% [75,4–89,9] | 211/270 = 78,1% [69,9–85,9] |
| K1 khẩu độ đúng số f (a1, a2) | 223/228 = 97,8% [95,8–99,5] | — | — |
| **K2 khẩu độ đúng khoảng nút** | 223/228 = 97,8% [95,8–99,5] | — | — |
| K3 [phụ] a1 đúng | 223/228 = 97,8% [95,8–99,5] | — | — |
| K4 [phụ] khẩu độ đầu tele đúng | 223/228 = 97,8% [95,8–99,5] | — | — |

- Bộ đọc cũ trên cùng holdout: mọi số tiêu cự **giống hệt**. Khẩu độ: K1 222/228 = 97,4%, K2 223/228, K3 223/228, K4 222/228. Tức là sửa S1–S3 chỉ đổi 1 ô (K1, K4 tăng 1).
- **Đọc số cho đúng:** trên nửa fix, 86/90 ô lệch là do đáp án (khớp nhầm sang ống khác mà nguồn có, hoặc Wikidata chỉ ghi 1 giá trị P2151 cho zoom), chỉ 2 ô do bộ đọc (kế hoạch 9.1). Vì vậy số tiêu cự thô là **cận dưới**, phần thiếu chủ yếu do bước khớp, không phải do bộ đọc. Holdout: 72 ống có đáp án tiêu cự từ cả hai nguồn, **chỉ 53 ống hai đáp án trùng** (nửa fix: 72/75), dấu hiệu nhiều ca khớp nhầm.

**Phân loại ca lệch của holdout** (sau khi đã commit số ở trên, commit `c9a369f`; chỉ để báo cáo, không sửa bộ đọc).
- Bảng: `ai/survey/content4/n4_fa_holdout_errors.csv`, người phân loại Claude. Đếm: `fa_errors.py`, log `ai/data/survey/n4_fa/run_fa_errors_holdout_20261008.log`.

| Phép đo / nguồn | Ô | Lệch | Khớp nhầm ống khác | Nguồn thiếu giá trị | Tiêu đề không ghi khẩu độ | **Do bộ đọc** |
|---|---:|---:|---:|---:|---:|---:|
| Khẩu độ / Lensfun | 228 | 5 | 3 | 0 | 2 | **0** |
| Tiêu cự / Lensfun | 202 | 40 | 40 | 0 | 0 | **0** |
| Tiêu cự / Wikidata | 140 | 32 | 23 | 9 | 0 | **0** |

- Số phụ (kế hoạch 9.2): ô không sai do bộ đọc 228/228, 202/202, 140/140. Bootstrap cho khoảng [100–100] vì không có ô sai nào. Khoảng này **không** có nghĩa là bộ đọc chắc chắn đúng 100%.
- Một ca nhắc riêng: B07GRSTN82 là ống cine "Meike 25mm T2.2". Tiêu đề ghi T-stop, không ghi số f, nên bộ đọc trả rỗng (đúng). Bước khớp lại nối nó với Meike 25mm f/1.8, là một ống khác.
- Ví dụ khớp nhầm điển hình: 10 listing "Sigma 150-600mm Contemporary" khớp với "Sigma 100-400mm Contemporary" của Lensfun (cùng khẩu độ F5-6.3, cùng token chữ), vì Lensfun không có ống 150-600 Contemporary.
- Chỉ đọc ca **lệch**. Ca mà bộ đọc và đáp án cùng sai giống nhau thì không thấy được (Lensfun và bộ đọc dùng cùng họ regex, kế hoạch 8.2).

**Kèm theo: luật mục đích** (`ai/config/usecase_rules.toml` v0.2 → v0.3, `count_usecase.py`)
- 3 câu trích có "..." thay bằng đoạn nguyên văn liền, theo chuẩn nội dung 3 (không ghép đoạn): Canon US lens guide (phong cảnh), Canon EU landscape (phong cảnh), Canon EU beginner (thể thao / chim). Cả 3 kiểm OK trên bản sao đã lưu.
- `count_usecase.py`: câu trích có "..." nay bị coi là THIẾU; đọc tiêu đề bằng `lens_specs` v1.
- Đếm lại. Log `ai/data/survey/run_c4_usecase_count_20261008_n4fa.log`; chạy 2 lần, CSV và log trùng sha256. Bảng nhãn cũ sao lưu ở `usecase_labels_draft_20261008_rt1b.csv`, so bằng `compare_usecase_labels.py` (log `run_c4_usecase_compare_rt1b_vs_n4fa_20261008.log`).

| Nhãn | Trước (`_rt1b`, /1.287) | Sau (/1.288) |
|---|---:|---:|
| Phong cảnh | 559 | **560** |
| Thể thao / chim | 287 | 287 |
| Chân dung | 144 | **147** |
| Macro | 86 | 86 |
| Không nhãn nào | 309 | 308 |

- 13 ống đổi kết quả đọc, 4 ống đổi nhãn:
  - SEL85F18 thêm chân dung (lỗi "F/1.8-22");
  - 2 listing SEL90M28G 90mm f/2.8 Macro thêm chân dung;
  - Lumix G Vario 14-140mm thêm phong cảnh (trước không đọc được vì khẩu độ nằm sau "with").
- **Phải làm theo:** khi dựng đồ thị (việc 3), script 04 dùng `lens_specs.read_title`, không dùng `eval_external.lens_sig`.

## 08/10/2026 (khuya): lần đo thứ 3 của nội dung 3 (đăng ký trước). Nhánh `nam/content4`

Theo kế hoạch `docs/reviews/n3_eval_lan3_plan.md` (commit `42da14b`; mục 8 đã chốt và mục 9 sửa đổi ở commit `fb30c65`, **trước khi đo**). Quy tắc không đổi (`ea6abb0`). Holdout **không sạch** (kế hoạch mục 2), nên đây là phép đo lại có điều chỉnh, không phải phép đo độc lập.

**Sửa gì**
1. `ai/survey/content3/eval_external.py` (chỉ chế độ `lan3`; `lan2` và `truoc_0710` không đổi):
   - "manual" đứng trước "focus" không còn là từ phụ kiện (`manual(?![\s-]*focus)`, kế hoạch 9.2). Vd "Pentax K1000 Manual Focus SLR Film Camera" không còn bị loại; "Instruction Manual" vẫn bị loại;
   - ô có đáp án `khac_ngam` chấm theo H3 (kế hoạch 9.3): quy tắc không gán ngàm cụ thể → không chấm; quy tắc gán ngàm cụ thể mà nguồn ghi một **ngàm thật** nhóm không có mã (danh sách `KHAC_NGAM_THAT`: Minolta MD, Olympus OM, Contax/Yashica, Mamiya 645…) → **sai**; nguồn ghi ngàm không rõ ("Generic", lỗi gõ "Pentak K"…) → không chấm;
   - cột thông tin mới `ngam_khac_that` (mọi chế độ, không dùng để chấm) và ghi được file khi không khớp được sản phẩm nào.
2. Script mới: `bootstrap_ci.py` (khoảng tin cậy bootstrap theo cụm, thay Wilson), `n3_lan3_measure.py` (phép đo (1)–(6) và tập N), `core_coverage.py` (tính lại "vấn đề cốt lõi" của STATUS).

**Kiểm trước khi đo** (chỉ nửa fix và ví dụ dựng tay)
- `test_eval_external.py`: 100/100 ca đúng (`run_test_eval_external_20261008_lan3do.log`). `bootstrap_ci.py` tự kiểm 6/6 (`n3_lan3/run_test_bootstrap_ci_20261008.log`).
- Nửa fix, 3 chế độ, so với bản trước sửa: **giống hệt từng ô** (`n3_lan3/run_compare_fix_*_cu_vs_moi2_20261008.log`).
- Script đo chạy thử trên nửa fix (`n3_lan3/run_measure_fix_thu_20261008.log`): F746 cho lại đúng số cũ của nửa fix (Lensfun 535/548, 352/357; Wikidata 283/295, 239/239; theo sản phẩm 582/598).
- Mã băm đầu vào trước khi đo trùng log đăng ký trước (`n3_lan3/run_lan3_prereg_check_20261008_truoc_do.log`).

**Chạy trên holdout: một lần.** Log và file trong `ai/data/survey/n3_lan3/`: `run_eval_holdout_{lan2,lan3,truoc_0710}_20261008.log`, `run_eval_ngoai_{lan3,lan2}_20261008.log`, `run_measure_holdout_20261008.log`; bảng mọi chỉ số `holdout_bang_so_20261008.csv`. Khoảng tin cậy 95%: bootstrap theo cụm `cum_nguon`, B = 10.000, seed 20261009. Không thấy lỗi script sau khi chạy; không chạy lại.

**Số chính: H733 (holdout bỏ 14 mẫu dev), quy tắc `ea6abb0`, bộ đánh giá `lan2`**

| Nguồn | Chỉ số | Đúng / chấm | Tỉ lệ [KTC 95%] |
|---|---|---:|---|
| Lensfun | loại | 553/558 | 99,1% [98,2–99,8] |
| Lensfun | ngàm (đúng / gán) | 383/394 | 97,2% [93,1–99,7] |
| Lensfun | khung thân | 196/196 | 100% [100–100] |
| openMVG | khung thân | 125/126 | 99,2% [97,4–100] |
| Wikidata | loại | 304/313 | 97,1% [94,9–99,0] |
| Wikidata | ngàm | 266/266 | 100% [100–100] |
| Gộp nguồn | loại đúng theo sản phẩm (đúng ở mọi nguồn có đáp án) | 585/598 | 97,8% [96,6–98,9] |

Cả 733 sản phẩm đều khớp được. Ngàm Lensfun: 4 ô quy tắc để trống; 1 ô đáp án `khac_ngam` tính sai (ở `lan2` mọi ô `khac_ngam` bị tính sai khi quy tắc gán ngàm).

**So các bộ đánh giá, cùng quy tắc `ea6abb0`, tập H733** (H747 trong ngoặc khi khác)

| Chỉ số | lần đo 2 (quy tắc trước `e8b39e6`) | **lan2 (chính)** | lan3 ¹ | truoc_0710 ² |
|---|---:|---:|---:|---:|
| Sản phẩm khớp được | 733 (747) | 733 (747) | 726 (740) | 733 (747) |
| Loại, Lensfun | 552/558 (565/571) | **553/558** (566/571) | 553/555 (566/568) | 572/577 (585/590) |
| Ngàm, Lensfun | 382/393 (391/402) | **383/394** (392/403) | 383/394 (392/403) | 332/334 (341/343) |
| Loại, Wikidata | 303/313 (305/315) | **304/313** (306/315) | 304/307 (306/309) | 335/359 (338/362) |
| Ngàm, Wikidata | 265/265 (266/266) | **266/266** (267/267) | 266/266 (267/267) | 242/267 (244/269) |
| Loại theo sản phẩm | 584/598 (598/612) | **585/598** (599/612) | 586/591 (600/605) | 570/598 (584/612) |
| Khung thân Lensfun / openMVG | 196/196, 125/126 (204/204, 132/133) | như cột bên | như cột bên | như cột bên |

¹ `lan3`: **sau khi sửa lỗi bộ đánh giá tìm từ ca holdout đã xem.** ² `truoc_0710`: **dựng lại theo mô tả, mã gốc không còn.**

Tỉ lệ và khoảng (H733): `lan2` xem bảng trên; `lan3` loại Lensfun 99,6% [99,1–100], Wikidata 99,0% [97,8–100], theo sản phẩm 99,2% [98,3–99,8]; `truoc_0710` loại Wikidata 93,3% [88,6–97,1], ngàm Wikidata 90,6% [82,6–97,6], theo sản phẩm 95,3% [92,2–97,8]. H747, `lan2`: loại Lensfun 99,1% [98,3–99,8], ngàm Lensfun 97,3% [93,3–99,7], loại Wikidata 97,1% [94,9–99,0], theo sản phẩm 97,9% [96,6–98,9].

Đọc bảng:
- **lần đo 2 → lan2** (đổi quy tắc, cùng bộ đánh giá): mỗi chỉ số tăng đúng 1 ô đúng. Kiểm từng dòng (`n3_lan3/run_holdout_errors_lan3do_20261008.log`): chỉ B00L2PN5L8 đổi ô chấm (ống EF-S 55-250 trước bị xếp thân, sửa ở `e8b39e6` theo đúng ca sai holdout này); ngoài ra B00ZY8CII0 đổi khung ống `khong_ro` → `ff` (sửa T2), cột không được chấm. Phần chênh này **không** độc lập.
- **lan2 → lan3** (đổi bộ đánh giá): 7 sản phẩm không còn được chấm; số ô **đúng** không đổi ở mọi chỉ số, chỉ bớt ô sai (loại: Lensfun bớt 3 ô sai, Wikidata bớt 6). Đúng như kế hoạch dự báo: các sửa N4 chỉ loại bớt các ca sai holdout đã xem. Sửa S2 và 9.2 không đổi gì trên holdout.
- **truoc_0710**: Wikidata giảm rõ (ngàm 100% → 90,6%), Lensfun ngàm tăng nhưng chấm ít ô hơn (334 thay vì 394). Bản này dựng lại, không có log gốc để đối chiếu.

**(3) Ngàm theo cách quy tắc suy ra ngàm (`mount_source`), `lan2`, H733**

| `mount_source` | Lensfun đúng / gán | Wikidata đúng / gán |
|---|---:|---:|
| `dong_may` (luật dòng máy, chủ yếu thân) | 196/196 = 100% [100–100] | 146/146 = 100% [100–100] |
| `tieu_de` (tên ngàm trong tiêu đề) | 166/176 = 94,3% [85,9–99,4] | 110/110 = 100% [100–100] |
| `hang_slr` (hãng + DSLR) | 19/20 = 95,0% [85,0–100] | 10/10 = 100% [100–100] |
| `dong_may_nhac_toi` | 2 / 2 (dưới 10 ô, chỉ đếm) | không có ô |
| `vong_t` | không có ô | không có ô |

Chỉ 20 + 10 ô thuộc `hang_slr` (trên 298 sản phẩm dùng đường này trong toàn dữ liệu) và 2 ô `dong_may_nhac_toi` (trên 83): **các đường suy luận yếu gần như chưa được đo** (Red Team S3).

**(4) Phần tử của M có thật là thân / ống không** (`lan2`, H733)
- M có 1.570 phần tử (537 thân + 1.033 ống). Thuộc H733: 472 (204 thân + 268 ống); có đáp án loại: 470 = **29,9% của M**, 99,6% của phần M thuộc H733.
- Theo sản phẩm (đúng vai trò ở mọi nguồn có đáp án): hàng (thân) **200/202 = 99,0%** [97,4–100]; cột (ống) **267/268 = 99,6%** [98,8–100]; cả M **467/470 = 99,4%** [98,5–100].
- Theo nguồn: Lensfun 438/439 = 99,8% [99,3–100]; Wikidata 287/289 = 99,3% [98,2–100].
- 3 ô lệch: một phần tử cột (ống) đáp án là thân; một phần tử hàng đáp án là "khác"; một phần tử hàng đáp án là ống. Phân loại ở mục dưới.

**(5) Baseline, cùng cách so ngàm (quy tắc H3 cho mọi phương pháp), `lan2`, H733, Lensfun** (Wikidata trong ngoặc)

| Phương pháp | Độ phủ ngàm (gán / có đáp án) | Chính xác, mức chặt (EF ≠ EF-S) | Chính xác, mức họ |
|---|---:|---:|---:|
| Quy tắc (`ea6abb0`) | 395/400 = 98,8% (270/276 = 97,8%) | 384/395 = 97,2% [93,1–99,7] (270/270 = 100%) | 391/395 = 99,0% [97,9–99,8] (270/270) |
| B1, bản của Hải | 85/400 = 21,2% [15,6–27,1] (65/276 = 23,6%) | 64/85 = 75,3% [58,2–91,4] (50/65 = 76,9%) | 82/85 = 96,5% [91,8–100] (64/65 = 98,5%) |
| B2, Compatible Mountings | mức chặt 232/400 = 58,0%; mức họ 353/400 = 88,2% (169/276; 244/276) | 220/232 = 94,8% [91,9–97,4] (161/169 = 95,3%) | 338/353 = 95,8% [93,5–97,7] (234/244 = 95,9%) |

- B1 mức chặt thấp vì bản của Hải không tách EF / EF-S (ống EF-S bị ghi "Canon EF"). B2 mức chặt: "Canon EF" của trường này gộp EF / EF-S nên coi là không gán.
- Loại (Lensfun): quy tắc thân 196/197 chính xác, phủ 196/198; ống 284/284, 284/284. Bản của Hải thân 46/46 chính xác nhưng chỉ phủ **46/198 = 23,2%** [13,8–33,3]; ống 41/41, phủ **41/284 = 14,4%** [10,1–18,9].
- Cả 733 sản phẩm H733 đều có trong `item_map.json` của dữ liệu cũ; 90 sản phẩm có trong `linked_products.csv` của Hải.

**Tập N (H1): sản phẩm ngoài 1.493 khớp được ở `lan3`. Không độc lập, chỉ tham khảo.**
- `lan2` ngoài 1.493: 0 sản phẩm khớp (đúng kỳ vọng). `lan3`: **65 sản phẩm**, cả 65 là do bộ lọc phụ kiện `lan2` từng loại (S2 / "Manual Focus").
- Toàn N: loại Lensfun 43/54 = 79,6% [67,9–89,8], Wikidata 23/35 = 65,7% [48,6–80,6], theo sản phẩm 49/61 = 80,3% [69,4–89,7]; ngàm Lensfun 22/24, Wikidata 22/22. Bảng nhầm loại: thân → phụ kiện 12 (chưa xem từng ca).
- **Phần máy phim** (chữ "film" ở phần đầu tiêu đề): 5 sản phẩm (Nikon N80, Nikon F6, Canon AE-1, 2 bộ Canon EOS Rebel 2000). Cả 5 quy tắc xếp thân, có cờ `may_phim`; Wikidata loại 5/5, ngàm 5/5. Lensfun và openMVG không có máy phim nào. Đây chỉ là số đếm, **không phải độ chính xác nhận diện máy phim** (nguồn ngoài không ghi máy nào là máy phim). Pentax K1000 không còn bị bộ lọc loại nhưng không khớp được nguồn nào.

**Vấn đề cốt lõi, tính lại** (`core_coverage.py`, log `ai/data/survey/run_core_coverage_20261008.log`)

| Chỉ số | Bản của Hải | Bản mới |
|---|---:|---:|
| Sản phẩm xác định được ngàm (thân / ống) | 257/28.867 = 0,89% | thân + ống có 1 ngàm 1.704/27.940 = 6,10%; vào M 1.570 = 5,62% |
| Tương tác k-core chạm sản phẩm đó | 14.258/622.997 = 2,29% | vào M: 50.503/595.515 = 8,48%; có ngàm: 57.767 = 9,70% |
| Tương tác train | 11.013/482.149 = 2,28% | vào M: 40.181/460.193 = 8,73% |

**Phân loại ca sai của holdout, lần đo 3** (xem **sau** khi đã ghi số ở trên và commit `bca5f91`; chỉ để báo cáo, không sửa quy tắc hay bộ đánh giá)
- Bảng: `ai/survey/content3/n3_lan3_holdout_errors.csv` (26 ô, mỗi ô có lý do). **Người phân loại: Claude, cũng là người viết luật, nên không độc lập.** Đếm bằng `n3_lan3_errors.py --dem` (log `n3_lan3/run_holdout_errors_dem_20261008.log`); script kiểm bảng phủ đúng mọi ô sai.
- Bộ đánh giá `lan2`, H747: 26 ô sai trên 25 sản phẩm, **cả 26 đều thuộc H733** (14 mẫu dev không có ô sai nào), nên số dưới đây đúng cho cả H733 và H747.

| Ô sai | Đáp án sai | Quy tắc sai | Cả hai sai |
|---|---:|---:|---:|
| Loại, Lensfun (5) | 4 | 1 (Dimage A200: máy ống liền ra thân) | 0 |
| Loại, Wikidata (9) | 8 | 0 | 1 (Tokina 12-28 F4: đáp án "thân Nikon F4", quy tắc "phụ kiện", đúng là ống) |
| Ngàm, Lensfun (11) | 11 (7 ô Canon EF 75-300 III bị Lensfun ghi EF-S; Zeiss ZE khớp vào mục Contax/Yashica; M.Zuiko ↔ Zuiko Digital; Samyang AF 85 RF; Sony FE 35 GM ↔ 35mm G ngàm A) | 0 | 0 |
| Khung thân, openMVG (1) | 0 | 1 (Lumix DMC-S1: máy compact bị luật Lumix S bắt thành thân L-mount) | 0 |

- Cách nói đúng (thay câu "quy tắc chỉ sai ở 4 sản phẩm", Red Team T7): **trong 13 sản phẩm lệch về loại, đọc thủ công thấy 2 sản phẩm do quy tắc** (1 trong 2 ca đáp án cũng sai); thêm 1 sản phẩm sai loại chỉ lộ ra ở cột khung (DMC-S1). Mới đọc các ca **lệch** với đáp án; ca quy tắc và đáp án cùng sai giống nhau thì không thấy được.
- Phép đo (4): 3 phần tử M lệch vai trò, đọc ra 1 do quy tắc (Dimage A200 nằm trong hàng của M), 2 do đáp án (ống Nikon 70-210 bị khớp thành thân F4; bộ OM-1 + ống bị Wikidata khớp thành ống). DMC-S1 cũng là phần tử sai của M nhưng (4) không thấy vì openMVG không có đáp án loại.
- Bộ đánh giá `lan3` bỏ 10 dòng so với `lan2` (9 dòng có ô sai loại, 1 dòng openMVG không có ô chấm), trong đó có Tokina 12-28 (ca **cả hai sai**): sửa N4 (chặn "F4") làm mất luôn một ca quy tắc sai thật khỏi phép đo.

**Đã kiểm chứng / chỗ trước đây ghi sai**
- Các khoảng Wilson ở mục 08/10 (chia đôi, sửa loại) **không có script nào sinh ra** và giả định mẫu độc lập (Red Team T6): không dùng trong báo cáo; thay bằng khoảng bootstrap ở trên.
- Câu "quy tắc chỉ sai ở 4 sản phẩm" (mục "QĐ 16 …", 08/10) trộn mẫu số và do người viết luật tự phân loại (Red Team T7): không dùng nữa; thay bằng phân loại lần 3 ở trên.
- Số không còn log (Red Team phụ lục A), ghi "không còn log, không dùng trong báo cáo" ngay tại chỗ trong các mục cũ dưới đây: M sau lần sửa loại thứ nhất (538 × 1.037, 1.167 / 1.037 ống, 75.690, 2.186, 2.960); phân nhóm 84 ca sai nửa fix (68 / 16; 47 / 15 / 3 / 2 / 1); đổi loại ngoài holdout (138 / 32 / 7 / 2 / 1); dev 50 (49/50, 46/50, 43/50; 35/36, 32/36, 30/36); 53 và 36 cặp trước sửa; 801 máy compact; khoảng Wilson.
- "Lần đo hai giống hệt lần một từng ô": hai file có cùng sha256 (`run_sha256_holdout_lan1_vs_lan2_20261008.log`), nhưng bản sao "lần 1" được ghi cùng phút (01:39) với file lần 2, nên không loại trừ được việc sao chép sau lần 2. Bằng chứng còn lại là **số tổng** của hai log (`run_typefix_report.log`, `run_typefix_report_lan2.log`) trùng nhau.

**Phía sau phải làm**
- Recall của loại ống và việc nhận diện máy phim **chưa đo được trên holdout** (cách khớp ống cần tiêu cự + khẩu độ trong tiêu đề; nguồn không ghi máy phim).
- Đường suy ngàm `hang_slr`, `dong_may_nhac_toi`, `vong_t` gần như chưa có ô chấm.
- Số độc lập thật cần một tập mới chưa ai xem (Red Team S1 (d)).

---

## 08/10/2026 (tối, tiếp): sửa phần nguồn của nội dung 3 theo Red Team lần 1 (T5, T2, N1). Nhánh `nam/content4`

Theo `docs/reviews/redteam_n3_lan1.md` (T5, T2, N1 và phụ lục B). **Chưa đo lại holdout.** Bản trước khi sửa sao lưu ở `ai/data/kg_e8b39e6/` (sha256 từng file trùng `ai/data/kg/` lúc đó; hai file CSV khác git chỉ ở ký tự xuống dòng CRLF do `core.autocrlf`).

**Sửa gì**

1. **T5: áp chuẩn nguồn QĐ 4-15 cho `ai/config/mount_rules.toml` (v0.4 → v0.5).**
   - Mỗi nguồn có bản sao HTML + văn bản, sha256 của cả hai ghi trong TOML (16 nguồn). Chi tiết cách lưu ở `docs/DATA_SOURCES.md` mục 2.4.
   - Mỗi luật có danh sách căn cứ `[[rule.can_cu]]` (nguồn + câu trích nguyên văn, liền một đoạn), trường `suy_rong` (chỗ luật áp rộng hơn nguồn) và `nhan_dinh_nhom` (khẳng định không có nguồn). Bỏ trường `source` một dòng.
   - Script mới `ai/survey/content3/check_rule_sources.py`: kiểm sha256, kiểm bản sao có nội dung bài, kiểm từng câu trích; câu trích có "..." bị coi là THIẾU.
   - **Phát hiện: 6 bản sao 07/10 không dùng được.** 4 file là trang lỗi "Access Denied" (Canon Europe: EF-EOS R, EF-EOS M; Sony: bài APS-C/FF, bài ống DT), `olympus_mmf.html` là trang chặn bot "Just a moment…", `sony_la_ea.html` gần rỗng. Nay thay bằng bản Wayback thô (`id_`) và bản Nam lưu tay (Olympus).
   - **Sửa 2 câu trích không nguyên văn:**
     - Nikon DX/FX: v0.4 viết "…DX crop mode … DX lenses and FX lenses can be used interchangeably" như một đoạn, nhưng câu "interchangeably" nằm ở mục khác ("Can you use an FX lens on a DX camera body?") và đứng **trước**. Nay tách thành 3 căn cứ riêng, mỗi căn cứ ghi nó thuộc mục nào.
     - Ricoh K-1: trang ghi "DA★-, DA Limited- or DA-series", v0.4 ghi "DA-, …" (mất "★"). Đã sửa.
     - Ngoài ra trích đủ các đoạn mà v0.4 thay bằng "…" (Canon EF-EOS M, Sony DT, Sigma), và sửa câu Nikon Z f theo đúng ký tự trên trang ("[DX (24×16)]").
   - **Ghi đủ 6 chỗ suy rộng Red Team nêu** (tổng cộng nay ghi 11 chỗ): Zf → mọi thân Z FX; Sigma 17-50 → mọi ống APS-C hãng thứ ba ngàm EF; K-1 DA → ống APS-C hãng thứ ba ngàm K; danh sách thân **tương thích** EF-S dừng ở đời 2015; danh sách thân **không nhận** EF-S dừng ở 6D; LA-EA (câu nói về ống DT, áp cho mọi ống ngàm A). Thêm: FTZ II có ống không dùng được (non-AI); câu Olympus nằm trong đoạn nói về chống rung của E-P2; 3 ống DA phủ được FF; thân EF-S nhận ống EF là suy từ mốc gắn đỏ; Fuji M "a wide variety of M Mount lenses".
   - **3 khẳng định không có nguồn → "nhận định nhóm, chưa có nguồn", bỏ khỏi lý do luật.** Tìm trang hãng ngày 08/10/2026 chỉ thấy bài diễn đàn Canon Community:
     - "phần sau ống EF-S chạm gương" (`canon_efs_on_ef_body`): trang Canon chỉ nói ống EF-S có back focus ngắn hơn và "a mechanical configuration that makes it so that they cannot be mounted" lên thân không tương thích → dùng câu này làm căn cứ;
     - "DSLR Canon FF không tự cắt khung" (`canon_ef_apsc_on_ef_ff_body`, QĐ 8): lý do còn lại là câu Sigma "Not for use … as vignetting will occur";
     - "ống DX hãng thứ ba có thể phải chọn tay" (`nikon_dx_on_fx_f`): mức `crops_sensor` (M = 1) không phụ thuộc điểm này.
   - **Bổ sung cụm Sigma về máy phim:** câu trích nay đủ "Not for use on digital cameras having image sensors larger than APS-C size **or on 35mm or APS film cameras**, as vignetting will occur." Dùng làm căn cứ hãng cho QĐ 16 (luật `film_body_unknown`) với ống APS-C. Phần lý do về lấy nét / khẩu độ trên máy phim vẫn là nhận định nhóm.
   - Gộp `sony_dt` và `sony_la_ea` (cùng một URL) thành một nguồn `sony_dt`.
2. **T2: khung ống Sony không còn đoán theo mã SEL / SAL** (`mount_detect.py`, hàm mới `sony_lens_khung`; bảng mã mới `ai/config/sony_lens_codes.toml`).
   - Ví dụ: "Sony SEL85F18 85mm F/1.8" bị v0.4 xếp `apsc` (mẫu "SEL → APS-C"), nhưng đây là ống **FE** 85mm (full-frame); "Sony SAL16105 16-105mm" bị xếp `ff` (mẫu "SAL → FF"), nhưng đây là ống **DT** (APS-C).
   - Quy tắc mới, áp cho ống ngàm `sony_e` / `sony_a` có tiêu đề mở đầu bằng "Sony":
     1. chữ trong phần đầu tiêu đề: "FE" → `ff`; "DT", "E <tiêu cự>", "E PZ <tiêu cự>", "APS-C" → `apsc`. Căn cứ: trang Sony "Lens names start with FE" (full frame) / "Lens names start with E" (APS-C), và bài ống DT;
     2. không có chữ nào → tra mã trong bảng mã. Mỗi mã có trang thông số trên sony.jp (bản sao + sha256), câu trích mục 対応撮像画面サイズ ("cỡ cảm biến tương ứng"), vd SEL85F18: "●35mmフルサイズ";
     3. có mã mà mã không có trong bảng → `khong_ro`.
   - Bỏ `selp?\d{2,4}(?!g?m)` khỏi `LENS_APSC` và `sal\d` khỏi `LENS_FF`.
   - Bảng mã có **13 mã**: 12 mã của chẩn đoán T2 + **SEL30M35** (E 30mm Macro, 2 ống). Chẩn đoán T2 bỏ sót mã này vì regex cũ không bắt được "sel30m35"; `check_rule_sources.py` (mục 4) tìm ra khi kiểm mọi mã cần tra trong dữ liệu.
3. **N1: thêm 2 luật ngàm chuyển chính hãng** (`requires_adapter`, M vẫn = 0):
   - `pentax_k_on_q_adapter`: ống ngàm K trên thân PENTAX Q, nguồn thông cáo Ricoh 11/09/2012 ("a lens mount adapter that makes it possible to use PENTAX K-mount lenses on the PENTAX Q series"; chỉ lấy nét tay);
   - `leica_m_on_fuji_x_adapter`: ống Leica M trên thân Fujifilm X. **Có thêm** vì tìm được trang Fujifilm (trang sản phẩm + bảng tương thích, mọi thân X liệt kê đều ✔). Ghi là suy rộng vì trang nói "a wide variety of M Mount lenses" và có danh sách ống tương thích riêng.
4. `ai/survey/content4/html_to_text.py`: đọc bảng mã theo thẻ meta charset (trang sony.jp là Shift_JIS). Kiểm trên 12 bản sao của nội dung 4: bản cũ và bản mới cho văn bản giống hệt 12/12 (`run_c4_html_to_text_check_20261008.log`).
5. `ai/survey/redteam_n3/compare_kg_runs.py`: thêm `--expect-khung`, `--expect-rules`, `--keep-m` và các bộ kỳ vọng có tên (`--preset rt1` cho lần sửa trước, `rt1b` cho lần này, mặc định). Đã kiểm `--preset rt1` (so `kg_d339dda` với `kg_e8b39e6`): mọi số liệu giống log `run_compare_kg_20261008_rt1.log`; chỉ khác các dòng tóm tắt mới và chữ ở mục 4 (`run_compare_kg_20261008_rt1_preset_check.log`).

**Cách chạy và kiểm tra**
- `check_rule_sources.py` → `run_check_rule_sources_20261008_rt1b_lan2.log`: 16 nguồn + 13 mã OK, mọi căn cứ OK, mã thoát 0. (Lần 1 `…_lan1.log` báo DỪNG vì thiếu SEL30M35 → thêm vào bảng.)
- Chạy nháp vào `ai/data/kg_draft_rt1b/` *(đã xóa)*, so với `kg_e8b39e6`: **DỪNG**, vì có 5 ống Sony đổi khung ngoài 12 ống của chẩn đoán T2 (xem bảng dưới). Nam xem và **duyệt nhận cả 17 ống** (cách 1).
- Chạy thật vào `ai/data/kg/` (log `ai/data/kg/run03_mount_compat_20261008_rt1b_lan1.log`), chạy lần 2 vào `ai/data/kg_draft_rt1b_lan2_final/` (log `ai/data/survey/run03_mount_compat_20261008_rt1b_lan2.log`): sha256 cả 8 file trùng nhau và trùng hai lần chạy nháp (`run_sha256_kg_20261008_rt1b.log`). Các thư mục nháp giữ nguyên *(đã xóa 08/10 khuya theo yêu cầu của Nam; log sha256 vẫn còn)*.
- So sánh cuối: `run_compare_kg_20261008_rt1b.log` (`--preset rt1b`): **0 sản phẩm đổi ngoài dự kiến, 0 cặp đổi mức ngoài dự kiến, 0 ô M đổi**.

**Ảnh hưởng: M** (`compare_kg_runs.py`, log `run_compare_kg_20261008_rt1b.log`; mức tính trên ống vào M)

| Chỉ số | Trước (`kg_e8b39e6`) | Sau (`kg`) |
|---|---:|---:|
| Kích thước M | 537 × 1.033 | 537 × 1.033 |
| Cặp M = 1 | 72.720 | **72.720** (file `.npz` giống hệt từng byte) |
| … cờ "chưa rõ có cắt khung" | 1.892 | 1.686 |
| Cặp "không biết" | 5.846 | 5.846 |
| `compatible_with` / `crops_sensor` | 70.542 / 2.178 | 70.472 / 2.248 |
| `requires_adapter` | 16.033 | 16.301 (+152 Pentax Q, +116 Fuji X + Leica M) |
| `incompatible` | 460.122 | 459.854 |
| Ống "không chắc": `requires_adapter` | 2.362 | 2.419 (+28 Pentax Q, +29 Fuji) |
| Cặp đổi giữa `compatible_with` và `crops_sensor` | – | 106 |
| Cặp đổi cờ `crop_unknown` | – | 206 |

**17 ống Sony đổi khung** (loại, ngàm, cờ phim, "không chắc" giữ nguyên):

| Nhóm | ASIN | Ống | Trước → sau | Căn cứ |
|---|---|---|---|---|
| Chẩn đoán T2: sai hẳn | B077VYV7PH | SEL85F18 (FE 85mm) | apsc → **ff** | bảng mã (sony.jp) |
| | B000VUIXOE | SAL16105 (DT 16-105) | ff → **apsc** | bảng mã |
| | B00836H3Z8 | SAL18135 (DT 18-135) | ff → **apsc** | bảng mã |
| Chẩn đoán T2: mất thông tin | B000VUFDPG | SAL18250 "Alpha DT 18-250mm" | khong_ro → apsc | chữ DT |
| | B00FYOF61K, B06X9CV5VK, B00ZY8CII0, B0CFX2LJCB, B00U29GN6O, B0199BF87K, B078GGJLCD, B0B49YVGCH | 8 ống có cả mã SEL lẫn chữ "FE" | khong_ro → ff | chữ FE |
| **Ngoài chẩn đoán T2** (Nam duyệt) | B0054I54JU, B006GPZ28I | SEL30M35 (E 30mm Macro) | khong_ro → apsc | bảng mã (regex cũ không bắt được mã này nên T2 bỏ sót) |
| | B005IHAI8O | "Sony Carl ZEISS Sonnar T E 24mm F1.8 ZA" | **ff → apsc** | chữ "E 24mm". v0.4 sai: mẫu chung "zeiss … sonnar" ép thành FF |
| | B00EZK12TY | "Sony E PZ 18-105mm f/4 G OSS" | khong_ro → apsc | chữ "E PZ 18-105mm" (mẫu chung chỉ bắt "sony e <số>") |
| | B000JE5CKA | "Sony 16-80mm … Carl Zeiss Vario-Sonnar T DT" | khong_ro → apsc | chữ DT (v0.4 mâu thuẫn giữa "dt" và "zeiss … sonnar") |

- Vì sao 106 cặp (chẩn đoán T2 ước 30): 18 (SEL85F18 trên 18 thân E FF: `crops_sensor` → `compatible_with`) + 8 (2 ống DT trên 4 thân A FF: ngược lại) + 4 (SAL18250) = **30 như chẩn đoán**; thêm 54 (SEL30M35 ×2 và E PZ 18-105 trên 18 thân E FF: `compatible_with` + cờ → `crops_sensor`) + 18 (Zeiss E 24: `compatible_with` → `crops_sensor`) + 4 (DT 16-80) = 76.
- Vì sao 206 cặp đổi cờ (chẩn đoán ước 144): 144 (8 ống FE × 18 thân E FF: bỏ cờ, vẫn `compatible_with`) + 54 + 8 (SAL18250 và DT 16-80 trên 4 thân A FF).
- 485 cặp trên thân APS-C chỉ đổi tên luật (`same_mount_body_apsc_lens_unknown_khung` → `same_mount_lens_covers_body`), mức vẫn `compatible_with`.
- 66 ống Sony khác chỉ đổi chữ `evidence` (vd `khung: dt` → `khung: sony chữ: dt`, `khung: sel1855` → `khung: sony mã: SEL1855`).

**Đã kiểm chứng đúng**
- Khung 12 ống của bảng T2 (phụ lục B, cột "khung thật") khớp trang thông số Sony: 7 mã trước đây "theo hiểu biết, chưa đối chiếu nguồn" (SAL70200G/70300G/70400G, SEL16F28, SEL18200, SEL1855, SELP1650) nay đã có trang Sony xác nhận.
- Kiểm câu trích nội dung 4 (`count_usecase.py`, log `run_c4_usecase_count_20261008_rt1b.log`): mục 1–2 (bản sao + câu trích) **giống hệt** log cũ; cả 4 luật OK.

**Ảnh hưởng tới phía sau, phải chạy lại hoặc sửa theo**
- **Holdout chưa đo lại.** Khung ống không có trong đáp án ngoài (hạn chế 4), nên lần sửa này không đổi số holdout về loại / ngàm / khung thân; chưa chạy để xác nhận.
- Số nhãn mục đích (nội dung 4) đổi vì `kg/` đổi (so với log cũ tính trên `kg` trước `e8b39e6`): 1.285 → 1.287 ống đọc được tiêu cự + khẩu độ; phong cảnh 556 → 559, thể thao/chim 285 → 287, chân dung 144, macro 86, không nhãn 311 → 309; ống không rõ khổ 366 → 354. `ai/data/survey/usecase_labels_draft.csv` bị ghi đè; bản trước sao lưu ở `usecase_labels_draft_e8b39e6.csv`. STATUS (nội dung 4, hạn chế 7) và `content4_design.md` còn số cũ.
- Thấy thêm khi đọc bảng nhãn (chưa sửa, thuộc việc 2 của nội dung 4): "SEL85F18 85mm **F/1.8-22**" không được nhãn chân dung vì bước đọc khẩu độ lấy "1.8-22" thành khoảng khẩu độ (ap1 = 1,8, ap2 = 22; 22 thực ra là khẩu độ nhỏ nhất), nên `ap_tele` = 22 > 2,8 (đã xem trong `usecase_labels_draft.csv`). "SEL28F20 FE 28mm f/2-22" cũng bị đọc như vậy. Chưa đếm có bao nhiêu ống bị.
- Câu trích của `usecase_rules.toml` vẫn dùng "..." ở 3 chỗ (Canon US lens guide, Canon EU landscape, Canon EU beginner); chuẩn mới của nội dung 3 không cho phép. Chưa sửa.

---

## 08/10/2026 (tối): sửa lỗi logic nội dung 3 theo Red Team lần 1 (phần code). Nhánh `nam/content4`

Theo `docs/reviews/redteam_n3_lan1.md` (bản phản biện và hai phụ lục chẩn đoán A, B). Lần này **chỉ sửa code**: chưa sửa nguồn, chưa sửa bảng luật Sony SEL/SAL (T2), chưa thêm ngàm chuyển (N1), **chưa đo lại holdout**.

> **Lưu ý về độ độc lập của holdout.** Một số sửa xuất phát từ ca sai **đã thấy ở holdout**: B00L2PN5L8 (ống EF-S 55-250 ra thân) là 1 trong 4 ca "quy tắc sai" của holdout (hạn chế 6e trong STATUS), và Red Team dùng chính ca này làm bằng chứng cho T1. Pentax K1000 được ghi là "lỗi đã biết, không sửa để giữ số holdout" (hạn chế 6f), K1000 thì không nằm trong tập chấm. Vì vậy nếu đo lại holdout sau lần sửa này, số đo **không còn độc lập** với các ca đó. Số holdout chính thức vẫn là lần đo thứ hai (trước lần sửa này).

**Sửa gì**

1. **T1: luật dòng máy chỉ đọc chủ thể tiêu đề** (`mount_detect.py`, hàm `body_series`).
   - Ví dụ: "Canon EF-S 55-250mm … **for Canon EOS 7D, 60D, Rebel T3i**…" (B00L2PN5L8). Trước đây `body_series` đọc cả phần "for …", thấy "7D" nên tưởng đây là thân máy → xếp `than`. Nay chỉ đọc phần trước "for / with / + / &…" (hàm `subject()` có sẵn), nên ra `ong`.
   - Luật phim EOS (`[phim] EOS`) **bỏ mẫu `eos … film|35mm`**, chỉ còn tên máy phim cụ thể (EOS-1V, Elan, Rebel G/GII/K2/Ti/2000/X). Mẫu cũ có thể bắt nhầm bộ kit kiểu "EOS Rebel T7 + 35mm f/1.8" thành máy phim. Trong dữ liệu hiện tại mẫu này không gây ca sai nào; bỏ đi chỉ đổi chữ `evidence` của 9 sản phẩm (vd `eos rebel 2000 35mm` → `rebel 2000`).
2. **Pentax K1000 bị xếp `khac` vì chữ "manual"** (`ACC_BODY`).
   - "Pentax K1000 **Manual** Focus SLR Film Camera" (B001AO4JRK): "manual" ở đây là "lấy nét tay", không phải sách hướng dẫn. Trước đây chữ "manual" đứng một mình đủ để coi chủ thể là phụ kiện.
   - Nay chỉ các cụm chỉ sách hướng dẫn mới tính: "instruction / user / owner('s) / operating / operation / service / repair / reference manual(s)".
3. **T4: sửa QĐ 16 — luật thân phim không còn áp cho cặp chắc chắn không lắp được.**
   - Ví dụ: thân phim Nikon N70 (ngàm F) + ống Canon EF 28-80mm. Bản đầu của QĐ 16 xếp cặp này "không biết". Nhưng khác ngàm thì máy phim hay máy số đều không lắp được, nên nay giữ `incompatible`.
   - Quy tắc mới: luật `film_body_unknown` chỉ đổi thành "không biết" những cặp mà **luật thường** (coi thân như máy số) cho M = 1 (`compatible_with`, `crops_sensor`) hoặc `requires_adapter`. Cặp luật thường cho `incompatible` giữ `incompatible`. Cặp luật thường cho `unknown` vẫn `unknown` (do luật thường đó).
   - Cách cài: trường mới `when_regular_level` trong `mount_rules.toml` (v0.4), lớp `Rules` trong `03_mount_compat.py` tính mức theo luật thường rồi mới quyết định có áp luật phim không. Cập nhật lý do trong `note` của luật.
4. **N2: hãng thứ ba = mọi hãng không thuộc danh sách chính hãng** (`mount_detect.py`, thay `THIRD_PARTY` bằng `FIRST_PARTY` + `is_third_party`).
   - Ví dụ: Brightin Star 50mm F1.4 (B0BQ6WX3V5) có 9 asin con, nhưng tên hãng không có trong danh sách hãng thứ ba liệt kê tay, nên trước đây không bị đánh dấu "không chắc" (QĐ 4).
   - Nay xét phần **đầu tiêu đề**: mở đầu bằng hãng chính hãng (Canon, Nikon/Nikkor/AF-S/AF-P, Sony, Fujifilm/Fuji/Fujinon, Olympus/OM System, Panasonic/Lumix, Leica, Pentax/HD Pentax/smc Pentax/Ricoh, Samsung, Minolta, Hasselblad) thì là chính hãng; còn lại (kể cả tiêu đề không mở đầu bằng tên hãng) là hãng thứ ba. **Sigma và Zeiss cố ý không tính là chính hãng** vì bán cùng một ống cho nhiều ngàm. Danh sách và lý do ghi trong code.
   - Trước khi sửa đã kiểm: trong 204 ống 1 ngàm có > 1 asin con, không ống nào đang "không chắc" có chữ đầu thuộc danh sách chính hãng, nên sửa này chỉ có thể thêm ống "không chắc", không bớt.
5. **N3: `COMPACT_LINE` không chặn FinePix S1–S5 Pro** (DSLR ngàm Nikon F). Chỉ bỏ chặn đúng mẫu "finepix s[1-5] pro"; các FinePix khác vẫn bị coi là máy ống liền. Hiện không đổi sản phẩm nào (2 thân S2 Pro, S5 Pro đã ra `than/nikon_f` nhờ nhánh danh mục).
6. `CLAUDE.md`: thêm quy tắc log không ghi đè (mỗi lần chạy một tên log mới, kèm ngày hoặc nhãn lần chạy). Lý do: phụ lục A của Red Team thấy `run_eval_external.log` và `kg/mount_compat_log.txt` đã bị lần chạy sau ghi đè, mất bằng chứng cho số cũ.
7. Script mới `ai/survey/redteam_n3/compare_kg_runs.py`: so hai thư mục đầu ra của script 03 (M, số cặp theo mức / luật, sản phẩm đổi thuộc tính, cặp đổi mức) và tự báo "DỪNG" nếu có thay đổi ngoài nhóm dự kiến.

**Cách chạy và kiểm tra**
- Sao lưu `ai/data/kg/` sang `ai/data/kg_d339dda/` (sha256 từng file trùng bản gốc; không lên git).
- Chạy thử vào thư mục nháp, so với bản cũ: không có thay đổi ngoài nhóm dự kiến → mới chạy thật vào `ai/data/kg/` (log `ai/data/kg/run03_mount_compat_20261008_rt1_lan1.log`).
- Chạy lần 2 vào thư mục nháp (log `ai/data/survey/run03_mount_compat_20261008_rt1_lan2.log`): sha256 của cả 8 file đầu ra trùng lần 1 (`ai/data/survey/run_sha256_kg_20261008_rt1.log`).
- So sánh trước/sau: `ai/data/survey/run_compare_kg_20261008_rt1.log` — **0 sản phẩm đổi ngoài dự kiến, 0 cặp đổi mức ngoài dự kiến**.

**Ảnh hưởng: M** (`compare_kg_runs.py`, log `run_compare_kg_20261008_rt1.log`)

| Chỉ số | Trước (`kg_d339dda`) | Sau (`kg`) |
|---|---:|---:|
| Số sản phẩm theo loại thân / ống / khác / phụ kiện | 544 / 1.337 / 1.758 / 24.301 | 543 / 1.339 / 1.757 / 24.301 |
| Thân 1 ngàm / trong đó máy phim | 538 / 17 | 537 / **18** (thêm K1000) |
| Ống 1 ngàm / "không chắc" / vào M | 1.166 / 130 / 1.036 | 1.167 / **134** / 1.033 |
| Kích thước M | 538 × 1.036 = 557.368 | 537 × 1.033 = 554.721 |
| Cặp M = 1 | 73.050 | **72.720** |
| … cờ "chưa rõ có cắt khung" | 1.892 | 1.892 |
| Cặp "không biết" | 19.932 | **5.846** |
| … trong đó luật `film_body_unknown` | 17.612 | 2.819 |
| `compatible_with` / `crops_sensor` | 70.854 / 2.196 | 70.542 / 2.178 |
| `requires_adapter` | 16.005 | 16.033 |
| `incompatible` | 448.381 | 460.122 |

Các mức ở bảng trên chỉ tính ống vào M; số của ống "không chắc" có trong log.

**Sản phẩm đổi** (đúng các nhóm dự kiến):

| ASIN | Tiêu đề (rút gọn) | Trước | Sau | Do sửa |
|---|---|---|---|---|
| B00L2PN5L8 | Canon EF-S 55-250mm … for Canon EOS 7D, 60D… | `than/canon_efs` | `ong/canon_efs/apsc` | T1 (ca sai của holdout) |
| B00GX6K1X6 | SainSonic 25mm F/1.4 C Mount CCTV Lens for Pentax Q | `than/pentax_q` | `ong/nhieu` (ra khỏi M) | T1 |
| B001AO4JRK | Pentax K1000 Manual Focus SLR Film Camera | `khac` | `than/pentax_k/ff`, máy phim | "manual" |
| B0BQ6WX3V5 | Brightin Star 50mm F1.4 … for Canon EOS-M (9 asin con) | vào M | "không chắc" | N2 |
| B0BP64H129 | Brightin Star 23mm F5.6 … for Nikon Z (7 asin con) | vào M | "không chắc" | N2 |
| B09P4QQTRG | AstrHori 50mm F1.4 … Sony E-Mount (2 asin con) | vào M | "không chắc" | N2 |
| B0857XT4GW | SIRUI 50mm F1.8 Anamorphic … E Mount (2 asin con) | vào M | "không chắc" | N2 |

Ngoài ra 9 sản phẩm chỉ đổi chữ `evidence` (do bỏ mẫu phim EOS), loại / ngàm / khung / cờ phim giữ nguyên.

**Giải thích số "không biết" 19.932 → 5.846** (ví dụ trước, cộng sau):
- Ví dụ: Nikon N70 + Canon EF 28-80mm: trước "không biết", nay `incompatible`. Có **14.123** cặp như vậy (thân phim × ống khác ngàm, hoặc ống EF-S trên thân EF phim), đúng bằng số chẩn đoán T4. Trong đó 14.055 cặp vẫn thuộc M; 68 cặp là của 4 ống N2 (17 thân phim × 4), nay ra khỏi M.
- 708 cặp cùng ngàm mà luật thường đã cho "không biết" (ống APS-C hãng thứ ba trên thân Canon FF phim, QĐ 8: 704; luật `same_mount_other`: 4) vẫn "không biết", chỉ đổi tên luật.
- K1000 thêm **38** cặp "không biết" (máy phim × ống Pentax K).
- 1 cặp "không biết" (`same_mount_other`) của ống Brightin Star 23mm ra khỏi M vì ống thành "không chắc".
- 19.932 − 14.123 + 38 − 1 = **5.846**.

**Ảnh hưởng tới phía sau, phải chạy lại hoặc sửa theo**
- **Holdout chưa đo lại** (Nam dặn). Nếu đo lại, phải ghi B00L2PN5L8 là ca đã sửa theo holdout. FinePix S2 Pro, S5 Pro cũng nằm trong holdout nhưng không đổi.
- Các số trong STATUS / CHANGELOG / `content4_design.md` tính trên M cũ (73.050, 19.932, 17 thân phim, 1.036 ống, `compatible_with` 70.854, `requires_adapter` 16.005…) đã cũ. Script khảo sát nội dung 4 (`count_usecase.py`, `survey_kg_counts.py`…) đọc `ai/data/kg/` nên cần chạy lại (log tên mới).
- Script chẩn đoán `ai/survey/redteam_n3/n2_n3_thirdparty_finepix.py` dùng `THIRD_PARTY` (đã bỏ) nên không chạy được với code mới; các script T1–T4 so với `item_attributes.csv` cũ. Muốn chạy lại thì checkout commit `ed5280d`.

---

## 08/10/2026 (tiếp): QĐ 16 thân máy phim; sửa 2 lỗi gán ngàm; đo holdout lần hai; phân loại ca sai của holdout. Nhánh `nam/content3`

Làm theo thứ tự Nam giao: (1) máy phim, (2) sửa 2 lỗi ngàm, (3) chốt quy tắc và đo holdout lần hai, (4) mới xem ca sai của holdout, **không sửa quy tắc nữa**.

**Sửa gì**
1. **QĐ 16: mọi cặp (thân máy phim, ống) xếp "không biết".** Các cặp này bị loại khỏi M và CVR nhưng vẫn giữ trong đồ thị.
   - `mount_detect.py`:
     - ghi chú của các luật dòng máy phim nay bắt đầu bằng nhãn `[phim]` (EOS phim, Canon FD, Nikon F phim, Minolta, Leica M phim, Spotmatic, Pentax K phim);
     - thân có cờ `may_phim = True` nếu khớp luật có nhãn này, hoặc chủ thể tiêu đề có chữ "film".
   - `03_mount_compat.py`:
     - `item_attributes.csv` thêm cột `may_phim`;
     - bộ áp luật nhận điều kiện mới `body_film`.
   - `ai/config/mount_rules.toml` (v0.3):
     - thêm luật `film_body_unknown` (`body_film = true`, mọi ngàm, mọi khung → `unknown`), đặt đầu tiên;
     - kèm lý do: máy phim không có chế độ cắt khung; nhiều ống đời mới không lấy nét hoặc không chỉnh được khẩu độ trên máy phim.
   - Đúng như Nam giao, luật áp cho **mọi** cặp, kể cả cặp khác ngàm (vd thân Nikon phim + ống Canon). Các cặp này trước là `incompatible`, nay là `unknown`.
2. **Sửa 2 lỗi gán ngàm thấy ngoài holdout** (`mount_detect.py`, nhánh ống):
   - **Bỏ phần combo nói về ngàm chuyển** (`drop_adapter_bundle`):
     - Sau dấu nối "&", "+", "with" hay "w/", đoạn nào có adapter / converter / MC-xx và nhắc ngàm thì bị bỏ trước khi tìm ngàm. Không bỏ nếu đoạn đó là ngàm T hay teleconverter.
     - Ví dụ "Sigma 150-600mm … (for Canon EOS) & MC-11 Mount Converter … for Sony FE & E-Mount": trước gán `sony_e`, nay `khong_ro`. Tiêu đề chỉ ghi "Canon EOS", không nói rõ EF hay RF, nên ống rời khỏi M.
   - **Cài QĐ 9 cho ống ngàm T** (nguồn ngàm `vong_t`):
     - Ngàm lấy theo vòng T đi kèm: tên ngàm khác trong tiêu đề, dòng máy được nhắc, hoặc hãng + DSLR.
     - Có vòng/adapter mà không biết cho máy nào → `khong_ro`. Không nói gì đến vòng → giữ `t_mount`.
   - Ngoài holdout chỉ 5 ống đổi ngàm, Claude đã xem cả 5:

     | ASIN | Tiêu đề (rút gọn) | Trước | Sau |
     |---|---|---|---|
     | B08GQ2VHQ6 | Lightdow 420-800mm … + T Mount Ring for Nikon D3500… | `t_mount` | `nikon_f` |
     | B07NPP2X4N | Lightdow 420-800mm … + T-Mount for Nikon D5500… | `t_mount` | `nikon_f` |
     | B07MW118KD | JINTU 420-800mm … + T-Mount for Canon EOS Rebel… | `t_mount` | `canon_ef` |
     | B00GB3PDIE | Opteka 650-2600mm … T-Mount Adapter … for Canon DSLR Cameras | `t_mount` | `canon_ef` |
     | B078S8GL8Y | Sigma 150-600mm (for Canon EOS) & MC-11 … | `sony_e` | `khong_ro` |
3. `eval_split_report.py` thêm cờ `--holdout-errors`. Cờ này được thêm **sau** lần đo holdout thứ hai, chỉ để phân loại ca sai cho báo cáo.

**Ảnh hưởng: M** (`ai/data/kg/mount_compat_log.txt`, nay bản sao ở `ai/data/kg_d339dda/mount_compat_log.txt`). Cột "Sau sửa loại (lần 1)": **không còn log, không dùng trong báo cáo** (log bị lần chạy QĐ 16 ghi đè).

| Chỉ số | Sau sửa loại (lần 1) | Sau QĐ 16 + sửa ngàm |
|---|---:|---:|
| Thân có 1 ngàm / trong đó máy phim | 538 / 17 | 538 / 17 |
| Ống có 1 ngàm / vào M | 1.167 / 1.037 | 1.166 / 1.036 |
| Ống `t_mount` | 5 | 1 |
| Kích thước M | 538 × 1.037 | 538 × 1.036 |
| Cặp M = 1 | 75.690 | **73.050** |
| … cờ "chưa rõ có cắt khung" | 2.186 | 1.892 |
| Cặp "không biết" | 2.960 | **19.932** (trong đó 17.612 = 17 thân phim × 1.036 ống, luật `film_body_unknown`) |

**Ảnh hưởng: độ chính xác.** Lần đo holdout thứ hai, log `ai/data/survey/run_typefix_report_lan2.log`.
- Kết quả **giống hệt lần một** ở cả hai nửa. File `eval_external_matches.csv` của hai lần giống nhau từng ô (bản lần một lưu ở `ai/data/survey/before_typefix/eval_external_matches_lan1.csv`). *(Kiểm lại 08/10 khuya: hai file cùng sha256, nhưng bản lần một được ghi cùng phút 01:39 với file lần hai nên không chứng minh được "trùng từng ô"; số tổng của hai log trùng nhau.)*
- Lý do: thay đổi lần này không chạm vào loại; 5 ống đổi ngàm và 17 thân phim không làm đổi ô chấm nào.
- Holdout: loại 565/571 = 98,9% (Lensfun), 305/315 = 96,8% (Wikidata), theo sản phẩm 598/612 = 97,7%. Ngàm Lensfun 391/402 = 97,3%, Wikidata 266/266. Khung thân 204/204 (Lensfun), 132/133 (openMVG).

**Phân loại ca sai của holdout** (xem SAU khi chốt; `eval_split_report.py --holdout --holdout-errors`, log `ai/data/survey/run_holdout_errors.log`; Claude đọc từng ca, không phải người chấm độc lập)

*Loại: 14 sản phẩm sai.*
- **11 ca đáp án sai, quy tắc đúng.** Bước khớp tên bắt nhầm:
  - phụ kiện: ốp silicon TG-3, ốp Nikon 1 AW1, kính dán Galaxy S8, cốc mắt ngắm Nikon D7000, cốc mắt ngắm Lumix G9, sách "Canon EOS Rebel T6s Expanded Guides";
  - máy quay: Canon XH A1 bị khớp thành máy phim A-1, Canon VIXIA HF R50 thành EOS R50;
  - ống: Nikon 70-210mm f/4 thành thân Nikon F4, Helios 44-2 "for Nikon" thành thân Nikon F2;
  - bộ máy: OM System OM-1 + 12-40mm, Wikidata ghi là ống, thực tế là bộ máy + ống. Quy tắc xếp thân là đúng.
- **2 ca quy tắc sai:**
  - B000683VIY "Konica Minolta Dimage A200 … Digital Camera" (máy ống liền) → quy tắc ra thân `sony_a`, vì luật dòng máy Sony A bắt "A200".
  - B00L2PN5L8 "Canon EF-S 55-250mm … for Canon EOS 7D, 60D…" nằm trong danh mục thân → quy tắc ra thân, vì luật cũ của nhánh danh mục thân thấy dòng máy 7D.
  - Cả 2 ca đều đã sai từ trước lần sửa này.
- **1 ca cả hai cùng sai:** B09J21XNFS "Tokina at-X PRO 12-28 F4 DX Lens for Nikon". Đáp án ghi "thân Nikon F4"; quy tắc ra "phụ kiện" vì tiêu đề không có chữ "mm" nên không nhận ra tiêu cự. Đúng phải là ống.

*Ngàm: 11 ô sai (đều Lensfun), cả 11 là đáp án sai.*
- 7 ô: Canon EF 75-300mm III. Lensfun ghi `EF-S` theo máy dùng để hiệu chỉnh; đây là lỗi đã biết của Lensfun (hạn chế 3 trong STATUS).
- Zeiss 21mm Distagon **ZE** (bản ngàm Canon EF): Lensfun ghi ngàm mà bước ánh xạ không đổi được sang mã của nhóm (`khac_ngam`).
- Olympus **M.Zuiko** 40-150mm (MFT) bị khớp với Zuiko Digital 40-150mm (Four Thirds) vì cùng tiêu cự và khẩu độ.
- Samyang AF 85mm F1.4 **RF Mount**: Lensfun chỉ có bản ngàm E.
- Sony **FE** 35mm F1.4 GM bị khớp với Sony 35mm f/1.4 G (ngàm A).

*Khung thân: 1 ô sai, quy tắc sai.*
- B005HTHX22 "Panasonic Lumix DMC-S1 … Digital Camera" là máy compact. Luật dòng máy Lumix S (L-mount) bắt "S1" nên quy tắc ra thân `l_mount`, ff. Đây thực chất là lỗi **loại**, nhưng openMVG không có đáp án loại nên chỉ lộ ra ở cột khung.

**Tóm lại** *(câu này nói quá, trộn mẫu số; không dùng trong báo cáo — Red Team T7; thay bằng phân loại lần đo 3, mục 08/10 khuya)*: trên holdout, sau khi đọc từng ca sai, quy tắc sai ở **4 sản phẩm**: 3 sai loại (Dimage A200, EF-S 55-250, Tokina 12-28) + 1 lộ ra ở cột khung (DMC-S1). Mọi ca sai ngàm còn lại là do đáp án.
- Mới đọc các ca **lệch** với đáp án. Các ca quy tắc và đáp án cùng sai giống nhau thì không phát hiện được.

**Lỗi quy tắc đã biết, KHÔNG sửa** (theo yêu cầu của Nam, để giữ số holdout)
- 4 ca trên.
- "Pentax K1000 Manual Focus SLR Film Camera" (ngoài holdout) vẫn là "khác", vì từ "manual" nằm trong danh sách từ phụ kiện (để bắt sách hướng dẫn). Phát hiện khi kiểm cờ máy phim, sau khi Nam đã giới hạn phạm vi sửa.

---

## 08/10/2026: Sửa lỗi phân loại thân / ống / phụ kiện (`mount_detect.py`), chấm holdout một lần. Nhánh `nam/content3`

**Cách làm (giữ số đo độc lập, QĐ 13)**
- Chỉ xem ca sai của nửa **fix** (`eval_split_report.py --errors`, chỉ in nửa fix). Ngoài ra chỉ xem các sản phẩm **không** nằm trong holdout (lọc theo `eval_split.csv` trước khi in).
- Log tổng của `eval_external.py` có lẫn số của holdout nên trong lúc sửa chỉ ghi ra file nháp, không đọc.
- Chốt quy tắc xong mới chạy lại pipeline vào `ai/data/kg/` và chấm holdout **một lần**.
- Bước khớp tên của phía đánh giá **không sửa**. `eval_external.py` chỉ thêm tham số `--ours / --out-csv / --out-json` để chạy vào thư mục nháp.

**Ca sai loại của nửa fix trước khi sửa: 84 sản phẩm** (có log `run_fix_errors_before.log`), chia 2 nhóm. Phân nhóm do Claude đọc tay; các số 68 / 16 / 47 / 15 / 3 / 2 / 1 dưới đây *(không còn log, không dùng trong báo cáo)*:
- **68 ca quy tắc sai thật**, do quy tắc tin danh mục Amazon:
  - 47 ống bán kèm combo bị xếp phụ kiện. Amazon xếp chúng vào "Accessory Kits", "Accessory Bundles", "Filter Sets", thậm chí "Tablets" hay "Microscope Accessories". Ví dụ: "Canon EF 50mm f/1.8 STM Lens with 3pc Filter Kit…", "Fujinon XF33mmF1.4 R LM WR" (danh mục Tablets).
  - 15 thân thành "khác": 11 thân bị xếp "Point & Shoot" (Olympus E-P1, Lumix G3, Sony a6000…), 1 thân trong "Instant Cameras" (Nikon D5500), 3 máy phim SLR (Canon EOS Rebel 2000, Nikon F100, Canon AE-1 Program).
  - 3 thân thành phụ kiện: Leica M8 (thiếu luật dòng máy), Olympus E-5 nằm trong danh mục ống, Sony a7 III bán kèm combo.
  - 2 thân bán kèm ống nằm trong danh mục ống thành "ống": Sony a5100 + 16-50mm, Fujifilm X-T30 + XF18-55mm.
  - 1 máy ống liền thành thân: Fujifilm X-S1 bị luật dòng máy Fuji X bắt nhầm.
- **16 ca đáp án sai**, quy tắc đúng. Bước khớp tên bắt nhầm phụ kiện có nhắc tên máy:
  - pin LP-E6 "Canon EOS 60D EOS 7D EOS 5D Mark II", dây bấm mềm, chân máy, ốp, cốc mắt ngắm A6500, DC coupler Lumix;
  - sách "Introduction To Canon EOS 70D", ống chuyển đổi gắn ren "0.42x … for Canon Rebel SL1";
  - bộ cốc hình ống kính "LenZcup EF Shotglass", vỏ chống nước RX100, ống phụ gắn ngoài ZV-1…

**Sửa gì** (`ai/pipeline/mount_detect.py`)
1. **Loại xét theo tiêu đề trước, danh mục chỉ là dự phòng.** "Chủ thể" là phần tiêu đề trước *for / fits / compatible / with / w/ / + / & / bundle / includes…*. Khác `head()` cũ ở chỗ giữ "(" và " - ".
   - **Thân theo tiêu đề** (`title_body`, áp cho mọi danh mục trừ bảo hành): chủ thể (cắt thêm ở dấu phẩy) phải có đủ:
     - một luật dòng máy;
     - một từ chỉ máy ảnh: camera (trừ "camera lens"), body, DSLR, SLR, mirrorless, rangefinder, DSLM, interchangeable, "xx MP"; hoặc "kit" kèm tiêu cự;
     - không có từ phụ kiện (ACC_WORDS, LENS_NEG, danh sách mới `ACC_BODY`: accessory, replacement, eyepiece, housing, coupler, introduction, guide, book, monopod, shutter release, starter kit, software, upgrade…);
     - không thuộc dòng máy compact (Cyber-shot, PowerShot, Coolpix, FinePix, Lumix FZ/ZS/LX…);
     - không có tiêu cự + khẩu độ đứng trước dòng máy.
   - **Ống theo tiêu đề** (`title_lens`, chỉ áp cho danh mục "khác"; danh mục ống / thân / máy ống liền vẫn dùng luật cũ):
     - chủ thể có tiêu cự + khẩu độ;
     - không có từ phụ kiện: hood, cap, filter… và danh sách mới `LENS_NEG_TITLE` (cover, foot, plate, tripod ring, quick release, *scope, adapt*, 1.4x/2x, replica, shotglass, MP, "digital camera"…);
     - không thuộc dòng máy compact.
2. **Luật dòng máy** (`BODY_SERIES`):
   - thêm máy phim Canon FD (AE-1, AE-1 Program, A-1, AT-1, AV-1, AL-1, FTb, T50/T70/T90, F-1) → `canon_fd`, ff;
   - thêm máy phim Pentax ngàm K (K1000, ME Super, MX, Program A/Plus, ZX-/MZ-/PZ-) → `pentax_k`, ff;
   - thêm Spotmatic → `m42`, ff;
   - thêm máy phim Minolta Maxxum/Dynax → `sony_a`, ff;
   - thêm Leica M8 → `leica_m`, khung `khac` (APS-H, crop 1,33); Leica M2–M7 phim → `leica_m`, ff;
   - "Rebel GII" thêm vào luật máy phim EOS;
   - luật Fuji X không bắt X-S1 (máy ống liền), chỉ bắt X-S10/X-S20;
   - luật Samsung NX không bắt "NX 60mm", "NX 18-55mm" (đó là tên ống). Nếu không sửa, luật thân theo tiêu đề sẽ biến 10 ống Samsung NX thành thân;
   - Olympus OM-1/OM-5: thêm "35mm" vào điều kiện loại máy phim ngàm OM.
3. Ngàm, khung, bảng luật tương thích (`mount_rules.toml`) và `03_mount_compat.py`: **không đổi**.

**Kiểm tra phụ trước khi chốt** (không dùng holdout)
- Đổi loại trên các sản phẩm **ngoài holdout** (so `item_attributes.csv` trước/sau, script nháp): phụ kiện → ống 138, khác → thân 32, phụ kiện → thân 7, ống → thân 2, thân → khác 1 (X-S1). *(không còn log, không dùng trong báo cáo)* Claude đọc hết từng tiêu đề.
  - 2 lượt sửa đầu còn sai: 10 ống Samsung NX, "Canon Digital Rebel Kit with Case…", "Nikon D3000-D5000 DSLR Starter Kit", "Water Resistant Kit CVR-XT2", phần mềm "V-Log L Upgrade", vòng chân máy, đế tháo nhanh, áo trùm ống, ống ngắm phụ (guidescope), teleconverter 1.4X. Đã chặn hết bằng các luật ở mục 2 và danh sách từ phụ kiện.
  - Bản chốt: Claude xem lại hết, không thấy ca đổi sai.
- Mẫu dev 50 (`label_dev_50_claude.csv`), chỉ tính 36 mẫu **không** thuộc holdout (14 mẫu dev nằm trong holdout): trước = sau = loại 35/36, ngàm 32/36, khung 30/36. *(không còn log, không dùng trong báo cáo)*

**Ảnh hưởng: độ chính xác so với nguồn ngoài**
- Script: `eval_external.py` rồi `eval_split_report.py --holdout`. Log: `ai/data/survey/run_typefix_report.log`.
- Bản "trước": `ai/data/survey/before_typefix/eval_external_matches.csv`. Đã chạy lại từ mã commit `68ffa56`: mọi cột đúng/sai giống hệt. Chỉ cột tên hiển thị `ten_nguon` khác ở 24 dòng, do thứ tự `set` của Python; từ nay chạy với `PYTHONHASHSEED=0`.
- Khoảng tin cậy 95% (Wilson) ghi trong ngoặc. *(Không có script nào sinh ra các khoảng này và chúng giả định mẫu độc lập (Red Team T6): không dùng trong báo cáo; thay bằng bootstrap theo cụm ở lần đo 3.)*

| Chỉ số | Fix trước | Fix sau | **Holdout trước** | **Holdout sau** |
|---|---:|---:|---:|---:|
| Loại đúng, Lensfun | 481/548 = 87,8% | 535/548 = 97,6% | 502/571 = 87,9% [85,0–90,3] | **565/571 = 98,9%** [97,7–99,5] |
| Loại đúng, Wikidata | 245/295 = 83,1% | 283/295 = 95,9% | 263/315 = 83,5% [79,0–87,2] | **305/315 = 96,8%** [94,3–98,3] |
| Loại đúng theo sản phẩm (đúng ở mọi nguồn) | 514/598 = 86,0% | 582/598 = 97,3% | 527/612 = 86,1% [83,1–88,6] | **598/612 = 97,7%** [96,2–98,6] |
| Ngàm đúng / gán, Lensfun | 314/319 = 98,4% | 352/357 = 98,6% | 358/366 = 97,8% [95,7–98,9] | 391/402 = 97,3% [95,2–98,5] |
| Ngàm đúng / gán, Wikidata | 212/212 | 239/239 | 238/238 | 266/266 |
| Khung thân đúng / gán, Lensfun | 161/161 | 177/177 | 190/190 | 204/204 |
| Khung thân đúng / gán, openMVG | 93/94 | 106/106 | 121/121 | 132/133 = 99,2% |

Bảng nhầm loại của holdout sau sửa (đáp án → quy tắc): thân → phụ kiện 5, thân → khác 2, thân → ống 1, ống → thân 1, khác → phụ kiện 2, khác → thân 1.
- **Chưa xem từng ca sai của holdout**, nên chưa biết bao nhiêu trong 14 ca là đáp án sai. Ở nửa fix, 16/16 ca còn lại đều là đáp án sai.
- Ngàm theo Lensfun ở holdout: số được gán tăng 366 → 402 (thêm thân/ống vừa được nhận đúng loại), số sai tăng 8 → 11. Chưa xem 3 ca sai mới.

**Ảnh hưởng: số sản phẩm và ma trận M** (`ai/data/kg/mount_compat_log.txt`)

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Thân (`than`) | 488 | **544** |
| Ống (`ong`) | 1.143 | **1.337** |
| Máy ống liền / khác (`khac`) | 1.802 | 1.758 |
| Phụ kiện | 24.507 | 24.301 |
| Thân có 1 ngàm (hàng của M) | 482 | **538** |
| Ống có 1 ngàm / "không chắc" QĐ 4 / vào M | 999 / 113 / 886 | **1.167 / 130 / 1.037** (không còn log) |
| Kích thước M | 482 × 886 | **538 × 1.037** (không còn log) |
| Cặp M = 1 | 56.276 | **75.690** (không còn log) |
| … trong đó cờ "chưa rõ có cắt khung" (QĐ 11) | 1.638 | 2.186 (không còn log) |
| Cặp "không biết" | 1.836 | 2.960 (không còn log) |

Cột "Sau" của 5 dòng cuối: **không còn log, không dùng trong báo cáo** (`kg/mount_compat_log.txt` bị lần chạy QĐ 16 ghi đè).

**Còn chưa chắc / phải làm theo**
- **Máy phim trong M (cần Nam quyết).** Sau sửa có 17 thân máy phim (Nikon F 7, Canon EF 8, Canon FD 2); trước chỉ có 2.
  - Bảng luật đang coi chúng là thân FF. Nên ống DX trên thân Nikon phim bị xếp `crops_sensor` (M = 1): **462 cặp**, trước sửa 53. Luật QĐ 11 còn cho thêm **294 cặp** M = 1 có cờ, trước sửa 36. *(462 và 294 có log `run_redteam_n3_t4.log`; 53 và 36: không còn log, không dùng trong báo cáo.)*
  - Nhưng máy phim **không có chế độ cắt khung**: ống DX sẽ tối góc. Thân cơ như FM-10 còn không chỉnh được khẩu độ với ống G (không có vòng khẩu).
  - Canon EF phim + EF-S → `incompatible`: đúng.
- Hai ống mới được nhận loại có ngàm chưa chuẩn (lỗi bước gán ngàm, không thuộc lần sửa này):
  - "Sigma 150-600mm … (for Canon EOS) & MC-11 Mount Converter" bị gán `sony_e`;
  - "Lightdow 420-800mm … + T Mount Ring for Nikon" bị gán `t_mount`, trong khi QĐ 9 nói phải theo ngàm của vòng.
- Kết quả holdout là **lần chấm duy nhất**. Nếu sửa thêm quy tắc thì holdout không còn độc lập.
- Script 04 / `common_05.py` vẫn chưa đọc được đầu ra mới (như mục dưới).

---

## 08/10/2026: Gỡ các file nội dung 3–4 cũ của Hải khỏi `ai/data/kg/`; đưa đầu ra mới lên git. Nhánh `nam/content3`

**Sửa gì**
- `git rm` 8 file cũ trong `ai/data/kg/`: `linked_products.csv`, `compatible_item_edges.csv`, `compatibility_stats.json`, `kg_stats.json`, `mount_mapping.json`, `validation_log.txt`, `validation_samples_50.csv`, `unlinked_audit_samples_50.csv`.
  - Trước khi gỡ, đã kiểm sha256: cả 8 file giống hệt bản sao lưu ở `ai/data/kg_v62abf54/` (bản này không lên git).
  - Muốn xem lại bản của Hải thì lấy từ commit `62abf54`.
- Đưa lên git đầu ra nội dung 3 mới: `compatibility_matrix.npz` (M), `unknown_mask.npz` (ma trận "không biết"), `item_attributes.csv`, `compat_pairs.csv`.
  - `.gitignore` vẫn chặn `ai/data/kg/*.npz`, nhưng thêm ngoại lệ `!` cho đúng 2 file `.npz` này.
- Dữ liệu gốc (`ai/data/raw/`) và dữ liệu nguồn ngoài (`ai/data/external/`) vẫn **không** lên git.

**Vì sao**
- Các file cũ được sinh từ cách khớp model cũ (257 sản phẩm có ngàm) và mã sản phẩm cũ, nên không còn đúng với dữ liệu sau gộp lặp.
- Cô yêu cầu nộp ma trận M (lỗi 3 trong STATUS).

**Ảnh hưởng / phải làm theo**
- `04_build_knowledge_graph.py` đọc `linked_products.csv`, `compatibility_matrix.npz` theo định dạng cũ, `body_index.json`, `lens_index.json`, nên **hiện không chạy được**. Phải sửa để đọc `item_attributes.csv` và `compat_pairs.csv`.
- `common_05.py` đọc `compatible_item_edges.csv` (đã gỡ), nên các baseline nội dung 5 cũng phải sửa theo.

---

## 07/10/2026: Ghi đè `ai/data/kg/` bằng đầu ra nội dung 3 mới; QĐ 11; đo độ chính xác bằng nguồn ngoài. Nhánh `nam/content3`

**Sửa gì**
1. **Sao lưu rồi ghi đè `ai/data/kg/`.**
   - Bản cũ chép sang `ai/data/kg_v62abf54/` (10 file, kiểm sha256 khớp từng file; không đưa lên git).
   - Chạy `03_mount_compat.py --out-dir ai/data/kg --overwrite`. Các file bị thay: `body_index.json`, `lens_index.json`. File mới: `item_attributes.csv`, `compat_pairs.csv`, `compatibility_matrix.npz`, `unknown_mask.npz`, `mount_compat_stats.json`, `mount_compat_log.txt`.
   - **Các file cũ của Hải vẫn nằm trong `ai/data/kg/` và nay đã cũ**, vì pipeline mới không ghi đè chúng: `linked_products.csv`, `compatible_item_edges.csv`, `compatibility_stats.json`, `kg_stats.json`, `mount_mapping.json`, `validation_*`, `unlinked_audit_samples_50.csv`. Script 04 cũ vẫn đọc các file này.
2. **QĐ 11** (`ai/config/mount_rules.toml`, luật `same_mount_ff_body_lens_khung_unknown_autocrop`):
   - Áp cho thân FF ở các ngàm có chế độ cắt khung chính hãng (Nikon F/Z, Sony E/A, Canon RF, Pentax K), gắn ống cùng ngàm nhưng không rõ khung.
   - Kết quả: M = 1, mức `compatible_with`, kèm cờ `crop_unknown = 1` ("chưa rõ có cắt khung").
   - `compat_pairs.csv` có thêm cột `crop_unknown`.
3. **Nguồn của luật:**
   - Mở và đọc cả 14 trang; mỗi nguồn ghi URL, câu trích nguyên văn, `kiem_chung = "da_doc_trang"`.
   - Ba nguồn bán lẻ (B&H) được thay bằng trang hãng: thông cáo Nikon FT1 (2011), trang hỗ trợ Sony về ống DT (có câu nói ngàm chuyển LA-EA), thông cáo Olympus về E-P2 (nói MMF-1).
   - Trang Sigma xác nhận ống DC bản Canon dùng **ngàm EF**. Điểm "chưa đối chiếu" của QĐ 8 nay đã có nguồn.

**Ảnh hưởng** (`ai/data/kg/mount_compat_log.txt`)

| Chỉ số | Trước QĐ 11 (`kg_new`) | Sau QĐ 11 (`kg`) |
|---|---:|---:|
| Kích thước M | 482 × 886 | 482 × 886 |
| Cặp M = 1 | 54.638 | **56.276** |
| … trong đó cờ "chưa rõ có cắt khung" | – | 1.638 |
| Cặp "không biết" | 3.474 | **1.836** |

**Độ chính xác so với nguồn ngoài** (`ai/survey/content3/eval_external.py`, log `ai/data/survey/run_eval_external.log`; nguồn ở `docs/DATA_SOURCES.md`)

Cách đọc bảng:
- Mỗi nguồn chỉ chấm trên các sản phẩm khớp tên chắc chắn.
- "Gán" là số sản phẩm mà quy tắc đưa ra 1 ngàm / 1 khung.
- "Để trống" là quy tắc trả "không rõ".

| Nguồn | Khớp được | Loại đúng | Ngàm: đúng / gán (để trống) | Khung thân: đúng / gán (để trống) |
|---|---:|---:|---:|---:|
| Lensfun | 1.119 (551 thân/máy, 568 ống) | 983/1.119 (87,8%) | 672/685 = **98,1%** (12) | 351/351 = **100%** (1) |
| openMVG | 635 máy | – | – | 214/215 = **99,5%** (2) |
| Wikidata | 610 (297 thân, 313 ống) | 508/610 (83,3%) | 450/450 = **100%** (2) | – |

Tổng cộng 1.493 sản phẩm khác nhau khớp được ít nhất một nguồn.

Các ca sai, Claude đã đọc từng ca:
- **Ngàm, 13 ca lệch với Lensfun: không ca nào là lỗi quy tắc.**
  - 7 ca: Lensfun ghi ngàm "EF-S" cho ống EF 75-300 III, vì ghi theo máy dùng để hiệu chỉnh.
  - 6 ca: khớp nhầm sang bản ngàm khác mà Lensfun chỉ có một bản, vd Sony FE 50mm f/1.4 ZA bị khớp với "Sony 50mm f/1.4" ngàm A; Samyang AF 85mm bản RF với bản E; Voigtlander 15mm bản Leica M với bản E; Zeiss ZE.
- **Khung, 1 ca sai với openMVG: lỗi quy tắc thật.** Fujifilm X-S1 là máy bridge 2011, nhưng luật dòng máy `x-s\d` coi là thân X-mount.
- **Loại, khoảng 100–140 ca sai mỗi nguồn: phần lớn là lỗi quy tắc thật.** Quy tắc tin danh mục Amazon:
  - ống kính bán kèm combo nằm ở "Accessory Kits" / "Accessory Bundles" bị xếp `phu_kien` (Lensfun: 59 + 18 ca);
  - thân máy bị Amazon xếp vào "Point & Shoot" / "Instant Cameras" bị xếp `khac` (vd Olympus PEN E-P1, Pentax K-01, Nikon D3300);
  - máy phim SLR (danh mục Film Cameras) bị xếp `khac`;
  - còn một ít là lỗi khớp: chữ "f4" trong khẩu độ bị khớp với máy phim "Nikon F4"; "Canon VIXIA HF R50" bị khớp với "EOS R50".
- **Hệ quả:** độ chính xác khi quy tắc **đã gán** ngàm hoặc khung rất cao, nhưng **độ phủ** bị giới hạn bởi lỗi phân loại. Các ống, thân bị xếp nhầm thành phụ kiện / khác thì không vào M.

**Chưa làm / phải làm theo**
- **Chưa sửa lỗi phân loại** vừa tìm được. Nếu sửa theo chính tập đánh giá này thì số đo lần sau không còn độc lập. Cần Nam quyết cách làm.
- Script 04 và `common_05.py` (CVR) chưa đọc đầu ra mới (xem mục bên dưới).

---

## 07/10/2026: Nội dung 3 bản mới — `03_mount_compat.py` (xác định ngàm tách khỏi khớp model). Nhánh `nam/content3`

**Sửa gì**
- **Thêm** (không sửa file của Hải):
  - `ai/pipeline/03_mount_compat.py`: pipeline chính;
  - `ai/pipeline/mount_detect.py`: bộ nhận diện loại / ngàm / khung;
  - `ai/config/mount_rules.toml`: bảng luật tương thích, mỗi luật có nguồn hoặc lý do.
- `03_entity_linking_matrix.py` của Hải **giữ nguyên**. Từ nay nó chỉ còn vai trò khớp model để lấy thông số (bước 3d). Ma trận M **không** lấy từ nó nữa.
- Cách mới, ví dụ trước:
  - "Sigma 30mm DC DN for Sony E-mount" → đọc chữ "E-mount" → ngàm `sony_e`; chữ "DC" → khung `apsc`. Cách cũ bỏ sót ống này vì nó không có trong bảng 139 model.
  - "Nikon D3200" → luật dòng máy → `nikon_f`, `apsc`.
  - Cặp (D750, ống DX) → mức `crops_sensor`, M = 1.
- Loại sản phẩm lấy từ danh mục, có lọc thêm bằng tiêu đề. Bản cũ coi 801 máy compact là "thân máy" *(không còn log, không dùng trong báo cáo)*; bản mới xếp chúng vào `khac`.
- Ma trận M có 5 mức (QĐ 2, 8): `compatible_with`, `crops_sensor` (M = 1); `requires_adapter`, `incompatible`, `unknown` (M = 0). Cặp `unknown` lưu ở ma trận riêng `unknown_mask.npz`.
- 113 ống hãng thứ ba có nhiều asin con được đánh dấu "không chắc" (QĐ 4): không vào M, vẫn có trong `item_attributes.csv` và `compat_pairs.csv`.

**Vì sao**
- Bản cũ chỉ gán được ngàm cho 257/28.867 sản phẩm (0,9%), vì phải khớp đúng tên model với bảng 139 dòng.
- Bản cũ có 1.414 "thân máy" thì hơn một nửa là máy compact không có ngàm.
- Bằng chứng ở `docs/content3_survey.md`.

**Ảnh hưởng** (số mới từ `03_mount_compat.py --out-dir ai/data/kg_new`, log ở `ai/data/kg_new/mount_compat_log.txt`)

| Chỉ số | Bản cũ (62abf54, dữ liệu cũ) | Bản mới (dữ liệu sau gộp lặp) |
|---|---:|---:|
| "Thân máy" theo phân loại | 1.414 | 488 (`than`); thêm 1.802 `khac` (compact, máy quay…) |
| "Ống kính" theo phân loại | 1.462 | 1.143 (`ong`) |
| Thân có ngàm (vào M) | (257 thân + ống) | **482** |
| Ống có ngàm | | 999, trong đó 886 vào M và 113 "không chắc" |
| Kích thước M | (theo bảng cũ) | 482 × 886 |
| Cặp M = 1 | | 54.638 (12,79%) |
| Cặp "không biết" | không có mức này | 3.474 (0,81%) |
| User có thân trong M ở train và item test là ống trong M | (chưa tính) | 951. Ống test so với thân đã có: 661 `compatible_with`, 9 `crops_sensor`, 10 `requires_adapter`, 23 `unknown`, 248 `incompatible` (`ai/survey/content3/scenario_kgnew.py`) |

**Đã kiểm chứng / chưa**
- Kiểm trên 50 mẫu dev do Claude tự chấm (`check_dev.py`): loại đúng 49/50, ngàm 46/50, khung 43/50 *(không còn log, không dùng trong báo cáo)*. Mọi giá trị quy tắc **đã gán** đều khớp nhãn; các chỗ lệch là quy tắc để "không rõ" (vd chỉ ghi "for Canon"). **Đây không phải số đánh giá chính thức**, vì người chấm và người viết quy tắc là một.
- Chưa đối chiếu với nguồn thông số bên ngoài (chờ Nam duyệt tải về, QĐ 10).

**Phải làm theo**
- **Chưa ghi vào `ai/data/kg/`.** Đầu ra mới đang ở `ai/data/kg_new/`, chờ Nam đồng ý ghi đè.
- Script 04 đọc `linked_products.csv` (đầu ra cũ) → phải sửa để đọc `item_attributes.csv` và `compat_pairs.csv`. Bỏ `assert after == 257`.
- `common_05.py` (CVR): chỉ tính các ống có trong `lens_index.json`, và bỏ các cặp có trong `unknown_mask.npz` (QĐ 4, 8).

---

## 07/10/2026: Bỏ số ghi cứng trong `common_05.py` và `04_build_knowledge_graph.py`. Nhánh `nam/content3`

**Sửa gì**
- `ai/pipeline/common_05.py`: `N_USERS` và `N_ITEMS` không còn ghi cứng `70424` / `28867`. Nay đọc từ `ai/data/processed/user_map.json` và `item_map.json` rồi lấy `len()`, giống cách `04_build_knowledge_graph.py` đã làm. Sửa luôn docstring đầu file (bỏ "70,424 users", "2,491 users").
- `ai/pipeline/04_build_knowledge_graph.py`, phần ghi `kg_stats.json` (mục `notes`):
  - `full_kcore_interactions`: trước ghi cứng `622997`, nay đọc `filtered_interactions` trong `ai/data/processed/filtering_stats.json`.
  - `val_interactions`, `test_interactions`: trước ghi cứng `70424`, nay đếm số dòng của `val.txt` / `test.txt` (hàm mới `count_lines`).

**Vì sao**
- Sau khi gộp tương tác lặp (mục bên dưới), số người dùng và sản phẩm đã đổi. Ví dụ: nếu để `N_ITEMS = 28867` trong khi chỉ còn 27.940 sản phẩm, LightGCN sẽ tạo thừa 927 embedding sản phẩm "ma", còn bộ lấy mẫu âm có thể bốc trúng mã sản phẩm không tồn tại.
- Lấy số từ file đầu ra của bước 2 thì lần sau dữ liệu đổi cũng không phải sửa tay.

**Ảnh hưởng (kiểm bằng lệnh Python chạy ngày 07/10/2026)**

| Hằng số | Cũ (ghi cứng) | Mới (đọc từ file) |
|---|---:|---:|
| `common_05.N_USERS` | 70.424 | 67.661 |
| `common_05.N_ITEMS` | 28.867 | 27.940 |
| `kg_stats.notes.full_kcore_interactions` | 622.997 | 595.515 |
| `kg_stats.notes.val_interactions` / `test_interactions` | 70.424 / 70.424 | 67.661 / 67.661 |

**Chưa làm / phải sửa tiếp**
- **Chưa chạy lại toàn bộ script 04**, vì script 04 cần đầu ra của script 03 (nội dung 3), mà nội dung 3 đang được thiết kế lại.
- Script 04 còn một chỗ ghi cứng nữa: `assert after == 257` (số sản phẩm đã gán ngàm theo bản cũ). Chỗ này phụ thuộc kết quả nội dung 3 nên chưa sửa; khi làm lại nội dung 3 phải bỏ hoặc thay.

---

## 07/10/2026: Bước 01–02 (lọc dữ liệu, chia train/val/test). Nhánh `nam/fix-data`

### 1. Những điểm đã kiểm chứng là đúng (không sửa)

Nam tải lại dữ liệu gốc và chạy lại `01_filter_camera_domain.py` và `02_split_time_aware.py` **bằng code của Hải, chưa sửa gì**. Các số sau khớp đúng với báo cáo 2:

- 43.886.944 đánh giá và 1.610.012 sản phẩm trong Electronics.
- 253.260 sản phẩm camera sau khi lọc metadata; 4.042.112 tương tác camera.
- Cả 14 vòng k-core, từng con số một.
- Sau k-core: 70.424 người dùng, 28.867 sản phẩm, 622.997 tương tác, độ thưa 99,969%, trung bình 8,85 tương tác/người.
- Phân vị số tương tác mỗi người (5 / 5 / 7 / 9 / 15 / 20 / 188), phân bố số sao.
- Train 482.149 tương tác, val và test mỗi tập 70.424.
- Số người dùng có item trùng giữa các tập: val–train 1.290, test–train 1.166, test–val 2.544.
- Script 02 chạy 2 lần cho ra file giống hệt nhau (kiểm bằng sha256), nên seed 42 tái lập được.

Dữ liệu gốc dùng để kiểm (tải từ trang chính thức, ngày sửa trên server là 16/01/2025):

| File | Kích thước (byte) | sha256 |
|---|---|---|
| `Electronics.jsonl.gz` | 6.474.438.619 | `17b2c5f3736d4c0cb874859076436ebd4513f4c2396c528440a63204084e6a28` |
| `meta_Electronics.jsonl.gz` | 1.312.900.427 | `a4a196a1c8e443e0942d8a5c79b5a5d2d68e29d483f2badec1126690b4b2790d` |

### 2. Những chỗ báo cáo 2 (`ai/docs/02_DATA_PREPROCESSING.md`) ghi sai

Code tính đúng. Sai nằm ở chỗ báo cáo ghi số không do script in ra, hoặc diễn giải sai.

| Chỗ trong báo cáo | Báo cáo ghi | Số đúng | Vì sao sai |
|---|---|---|---|
| Bảng 2.1, dòng "Sau Domain Filtering", cột Users | ~2,1 triệu (ước tính) | **2.502.236** | Script cũ không đếm số này, nên báo cáo phải ước tính. Nay script đã đếm. |
| Bảng 2.1, cột "Items có tương tác" | 72.775 | **253.208** | 72.775 là số sản phẩm **sau vòng 1 của k-core** (xem dòng "Vòng 1" trong log), không phải số sản phẩm có ít nhất 1 tương tác. |
| Bảng 2.1, TB tương tác/người | 1,92 | **1,62** | Hệ quả của 2 dòng trên: 4.042.112 / 2.502.236. |
| Bảng 2.1, độ thưa | 99,997% | **99,9994%** | Cũng là hệ quả của 2 dòng trên. |
| Phụ lục A, ghi chú vòng 1 | "toàn bộ 72.775 items tạm thời đều thỏa mãn" | Vòng 1 giảm sản phẩm từ 253.208 xuống 72.775 | Cùng nguyên nhân với dòng 72.775 ở trên. |
| Mục 2.2, giải thích 16.195 tương tác lặp | "người dùng tương tác lại ở các thời điểm khác nhau", "mua lặp lại" | **13.079 dòng là bản sao y hệt**, chỉ 3.116 dòng là đánh giá lại thật | Xem mục 3 bên dưới. |

Ví dụ một bản sao y hệt trong file gốc: user `AHSRW3FML7LW3G5LZK5REGJGDNLQ`, sản phẩm `B01E3QM34W`, timestamp `1489165051000`. File gốc có **2 dòng giống nhau hoàn toàn**: cùng asin, cùng tiêu đề "Five Stars", cùng nội dung "Works great but film is pricy." Đây không phải mua lại, mà là dữ liệu Amazon bị lặp dòng. Khi kiểm cả 9.461 nhóm bị lặp trong file gốc, có 9.460 nhóm trùng y hệt cả asin lẫn nội dung.

### 3. Sửa code: gộp tương tác lặp trong `ai/pipeline/01_filter_camera_domain.py`

**Sửa gì**
- Thêm hàm `step_2b_dedup_user_item`, chạy sau bước lọc tương tác và **trước k-core**.
- Mỗi cặp (user, parent_asin) chỉ giữ **1 dòng có timestamp sớm nhất**. Nếu hai dòng trùng timestamp thì giữ dòng có số sao thấp hơn. Trong dữ liệu sau k-core của bản cũ không có trường hợp nào trùng timestamp mà khác số sao.
- Log in ra số dòng bị bỏ, chia làm hai loại:
  - **bản sao y hệt:** trùng cả user, sản phẩm, timestamp và số sao với một dòng khác;
  - **đánh giá lại:** cùng user và sản phẩm nhưng khác timestamp hoặc số sao.
- `filtering_stats.json` có thêm các trường: `raw_camera_users`, `raw_camera_items_with_interaction`, `dedup_removed_total`, `dedup_removed_exact_copy`, `dedup_removed_re_review`, `dedup_interactions`.
- Phần còn lại của script 01 và toàn bộ script 02 **không đổi**.

**Vì sao**
1. **Bài toán là gợi ý sản phẩm người dùng chưa có.** Một sản phẩm đã mua rồi thì không cần gợi ý lại, nên mỗi cặp user–sản phẩm chỉ cần tính một lần.
2. **Bản ghi lặp làm rò rỉ dữ liệu sang val/test.**
   - Ví dụ: đánh giá cuối của một người bị lặp 2 dòng. Khi đó dòng thứ nhất rơi vào val, dòng thứ hai rơi vào test, tức là val và test là cùng một sản phẩm.
   - Bản cũ có 2.544 người dùng bị như vậy, trong đó 2.396 người chỉ vì bản sao y hệt.
   - Ngoài ra, bản sao còn được đếm vào điều kiện "≥ 5 tương tác" của k-core. Vì vậy một người chỉ có 3 sản phẩm khác nhau, cộng thêm 2 dòng lặp, vẫn lọt qua k-core.
3. **Giữ lặp làm sai kết quả đánh giá.**
   - Hàm `full_catalog_cvr` (`ai/pipeline/common_05.py`, dòng 182–186) loại các item đã có trong train bằng cách gán điểm −∞. Đánh giá xếp hạng toàn bộ (full ranking), cách đo dự định dùng làm kết quả chính, theo chuẩn cũng loại như vậy.
   - Hệ quả: nếu item test đã nằm trong train, mô hình không thể đoán trúng, và kết quả bị kéo xuống một cách oan uổng.
   - Lưu ý: hàm `sampled_eval` (1 + 99) **không** loại item train. Ở đó item test trùng train lại có thể làm kết quả đẹp lên giả.
   - Bản cũ có 1.166 người dùng có item test nằm trong train.

**Ảnh hưởng (số cũ → số mới)**

Số mới lấy từ `filtering_stats.json`, log của script 01 và 02, và script so sánh chạy ngày 07/10/2026.

| Chỉ số | Bản cũ (62abf54) | Bản mới |
|---|---:|---:|
| Tương tác camera đọc từ file gốc | 4.042.112 | 4.042.112 |
| Người dùng / sản phẩm có tương tác, trước k-core | 2.502.236 / 253.208 | 2.502.236 / 253.208 (không đổi) |
| Dòng bị bỏ khi gộp | 0 | **51.199** (45.684 bản sao y hệt + 5.515 đánh giá lại) |
| Tương tác đưa vào k-core | 4.042.112 | **3.990.913** |
| Vòng 1 k-core (tương tác / người dùng / sản phẩm) | 826.275 / 99.317 / 72.775 | 799.073 / 96.648 / 72.081 |
| Số vòng đến khi hội tụ | 14 | 14 |
| **Người dùng sau k-core** | 70.424 | **67.661** |
| **Sản phẩm sau k-core** | 28.867 | **27.940** |
| **Tương tác sau k-core** | 622.997 | **595.515** |
| Độ thưa | 99,969% | 99,968% |
| TB tương tác/người (trung vị / P90 / max) | 8,85 (7 / 15 / 188) | 8,80 (7 / 15 / 184) |
| **Train** (đếm từng dòng) | 482.149 | **460.193** |
| Train (gộp lặp từng người, như `load_train`) | 470.009 | 460.193 (hai cách đếm giờ bằng nhau) |
| Val / Test | 70.424 / 70.424 | 67.661 / 67.661 |
| Dòng lặp (user, item) trong `camera_interactions_k5.csv` | 16.195 | **0** |
| Người dùng có val = test | 2.544 | **0** |
| Người dùng có test nằm trong train | 1.166 | **0** |
| Người dùng có val nằm trong train | 1.290 | **0** |
| RAM đỉnh khi chạy script 01 | 2,03 GiB | 2,02 GiB |

Ghi chú: còn **4 người dùng** có hai sản phẩm *khác nhau* cùng timestamp ở ranh giới train/val/test, nên thứ tự giữa hai sản phẩm đó do thuật toán sắp xếp quyết định. Kết quả vẫn tái lập được vì cùng đầu vào cho cùng đầu ra. Số này quá nhỏ nên chưa sửa.

### 4. Thay đổi phụ
- `.gitignore`: thêm `ai/data/processed_*/`.
- Đầu ra của bản cũ được sao lưu ở `ai/data/processed_v62abf54/` (không đưa lên git) để còn đối chiếu.

### 5. Việc cần làm tiếp vì số người dùng và sản phẩm đã đổi

Mã số người dùng và sản phẩm (`user_map.json`, `item_map.json`) đã thay đổi, nên **mọi kết quả của bước 03–05 trên dữ liệu cũ không còn dùng được**. Phải chạy lại các bước này. Những chỗ đang ghi cứng số cũ (chưa sửa):
- `ai/pipeline/common_05.py` dòng 36–37: `N_USERS = 70424`, `N_ITEMS = 28867`.
- `ai/pipeline/04_build_knowledge_graph.py` dòng 432–433: `val_interactions` / `test_interactions` = 70424.
- Các file trong `ai/data/kg/` (ví dụ `compatible_item_edges.csv`, `kg_stats.json`) đang dùng mã sản phẩm cũ.
- Báo cáo `ai/docs/02_DATA_PREPROCESSING.md` cần cập nhật theo số mới và sửa các chỗ sai ở mục 2.

### 6. Chưa kiểm chứng
- 18.286.191 người dùng thô của Electronics: script không đếm. Số này khớp với con số 18,3M ghi trên trang dataset, nhưng nhóm chưa tự đếm.
- Bảng 2.3 trong báo cáo 2 (1.414 thân máy / 1.462 ống kính) và mục 5 của báo cáo 2.
