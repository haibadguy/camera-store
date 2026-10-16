# Kế hoạch CaKG-Rec v2 — thiết kế và đăng ký trước (test lần 2)

- Viết 16/10/2026, nhánh `nam/cakg-v2` (tách từ `main` `98e5100`). **Trước khi huấn luyện dài và trước khi chấm test lần 2.** Chỉ mới chạy thử 1 epoch (mục 7).
- Lý do: test lần 1 (kế hoạch đăng ký trước `docs/reviews/cakg_eval_plan.md`, chấm 15/10) cho CaKG-Rec kém LightGCN nhỏ nhưng khác 0 (C1, C2) và ngang LightGCN + mặt nạ ở nhóm lắp được (C6). Red Team lần 1 (`docs/reviews/redteam_cakg_lan1.md`) không thấy lỗi; nguyên nhân là kênh phần cứng đẩy 2,39–3,41 thân máy cùng ngàm vào top-10 của người có thân (LightGCN 0,88–0,93). Cô hướng dẫn 16/10: chọn cách làm cho kết quả tốt nhất, tìm ra giải pháp hiệu quả hơn thì điều chỉnh. Việc này thay quyết định 15/10 "không làm thăm dò sửa hiện tượng chèn thân" (STATUS mục 7).
- **Kết quả test lần 1 giữ nguyên, không xóa, không sửa** (`results/cakg/test_final_20261015/`). Mọi số của lần 2 ghi nhãn "test lần 2" (mục 8).
- Theo khuôn `cakg_eval_plan.md`. Sau commit chứa file này, không đổi kế hoạch nếu chưa hỏi Nam; thay đổi trước khi chấm test lần 2 ghi ở mục 10, commit riêng.

**Nguồn số trong file** (chỉ train và val; không đọc mảng test theo từng người):

| Nguồn | Nội dung |
|---|---|
| `ai/survey/cakg_v2/chan_doan_v2.py` → `ai/data/survey/cakg_v2/run_chan_doan_v2_20261016_lan1.log` (sha256 `78b3f256…296f24`, commit `a90a6a2`, cây sạch) | chẩn đoán trên **train** + checkpoint v1 seed 1 (không đọc val / test) |
| `ai/survey/cakg_v2/test_cakg_v2.py` → `run_test_cakg_v2_20261016_lan1.log` (sha256 `e1a494fb…62dca`, commit `a90a6a2`, cây sạch) | kiểm thử dựng tay, mọi ví dụ tính tay ở mục 3 |
| `results/cakg/finalcheck_val_20261015_nhap1/*/result.json` (commit `e661ea1`) | NDCG@20 **val** của LightGCN, LightGCN + mặt nạ, CaKG-Rec v1 |
| `results/cakg/smoke_val_sweep_v2_20261016/` | chạy thử 1 epoch (thời gian, VRAM) |
| `docs/reviews/redteam_cakg_lan1.md` | số đã có từ Red Team lần 1 (không tính lại) |

---

## 0. Nguyên tắc

1. **Mọi chẩn đoán và lựa chọn chỉ dùng train / val.** Không mở mảng test theo từng người cho tới bước chấm test lần 2. Chẩn đoán mới ở mục 2 dùng **train** (còn chặt hơn val).
2. **Hệ thống cuối được quyết trên val** (mục 4). Test lần 2 chỉ để **báo**, không dùng để đổi lựa chọn (nếu đổi theo test thì test thành tập chọn).
3. Không giả định chiều: v2 có thể không hơn; kết quả nào cũng báo.
4. Test lần 2 **không mù**: nguyên nhân được tìm ra nhờ phân tích sau test lần 1 (Red Team có đọc mảng test đã lưu để xác nhận cơ chế). Phải nói điều này mỗi khi báo số lần 2 (mục 8, 9).

---

## 1. Ví dụ trước: chuyện gì xảy ra ở v1

Người u có một thân Canon 80D (ngàm EF-S). Ba ứng viên (số làm tròn cho dễ đọc, cùng cỡ với số trung bình thật ở mục 2):

