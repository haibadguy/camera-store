# Red Team lần 1 — nội dung 6–8 (CaKG-Rec), sau khi chấm test

- Ngày 15/10/2026, nhánh `nam/cakg-rec`, HEAD lúc kiểm `4bb6c28` (cây sạch). Người làm: Claude, vai Red Team độc lập theo yêu cầu của Nam.
- Phạm vi: `docs/STATUS.md`, `docs/cakg_design.md`, `docs/reviews/cakg_eval_plan.md`, `results/cakg/test_final_20261015/summary_test_20261015_183745.md`, `compare_test_20261015_183817.md`; code `ai/pipeline/06_*`, `07_*`, `08_*`, `eval_cakg.py`, `cakg_model.py`, `kgat_model.py` (đọc thêm `rgat_layer.py`, `train_05.py`, `eval_05.py`); khung của cô `E:\DATN\co\khung_do_an_co_11102026.md` mục 1.4, 2.6.
- **Không** sửa code mô hình, cấu hình hay kết quả; **không** huấn luyện; **không** chấm lại test. Chỉ viết 2 script chẩn đoán chỉ đọc:

| Script | Làm gì | Log (ngoài git, `*.log` bị `.gitignore`) | sha256 log |
|---|---|---|---|
| `ai/survey/redteam/redteam_cakg_lan1.py` | **chấm lại trên val** 5 checkpoint CaKG-Rec + 3 LightGCN: checkpoint, h_u, cổng, tắt kênh phần cứng, tách nhóm người; đọc mảng đã lưu cho C4, C6, PC, tập ứng viên (mảng test), mặt nạ, C9 | `ai/data/survey/redteam/run_redteam_cakg_20261015_lan1.log` | `5c0aa0db…ca229a2` |
| `ai/survey/redteam/redteam_cakg_lan1_b.py` | **chỉ đọc mảng / bảng đã lưu** (val và test): loại sản phẩm top-10 của người có thân, tách C2, thứ tự full / sampled | `ai/data/survey/redteam/run_redteam_cakg_b_20261015_lan1.log` | `7829040d…16324a2` |

Dùng mảng **test đã lưu** (không tính lại điểm) ở 3 chỗ, vì cần thật: (i) kiểm "bỏ train + val khi chấm test" chỉ kiểm được trên mảng test; (ii) kiểm cơ chế tìm thấy trên val có lặp lại trên test; (iii) tách FS_PN của C9 (mảng `faithfulness_pairs.npz`). Kết quả test đã commit trước đó (`3e830aa`), nên đây là phân tích sau test, đúng kế hoạch mục 4.2 bước 7.

Mọi số dưới đây lấy từ 2 log trên, trừ chỗ ghi nguồn khác.

---

## 0. Trả lời thẳng

**Không tìm thấy lỗi nào làm sai số liệu.** Checkpoint nạp đúng, h_u dựng đúng, kênh phần cứng có tham gia khi chấm, mọi mô hình bỏ đúng cùng tập ứng viên, mặt nạ áp đúng, chạy test đúng một lần theo đúng thứ tự đã đăng ký.

**Nhưng có một nguyên nhân thiết kế làm CaKG-Rec kém hơn mức đáng có, chưa được ghi ở đâu:** kênh phần cứng (nhất là khi có L_comp) **đẩy thân máy cùng ngàm vào top-10 của người đã có thân**. Trên test, người có thân nhận trung bình 2,39–3,41 thân trong top-10 (LightGCN: 0,88–0,93), trong khi chỉ 4,4% item test của họ là thân. Gần như toàn bộ phần kém của C1 / C2 nằm ở đây. Đây không phải lỗi code (mô hình làm đúng công thức đã đăng ký) nên không đổi số, nhưng phải đưa vào phần giải thích kết quả.

Một số câu đang có trong STATUS / sẽ viết vào báo cáo **phải sửa** (mục 3): C3, C4, C6 val–test, C9 / FS_PN, PC, và nhiều câu của khung mục 1.4, 2.6 không được kết quả ủng hộ (mục 5).

---

## 1. Ví dụ trước: chuyện gì xảy ra với một người có thân

Người u có một thân Canon EF-S trong train. Item test của u là **một phụ kiện** (thẻ nhớ) — trường hợp chiếm 77% người có thân (8.027 / 10.406 item test là phụ kiện).

- LightGCN: top-10 của u gồm khoảng 0,9 thân, 2,5 ống, 6,3 phụ kiện. Thẻ nhớ có chỗ để lọt vào top-10.
- CaKG-Rec: u có h_u (trung bình h của thân Canon), nên mọi sản phẩm có nút trong H (thân, ống) được chấm bằng z_uᵀz_i = phần hành vi + phần phần cứng h_uᵀh_i. Các **thân Canon khác** có h rất gần h_u (cùng ngàm, cùng tập ống lắp được nên L_comp kéo chúng về cùng một vùng), nên phần phần cứng dương và lớn. Kết quả: top-10 của u có khoảng 3 thân (93% cùng ngàm với thân u đã có) — chiếm chỗ của phụ kiện. Thẻ nhớ bị đẩy xuống.

