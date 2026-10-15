# Đối chiếu khung quyển đồ án của cô (bản 11/10/2026) với repo

Ngày: 14/10/2026 · Nhánh `nam/khung-co` · Người làm: Nam (Claude hỗ trợ) · Việc **chỉ đọc**: không sửa pipeline, không sửa dữ liệu, không huấn luyện.

- **Khung:** file cô gửi khoảng 13/10/2026, để ngoài repo. Từ nay khung là hướng chính. Tài liệu này chỉ ghi số mục và tóm tắt ngắn từng ý, không chép nội dung khung.
- **Mốc so sánh:** commit `24824b9` (main) và đầu ra đã có trong `ai/data/`, `results/n5/`.
- **Script** (thư mục `ai/survey/khung/`; log ở `ai/data/survey/khung/`):

| Script | Log chính | sha256 log |
|---|---|---|
| `kiem_so_khung.py` (bước 2) | `run_kiem_so_khung_20261014_lan1.log` | `e148b5e2…74e8` |
| `khac_biet_khung.py` (bước 3a–d) | `run_khac_biet_khung_20261014_lan1.log` | `c3e19fd9…504c` |
| `sampled_va_loai_top10.py` (số phụ cho 1.2.2, 2.6) | `run_sampled_va_loai_top10_20261014_lan1.log` | `a5048a05…cbce4` |

Mỗi log chính chạy trên cây sạch, script đã commit (HEAD ghi ở dòng 2 của log). Các bản nháp (`*_nhap*.log`) cho cùng kết quả, trừ một dòng ghi chú đã sửa câu chữ; không đưa lên git.

---

## 1. Bảng đối chiếu từng ý của mục 1.1 – 2.6

Ký hiệu: **ĐÃ CÓ** (kèm file / log / commit) · **MỘT PHẦN** (thiếu gì) · **CHƯA CÓ**.

### Chương 1