| Ứng viên | phần hành vi e_uᵀe_i | phần phần cứng | điểm v1 |
|---|---:|---:|---:|
| Canon 90D (thân, cùng ngàm) | 1,1 | 2,4 | **3,5** |
| ống EF-S 10-18 | 2,8 | 0,5 | 3,3 |
| thẻ nhớ (không có nút trong H) | 3,0 | — (cổng đóng) | 3,0 |

v1 xếp 90D đầu tiên, dù người đã có thân hiếm khi đánh giá thêm thân (4,2% item val, 4,4% item test của người có thân; Red Team mục 1). Phần phần cứng của thân lớn vì hai lý do đo được trên **train** (mục 2): (i) h của các thân cùng ngàm gần như trùng nhau (cos ≈ 1); (ii) lúc huấn luyện, cặp dương (u, thân của u) có h_u **chứa chính thân đó** (công thức 7), nên BPR "thưởng" cho phần phần cứng của thân; lúc chấm, thân của u bị bỏ (item train) nhưng thân cùng ngàm có h gần như y hệt vẫn được cộng điểm.

---

## 2. Chẩn đoán thêm (chỉ train; checkpoint v1 seed 1)

Log `run_chan_doan_v2_20261016_lan1.log`. "Phần phần cứng" = β_{u,h} β_{i,h} h_uᵀh_i (công thức 9, đã nhân β).