Tổng quát (công thức 9 của thiết kế): với người có h_u, mọi sản phẩm có h được cộng thêm β_{u,h}β_{i,h} h_uᵀh_i. Không có gì trong L_comp hay BPR ngăn **thân ↔ thân** gần nhau (L_comp chỉ có cặp thân–ống; âm mẫu BPR lấy đều, 87% là phụ kiện). Người đã có thân hiếm khi đánh giá thêm một thân (4,2% val, 4,4% test), nên mỗi thân chen vào top-10 gần như chắc chắn là một chỗ bị phí.

---

## 2. LỖI làm sai số — **không có**

Đã kiểm theo đúng danh sách Nam yêu cầu:

| Kiểm | Cách kiểm | Kết quả |
|---|---|---|
| Checkpoint nạp đúng | sha256 `best.pt` = `cakg_final.toml`; `load_state_dict(strict=True)`; chấm lại NDCG@20 val | 5/5 khớp sha256; NDCG@20 val chấm lại **trùng đúng** `result.json` và toml: 0,039731 / 0,039773 / 0,039569 (CaKG s1–s3), 0,039776 (λ1 = 0), 0,039681 (bỏ suitable_for). LightGCN s1–s3 0,04045 / 0,04040 / 0,04054, hạng khác mảng finalcheck_val ở 11 / 11 / 8 người (GPU không tất định, đã biết) |
| h_u dựng đúng | tính lại độc lập: trung bình h_b trên thân (loại 0) trong train có nút trong H | 10.359 người có h_u, trùng tập `user_body_matrix`; lệch tối đa 1,14e-05 (sai số float32); 0 người không có thân trong H bị bật has_hu, h_u của họ = 0 |
| Kênh phần cứng có tham gia khi chấm | so điểm đầy đủ với điểm khi tắt kênh phần cứng (mọi cặp dùng e_uᵀe_i) | cặp cổng mở = 10.359 người × 1.788 item = 0,98% mọi cặp; trong cặp ứng viên của người có h_u, **6,39%** có điểm khác (18.495.081–18.495.084 / 18.495.085 cặp cổng mở; vài cặp trùng điểm ngẫu nhiên); **top-10 đổi ở 8.744 / 7.871 / 8.304 trên 10.359 người có h_u** (s1 / s2 / s3), 0 người không có h_u |
| Giá trị cổng gộp β | `components()["betaU"/"betaI"]` | β_h phía người TB 0,0129 / 0,0107 / 0,0116; phía item TB 0,0122 / 0,0125 / 0,0118 (max 0,64). β nhỏ nhưng phần phần cứng chiếm trung vị **0,40 / 0,25 / 0,35** điểm của cặp cổng mở trong top-10 (do ‖h‖ lớn; khớp hạn chế 4 của STATUS) |
| Cùng tập ứng viên khi chấm test | đọc top-20 đã lưu của **mọi** mô hình × mọi nhánh (CaKG 3 seed, 2 ablation, LightGCN 3 seed, KGAT 3 seed, R-GCN 09/10): có item train hay item val của người đó không; mảng users có trùng tập test không | **0** item train / val ở mọi mảng; users trùng ở mọi mảng; top-20 "chỉ ống" chỉ có ống, 0 item train / val. Code: mọi mô hình đi qua cùng `eval_05.full_rank` với cùng `Split` (`make_split(..., val=val)`) |
| Mặt nạ áp đúng | đếm ống `judge_lens is True` trong top-20 sau mặt nạ QĐ 4-9 (val) | 0 ở CaKG s1 và LightGCN s1; 10.335 người có hàng mặt nạ khác 0 (= 10.406 − 71 người có thân ngoài M, khớp STATUS hạn chế 14) |
| eval R-GCN / Popularity (09/10) và CaKG (15/10) cùng phiên bản | sha256 đầu vào trong `meta` hai lần chạy | dữ liệu trùng cả 13 file; `common_05.py`, `eval_05.py` khác sha256 nhưng **chỉ khác kiểu xuống dòng** (LF lúc 09/10, CRLF bây giờ; nội dung = blob `f21ced4`). Không ảnh hưởng số (ghi chú G2) |
| Kênh hành vi kém LightGCN vì học chung? | người **không có thân** (điểm của CaKG-Rec = e_uᵀe_i thuần) | R@10 val CaKG − LightGCN cùng seed: +0,00089 / +0,00050 / −0,00070; NDCG@10 −0,00009 / +0,00016 / −0,00036 → **không thấy kém có hệ thống**. Trên test, phần người không có thân của C2 chỉ −0,00009 (Recall@10). Xem thêm mục 3.1 |
| C1–C8 tính đúng từ mảng | cài lại bootstrap riêng (seed khác) cho C6 val và test | khớp: vd C6 val vs LightGCN + mặt nạ [−0,00627; +0,01733] (cài riêng) so với [−0,00590; +0,01696] (`06_test_compare`) |