| Mục | Ý trong khung (tóm tắt) | Mức | Bằng chứng / còn thiếu |
|---|---|---|---|
| 1.1 | Thiết bị có tính hệ sinh thái; tương thích cơ – quang (ngàm, khoảng cách mặt bích, khổ cảm biến, tiêu cự, khẩu độ) | MỘT PHẦN | Có ngàm, khổ, tiêu cự, khẩu độ (`mount_rules.toml`, `lens_specs.py`, đồ thị). **Không có khoảng cách mặt bích** (không có trong dữ liệu hay luật) |
| 1.1 | Nhu cầu chia theo thể loại chụp; người mới dễ mua ống không lắp vừa thân | MỘT PHẦN | 4 nhãn mục đích (`usecase_rules.toml` v0.3). "Mua nhầm" chưa có số; chỉ biết 282/1.060 người trong kịch bản test có ống test không lắp được thân đã đánh giá. Đó có thể là mua chéo hệ, không chắc là mua nhầm |
| 1.1 | CF / LightGCN "mù ràng buộc", vi phạm ~13% | ĐÃ CÓ | CVR@10 LightGCN 12,97% ± 0,11 (mục 2, bảng số 15) |
| 1.1 | R-GCN: nhiễu quan hệ, oversmoothing, Recall giảm, CVR ~40% | MỘT PHẦN | Có số: Recall giảm (S2), CVR@10 40,38% ± 10,90. **Chưa đo nguyên nhân** "nhiễu quan hệ / oversmoothing" (mục 3e) |
| 1.1 | Bộ lọc quy tắc tĩnh triệt tiêu vi phạm nhưng mất cá nhân hóa, bỏ người mua chéo hệ | MỘT PHẦN | Có MountAware; S5: nhóm "không lắp được" Recall@10 giảm 0,039. Nhưng MountAware đặt lên Popularity, vốn đã không cá nhân hóa, nên câu "mất cá nhân hóa" chưa có số đo |
| 1.1 | Hộp đen, thiếu giải thích | CHƯA CÓ | Nội dung 8 chưa bắt đầu |
| 1.2.1 | Đầu vào: đồ thị G = (V, E, R) với 4 tập nút, 6 tên quan hệ | ĐÃ CÓ | `kg_hetero.pt`, 7 loại nút, 6 tên quan hệ (log bước 2, mục 5). Khung tách I thành body / lens / acc; đồ thị có thêm loại **"khac"** (máy ống liền…, 1.757 sản phẩm) |
| 1.2.1 | M nhị phân và mặt nạ bất định U | ĐÃ CÓ | `compatibility_matrix.npz`, `unknown_mask.npz` (537 × 1.033) |
| 1.2.1 | Lịch sử H_u xếp theo thời gian | ĐÃ CÓ | `camera_interactions_k5.csv` có timestamp; script 02 chia theo thời gian |
| 1.2.1 | Hai kênh biểu diễn e (hành vi) và h (phần cứng) | CHƯA CÓ | Chỉ có LightGCN (một kênh) và R-GCN (gộp) |
| 1.2.1 | L_comp (InfoNCE theo M) | CHƯA CÓ | Quét repo: 0 file (log bước 3, mục d) |
| 1.2.1 | Mặt nạ −∞ khi ∃ b ∈ H_u có M = 0 ∧ U = 0 | MỘT PHẦN | Có mặt nạ cho MountAware nhưng theo **QĐ 4-9**, khác công thức khung (mục 3a) |
| 1.2.1 | Truy vết metapath để giải thích | CHƯA CÓ | 0 file có "metapath" |
| 1.2.1 | Đầu ra: top-K với Recall, NDCG và CVR → 0 | MỘT PHẦN | Có top-K và chỉ số cho 4 baseline. CVR = 0 mới có ở MountAware, và là do cách dựng (STATUS, hạn chế nội dung 5, điểm 6) |
| 1.2.1 | Chuỗi u → b → mount → l → spec → c | CHƯA CÓ | Đồ thị **không có** cạnh spec → usecase, và không có quan hệ "owns" (mục 3b) |
| 1.2.2 | Mất cân đối: phụ kiện 86,98%, tương tác thân – ống 8,48% | ĐÃ CÓ | Khớp (mục 2, bảng số 1–2). Phải ghi rõ 8,48% là tương tác với thân / ống **thuộc M**; với mọi thân / ống là 10,40%. Top-10 của LightGCN trung bình có 7,99 phụ kiện (`run_sampled_va_loai_top10…`) |
| 1.2.2 | Đánh đổi độ chính xác – CVR | MỘT PHẦN | Có số baseline (S3, S5). Chưa có mô hình đề xuất |
| 1.2.2 | Giải thích phải trung thực, không ảo giác | CHƯA CÓ | |
| 1.3 | Tổng quan: NGCF, LightGCN, UltraGCN | MỘT PHẦN | LightGCN có trong kế hoạch n5 và báo cáo 1–5; NGCF / UltraGCN chỉ được nhắc trong `n5_eval_plan.md`; chưa có phần tổng quan |
| 1.3 | Tổng quan: CKE, R-GCN, KGAT, KGIN | MỘT PHẦN | R-GCN có (bài gốc, kế hoạch n5). CKE chỉ có trong tài liệu cũ đã lỗi thời. KGAT, KGIN chưa có |
| 1.3 | Tổng quan: gợi ý có ràng buộc, gợi ý theo gói, neuro-symbolic | CHƯA CÓ | |
| 1.3 | Tổng quan: XAI trong RecSys (PGPR, CAFE, Faithfulness, Path Coverage) | CHƯA CÓ | 0 file nhắc PGPR / CAFE |
| 1.4 | Đóng góp 1: bộ dữ liệu sạch + M 537 × 1.033 + 22 luật hãng, kiểm độc lập bằng Lensfun / Wikidata | MỘT PHẦN | Số khớp. Ba câu chưa đúng: không phải cả 22 luật đều theo tài liệu hãng; phép đo **không độc lập** (STATUS, hạn chế nội dung 3, điểm 10); chưa "đóng gói" bộ dữ liệu (dữ liệu gốc và `train.txt` không lên git). Xem mục 2, bảng số 9 và mục 3e |
| 1.4 | Đóng góp 2: mô hình hai kênh CaKG-Rec | CHƯA CÓ | 0 file nhắc "CaKG" |
| 1.4 | Đóng góp 3: học tương phản + lớp chiếu cứng, CVR → 0 mà không mất độ chính xác | CHƯA CÓ | Mới có lớp chiếu cứng cho Popularity (MountAware) |
| 1.4 | Đóng góp 4: động cơ giải thích theo metapath | CHƯA CÓ | |

### Chương 2