| Đại lượng | Số |
|---|---|
| người có h_u: \|B_u^H\| = 1 / ≥ 2 | 8.485 / 1.874 |
| cặp dương train của họ: thân có h / ống có h / không có h | 13.424 (12,6%) / 13.383 (12,5%) / 80.029 (74,9%) |
| phần phần cứng, cặp dương là thân, \|B\| = 1 (h_u = h_b) | TB 3,01, trung vị 2,70 |
| phần phần cứng, cặp dương là thân, \|B\| ≥ 2: h_u gồm b / bỏ b | TB 2,64 / 1,36 |
| phần phần cứng, cặp dương là ống | TB 0,56, trung vị 0,51 |
| phần phần cứng, **thân cùng ngàm u chưa có** (ngẫu nhiên) | TB 2,40, trung vị 2,12 |
| điểm hành vi, thân cùng ngàm u chưa có | TB 1,13 |
| cos(h_b, h_b') thân cùng ngàm / khác ngàm | TB 0,957 (trung vị 1,000) / TB −0,101 |
| ‖h_b‖ của thân | TB 197, trung vị 191 |

Đọc: với thân cùng ngàm chưa có, phần phần cứng (2,40) lớn gấp đôi phần hành vi (1,13) và gấp ~4 lần phần phần cứng của ống dương (0,56). Kênh phần cứng thực chất đang chấm "thân cùng ngàm", không phải "ống hợp với thân". Chỉ trên 1 checkpoint (seed 1), không phải kiểm định.

---

## 3. Ba biến thể

Không đổi: dữ liệu, đồ thị con H_lõi (thân vẫn là nút của H, vẫn dựng h_u và L_comp), RGAT, gộp kênh (8), L_comp (10)–(12), τ = 0,2, **λ1 = 0,1** (cấu hình chốt v1, không dò lại), λ2, lr, batch, khởi tạo, ngân sách 300 epoch / chấm val mỗi 10 epoch / dừng sau 5 lần không tăng, mặt nạ (15) / (16), cách chấm (`eval_05`, `eval_cakg`). Code: `ai/pipeline/cakg_model.py` (`variant`), `06_cakg_train.py --variant`. `variant = "v1"` cho đúng mô hình test lần 1 (kiểm thử V1, mục 7).

### Biến thể A — "kênh phần cứng chỉ tác động lên điểm của ống kính" (`lens_gate`)

**Thay đổi.** Công thức (9) đổi cổng phía sản phẩm từ "i có h" thành "i là **ống** có h":

  (9A) ŷ_ui = z_uᵀz_i nếu has_h(u) = 1 và i ∈ ℐ_lens có nút trong H; ngược lại ŷ_ui = e_uᵀe_i

Áp dụng cả lúc huấn luyện (BPR) và lúc chấm. 1.251 ống có h mở cổng, 537 thân không.

**Ví dụ tính tay** (mục 1, chạy qua `gated_score` thật, kiểm thử V0): v1 3,5 / 3,3 / 3,0 → A: 90D = **1,1** (chỉ còn phần hành vi), ống 3,3, thẻ 3,0. Thứ tự: ống > thẻ > 90D.

**Vì sao sửa đúng nguyên nhân.** Thân không còn nhận phần phần cứng, nên không còn đường nào để h cùng ngàm (cos ≈ 1) đẩy thân lên; cũng không còn "thưởng chính mình" vì cặp dương là thân chấm bằng e_uᵀe_i. Điểm của thân giống LightGCN (chỉ kênh hành vi). Ý nghĩa đúng với đề tài: tri thức lắp được / không lắp được chỉ có nghĩa với ống (M là thân × ống).

**Rủi ro.** (i) Bỏ hẳn tác dụng của kênh phần cứng với thân (người mua thân thứ hai: 4,2% item val của người có thân); (ii) ống có thể chen chỗ phụ kiện thay cho thân (phần phần cứng của ống dương TB 0,56, nhỏ hơn nhiều so với thân, nên dự kiến nhẹ hơn; phải xem số ống / phụ kiện trong top-10, mục 4.4); (iii) chỉ còn tác dụng ở cặp (người có thân × ống có h), vùng rất nhỏ: có thể không đủ để hơn LightGCN + mặt nạ.

### Biến thể B — "h_u bỏ chính thân đang là item dương" (`loo_hu`)

**Thay đổi.** Giữ cổng v1 (thân và ống). Chỉ lúc **huấn luyện**, với cặp dương (u, i) mà i ∈ B_u^H:

  (7B) h_u⁻ⁱ = ( |B_u^H| h_u − h_i ) / ( |B_u^H| − 1 ),  dùng h_u⁻ⁱ thay h_u cho cặp này; nếu |B_u^H| = 1 thì cổng phía người **đóng** (ŷ_ui = e_uᵀe_i)

Âm mẫu j và lúc chấm giữ h_u như v1 (lúc chấm, thân của u là item train, đã bị bỏ khỏi ứng viên).

**Ví dụ tính tay** (kiểm thử V0): h_80D = (1; 0), h_90D = (0,8; 0,6). u có cả hai: h_u = (0,9; 0,3). Cặp dương (u, 90D): v1 h_uᵀh_90D = **0,90** (có 0,8·0,8 + 0,6·0,6 = 1 của chính 90D chia đôi); B: h_u⁻⁹⁰ᴰ = (1; 0), h_uᵀh_90D = **0,80** (chỉ còn phần "thân kia giống 90D"). Người u' chỉ có 80D, cặp dương (u', 80D): v1 ‖h_80D‖² = **1**; B: cổng đóng, phần phần cứng **0**.

**Vì sao sửa đúng nguyên nhân.** Bỏ phần "thưởng chính mình" — một rò rỉ giữa huấn luyện và lúc chấm: lúc chấm không bao giờ có cặp (u, thân u đã có), nên lúc huấn luyện cũng không nên có. Với 8.485 người một thân, BPR không còn lý do kéo phần phần cứng của thân lên (trên train v1: TB 3,01 → 0). Phần còn lại (người có ≥ 2 thân, TB 1,36 khi bỏ chính b) là tín hiệu thật: người đó đúng là đã mua thêm thân cùng ngàm.

**Rủi ro.** (i) Thân vẫn được chấm qua kênh phần cứng, và h thân cùng ngàm vẫn gần trùng (L_comp kéo về một chỗ) nên tín hiệu thật của 1.874 người ≥ 2 thân vẫn có thể đẩy thân lên cho mọi người có thân; (ii) sửa ít hơn A; nếu giả thuyết "thưởng chính mình là nguyên nhân chính" sai, B không đỡ được.

### Biến thể C — "âm mẫu thân cùng ngàm" (`body_hardneg`)