Kết luận mục 2: số trong `summary_test_*.md` và `compare_test_*.md` đúng với mô hình đã đăng ký.

---

## 3. CẦN SỬA CÂU CHỮ (xếp theo mức nghiêm trọng)

### 3.1. [Nặng nhất] Nguyên nhân C1 / C2 chưa được nêu: kênh phần cứng chèn thân máy vào top-10 người có thân

STATUS "hạn chế sau test" điểm 1 chỉ ghi "kém hơn nhỏ nhưng khác 0 … đúng điều kế hoạch đã cảnh báo". Câu này đúng nhưng **thiếu nguyên nhân**, mà nguyên nhân đo được:

**(a) Phần kém nằm ở người có thân.** Tách C2 (test): hiệu Recall@10 mọi người −0,00066 = **−0,00058 từ người có thân (89%)** + −0,00007 từ người không có thân (log b, mục b3). NDCG@10: phần người có thân còn lớn hơn cả hiệu tổng.

**(b) Trong người có thân, kênh phần cứng làm hại** (val, chấm lại; "tắt" = mọi cặp dùng e_uᵀe_i của chính CaKG-Rec):

| R@10 val, người có thân (10.406) | s1 | s2 | s3 |
|---|---:|---:|---:|
| LightGCN cùng seed | 0,05660 | 0,05593 | 0,05487 |
| CaKG-Rec tắt kênh phần cứng | 0,05458 | 0,05353 | 0,05372 |
| CaKG-Rec đầy đủ | **0,04738** | **0,05026** | **0,04968** |

Bật kênh phần cứng làm R@10 người có thân giảm 0,0033–0,0072; phần "kênh hành vi yếu hơn LightGCN" chỉ 0,0012–0,0024 (và kênh hành vi một mình không phải là mô hình, vì nó được huấn luyện cùng kênh phần cứng).

**(c) Lợi ở item có h, thiệt lớn hơn ở item không có h.** Người có thân, tách theo item cần đoán có nút trong H hay không (R@10, test, sau mặt nạ, log b):

| | item có nút trong H (1.737) | item không có (8.669) |
|---|---:|---:|
| CaKG-Rec s1 / s2 / s3 | 0,0921 / 0,0915 / 0,0950 | **0,0197 / 0,0237 / 0,0230** |
| LightGCN + mặt nạ s1 / s2 / s3 | 0,0869 / 0,0904 / 0,0898 | 0,0279 / 0,0275 / 0,0269 |

Trên val cùng hình: item có h 0,123 / 0,117 / 0,122 so với 0,124 / 0,116 / 0,116; item không có h 0,031 / 0,036 / 0,034 so với 0,042 / 0,043 / 0,041.

**(d) Cơ chế: top-10 của người có thân bị chèn thân máy cùng ngàm.**

| Top-10 người có thân (trước mặt nạ) | thân | ống | phụ kiện | thân cùng ngàm với thân đã có |
|---|---:|---:|---:|---:|
| CaKG-Rec s1 / s2 / s3, **test** | **3,41 / 2,39 / 2,99** | 1,81 / 2,00 / 1,86 | 4,58 / 5,34 / 4,90 | 93,5% / 94,0% / 93,6% |
| LightGCN s1 / s2 / s3, test | 0,88 / 0,93 / 0,88 | 2,46 / 2,43 / 2,45 | 6,31 / 6,31 / 6,34 | 77–78% |
| CaKG-Rec s1 tắt kênh phần cứng, val | 0,15 | 2,27 | 7,11 | — |
| Ablation λ1 = 0 (s1), test | 1,02 | 3,00 | 5,70 | 82,0% |
| Ablation bỏ suitable_for (s1), test | 3,57 | 2,01 | 4,23 | 92,7% |
| **Item test của người có thân** | **457 (4,4%)** | 1.350 | 8.027 | — |

Bảng "Loại sản phẩm trong top-10" của `summary_test_*.md` lấy trung bình **trên mọi 67.661 người** (0,47 so với 0,38 thân), nên che mất hiện tượng này. Đây đúng là rủi ro thiết kế khối 4 (e) đã nêu ("thang khác nhau … in tỉ lệ loại sản phẩm trong top-10 để thấy nếu bị lệch") — rủi ro **đã xảy ra** nhưng chưa được đọc ra vì bảng tính trên mọi người.

**(e) L_comp làm hiện tượng nặng hơn (thăm dò, 1 seed).** λ1 = 0: 1,01 thân / top-10, R@10 người có thân val 0,05401; CaKG-Rec s1 (λ1 = 0,1): 3,40 thân, 0,04738. Chỉ 1 seed (dao động giữa 3 seed CaKG-Rec: 2,39–3,40 thân), nên chỉ được ghi "gợi ý rằng", không kết luận.