| Mục | Ý trong khung (tóm tắt) | Mức | Bằng chứng / còn thiếu |
|---|---|---|---|
| 2.1 | Sơ đồ end-to-end, vẽ bằng công cụ vector | MỘT PHẦN | Đã có hình pipeline nội dung 2–5 (`ai/survey/report/hinh_pipeline.py`, vẽ bằng script, PNG), chưa có các khối của CaKG-Rec. Cô yêu cầu Visio / TikZ / draw.io |
| 2.1 | Mỗi module có công thức tự soạn, đánh số | CHƯA CÓ | Làm khi viết chương 2 |
| 2.2 | Lọc lĩnh vực, gộp lặp, bỏ đánh giá lại, k-core k = 5 hội tụ sau 14 vòng | ĐÃ CÓ | `01_filter_camera_domain.py`, `run01_fix.log`; số khớp (mục 2, bảng số 3–7). Gộp lặp: bỏ 45.684 bản sao y hệt + 5.515 đánh giá lại, mỗi cặp (người, sản phẩm) giữ dòng sớm nhất (`filtering_stats.json`) |
| 2.2 | Chia theo thời gian, train 460.193 / val / test 67.661, không rò rỉ | ĐÃ CÓ | `02_split_time_aware.py`; rò rỉ 0 / 0 / 0 (log bước 2, mục 2) |
| 2.2 | LightGCN backbone (công thức lan truyền) | ĐÃ CÓ | `05b_lightgcn_train.py`, số test 09/10. Khung dùng K cho cả số lớp lẫn top-K, nên đổi ký hiệu số lớp (vd L) |
| 2.3 | 7 loại nút (95.646), 18 loại quan hệ hai chiều (1.116.950 cạnh) | ĐÃ CÓ | Khớp. Thực tế là 9 loại cạnh xuôi + 9 loại cạnh ngược; theo tên chỉ có 6 quan hệ |
| 2.3 | Ngàm 23, khổ 7, tiêu cự 6, khẩu độ 5, mục đích 4 (quy đổi theo hệ số crop) | ĐÃ CÓ | Khớp. Hệ số crop lấy theo **khổ ống** chứ không theo thân người dùng (STATUS, hạn chế nội dung 4, điểm 2); hệ số ngoài 1,0 chưa có câu trích kiểm bằng script (điểm 18) |
| 2.3 | Trích xuất bằng quy tắc, thay Sentence-Transformers; phân loại 97,8%, ngàm 97,2% | ĐÃ CÓ | Khớp, có kèm lưu ý (mục 2, bảng số 10). Bản của Hải dùng Sentence-Transformers (`03_entity_linking_matrix.py`, tầng 3); bản mới `03_mount_compat.py` chỉ dùng quy tắc |
| 2.3 | 22 luật theo tài liệu hãng (Canon, Nikon, Sony, Pentax, Olympus) | MỘT PHẦN | Có 22 luật. Chỉ 16 luật có căn cứ đã đọc trang; nguồn còn có Sigma và Fujifilm (mục 2, bảng số 9) |
| 2.3 | 4 cấp độ + unknown: 70.472 / 2.248 / 16.301 / 459.854 / 5.846 | ĐÃ CÓ | Khớp, rời nhau, tổng 554.721 (mục 2, bảng số 12). Thực tế là 5 mức; `requires_adapter` là M = 0 |
| 2.3 | RGAT trên đồ thị con phần cứng | CHƯA CÓ | 0 file có RGAT / GATConv. Độ phủ của kênh này: mục 3c |
| 2.4 | Gộp hai kênh bằng attention | CHƯA CÓ | |
| 2.4 | L_comp (InfoNCE) | CHƯA CÓ | |
| 2.4 | L_total = BPR + λ1 L_comp + λ2 ‖Θ‖² | MỘT PHẦN | BPR + L2 có ở LightGCN / R-GCN; L_comp chưa có |
| 2.4 | Mặt nạ cứng lúc suy luận, CVR = 0% | MỘT PHẦN | Có ở MountAware (`eval_05.certain_violation_mask`), theo QĐ 4-9 (mục 3a) |
| 2.4 | Đường giải thích u –owns→ b –compatible_with→ l –suitable_for→ c | CHƯA CÓ | Không có "owns" (mục 3b) |
| 2.4 | Chuyển đường giải thích thành câu văn | CHƯA CÓ | |
| 2.5 | Dữ liệu: 67.661 người, 27.940 sản phẩm | ĐÃ CÓ | Khớp |
| 2.5 | Kịch bản: 10.406 người có thân; 1.060 = 762 lắp được + 282 không lắp được | ĐÃ CÓ | Khớp; còn **16 người "không phán được"** mà khung không nêu (762 + 282 + 16 = 1.060) |
| 2.5 | Recall, NDCG, Hit @ 5/10/20, full ranking | ĐÃ CÓ | `eval_05.K_LIST = [5, 10, 20]`; số test có cả `hit@5` |
| 2.5 | CVR_strict@K | ĐÃ CÓ | CVR theo QĐ 4-9 (`eval_05.cvr_from_top`) |
| 2.5 | CVR_relaxed@K (tính cả adapter người dùng có) | CHƯA CÓ | Mới có số đếm thăm dò (`ai/survey/report/c5_checks.py`: 637 người có ngàm chuyển dạng a>b); chưa có độ đo |
| 2.5 | Path Coverage, Faithfulness | CHƯA CÓ | 0 file |
| 2.5 | Bootstrap ghép cặp theo người dùng, 2.000 lần, khoảng 95% | ĐÃ CÓ | B = 2.000, seed 20261009 (`n5_final.toml`, summary test). Chỉ làm ở **K = 10** cho S1–S5 |
| 2.5 | Baseline Popularity, Popularity-MountAware | ĐÃ CÓ | `05a_popularity.py`, số test 09/10 |
| 2.5 | LightGCN | ĐÃ CÓ | |
| 2.5 | R-GCN (DistMult, BPR) | ĐÃ CÓ | `05c_rgcn_train.py`: `RGCNConv`, giải mã DistMult, loss BPR |
| 2.5 | KGAT | CHƯA CÓ | Chỉ được nhắc trong STATUS / roadmap |
| 2.6 | CaKG-Rec so với baseline, vượt LightGCN | CHƯA CÓ | Mới có số 4 baseline |
| 2.6 | Kịch bản người có thân: CVR@10 = 0, Recall@10 nhóm lắp được tăng | MỘT PHẦN | Có số baseline cho kịch bản (S5); chưa có mô hình đề xuất |
| 2.6 | Full ranking so với sampled 1+99 | MỘT PHẦN | Có số cả hai cách. Thứ tự LightGCN / R-GCN **chỉ đảo ở K = 20** (sampled: R-GCN 0,6265 > LightGCN 0,6161; full ranking ngược lại); ở K = 5 và 10 giữ nguyên. Popularity / MountAware đổi chỗ ở mọi K nhưng chỉ lệch ở chữ số thứ 4 (`run_sampled_va_loai_top10…`). Chưa làm kiểm định |
| 2.6 | Ablation: hai kênh / một kênh, L_comp, mặt nạ M, cạnh suitable_for | CHƯA CÓ | |
| 2.6 | Cây suy luận mẫu (vd người dùng Canon EOS M) | MỘT PHẦN | Có ví dụ thật uid 2465 (EOS M + ngàm chuyển; STATUS, hạn chế nội dung 5, điểm 12); chưa có cây suy luận |
| 2.6 | Ca thất bại: ống hãng thứ ba không rõ biến thể, ngàm chuyển chưa lập chỉ mục | MỘT PHẦN | Đã đếm 134 ống "không chắc" và ngàm chuyển bị bỏ sót (hạn chế nội dung 3, điểm 7; nội dung 5, điểm 12). Chưa phân tích theo mô hình đề xuất |
| 2.6 | Thời gian / epoch, VRAM đỉnh, độ trễ suy luận | MỘT PHẦN | Có thời gian / epoch (`median_sec_per_epoch` trong `result.json`, LightGCN 13,7 s). VRAM chỉ đo bằng trọng số ngẫu nhiên (`run_probe_gpu_20261009_lan1.log`, đỉnh ≤ 1.576 MiB); **chưa đo VRAM khi huấn luyện thật**; **chưa đo độ trễ cho một yêu cầu**, mới có thời gian chấm cả lô (0,55–0,82 s cho 67.661 người) |
| 2.7 | Tổng kết | — | Không có nội dung trong khung |