**Thay đổi.** Giữ cổng v1. Mỗi bộ ba (u, i, j) của người có h_u thêm **một** âm mẫu j2 lấy đều trong 𝒥(u) = {thân có nút trong H, cùng ngàm với ít nhất một thân của u, không có trong train của u}:

  (13C) ℒ_BPR = (1/|ℬ|) Σ_{(u,i,j)∈ℬ} [ −ln σ(ŷ_ui − ŷ_uj) + 𝟙[𝒥(u) ≠ ∅] · ( −ln σ(ŷ_ui − ŷ_uj2) ) ],  L2 thêm ‖e_j2⁽⁰⁾‖²

Ngàm của thân lấy từ `has_spec_mount` (thân, không phụ kiện, không cờ `ngam_khong_chac`). Không có siêu tham số mới (trọng số 1, một âm mẫu).

**Ví dụ tính tay** (kiểm thử V0): ŷ(thẻ nhớ, dương) = 3,0, ŷ(đèn, âm thường) = 1,0, ŷ(90D, âm thân) = 3,5. v1: −ln σ(2,0) = **0,12693**. C cộng thêm −ln σ(3,0 − 3,5) = **0,97408** → **1,1010**: gradient đẩy 90D xuống dưới thẻ nhớ.

**Vì sao sửa đúng nguyên nhân.** Âm mẫu đều (như LightGCN) có 87% là phụ kiện, gần như không bao giờ là thân cùng ngàm, nên BPR không bao giờ "thấy" lỗi xếp thân cùng ngàm lên cao. C cho mô hình thấy đúng lỗi đó và tự học cách giảm (vd β_h nhỏ ở thân), không cấm cứng như A.

**Rủi ro.** (i) Âm giả: một phần thân cùng ngàm là thứ người dùng sẽ mua (4,2% item val của người có thân là thân); (ii) đổi phân phối âm mẫu so với LightGCN (so sánh kém "sạch" hơn); (iii) sửa theo đúng triệu chứng đã thấy ở lần 1, dễ bị coi là "chỉnh theo test" hơn A, B.

---

## 4. Quy tắc chọn trên val và điều kiện DỪNG

### 4.1. Ví dụ trước

Giả sử sau khi dò (1 seed): A có NDCG@20 val trước / sau mặt nạ 0,0406 / 0,0406, điều kiện phụ đạt; B 0,0408 / 0,0408 nhưng ở nhóm lắp được kém LightGCN + mặt nạ rõ (khoảng 95% của hiệu [−0,04; −0,002], cận trên < 0) → B bị loại; C 0,0401 / 0,0401 (không hơn ngưỡng 0,04053). Chỉ A đạt cả hai điều kiện → chọn A. Nếu A cũng chỉ có 0,0404 (≤ 0,04053) → **DỪNG**, hệ thống cuối là LightGCN + mặt nạ.

### 4.2. Bước 1 — dò 3 biến thể (1 seed) và chọn (script `ai/pipeline/06v2_select.py`)

Mỗi biến thể chạy **seed 1**, λ1 = 0,1, cùng ngân sách v1. LightGCN seed 1–3 (checkpoint nội dung 5, kiểm sha256 theo `n5_final.toml`) được **chấm lại trên val** trong script chọn (trước mặt nạ và mặt nạ QĐ 4-9).