**Sửa câu:** thêm vào hạn chế / chương phân tích: "CaKG-Rec kém LightGCN chủ yếu ở người có thân (89% hiệu Recall@10 của C2). Kênh phần cứng chấm cả cặp người – thân máy, nên đưa trung bình 2,4–3,4 thân cùng ngàm vào top-10 của người đã có thân (LightGCN 0,9), trong khi chỉ 4,4% item test của họ là thân; các item không có biểu diễn phần cứng (phần lớn là phụ kiện) bị đẩy xuống." Không viết "kém hơn nhỏ, do kênh phần cứng chỉ chạm ít người" — kênh phần cứng chạm ít người nhưng ở những người đó tác động **âm** và không nhỏ (R@10 val của người có thân giảm 6–13% tương đối so với chính CaKG-Rec khi tắt kênh phần cứng; 10–16% so với LightGCN cùng seed).

**Hệ quả với kế hoạch:** mọi sửa thiết kế (vd không chấm thân qua kênh phần cứng, cổng chỉ mở cho ống, thêm âm thân–thân vào L_comp) là việc **sau khi đã chấm test**: chỉ được làm như **thăm dò trên val**, ghi rõ; không được dùng lại test làm số khẳng định, không thay số chính. Cần Nam quyết (mục 6).

### 3.2. C3 (CVR trước mặt nạ thấp hơn LightGCN): do một seed, và do top-10 ít ống hơn

STATUS: "CVR trước mặt nạ thấp hơn LightGCN (C3: −0,0061, tương đối ~5%)". Số đúng, nhưng:

| CVR_strict@10 trước mặt nạ, test (vi phạm / ống chấm được) | s1 | s2 | s3 |
|---|---|---|---|
| CaKG-Rec | **0,1144** (1.982 / 17.327) | 0,1286 (2.448 / 19.032) | 0,1273 (2.266 / 17.804) |
| LightGCN | 0,1285 (3.003 / 23.365) | 0,1307 (2.996 / 22.924) | 0,1299 (3.012 / 23.182) |

- Chỉ **seed 1** thấp rõ; seed 2, 3 nằm trong khoảng của LightGCN (val cũng vậy: 0,1139 / 0,1282 / 0,1267 so với 0,1282–0,1303). Khoảng của C3 là bootstrap **theo người** (gộp 3 seed), không chứa độ dao động giữa seed; độ chênh giữa seed của CaKG-Rec (0,014) lớn gấp đôi hiệu C3.
- Mẫu số khác nhau nhiều: CaKG-Rec có 17–19 nghìn ống chấm được trong top-10, LightGCN 23 nghìn (ống bị thân chèn chỗ, mục 3.1). CVR là tỉ số trên tập ống khác nhau.

**Sửa câu:** "Trung bình 3 seed, CVR_strict@10 trước mặt nạ của CaKG-Rec thấp hơn LightGCN 0,0061 (khoảng theo người không chứa 0), nhưng chủ yếu do seed 1; seed 2, 3 ngang LightGCN. Không đủ bằng chứng nói kênh phần cứng giúp mô hình học được ràng buộc ngàm."

### 3.3. C4: "không do L_comp" quá mạnh

STATUS: "nhưng **không do L_comp**: ablation λ1 = 0 còn có CVR thấp hơn". Với 1 seed ablation, chỉ được nói **chiều ngược lại cũng không chứng minh được**:
- C4 = +0,0082 (CaKG s1 0,1144 − λ1 = 0 0,1062) nhỏ hơn độ chênh giữa 3 seed CaKG-Rec (0,1144–0,1286). Khoảng của C4 là bootstrap theo người, không có độ dao động seed → "khác 0" không có nghĩa "khác nhau do L_comp".
- Hai mô hình có top-10 rất khác: λ1 = 0 có 28.115 ống chấm được, CaKG s1 17.327.

**Sửa câu:** "C4 (1 seed): không có bằng chứng L_comp làm giảm CVR; hiệu đo được (+0,008, CVR của mô hình có L_comp cao hơn) nhỏ hơn dao động giữa seed nên không kết luận được chiều nào. Recall@10 chứa 0." Bỏ cụm "không do L_comp".

### 3.4. C6 val so với test: "trên val C6 từng có lợi" chỉ đúng với so sánh phụ, và phần lợi chủ yếu là của mặt nạ

Khoảng bootstrap C6 trên val **đã có từ trước khi chấm test** (`results/cakg/finalcheck_val_20261015_nhap1/compare_val_20261015_183304.md`, commit `e661ea1`); tính lại độc lập ra cùng số:

| C6, nhóm lắp được, Recall@10 chỉ ống | val (904 người) | test (762 người) | hiệu(val) − hiệu(test) |
|---|---|---|---|
| CaKG-Rec (mặt nạ) − **LightGCN + mặt nạ** (so sánh chính, tách tác dụng kênh phần cứng) | +0,0052 [−0,0059; +0,0170] **chứa 0** | −0,0031 [−0,0166; +0,0109] chứa 0 | +0,0082 [−0,0103; +0,0264] |
| CaKG-Rec (mặt nạ) − LightGCN (không mặt nạ) | +0,0332 [+0,0207; +0,0472] khác 0 | +0,0136 [−0,0013; +0,0280] chứa 0 | +0,0196 [+0,0009; +0,0409] |
| Riêng tác dụng mặt nạ trên LightGCN (LightGCN + mặt nạ − LightGCN) | +0,0280 | +0,0166 | |

Theo seed (CaKG − LightGCN + mặt nạ): val +0,0177 / −0,0066 / +0,0044; test −0,0092 / −0,0105 / +0,0105. Chỉ 144 người chung giữa hai nhóm.

Đọc:
- So sánh **chính** của C6 chứa 0 **cả trên val**; chênh val–test nằm trong dao động (khoảng của hiệu chứa 0).
- So sánh phụ (với LightGCN không mặt nạ) "có lợi" trên val chủ yếu vì **mặt nạ** chặn ống vi phạm (+0,028 trên val, +0,017 trên test), không phải vì kênh phần cứng. Hiệu nhỏ lại trên test chủ yếu do tác dụng của mặt nạ nhỏ lại.
- Seed 1 (seed dùng để chọn λ1 và epoch trên val) cho hiệu val lớn nhất → val lạc quan (chọn trên chính tập đó).

**Sửa câu:** không viết "trên val CaKG-Rec có lợi ở kịch bản lắp được". Viết: "Ở nhóm lắp được, CaKG-Rec ngang LightGCN + mặt nạ trên cả val và test (khoảng chứa 0); phần hơn LightGCN không mặt nạ là tác dụng của mặt nạ." STATUS "hạn chế sau dò val" điểm 6 ghi số 0,3717 / 0,3949 so với 0,3485 / 0,3772: đó là **seed 1**, cần ghi rõ.

### 3.5. C9 và FS_PN: số "0,18–0,23" không đo độ trung thực của đường giải thích

Tách FS_PN@10 theo số thân trong H của người dùng (test, mảng đã lưu):

| | s1 | s2 | s3 |
|---|---|---|---|
| cặp mà người chỉ có **1 thân** trong H (bỏ b* = đóng cổng, tắt cả kênh phần cứng) | 1.480 cặp, FS_PN 0,247 | 1.491, 0,186 | 1.489, 0,232 |
| ≥ 2 thân, không có đối chứng thân | 153, 0,444 | 128, 0,375 | 137, 0,416 |
| có đối chứng thân (C9): giải thích / đối chứng | 367, **0,057 / 0,055** | 381, **0,071 / 0,068** | 374, **0,064 / 0,062** |

- 74% cặp thuộc nhóm 1 thân: ở đó "bỏ đường giải thích" = tắt toàn bộ kênh phần cứng của người đó, nên FS_PN đo "kênh phần cứng có cần cho ống này không", **không** đo "đường u → b* → l → c* có đúng là lý do không". STATUS hạn chế 3 đã nói ý này; báo cáo không được gọi FS_PN@10 0,18–0,23 là "độ trung thực của lời giải thích".
- ΔS giải thích lớn hơn đối chứng (+0,028 đến +0,032, khoảng không chứa 0) **gần như do cách dựng**: b* là thân có h_bᵀh_l lớn nhất (công thức 24), và h_u là trung bình (công thức 7), nên bỏ b* làm h_uᵀh_l giảm nhiều nhất trong các thân. Thực tế ΔS giải thích ≥ ΔS đối chứng ở 84,5% / 92,1% / 93,9% số cặp (phần còn lại do β và RGAT chạy lại). Không được dùng ΔS làm bằng chứng trung thực.
- Bỏ c* gần như không đổi gì (đối chứng nhãn trùng giải thích, STATUS hạn chế 3): vế "phù hợp chụp {c*}" của câu giải thích không có bằng chứng là lý do của gợi ý.

**Sửa câu:** "C9 chứa 0 ở cả 3 seed: không có bằng chứng thân b* được chọn cần thiết hơn một thân phù hợp khác; vế mục đích sử dụng không ảnh hưởng điểm. Câu giải thích đúng sự kiện với đồ thị (0 lỗi) nhưng chưa chứng minh được là lý do thật của gợi ý."

### 3.6. Path Coverage: không phải ưu điểm riêng của CaKG-Rec; ablation bỏ suitable_for không được báo PC; PC 0,547 của λ1 = 0