---

## 2. Kiểm từng con số trong khung

Nguồn: `run_kiem_so_khung_20261014_lan1.log` (trừ dòng có ghi nguồn khác). Kết quả: **không số nào lệch**. Một số câu cần ghi lại cho đúng nghĩa (cột "Lưu ý").

| # | Số trong khung | Tính lại | Kết quả | Lưu ý |
|---|---|---|---|---|
| 1 | Phụ kiện 86,98% | 24.301 / 27.940 = 86,98% | Khớp | |
| 2 | Tương tác thân – ống 8,48% | 50.503 / 595.515 = 8,48% | Khớp | Chỉ đúng với thân / ống **thuộc M** (537 + 1.033). Với mọi thân / ống: 61.960 = 10,40% |
| 3 | 67.661 người dùng | 67.661 | Khớp | |
| 4 | 27.940 sản phẩm | 27.940 | Khớp | |
| 5 | 595.515 tương tác | 595.515 | Khớp | train + val + test = 595.515 |
| 6 | Train 460.193; val / test 67.661 | 460.193; 67.661; 67.661 | Khớp | Rò rỉ val = test, test ∈ train, val ∈ train đều 0 |
| 7 | k-core hội tụ sau 14 vòng | 14 dòng "Vòng" trong `run01_fix.log` | Khớp | Vòng 14 không đổi gì (vòng xác nhận) |
| 8 | M 537 × 1.033 | 537 × 1.033 | Khớp | |
| 9 | 22 luật; hãng Canon, Nikon, Sony, Pentax, Olympus | 22 `[[rule]]` (v0.5) | Khớp số; **thiếu hãng** | Theo mức kiểm chứng: 16 `da_doc_trang`, 2 `dinh_nghia` (cùng ngàm), 4 `quyet_dinh_nhom`. 9 luật có `suy_rong` (11 mục). Nguồn căn cứ còn có **Sigma** (2 luật) và **Fujifilm** (luật `leica_m_on_fuji_x_adapter`). Câu "22 luật logic chính hãng" chưa đúng |
| 10 | Phân loại 97,8%, ngàm 97,2% | 585/598 = 97,8%; 383/394 = 97,2% (tính lại từ `holdout_lan2_20261008.csv`, H733) | Khớp | 97,8% là phân loại **theo sản phẩm**; theo nguồn là 99,1% (Lensfun) và 97,1% (Wikidata). 97,2% là ngàm theo Lensfun; Wikidata 266/266. Tập đo là sản phẩm khớp được **tên** với Lensfun / Wikidata / openMVG, không phải "tập có bằng chứng text rõ ràng"; holdout không sạch |
| 11 | 95.646 nút; 7 loại; 23 / 7 / 6 / 5 / 4 | 95.646; 7; 23 / 7 / 6 / 5 / 4 | Khớp | Đọc từ `kg_hetero.pt` |
| 11b | 18 quan hệ hai chiều; 1.116.950 cạnh | 18 loại cạnh; 1.116.950 | Khớp | 18 = 9 xuôi + 9 `rev_`; 6 tên quan hệ; cạnh xuôi 558.475 |
| 12 | 70.472 / 2.248 / 16.301 / 459.854 / 5.846 | Giống hệt | Khớp, **rời nhau**, tổng = 554.721 = 537 × 1.033 | 94.867 cặp có ghi mức trong `compat_pairs.csv` (bỏ ống "không chắc"), không cặp nào lặp; cặp không ghi = incompatible. Đối chiếu từng ô: M = 1 ⇔ compatible_with / crops_sensor lệch 0 ô; U = 1 ⇔ unknown lệch 0 ô; M ∧ U = 0. Trùng `mount_compat_stats.json` |
| 13 | 10.406 người có thân | 10.406 | Khớp | Người có ít nhất 1 thân trong train |
| 14 | 1.060 / 762 / 282 | 1.060 / 762 / 282 | Khớp | Thêm 16 người "không phán được"; 11 người nhóm 282 có cặp requires_adapter |
| 15 | CVR@10 LightGCN ~13%, R-GCN ~40% | 12,97% ± 0,11 (seed: 12,85 / 13,07 / 12,99); 40,38% ± 10,90 (seed: 46,39 / 46,95 / 27,80) | Khớp (xấp xỉ) | Tính lại từ mảng từng người (sha256 khớp `result.json`). CVR là tỉ lệ trên **ống chấm được** trong top-10 của người có thân, không phải trên mọi gợi ý. R-GCN dao động mạnh theo seed: "~40%" che mất khoảng 28–47% |
| 16 | eval_05 có K = 5 | `K_LIST = [5, 10, 20]`; summary có recall / ndcg / hit @5 | Có | Hit@K = Recall@K vì mỗi người có 1 item test |
| 17 | Bootstrap 2.000 lần | B = 2.000, seed 20261009, ghép cặp theo người dùng | Khớp | Chỉ ở K = 10 (S1–S5); K = 5, 20 chỉ có số điểm |