- **(a) Điều kiện phụ (kịch bản lắp được).** Kịch bản "ống cho người có thân", nhóm lắp được (904 người val), Recall@10 chỉ ống, **sau mặt nạ QĐ 4-9**: khoảng 95% bootstrap ghép cặp (B = 2.000, seed 20261009) của hiệu (biến thể − LightGCN + mặt nạ seed 1) phải có **cận trên > 0** ("không kém có ý nghĩa"). Lý do: kịch bản này là trọng tâm của đề tài (khung 2.5), và là chỗ kênh phần cứng phải có ích; với 904 người, khoảng rộng nên điều kiện này chỉ loại biến thể làm hại rõ.
- **(b) Hơn LightGCN + mặt nạ.** NDCG@20 val (full ranking, mọi 67.661 người) **sau mặt nạ QĐ 4-9** của biến thể **lớn hơn NDCG@20 val của LightGCN + mặt nạ ở cả 3 seed** (theo `finalcheck_val`: 0,04044 / 0,04040 / 0,04053, nên ngưỡng hiện là 0,04053; script tính lại). So "sau mặt nạ với sau mặt nạ" vì hệ thống cuối có mặt nạ; lấy max 3 seed vì biến thể chỉ có 1 seed và được chọn trong 3 (bù một phần lạc quan khi chọn).
- **(c) Chọn.** Trong các biến thể đạt **cả (a) và (b)**, chọn biến thể có **NDCG@20 val trước mặt nạ** lớn nhất (giữ chỉ số chọn của kế hoạch lần 1, QĐ 5-6).
- **DỪNG 1.** Không biến thể nào đạt cả (a) và (b) → **không chạy seed 2, 3, không chấm test lần 2; hệ thống cuối = LightGCN + mặt nạ QĐ 4-9.** Ghi kết quả dò vào STATUS / CHANGELOG như kết quả âm.

### 4.3. Bước 2 — seed 2, 3 của biến thể được chọn, DỪNG 2

- Chạy seed 2, 3 với **đúng cfg** của biến thể chọn (chỉ khác seed). Lệnh đưa sau khi có kết quả bước 1 và Nam đồng ý.
- **DỪNG 2** (cùng hai điều kiện, trên 3 seed): (a') hiệu Recall@10 nhóm lắp được (chỉ số từng người = trung bình 3 seed) so với LightGCN + mặt nạ (trung bình 3 seed) có cận trên khoảng 95% > 0; (b') trung bình 3 seed NDCG@20 val sau mặt nạ của v2 > trung bình 3 seed LightGCN + mặt nạ. Không đạt → DỪNG như trên (hệ thống cuối = LightGCN + mặt nạ; không chấm test lần 2). Script cho bước này viết sau bước 1, commit trước khi chạy; quy tắc ghi ở đây là quy tắc chốt.
- Đạt → ghi `ai/config/cakg_v2_final.toml` (biến thể, cfg, thư mục, sha256 `best.pt`, best_epoch, NDCG@20 val 3 seed), **commit trước khi chấm test lần 2**.

### 4.4. In thêm để hiểu (mô tả, không dùng để chọn)

Người có thân (val, top-10 trước mặt nạ): số thân / ống / phụ kiện trung bình, tỉ lệ thân cùng ngàm; Recall@10 người có thân tách item val có / không có nút trong H; khoảng bootstrap NDCG@20 (biến thể − LightGCN + mặt nạ s1). Kỳ vọng nếu sửa đúng nguyên nhân: số thân / top-10 về gần LightGCN (~0,9) ở A; Recall@10 item không có h tăng về gần LightGCN. Không đạt kỳ vọng này thì ghi lại, **không** thêm biến thể mới khi chưa hỏi Nam.

---

## 5. Số seed và thời gian

| Việc | Lần chạy | Giờ / lần | Tổng |
|---|---:|---:|---:|
| Bước 1: A, B, C × seed 1 | 3 | A ~1,7; B ~1,9; C ~1,9 (chạy thử: 20,1 / 21,7 / 22,5 s / epoch + chấm val 7,3 s mỗi 10 epoch; 300 epoch) | **~5,5–6** (xấu nhất) |
| `06v2_select.py` (chấm lại LightGCN 3 seed × 2 nhánh trên val) | — | — | vài phút |
| Bước 2 (nếu không DỪNG 1): seed 2, 3 | 2 | ~1,9 | ~4 |
| Chấm test lần 2 + so sánh (nếu không DỪNG 2) | — | — | < 0,5 |

Seed: dò 1 seed (`06_val_sweep.py --group v2`); biến thể chọn 3 seed {1, 2, 3} trước test lần 2 (như v1). GPU không tất định: không cam kết trùng sha256 khi chạy lại.

---

## 6. So sánh đăng ký trước cho test lần 2 (chỉ khi qua DỪNG 1 và DỪNG 2)