- PC tính từ đồ thị, không từ mô hình: LightGCN + mặt nạ có PC@10 0,3933, CaKG-Rec 0,3905 (bảng test mục 4). **Không được** trình bày PC như lợi thế của CaKG-Rec; đúng hơn: "bộ giải thích dựa đường đồ thị dùng được cho mọi mô hình; điều CaKG-Rec thêm là cách chọn b* theo đóng góp vào điểm".
- **Lệch kế hoạch:** kế hoạch mục 6: "Bỏ suitable_for làm đường giải thích đủ 3 bước không còn: PC của biến thể này chỉ báo PC_ngắn". Bảng test lại báo PC@10 = 0,4219 / PC@5 cho biến thể bỏ suitable_for. Số này đếm cạnh `suitable_for` từ file CSV (`PathContext`), mà mô hình đó **không có** các cạnh này → vô nghĩa. Phải bỏ (hoặc ghi "không áp dụng") khi đưa bảng vào báo cáo. Không làm sai số khác.
- **PC@10 0,547 của λ1 = 0** (val, sau mặt nạ, người có thân) không bất thường về code; là do top-10 khác hẳn:

| val, sau mặt nạ | ống trong top-10 | đường đủ | PC | ống có `suitable_for` | số ống khác nhau | 5 ống nhiều nhất chiếm |
|---|---:|---:|---:|---:|---:|---:|
| CaKG-Rec s1 | 17.206 | 6.727 | 0,391 | 45,3% | 301 | 30,7% |
| λ1 = 0 (s1) | 29.033 | 15.858 | 0,546 | 63,6% | 732 | 17,1% |
| LightGCN s1 | 23.045 | 9.172 | 0,398 | 45,6% | 308 | 31,1% |

Không có L_comp, kênh phần cứng (chỉ học bằng BPR) gợi ý nhiều ống hơn, đa dạng hơn (732 so với 301 ống khác nhau) và nhiều ống có nhãn mục đích hơn; PC_ngắn gần như bằng nhau (0,885 so với 0,905). PC là tỉ số phụ thuộc thành phần top-10, không phản ánh chất lượng giải thích. Chưa phân tích vì sao ống được gợi ý không L_comp hay có nhãn mục đích hơn (1 seed).
- C8 PC_ngắn: biến thể bỏ suitable_for có PC_ngắn **cao hơn** (0,925 so với 0,904, khác 0). Không được đọc là "suitable_for làm giảm khả năng giải thích"; cũng do thành phần top-10 (biến thể này có 3,6 thân / top-10).

### 3.7. Bảng loại sản phẩm phải có dòng cho người có thân

Bảng mục 5 của `summary_test_*.md` tính trên mọi người dùng nên che mất mục 3.1. Khi viết chương 2, thêm bảng "top-10 người có thân" (số ở mục 3.1 (d), log b).

---

## 4. GHI CHÚ

**G1. Tuân thủ kế hoạch đăng ký trước — đạt.** Thứ tự (giờ commit / log):
1. `67b16b2` 07:56: chốt `cakg_final.toml` (λ1, lr) trước khi chạy seed 2, 3 / ablation.
2. Thử trên val `finalcheck_val_20261015_nhap1` 18:27 (cây chưa sạch, script chưa commit — được phép với `--split val`), cùng **sha256 script** `a46611b2…` và `eval_cakg` `848ed438…` với lần chạy test.
3. `e661ea1` 18:33:14: commit script chấm test, so sánh, toml có sha256 checkpoint, **và cả kết quả thử val (kèm C1–C8 trên val)**.
4. Chạy test 18:33:30 trên `e661ea1`, cây sạch (`dirty False`), một thư mục `test_final_20261015`, một log `run_test_*`.
5. `3e830aa` 18:37:55: commit kết quả test, ghi "chưa phân tích".
6. `06_test_compare` 18:38:04 (code đã commit ở `e661ea1`); `08_explain` test 18:38:37 / 18:39:32 / 18:40:28 trên `3e830aa` cây sạch; `1325f5c` 18:42; STATUS / CHANGELOG `4bb6c28` 18:43.

Không thấy lần chạy test nào khác: tìm mọi file / log có chữ "test" trong `results/cakg/` và `ai/data/survey/cakg/` (ngoài `test_final_20261015`) chỉ ra thư mục độ trễ `latency_test_20261015` (chạy sau, theo kế hoạch mục 10) và các log kiểm thử dựng tay `run_test_cakg_*`, `run_test_eval_cakg_*`; mọi script trong `ai/survey/cakg/` chỉ đọc tập val (`EvalContext("val")`, `load_pos("val")`).