---

## 3. Chỗ khung khác code hoặc QĐ hiện tại

Nguồn số: `run_khac_biet_khung_20261014_lan1.log`, trừ chỗ ghi khác.

### (a) Công thức mặt nạ cứng: khung khác QĐ 4-9

**Ví dụ thật (uid 378).** Trong train, người này có hai thân thuộc hai hệ máy:
- Sony a7 (ngàm `sony_e`, FF);
- Nikon D750 (ngàm `nikon_f`, FF).

Item test là ống **Nikon AF-S 200-500mm f/5.6E** (`nikon_f`), tức người này mua ống cho chiếc D750.
- Cặp (D750, ống) là `compatible_with`; cặp (a7, ống) là `incompatible`.
- **Khung:** có một thân (a7) với M = 0 và U = 0, nên ống bị gán −∞. Ống người dùng thực sự mua không bao giờ vào top-K.
- **QĐ 4-9 (code hiện tại):** có một thân lắp được (D750), nên ống không bị chặn và không tính vi phạm.

Ví dụ khác cùng log: uid 258 có EOS M3 (`canon_efm`) và EOS RP (`canon_rf`), item test là ống RF 16mm F2.8: khung chặn, QĐ 4-9 không chặn.

**Hai cách định nghĩa "bị chặn":**
- Khung: ống l bị chặn khi **tồn tại một** thân b có M[b,l] = 0 và U[b,l] = 0.
- QĐ 4-9: chỉ chặn khi **mọi** thân đều có M = 0 và không cặp nào "không biết".