Chấm test **một lần** bằng script mới (`06v2_test_final.py`, viết và commit trước khi chạy; kiểm cây sạch, sha256 `cakg_v2_final.toml` và checkpoint) cho v2 × 3 seed: trước mặt nạ, mặt nạ QĐ 4-9 (chính), mặt nạ ∃b (mô tả). **LightGCN, LightGCN + mặt nạ, CaKG-Rec v1: dùng lại mảng test đã lưu của lần 1** (`results/cakg/test_final_20261015/`, kiểm sha256 với `result.json`), không chấm lại. K = 10; bootstrap ghép cặp theo người, B = 2.000, seed 20261009; chỉ số từng người = trung bình 3 seed; CVR = tổng vi phạm / tổng ống chấm được cộng qua seed; kịch bản bootstrap riêng trong nhóm.

| # | So sánh | Chỉ số | Tập | Vai trò |
|---|---|---|---|---|
| **D1** | v2 (mặt nạ) − LightGCN + mặt nạ | Recall@10, NDCG@10 | mọi người dùng; người có thân | **chính** |
| **D2** | v2 (mặt nạ) − CaKG-Rec v1 (mặt nạ) | Recall@10, NDCG@10 | mọi người dùng; người có thân | **chính** (sửa có tác dụng không) |
| D3 | v2 (mặt nạ) − LightGCN | Recall@10, NDCG@10 | mọi người dùng | phụ |
| **D4** | kịch bản chỉ ống: v2 (mặt nạ) − LightGCN + mặt nạ; v2 (mặt nạ) − v1 (mặt nạ) | Recall@10 | nhóm lắp được (762) | **chính** |
| D5 | v2 (trước) − LightGCN (trước); v2 (trước) − v1 (trước) | CVR_strict@10 | người có thân | phụ |

- 14 khoảng tin cậy. Hiệu khác 0 khi khoảng 95% không chứa 0; không hiệu chỉnh đa so sánh (như lần 1); mọi so sánh ngoài bảng là thăm dò.
- **Mô tả kèm** (không kiểm định): bảng chính như lần 1 (Recall / NDCG @5, 10, 20, CVR strict / R1 / R2, ∃b, người mất item test do mặt nạ, sampled 1+99); **top-10 của người có thân** (thân / ống / phụ kiện, thân cùng ngàm); Recall@10 người có thân tách item có / không có nút trong H; PC, PC_ngắn và kiểm 0 lỗi sự kiện của câu giải thích (`08_explain.py`; nếu phải sửa cho biến thể thì sửa và commit trước test). Faithfulness / C9 không thuộc so sánh đăng ký lần 2 (chạy thì ghi "mô tả").
- Hệ thống cuối đã quyết ở mục 4 (trên val); kết quả D1–D5 **không** đổi quyết định đó, chỉ báo.

---

## 7. Kiểm thử trước khi chạy (đã làm 16/10/2026)

`ai/survey/cakg_v2/test_cakg_v2.py`, log `ai/data/survey/cakg_v2/run_test_cakg_v2_20261016_lan1.log` (cây sạch):
- V0: các ví dụ tính tay ở mục 3 chạy qua code thật ra đúng số (A: 3,5 / 3,3 / 3,0 → 1,1 / 3,3 / 3,0; B: 0,90 → 0,80, |B| = 1 cổng đóng; C: 0,12693 + 0,97408; lấy mẫu chỉ trong tập ứng viên, đều).
- V1: `variant = "v1"` không đổi mô hình test lần 1: `make_cfg(0,1; 1)` trùng cfg đã lưu; nạp `best.pt` v1 seed 1 vào code cũ (`98e5100`) và code mới: cùng biểu diễn → điểm trùng từng bit; tính lại biểu diễn → lệch tương đối 4,6e-7 so với |điểm| lớn nhất 26,9 (cùng cỡ lệch do GPU không tất định khi code cũ tự tính 2 lần: 1,8e-5 tuyệt đối), top-20 trùng, loss trùng. 33 kiểm, ĐẠT CẢ.
- V2–V4 (dữ liệu thật): A mở cổng đúng 1.251 ống có h, 0 thân; thân / sản phẩm không có h = e_uᵀe_i đúng từng bit. B: h_u bỏ thân dương khớp tính độc lập từ danh sách thân. C: tập ứng viên của 500 người trùng tính tay. Ở cả ba, `loss()` = tính độc lập từ điểm của bộ chấm (lệch 0).