Lệch nhỏ (không ảnh hưởng số):
- Kế hoạch 4.2 bước 7 ("ghi số vào CHANGELOG / STATUS và commit trước khi phân tích hay chạy thêm"): STATUS / CHANGELOG commit **sau** `06_test_compare` và `08_explain`. Hai script đó là phép đo đã đăng ký, code cố định trước test, và file kết quả test đã commit trước (`3e830aa`), nên không có chỗ "xem số rồi chỉnh".
- C9 báo 3 khoảng (mỗi seed) thay vì 1; kế hoạch không ghi seed (STATUS hạn chế 4 đã nêu). Tổng số khoảng thành 22, không phải 20.
- Kế hoạch mục 5 yêu cầu báo thứ tự mô hình theo full ranking và sampled ở K = 5, 10, 20; bảng md chỉ có K = 10. Đã tính ở log b (b4), xem mục 5.
- PC của biến thể bỏ suitable_for (mục 3.6).

**G2. sha256 code khác vì kiểu xuống dòng.** `common_05.py`, `eval_05.py` có sha256 khác nhau giữa lần chấm test 09/10 và 15/10 chỉ vì LF / CRLF (`core.autocrlf = true`); nội dung trùng blob `f21ced4`. Nên băm nội dung đã chuẩn hóa xuống dòng (hoặc băm blob git) để lần sau khỏi phải giải thích.

**G3. Val là tập chọn.** λ1, epoch tốt nhất và quy tắc dừng đều chọn trên val (seed 1), nên số val lạc quan, nhất là seed 1. Mọi so sánh val ↔ test phải nhớ điểm này.

**G4. "Kịch bản chỉ ống" không bị hiện tượng chèn thân ảnh hưởng** (ứng viên chỉ là ống), nên C6 là phép đo sạch nhất cho tác dụng kênh phần cứng lên xếp hạng ống: ở đó CaKG-Rec ngang LightGCN + mặt nạ.

**G5. KGAT** (C7, kém LightGCN rõ): lr ở biên lưới, đỉnh ở epoch 30–40; so sánh này phụ, đã có trong hạn chế. Không kiểm sâu thêm.

**G6. CaKG-Rec và LightGCN đều chạm 300 epoch** ("chưa chắc hội tụ"); không ảnh hưởng kết luận ở trên nhưng giữ trong hạn chế.

---

## 5. Khung của cô (mục 1.4, 2.6): câu nào kết quả **không** ủng hộ, câu nào được khẳng định

### 5.1. Câu kết quả không ủng hộ (phải sửa hoặc bỏ)

| Khung | Câu | Vì sao không được |
|---|---|---|
| 1.4 | "22 luật logic chính hãng được **kiểm chứng độc lập** với Lensfun và Wikidata" | STATUS (nội dung 3): số lần đo 3 "không phải số độc lập" (holdout không sạch, người viết luật cũng đọc ca sai). Viết "đối chiếu với Lensfun / Wikidata trên tập giữ lại" |
| 1.4 | "**giải quyết triệt để** hiện tượng suy giảm hiệu năng và **nhiễu quan hệ** của R-GCN" | CaKG-Rec cao hơn R-GCN rõ (C5), nhưng vẫn thấp hơn LightGCN (C1); "nhiễu quan hệ" không được đo |
| 1.4 | "học tương phản … **đảm bảo CVR → 0% mà không đánh đổi độ chính xác**" | CVR = 0 là **do mặt nạ** (cách dựng), có cả ở LightGCN + mặt nạ; L_comp không được chứng minh giảm CVR (C4, 1 seed); CaKG-Rec kém Recall / NDCG hơn LightGCN (C1, C2) — tức là có đánh đổi, và phần học (kênh phần cứng + L_comp) là phần gây ra |
| 1.4 | "độ trung thực **cao**, **triệt tiêu hoàn toàn** nguy cơ ảo giác kỹ thuật" | C9 chứa 0 ở cả 3 seed; câu giải thích chỉ "không ảo giác so với đồ thị", còn đồ thị có sai số (loại đúng 97–99%, tiêu cự đúng khoảng ~82%, nội dung 3–4) |
| 2.6 | "chứng minh CaKG-Rec **vượt LightGCN** về Recall/NDCG" | **Ngược lại**: C1 Recall@10 −0,00064 [−0,00122; −0,00003], NDCG@10 −0,00030 [−0,00059; −0,00001] |
| 2.6 | "Đưa CVR@10 về 0% trong khi **gia tăng đáng kể Recall@10** trên nhóm Lắp được" | CVR = 0 do mặt nạ; Recall@10 nhóm lắp được: so với LightGCN + mặt nạ −0,0031 [−0,0166; +0,0109], so với LightGCN +0,0136 [−0,0013; +0,0280] — **cả hai chứa 0** |
| 2.6 | Ablation "vai trò Kênh phân tách (Dual vs Single R-GCN)" theo nghĩa hai kênh tốt hơn | Hai kênh hơn R-GCN (C5) nhưng thua LightGCN một kênh (C1). Không kết luận được "hai kênh tốt hơn một kênh" |
| 2.6 | "đóng góp của L_comp" (theo nghĩa có đóng góp) | C4: Recall chứa 0, CVR ngược chiều mong đợi và nhỏ hơn dao động seed (mục 3.3); λ1 không đổi NDCG@20 val (hạn chế sau dò val 2) |
| 2.6 | "tác động của suitable_for" (theo nghĩa có tác động lên gợi ý) | C8 Recall chứa 0; bỏ c* không đổi điểm (đối chứng nhãn) |
| 2.6 | "Thực nghiệm **chứng minh** cách đo 1:99 làm sai lệch thứ tự" | Chỉ **minh họa**, không kiểm định (mục 5.2) |