**Đếm trên dữ liệu thật** (thân ngoài M không có hàng trong M, cả hai cách đều bỏ qua):

| Đếm | QĐ 4-9 | Khung |
|---|---:|---:|
| Cặp (người có thân, ống trong M) bị chặn, trên 10.749.398 cặp | 8.557.447 | 8.904.038 (+346.591) |
| Người có ít nhất 1 ống bị chặn | 10.335 | 10.359 |
| Người có tập ống bị chặn khác nhau giữa hai cách | — | **1.107** |
| Kịch bản test, nhóm "lắp được" (762): item test bị chặn | 0 | **93** |
| Kịch bản test, nhóm "không lắp được" (282): item test bị chặn | 282 | 282 |
| Kịch bản test, nhóm "không phán được" (16): item test bị chặn | 0 | 3 |
| **Tổng người mất item test vì mặt nạ** | 282 | **378** (+96) |
| Top-10 của LightGCN seed 1 (23.555 ống trong M, người có thân): ống bị chặn | 3.003 | 5.269 (+2.266) |

- Có 1.090 người sở hữu thân thuộc từ 2 ngàm trở lên. Công thức của khung phạt đúng nhóm người dùng nhiều hệ máy mà mục 1.1 nói cần giữ lại.
- Với mặt nạ của khung, câu "CVR = 0 mà Recall@10 nhóm lắp được tăng" (mục 2.6) khó đạt: 93/762 người (12,2%) nhóm này có Recall@K = 0 với mọi mô hình.
- **Cần Nam chốt:** viết lại công thức khung theo QĐ 4-9 (đề xuất), hay đổi QĐ.

### (b) Quan hệ "owns" không có trong đồ thị

- `kg_hetero.pt` có 6 tên quan hệ (cùng các bản `rev_`), **không có `owns`**.
- Quan hệ gần nhất là cạnh `('user', 'interacted_with', 'item')` tới sản phẩm loại thân: 13.495 cạnh của 10.406 người. Cạnh này nghĩa là người dùng **có viết đánh giá** sản phẩm trong train (QĐ 3-5), không xác nhận đang sở hữu. Gọi là "owns" trong luận văn thì phải nói rõ là suy ra, hoặc đổi tên thành "đã đánh giá thân".
- Đường ở 1.2.1 (u → b → mount → l → spec → c) **không đi được** trên đồ thị hiện tại: chỉ nút `item` có cạnh tới `usecase` (`suitable_for`). Nút thông số (tiêu cự, khẩu độ, khổ) không nối tới mục đích.
- Đường ở 2.4 (u → b –compatible_with→ l –suitable_for→ c) đi được. Đếm thô trên nhóm "lắp được" (762):
  - 755 người có thân nối với item test bằng `compatible_with`; 7 người chỉ nối bằng `crops_sensor`. Đường của khung chưa tính `crops_sensor`.
  - **525 người** có đủ đường tới một nút mục đích. Chỉ 787/1.033 ống trong M có nhãn `suitable_for`.
  - Đây chỉ là trần thô, **chưa phải độ đo Path Coverage**.