Chạy thử 1 epoch / biến thể (cây chưa commit, `--allow-dirty`; chỉ để đo thời gian và chạy hết đường code): `06_val_sweep.py --group v2 --label v2_20261016 --smoke` → `results/cakg/smoke_val_sweep_v2_20261016/` (ngoài git): 20,1 / 21,7 / 22,5 s / epoch, đỉnh VRAM 475 / 475 / 483 MiB, chấm val 7,2–7,5 s; 10.359 / 10.359 người có h_u có ứng viên âm thân (trung vị 85, max 373). `06v2_select.py` chạy hết trên thư mục thử này (ra DỪNG, đúng vì mới 1 epoch; không phải kết quả). Kiểm chạy tiếp sau khi bị ngắt (biến thể C, có RNG lấy âm mẫu; `results/cakg/smoke_v2_resume_20261016/`): ngắt sau epoch 1 rồi chạy lại → loss epoch 1 trùng (0,82159), epoch 2 0,61065 so với 0,61063 khi chạy liền (lệch do GPU).

---

## 8. Ghi nhãn "test lần 2"

- Thư mục `results/cakg/test_lan2_<ngày>/`; tên file `summary_test_lan2_*.md/json`, `compare_test_lan2_*.md/json`; dòng đầu mọi bảng: **"TEST LẦN 2 — chấm sau khi đã biết kết quả test lần 1 (15/10/2026); không phải đánh giá mù."** `meta` của json có `"test_lan": 2`, `"biet_ket_qua_lan_1": true`.
- STATUS, CHANGELOG, báo cáo: mọi số lần 2 ghi "(test lần 2)". Số lần 1 **giữ nguyên** là kết quả của kế hoạch `cakg_eval_plan.md`, báo song song, không thay.
- Báo cáo phải kể đủ trình tự: đăng ký trước → test lần 1 → Red Team tìm nguyên nhân (có đọc mảng test đã lưu) → cô hướng dẫn 16/10 → thiết kế v2 chỉ trên train / val → test lần 2.

---

## 9. Hạn chế đã biết (đưa vào báo cáo nếu dùng v2)

1. Test lần 2 không mù (mục 0.4); số lần 2 là bằng chứng yếu hơn lần 1.
2. Chọn 1 trong 3 biến thể bằng 1 seed trên val → lạc quan khi chọn; đã bù một phần bằng ngưỡng (b) "hơn cả 3 seed" và DỪNG 2 trên 3 seed, không bù hết.
3. λ1 = 0,1 lấy lại từ v1, không dò lại cho từng biến thể (ngân sách).
4. Ngân sách 300 epoch có thể chưa hội tụ (như v1 và LightGCN).
5. A bỏ tác dụng kênh phần cứng với thân; C có âm giả.
6. Chẩn đoán mục 2 chỉ trên checkpoint seed 1 của v1.

---

## 10. Sửa đổi kế hoạch

| Ngày | Sửa | Lý do |
|---|---|---|
| 16/10/2026 | Sau commit `a90a6a2` (bản đăng ký): điền sha256 log, số chạy thử 1 epoch và giờ ước tính (nguồn, mục 5, 7). **Không đổi quy tắc chọn, điều kiện DỪNG hay so sánh** | Log chính thức chạy trên cây sạch `a90a6a2`, sau khi commit kế hoạch |
| 16/10/2026 chiều | Sau bước 1 (chọn `lens_gate`): cài bước 2 như mục 4.3 đã ghi — nhóm `v2seeds` (`06_val_sweep.py`) và `06v2_dung2.py`; DỪNG 2 tính trên mảng LightGCN + mặt nạ đã chấm lại ở bước 1 (`select_20261016_134128/lightgcn_s*`). **Không đổi quy tắc (a'), (b')** | Kế hoạch 4.3: script bước 2 viết sau bước 1, commit trước khi chạy |