### 5.2. Câu nhóm được phép khẳng định (có số, có nguồn)

1. **Mặt nạ cứng QĐ 4-9 đưa CVR@10 về 0 do cách dựng**, với mọi mô hình, mà gần như không đổi Recall@10 trên toàn bộ (LightGCN + mặt nạ 0,0449 so với LightGCN 0,0448); cái giá: 282 người "không lắp được" mất item test (Recall@10 chỉ ống = 0); bản ∃b của khung làm thêm 93 người "lắp được" mất item test. (`summary_test_*.md` mục 1, 3)
2. **CaKG-Rec cao hơn R-GCN rõ** (một kênh trộn hành vi + tri thức): Recall@10 +0,0168 [+0,0157; +0,0179], NDCG@10 +0,0101 [+0,0094; +0,0107] (C5); và cao hơn KGAT (0,0442 so với 0,0293; KGAT − LightGCN C7 −0,0156).
3. **CaKG-Rec gần LightGCN nhưng thấp hơn một chút, có ý nghĩa thống kê** (C1, C2), chủ yếu ở người có thân; nguyên nhân đo được (mục 3.1). Đây là kết quả âm cần báo trung thực, kế hoạch đã cảnh báo trước khi chạy.
4. **Ở kịch bản ống cho người có thân, nhóm lắp được, CaKG-Rec ngang LightGCN + mặt nạ** (C6 chứa 0 cả val lẫn test).
5. **Câu giải thích không chứa sự kiện ngoài đồ thị**: 0 lỗi trên 15.497 / 16.778 / 15.690 câu (kiểm tự động từng cạnh). PC@10 sau mặt nạ 0,39, PC_ngắn 0,90 (giới hạn chính: chỉ 787 / 1.033 ống của M có nhãn mục đích).
6. **Độ trung thực theo phép đo phản thực tế chưa hơn ngẫu nhiên** (C9 chứa 0) — nói thẳng, kèm cách đo.
7. **Full ranking và sampled 1+99 cho thứ tự khác nhau ở K = 20** (test, mô tả, không kiểm định): full LightGCN 0,0657 > CaKG-Rec 0,0652 > KGAT 0,0462 > R-GCN 0,0425; sampled Hit@20 R-GCN 0,6265 > KGAT 0,6238 > LightGCN 0,6161 > CaKG-Rec 0,6160. Ở K = 5, 10 thứ tự các mô hình học không đổi; sampled ép khoảng cách (CaKG − LightGCN: −0,0006 full Recall@10, −0,0012 sampled Hit@10, nhưng R-GCN − LightGCN: −0,0174 full so với −0,0097 sampled). Viết "minh họa nhận xét của Krichene & Rendle", không viết "chứng minh". (log b, b4)
8. **Chi phí tính toán**: CaKG-Rec 22,0–22,5 s / epoch, ~1,9 giờ / lần chạy, đỉnh VRAM huấn luyện 543 MiB; độ trễ một yêu cầu ở tầng mô hình GPU p50 0,81 / p95 1,19 ms, CPU p50 0,31 / p95 0,58 ms (không gồm HTTP; GTX 1660 Ti) (STATUS nội dung 7, 8).
9. **Ca thất bại có thật**: người dùng có ngàm chuyển chưa được lập chỉ mục (uid 2465, STATUS hạn chế nội dung 5 điểm 12); ống "không chắc" không chấm được.

---

## 6. Việc đề xuất (chưa làm, cần Nam quyết)

1. Sửa câu chữ trong STATUS "hạn chế sau test" theo mục 3.1–3.6 (thêm nguyên nhân C1 / C2; sửa C3, C4; C6 val; FS_PN / ΔS; PC).
2. Khi đưa bảng test vào báo cáo: bỏ PC@10 / PC@5 của biến thể bỏ suitable_for; thêm bảng top-10 người có thân; thêm bảng thứ tự full / sampled K = 5, 10, 20.
3. **Có làm thăm dò sửa hiện tượng chèn thân không?** (vd chỉ mở cổng cho ống, hoặc không chấm thân qua kênh phần cứng). Nếu làm: chỉ trên val, ghi "thăm dò sau test", không thay số chính, không chấm lại test như số khẳng định. Không làm cũng được: chỉ cần báo nguyên nhân.
4. Nội dung 6–8 **chưa nên lên "Đã đánh giá"** cho tới khi Nam đọc và quyết các mục trên (thang STATUS: "đã qua Red Team, Nam hiểu và giải thích được").