### (c) Kênh phần cứng (RGAT trên Body – Mount – Lens – Sensor Format)

Định nghĩa dùng để đếm: sản phẩm có ít nhất một cạnh `compatible_with`, `crops_sensor`, `requires_adapter`, `has_spec → mount` hoặc `has_spec → sensor_format`.

| Nhóm sản phẩm | Số sản phẩm | Item test (67.661) | Tương tác train (460.193) |
|---|---:|---:|---:|
| Thân có cạnh phần cứng | 537 | 1.443 (2,13%) | 13.424 (2,92%) |
| Ống có cạnh phần cứng (kể cả 134 ống "không chắc", chỉ có cạnh ngàm gắn cờ) | 1.167 | 4.206 (6,22%) | 32.589 (7,08%) |
| Phụ kiện chỉ có `has_spec → mount` (hood, ngàm chuyển…) | 1.109 | 2.767 (4,09%) | 20.338 (4,42%) |
| Ống chỉ có cạnh tiêu cự / khẩu độ / mục đích, không có cạnh ngàm | 161 | 393 (0,58%) | 2.988 (0,65%) |
| Phụ kiện không có cạnh tri thức | 23.192 | 55.343 (81,79%) | 366.425 (79,62%) |
| "Khác" (máy ống liền…) không có cạnh | 1.757 | 3.485 (5,15%) | 24.060 (5,23%) |
| Ống không có cạnh tri thức | 11 | 19 (0,03%) | 298 (0,06%) |
| Thân ngoài M, không có cạnh | 6 | 5 (0,01%) | 71 (0,02%) |

- Kênh phần cứng có biểu diễn cho **1.704 thân / ống** (6,1% catalog). Nếu đưa cả phụ kiện có cạnh ngàm vào thì thêm 1.109.
- **8,35%** item test (1.443 + 4.206 = 5.649) thuộc thân / ống có cạnh phần cứng.
- **86,98%** item test (55.343 + 3.485 + 19 + 5 = 58.852) không có cạnh tri thức nào. Với các item này, kênh phần cứng không có gì để học; gộp hai kênh phải có cách xử lý (vd véc-tơ rỗng, hoặc chỉ dùng kênh hành vi).
- Có 2.974 sản phẩm có ít nhất một cạnh tri thức bất kỳ, khớp STATUS.

### (d) Khung cần, repo chưa có

Quét repo (bỏ `.venv`, `data`, `results`), log mục (d):

| Thứ cần | Tình trạng |
|---|---|
| KGAT (baseline 2.5) | **Chưa có code**; chỉ được nhắc trong STATUS / roadmap |
| CVR_relaxed (tính ngàm chuyển người dùng đã có) | **Chưa có độ đo**. Đã có số đếm thăm dò `c5_checks.py`: 637 người có ngàm chuyển a>b, ống vi phạm lắp được qua ngàm chuyển < 2,3% ở mọi mô hình (cận dưới, STATUS hạn chế nội dung 5, điểm 12). Phải định nghĩa: ngàm chuyển một ngàm như "Canon EOS M Mount Adapter" (uid 2465) chưa được nhận diện là ngàm chuyển |
| Hit@5 | **Đã có** (`eval_05.K_LIST`, summary test có `hit@5`). Không phải việc mới |
| Path Coverage | Chưa có (0 file); trần thô ở mục (b) |
| Faithfulness | Chưa có (0 file); cần định nghĩa đo được (vd bỏ cạnh trên đường giải thích rồi xem điểm / hạng tụt bao nhiêu) |
| Độ trễ suy luận | Chưa có cho một yêu cầu; mới có thời gian chấm cả lô (probe) |
| VRAM đỉnh | Chỉ có probe với trọng số ngẫu nhiên; `result.json` huấn luyện không ghi bộ nhớ GPU |
| RGAT, L_comp, fusion, metapath, CaKG-Rec | Chưa có (0 file mỗi từ khoá) |

### (e) Câu khẳng định kết quả mà chưa có số đo

| Mục | Câu (tóm tắt) | Thực tế |
|---|---|---|
| 1.1 | R-GCN kém do nhiễu quan hệ / oversmoothing | Chưa đo (vd độ tương tự trung bình giữa các nút theo lớp, hay ablation bỏ từng quan hệ). STATUS hạn chế nội dung 5, điểm 3: "R-GCN kém LightGCN" chỉ đúng cho cài đặt này (d = 64, lr ở biên lưới, bỏ qua cờ cạnh) |
| 1.1 | Bộ lọc quy tắc làm mất cá nhân hóa | Popularity vốn không cá nhân hóa. Cái giá đo được: nhóm "không lắp được" Recall@10 = 0 (S5: −0,039) |
| 1.2.1, 1.4, 2.4 | CVR → 0 mà không đánh đổi Recall / NDCG | Chưa có mô hình. CVR = 0 là do cách dựng mặt nạ, không phải kết quả học. Mặt nạ (QĐ 4-9) chắc chắn làm 282 người kịch bản mất item test; theo công thức khung là 378 |
| 1.4 | "Giải quyết triệt để" sự suy giảm của R-GCN; CaKG-Rec vượt LightGCN (2.6) | Chưa có mô hình |
| 1.4 | M dựa trên 22 luật chính hãng, kiểm chứng độc lập với Lensfun / Wikidata | 6/22 luật không theo trang hãng; số đo không độc lập (hạn chế nội dung 3, điểm 10) |
| 1.2.2, 1.4 | Giải thích trung thực cao, triệt tiêu hoàn toàn ảo giác | Chưa có độ đo Faithfulness |
| 2.3 | RGAT "cô lập hoàn toàn" nhiễu hành vi | Là thiết kế, chưa có số |
| 2.3 | 97,8% / 97,2% "trên tập kiểm tra có bằng chứng text rõ ràng" | Tập đo là sản phẩm khớp tên với nguồn ngoài; holdout không sạch (hạn chế nội dung 3, điểm 1, 2, 10) |
| 2.6 | Sampled 1:99 "làm sai lệch thứ tự" các mô hình | Mới thấy đảo LightGCN / R-GCN ở K = 20; K = 5 và 10 giữ thứ tự. Chưa có kiểm định |
| 2.6 | CVR@10 = 0 và Recall@10 nhóm lắp được "gia tăng đáng kể" | Chưa có mô hình; với baseline, MountAware tăng +0,049 so với Popularity ở nhóm lắp được (S5) |

### Khác nhỏ cần sửa câu chữ khi viết

- "18 loại quan hệ" nên ghi rõ là 9 quan hệ, mỗi quan hệ có cạnh ngược; theo tên chỉ có 6.
- "4 cấp độ tương thích + unknown" nên ghi là 5 mức. `requires_adapter` là M = 0, không phải "tương thích".
- Tập I của khung chỉ có body / lens / acc; đồ thị có thêm loại "khác" (máy ống liền, 1.757 sản phẩm).
- Công thức LightGCN dùng K cho số lớp, trùng với K của top-K.
- Kịch bản có thêm 16 người "không phán được".
- Tên "MountAware" trong khung là "Popularity-MountAware", khớp code.

---

## 4. Ba việc lớn nhất phải làm tiếp (đề xuất, chờ Nam chốt)

1. **Chốt định nghĩa trước khi viết chương 2.** Gồm công thức mặt nạ (QĐ 4-9 hay khung), CVR_relaxed (ngàm chuyển nào được tính), "owns", đường giải thích. Rồi báo cô các chỗ trong khung cần sửa (mục 3a, 3b, bảng số 9 và 10 ở mục 2, các câu ở 3e) trước khi viết.
2. **Cài phần còn thiếu của mô hình đề xuất và baseline:** mô hình hai kênh (RGAT trên 1.704 thân / ống, kèm cách xử lý 87% item không có cạnh tri thức), L_comp, gộp kênh, mặt nạ cứng; thêm KGAT; ghi VRAM đỉnh và độ trễ trong lúc huấn luyện / suy luận thật. Đăng ký kế hoạch đánh giá trước, như đã làm ở nội dung 5.
3. **Độ đo và động cơ giải thích:** định nghĩa đo được cho Path Coverage và Faithfulness; thêm nhánh `crops_sensor` vào đường giải thích; cân nhắc mở rộng nhãn `suitable_for` (hiện 787/1.033 ống trong M có nhãn).

Song song: viết chương 1 (tổng quan 1.3 còn thiếu gần hết: KGAT, KGIN, CKE, PGPR, CAFE, gợi ý có ràng buộc) theo lời cô "xong ổn chương 1, chương 2 mới đi tiếp chương 3".
