# TRẠNG THÁI ĐỒ ÁN — Camera Recommender

Cập nhật lần cuối: 07/10/2026 (khảo sát nội dung 3, nhánh `nam/content3`) · Người cập nhật: Nam (Claude hỗ trợ kiểm định)

> File này là nguồn sự thật về trạng thái dự án. Khi file này mâu thuẫn với trí nhớ của một cuộc chat, tin file này.
> Mỗi khi có thay đổi quan trọng, cập nhật file rồi thay bản mới vào Project.

## 1. Thông tin chung

- **Tên đề tài (đã được GVHD chốt 17/09/2026):** Xây dựng hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh trong thương mại điện tử bằng mô hình gợi ý lai có ràng buộc và giải thích được
- **GVHD:** TS. Đỗ Thị Liên
- **Nhóm:** Trần Phương Nam (nhóm trưởng, phải nắm toàn bộ), Nguyễn Hồng Hải (Data/AI), Lò Văn Quyền (Frontend)
- **Lộ trình chính thức:** mail của cô ngày 22/09/2026, gồm 10 nội dung. Cô yêu cầu nộp nội dung 1–5 trong 1–2 tuần, kèm báo cáo chi tiết pipeline, công thức, ví dụ minh họa từng bước, code đẩy lên GitHub. Cô dặn: làm đến đâu phải hiểu đến đó, không lạm dụng AI mà không hiểu.
- **Lưu ý:** bản đề xuất ngày 16/09 (Spring Boot, chấm điểm theo quy tắc, không học sâu) **không còn là hướng chính**. Chỉ tham khảo phần kiến thức tương thích thiết bị và cách ghi nguồn dữ liệu.
- **Dữ liệu:** Amazon Reviews 2023, nhóm Electronics (https://amazon-reviews-2023.github.io/)
- **Repo:** bản cuối của Hải là commit `62abf54a` (28/09/2026)
- **Máy chạy:** Windows 11, GTX 1660 Ti 6 GB (CUDA 12.6), RAM 16 GB, Python 3.12.10. Dự án và dữ liệu đặt ở ổ E.

## 2. Thang trạng thái

Mỗi nội dung chỉ được ghi một mức khi có bằng chứng tương ứng:

- **Kế hoạch:** mới có ý tưởng hoặc tài liệu mô tả
- **Đã triển khai:** có code đã commit
- **Đã kiểm thử:** đã chạy lại được, có log hoặc kết quả kiểm tra
- **Đã đánh giá:** có số liệu cuối, đã qua Red Team, Nam hiểu và giải thích được

## 3. Trạng thái 10 nội dung

| # | Nội dung | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Pipeline tổng quát | Đã triển khai (tài liệu) | Cần cập nhật sau khi sửa nội dung 3 và 5 |
| 2 | Thu thập, lọc k-core, chia train/val/test | **Đã kiểm thử** (07/10) | Nhánh `nam/fix-data`: đã gộp tương tác lặp, số mới 67.661 users / 27.940 items / 595.515 tương tác. Báo cáo 2 chưa cập nhật theo số mới. Xem mục 4 và `docs/CHANGELOG.md` |
| 3 | Entity Linking, ma trận M | **Đã kiểm thử** (07/10, bản mới) | Độ phủ chỉ 8,9%. **Đã khảo sát dữ liệu cho thiết kế mới (07/10)**, xem `docs/content3_survey.md`. **Bản mới đã ghi vào `ai/data/kg/`** (bản cũ sao lưu ở `kg_v62abf54/`): 482 thân × 886 ống, 56.276 cặp M = 1 (1.638 cặp có cờ "chưa rõ có cắt khung"), 1.836 cặp "không biết".

Đối chiếu nguồn ngoài (`eval_external.py`):
- ngàm đúng 98,1% (Lensfun, 685 sản phẩm) và 100% (Wikidata, 450); 13 ca lệch đều do đáp án hoặc bước khớp;
- khung thân đúng 100% (Lensfun, 351) và 99,5% (openMVG, 215);
- **loại chỉ đúng 87,8% / 83,3%**: ống và thân bị Amazon xếp sai danh mục nên quy tắc xếp thành phụ kiện / khác.

Chưa sửa lỗi loại. Script 04/05 chưa đọc đầu ra mới. **Phải chạy lại trên dữ liệu mới** (mã item đã đổi) |
| 4 | Đồ thị tri thức | Đã triển khai, **cần làm lại sau nội dung 3** | 99% sản phẩm không có cạnh tri thức. **Phải chạy lại trên dữ liệu mới** |
| 5 | Baselines và đo lường | Đã triển khai, **có lỗi phải sửa** | Xem mục 4. `N_USERS`/`N_ITEMS` nay đọc từ `user_map.json`/`item_map.json` (07/10, nhánh `nam/content3`) |
| 6 | Module ràng buộc cứng và mềm | Chưa bắt đầu | |
| 7 | Mô hình gợi ý theo bộ (GNN có quan hệ) | Chưa bắt đầu | |
| 8 | Giải thích (path-based) | Chưa bắt đầu | |
| 9 | Ablation, khảo sát người dùng | Chưa bắt đầu | Cần tìm 20–30 người hiểu nhiếp ảnh từ sớm |
| 10 | API và web demo | Chưa bắt đầu | |

## 4. Kết quả kiểm định bài của Hải (07/10/2026)

### Giữ lại
- Lọc domain camera, k-core (k=5), chia leave-one-out theo thời gian: logic đúng, có seed cố định.
- Kết quả sau k-core (bản của Hải, chạy lại khớp): 70.424 người dùng, 28.867 sản phẩm, 622.997 tương tác. **Từ 07/10 dùng số mới sau khi gộp lặp: 67.661 / 27.940 / 595.515** (xem lỗi 9).
- Bảng ánh xạ ngàm và định nghĩa ma trận M đúng ý cô.

### Lỗi phải sửa
1. **"R-GCN variant" không phải R-GCN:** code dùng `SAGEConv` trong `HeteroConv`. Phải cài R-GCN thật (`RGCNConv`) hoặc KGAT, và gọi đúng tên.
2. **Số liệu mâu thuẫn:** train ghi 482.149 tương tác ở báo cáo 2, nhưng 470.009 ở báo cáo 5 (do `load_train` dùng `set` nên gộp tương tác lặp). Số người dùng tính CVR lúc 2.491, lúc 2.488. Phải thống nhất và giải thích. *(07/10: phần train đã hết mâu thuẫn sau khi gộp lặp — cả hai cách đếm đều ra 460.193. Phần CVR chưa kiểm.)*
3. **Thiếu file trên GitHub:** `compatibility_matrix.npz` và `kg_hetero.pt` không có trong repo, dù cô yêu cầu nộp.
4. **Cách đo:** đang dùng "1 đúng + 99 ngẫu nhiên" (sampled). Nên dùng xếp hạng toàn bộ sản phẩm (full ranking) làm kết quả chính, theo Krichene & Rendle (2020). Báo cáo Recall@K riêng như cô yêu cầu, kèm giải thích vì sao bằng Hit@K khi mỗi người dùng chỉ có một sản phẩm test.
5. **Bảng thông số 139 dòng không ghi nguồn:** cần thêm cột nguồn (URL) và ngày thu thập, ưu tiên các nguồn cô nêu (Kaggle, Wikidata, DPReview). Nhãn mục đích sử dụng phải ghi rõ là quy tắc nhóm tự đặt, kèm căn cứ.
6. **Mẫu kiểm định 50 sản phẩm không có cột nhãn của người chấm.** Con số 94% chưa kiểm chứng được. Đã thấy ít nhất một ca sai: "Canon EF 50mm f/1.8 II" bị khớp thành bản "STM".
7. **Tài liệu có dấu hiệu AI viết** (đường dẫn `file:///d:/`, giọng phóng đại). Phải viết lại bằng giọng của nhóm, đúng mức độ thực tế.
8. **Báo cáo 2 có 2 số sai ở dòng "Sau Domain Filtering"** (phát hiện khi chạy lại 07/10): users trước k-core là **2.502.236** (báo cáo ghi "~2,1M ước tính"); sản phẩm có tương tác trước k-core là **253.208** (báo cáo ghi 72.775 — thực ra là số sản phẩm *sau vòng 1* k-core). Kéo theo TB/user đúng là 1,62 (không phải 1,92). Giải thích ở Phụ lục A "toàn bộ 72.775 items đều thỏa mãn ở vòng 1" cũng sai.
9. **Dữ liệu gốc có bản ghi lặp y hệt** (cùng user, asin, nội dung, timestamp — đã kiểm trong `Electronics.jsonl.gz`). Trong 16.195 dòng lặp (user, item) sau k-core: **13.079 là bản ghi lặp y hệt**, chỉ 3.116 là đánh giá lại ở thời điểm khác. Báo cáo 2 giải thích tất cả là "mua lại" — sai. Hệ quả: 2.396/2.544 user có item test = item val chỉ vì cùng một đánh giá bị lặp; bản ghi lặp cũng được đếm vào bậc k-core. **Đã sửa 07/10 (nhánh `nam/fix-data`):** mỗi cặp (user, parent_asin) giữ 1 dòng sớm nhất trước k-core; bỏ 51.199 dòng (45.684 bản sao y hệt + 5.515 đánh giá lại). Sau sửa: val = test, test ∈ train, val ∈ train đều = 0.

### Kết quả chạy lại bước 01–02 trên máy Nam (07/10/2026)
- Dữ liệu gốc: `Electronics.jsonl.gz` 6.474.438.619 B (sha256 `17b2c5f3…4a28`), `meta_Electronics.jsonl.gz` 1.312.900.427 B (sha256 `a4a196a1…790d`), Last-Modified trên server 16/01/2025.
- Khớp với Hải: 43.886.944 review, 1.610.012 meta, 253.260 sản phẩm camera, 4.042.112 tương tác camera, cả 14 vòng k-core, 70.424 users / 28.867 items / 622.997 tương tác, sparsity 99,969%, phân vị bậc user, phân bố sao, train 482.149 (470.009 nếu gộp lặp), các số trùng train/val/test (1.290 / 1.166 / 2.544).
- Script 02 chạy 2 lần cho file đầu ra giống hệt (sha256) → seed 42 tái lập được.
- RAM đỉnh script 01: 2,03 GiB → không cần sửa đọc từng phần. Thời gian: 01 ≈ 6,4 phút, 02 ≈ 83 giây.
- Log: `ai/data/processed/run01_nam.log`, `run02_nam.log`, `prekcore_stats_nam.json`.
- Chưa kiểm: 18.286.191 users thô (script không đếm), Bảng 2.3 (1.414 body / 1.462 lens), mục 5 của báo cáo 2.

### Kết quả sau khi gộp tương tác lặp (07/10/2026, nhánh `nam/fix-data`)
- Script 01 (đã sửa): 4.042.112 → bỏ 51.199 → 3.990.913 tương tác vào k-core → hội tụ sau 14 vòng: **67.661 users, 27.940 items, 595.515 tương tác**, sparsity 99,968%, TB 8,80/user. RAM đỉnh 2,02 GiB.
- Script 02 (không sửa): train **460.193**, val/test 67.661 mỗi tập.
- Kiểm tra rò rỉ: val = test **0**, test ∈ train **0**, val ∈ train **0**; dòng lặp (user, item) trong CSV **0**. Còn 4 user có 2 item khác nhau cùng timestamp ở ranh giới (thứ tự do sort quyết định, vẫn tái lập được).
- Log: `ai/data/processed/run01_fix.log`, `run02_fix.log`. Đầu ra bản cũ sao lưu ở `ai/data/processed_v62abf54/`.
- Bảng so sánh đầy đủ cũ → mới: `docs/CHANGELOG.md`.

### Vấn đề cốt lõi
- 99% sản phẩm trong dữ liệu là phụ kiện. Chỉ 257/28.867 sản phẩm (0,9%) được xác định ngàm. *(Số theo dữ liệu cũ; cần tính lại trên 27.940 sản phẩm mới.)*
- Vì vậy LightGCN chỉ gợi ý sai ngàm khoảng 3%: vấn đề mà đề tài muốn giải quyết gần như không xuất hiện trong thí nghiệm, và đồ thị tri thức gần như rỗng.
- Nguyên nhân: ngàm được suy ra bằng cách khớp đúng tên model với bảng 139 dòng, quá chặt.

### Khảo sát cho nội dung 3 (07/10/2026, nhánh `nam/content3`, chi tiết ở `docs/content3_survey.md`)

Số liệu do các script trong `ai/survey/content3/` sinh ra, chạy trên 27.940 sản phẩm.

- **Script 03 cũ phân loại sai nhiều.** Trên dữ liệu mới, quy tắc của script 03 cho 1.364 "thân máy" / 1.434 "ống kính".
  - Trong 1.364 "thân máy", chỉ 494 là máy thay được ống kính; 826 là máy compact, máy chụp lấy liền, máy phim (không có ngàm).
  - Trong 1.434 "ống kính", 49 thuộc danh mục kính thiên văn, kính hiển vi, kính lọc, ống kính máy quay…
- **`details["Compatible Mountings"]` nhiễu**, không dùng một mình được:
  - 493 máy compact vẫn bị ghi ngàm;
  - khi cả tiêu đề và trường này đều cho 1 ngàm, hai bên lệch nhau ở 4,8% ống kính và 5,4% thân máy.
- **Quy tắc đề xuất** (ngàm lấy từ tiêu đề; thân máy suy từ dòng máy; ống kính dùng luật "hãng + DSLR"):
  - 445 thân + 967 ống có ngàm = 5,05% số sản phẩm (cũ 0,9%), tức 85,1% số thân và ống thật;
  - 8,83% số tương tác.
  - **Chưa đo độ chính xác.** Claude xem sơ bộ 25 thân + 25 ống được gán ngàm, thấy đúng cả, nhưng đó chưa phải nhãn chuẩn.
- **Kịch bản "gợi ý ống kính cho người đã có thân máy":** có 1.065 người dùng. Trong đó 326 người (30,6%) mua ống khác ngàm và không có ngàm chuyển chính hãng → ảnh hưởng cách đánh giá ràng buộc cứng.
- **Rủi ro gộp biến thể:** 104/967 ống kính có ngàm là ống hãng thứ ba có > 1 asin con. Ngàm trong tiêu đề có thể không đúng với bản người dùng đã mua.
- **Phát hiện phụ:** `camera_items_meta.jsonl` (đầu ra script 01) bỏ mất các trường `details`, `features`, `description`. Muốn dùng phải đọc lại từ file gốc.

### Hướng sửa (đề xuất, chờ Nam chốt)
1. **Tách hai việc:** xác định ngàm trực tiếp từ tiêu đề và metadata Amazon (ví dụ "for Canon EF", "Sony E-mount") để tăng độ phủ cho ma trận M; khớp model để lấy thông số chi tiết thì giữ cách cũ, chấp nhận độ phủ thấp hơn.
2. **Hai người chấm tay độc lập khoảng 200 mẫu** để đo độ chính xác thật của việc xác định ngàm.
3. **Thêm kịch bản đánh giá "gợi ý ống kính cho người đã có thân máy"**, nơi vấn đề tương thích thực sự xuất hiện.

## 5. Lộ trình 2 tháng (đề xuất, chờ Nam chốt)

| Tuần | Việc |
|---|---|
| 1 (7–13/10) | Báo cô tiến độ. Sửa lỗi 2, 3, 4. Nam chạy lại pipeline trên máy mình. Gửi cô báo cáo 1–5 bản đầu, nêu rõ hạn chế và kế hoạch sửa |
| 2 (14–20/10) | Tăng độ phủ ngàm, chấm tay 200 mẫu, dựng lại M và đồ thị, cài R-GCN hoặc KGAT thật, chạy lại baselines |
| 3–4 (21/10–3/11) | Nội dung 6 |
| 5–6 (4–17/11) | Nội dung 7. Bắt đầu tìm người cho khảo sát |
| 7 (18–24/11) | Nội dung 8 |
| 8 (25/11–1/12) | Nội dung 9 |
| Song song từ tuần 3 | Nội dung 10 (FastAPI + React) |

## 6. Quyết định đang chờ

- [ ] Chốt lộ trình 2 tháng ở mục 5
- [ ] Chốt hướng sửa vấn đề cốt lõi ở mục 4
- [ ] Giữ hay bỏ Spring Boot (đề xuất: bỏ, chỉ dùng FastAPI + React)
- [ ] Phân công lại vai trò sau khi đề tài chuyển hướng AI
- [x] Nội dung 3: 6 câu [HỎI] của khảo sát → **đã chốt 07/10** (xem nhật ký và `docs/content3_survey.md` mục 4)
- [x] Nội dung 3: 3 điểm chưa chắc trong `docs/labeling_guide.md` → **đã chốt 07/10** (xem nhật ký)
- [x] Nội dung 3: tải nguồn đáp án ngoài → **có** (07/10), xem `docs/DATA_SOURCES.md`
- [x] Nội dung 3: ống không rõ khung trên thân FF có chế độ cắt → **M = 1**, cờ "chưa rõ có cắt khung" (QĐ 11)
- [x] Nội dung 3: ghi đè `ai/data/kg/` → **đã làm** (sao lưu ở `kg_v62abf54/`)
- [ ] Nội dung 3: sửa lỗi phân loại (ống / thân nằm sai danh mục Amazon) thế nào để số đo vẫn độc lập?
- [ ] Nội dung 3: có đưa `item_attributes.csv`, `compat_pairs.csv` (~7 MB mỗi file) và các file `.npz` lên git không (cô yêu cầu nộp M)? Có xoá các file cũ đã lỗi thời trong `ai/data/kg/` không?
- [x] Có bỏ bản ghi lặp trước k-core không? → **Có**, mỗi cặp (user, item) giữ 1 dòng sớm nhất (07/10, xem nhật ký)

## 7. Nhật ký quyết định

| Ngày | Quyết định | Lý do |
|---|---|---|
| 07/10/2026 | Không làm lại từ đầu, giữ khung của Hải và sửa | Khung code và nội dung 2 dùng được |
| 07/10/2026 | Dựng môi trường `ai/.venv` (Python 3.12.10, torch 2.14.1+cu126, PyG 2.8.0.post1) trên nhánh `nam/setup`; thêm `CLAUDE.md` | Chạy thử: `torch.cuda.is_available()` = True, GPU GTX 1660 Ti, `RGCNConv` chạy được trên GPU. RecBole 1.2.0 import gói gốc được nhưng import `recbole.quick_start` lỗi thiếu `ray` — pipeline hiện không dùng RecBole |
| 07/10/2026 | Chốt `ai/requirements-lock.txt` (pip freeze) làm môi trường chuẩn; thêm mục "An toàn" vào `CLAUDE.md` | Để kết quả tái lập được trên đúng phiên bản thư viện; repo dùng chung với Hải nên chỉ làm trên nhánh riêng |
| 07/10/2026 | Nội dung 2 nâng lên "Đã kiểm thử"; giữ nguyên code 01/02 (không sửa) | Chạy lại ra đúng số chính của Hải, RAM đỉnh 2,03 GiB vừa máy. Phát hiện 2 số sai trong báo cáo và vấn đề bản ghi lặp y hệt — ghi ở mục 4, lỗi 8–9, chờ Nam quyết có lọc trùng hay không |
| 07/10/2026 | **Gộp tương tác lặp trước k-core:** mỗi cặp (user, parent_asin) chỉ giữ 1 tương tác có timestamp sớm nhất (sửa `01_filter_camera_domain.py`, nhánh `nam/fix-data`). Số mới: 67.661 users / 27.940 items / 595.515 tương tác, train 460.193 | (1) Bài toán là gợi ý sản phẩm người dùng chưa có, nên mỗi cặp user–item chỉ tính 1 lần. (2) Bản ghi lặp gây rò rỉ val/test: bản cũ có 2.544 user có val = test (2.396 do bản sao y hệt) và 1.166 user có test nằm trong train. (3) Đánh giá xếp hạng toàn bộ (`full_catalog_cvr`, `common_05.py:182-186`, và full ranking dự định dùng làm kết quả chính) loại các item đã có trong train, nên giữ lặp khiến item test không bao giờ trúng → kết quả sai. Lưu ý: `sampled_eval` (1+99) không loại item train, ở đó giữ lặp có thể làm kết quả đẹp giả. Sau sửa, cả ba loại trùng đều = 0 |
| 07/10/2026 | Thêm `docs/CHANGELOG.md` và quy tắc ghi CHANGELOG vào `CLAUDE.md` | Để Hải biết chính xác những gì đã đổi so với commit `62abf54` |
| 07/10/2026 | Nhánh `nam/content3` (tách từ `nam/fix-data`): `common_05.py` lấy `N_USERS`/`N_ITEMS` từ `user_map.json`/`item_map.json`; `04_build_knowledge_graph.py` lấy số tương tác từ `filtering_stats.json`, `val.txt`, `test.txt` | Số cũ ghi cứng (70.424 / 28.867) không còn đúng sau khi gộp lặp. Đã kiểm: đọc ra 67.661 / 27.940, val/test 67.661, k-core 595.515. Chưa chạy toàn bộ script 04 vì phụ thuộc nội dung 3 (còn `assert after == 257`). Ghi ở CHANGELOG |
| 07/10/2026 | Khảo sát dữ liệu cho nội dung 3, **chưa viết pipeline**. Script khảo sát để ở `ai/survey/content3/`, đầu ra ở `ai/data/survey/` (không đưa lên git) | Để thiết kế lại nội dung 3 dựa trên số đếm thật. Kết quả và 6 câu hỏi chờ Nam chốt ở `docs/content3_survey.md` |
| 07/10/2026 | **QĐ nội dung 3 – 1:** không dùng `details["Compatible Mountings"]` trong bản chính, chỉ lưu để phân tích | Trường này nhiễu: 493 máy compact vẫn bị ghi ngàm; lệch với tiêu đề ở 4,8% ống và 5,4% thân, và trong các ca lệch thì thường trường này sai (vd Nikon D3200 ghi "Nikon 1") |
| 07/10/2026 | **QĐ nội dung 3 – 2:** tách EF và EF-S, áp dụng cho mọi hãng. Mỗi cặp (thân, ống) xếp vào 1 trong 4 mức: `compatible_with` (lắp trực tiếp, đủ khung), `crops_sensor` (lắp trực tiếp, ống APS-C trên thân full-frame, ảnh bị cắt), `requires_adapter` (cần ngàm chuyển chính hãng), không lắp được. M = 1 khi lắp trực tiếp (2 mức đầu), còn lại M = 0. `crops_sensor` và `requires_adapter` lưu riêng cho đồ thị tri thức. Bảng luật viết thành file cấu hình dễ đọc, mỗi luật ghi nguồn hoặc lý do, chỗ chưa chắc đánh dấu và hỏi Nam | Gộp EF/EF-S cho kết quả sai, ví dụ ống EF-S không lắp được thân 5D. Tách thành mức giúp đồ thị và phần giải thích nói đúng mức độ tương thích. **Chưa viết file cấu hình** (để phiên sau). Để chấm được, thêm cột `khung` (ff/apsc) vào file chấm tay, chờ Nam duyệt |
| 07/10/2026 | **QĐ nội dung 3 – 3:** ma trận M chỉ gồm thân × ống kính. Phụ kiện có ngàm trong tiêu đề thì lưu ngàm làm thuộc tính (đánh dấu là phụ kiện), không đưa vào M | Đúng phạm vi cô yêu cầu; vẫn giữ được thông tin ngàm của khoảng 1.050 phụ kiện (hood, ngàm chuyển…) cho đồ thị |
| 07/10/2026 | **QĐ nội dung 3 – 4:** 104 ống kính hãng thứ ba có nhiều biến thể (asin con) đánh dấu "không chắc": loại khỏi M và khỏi CVR, vẫn giữ trong đồ thị | Metadata chỉ có ở mức `parent_asin`, không biết người dùng mua bản ngàm nào, nên không được dùng làm ràng buộc cứng |
| 07/10/2026 | **QĐ nội dung 3 – 5:** giữ nguyên tập test. Khi đánh giá, báo kết quả tách hai nhóm: item test cùng ngàm và khác ngàm với thân máy đã biết. Ghi rõ hạn chế: chỉ biết những thân máy người dùng có viết đánh giá | 326/1.065 (30,6%) người dùng trong kịch bản mua ống khác ngàm và không có ngàm chuyển chính hãng; bỏ họ khỏi test là chọn dữ liệu theo nhãn test |
| 07/10/2026 | **QĐ nội dung 3 – 6:** Nam chấm tay một mình: 50 mẫu dev, 200 mẫu test (mẫu test lấy sau, loại các ASIN đã có trong dev) | Không có người chấm thứ hai nên không tính được kappa; ghi đây là hạn chế |
| 07/10/2026 | Tạo file chấm mù `ai/survey/content3/label_dev_50.csv` (script `make_label_dev.py`, seed 20261007, 12 tầng) và `docs/labeling_guide.md`. Kết quả quy tắc để riêng ở `ai/data/survey/label_dev_50_rule.csv` (không đưa lên git, chạy lại script sẽ tạo lại giống hệt) | Để đo độ chính xác thật của quy tắc xác định loại và ngàm |
| 07/10/2026 | **QĐ nội dung 3 – 7:** giữ cột `khung` (ff / apsc / khac) trong file chấm tay | Quyết định 2 cần biết khổ của thân và ống để phân biệt `compatible_with` với `crops_sensor` (vd DX trên FX) |
| 07/10/2026 | **QĐ nội dung 3 – 8:** ống APS-C hãng thứ ba "for Canon" (Sigma DC, Tamron Di II…) trên thân Canon full-frame xếp **"không chắc"** ở mức từng cặp. M có thêm giá trị "không biết", lưu bằng một ma trận đánh dấu riêng; các cặp này bị loại khỏi ràng buộc cứng và CVR. Cùng ống đó trên thân Canon APS-C vẫn là `compatible_with` | Ống lắp vật lý được nhưng ảnh bị tối góc, và phần lớn DSLR Canon full-frame không tự cắt khung, nên không xếp chắc chắn vào `crops_sensor` hay "không lắp được". Việc các ống này dùng ngàm EF (không phải EF-S) **chưa đối chiếu tài liệu hãng**, sẽ kiểm khi viết file cấu hình luật |
| 07/10/2026 | **QĐ nội dung 3 – 9:** ống ngàm T bán kèm vòng T ghi theo ngàm của vòng (vd `canon_ef`); tiêu đề không nói rõ vòng nào thì ghi `khong_chac` (giá trị mới của cột `ngam`) | Người mua lắp ống lên thân qua vòng T đi kèm, nên ngàm thực tế là ngàm của vòng |
| 07/10/2026 | **QĐ nội dung 3 – 10: đổi cách đo độ chính xác, Nam không chấm tay.** (1) Tìm nguồn thông số bên ngoài có ngàm và khung (ưu tiên Wikidata, Kaggle/GitHub), báo giấy phép và độ phủ, hỏi Nam trước khi tải. (2) Nguồn này **chỉ làm đáp án đối chiếu, không dùng trong quy tắc**, để hai bên độc lập. (3) Mẫu dev 50: Claude tự chấm để tìm lỗi và sửa quy tắc. (4) Bỏ mẫu test 200 chấm tay | Nam không có thời gian chấm tay. Hạn chế đã biết: đáp án ngoài chỉ phủ được các sản phẩm khớp được tên model, và bước khớp tên cũng có thể sai. Phần dev do Claude chấm không độc lập với người viết quy tắc |
| 07/10/2026 | **Viết pipeline nội dung 3 mới** (`03_mount_compat.py`, `mount_detect.py`, `ai/config/mount_rules.toml`); chạy thử vào `ai/data/kg_new/`, **chưa** ghi đè `ai/data/kg/`. Claude tự chấm dev 50 (`label_dev_50_claude.csv`) và sửa luật theo các lỗi tìm được: ngàm suy từ dòng máy được nhắc trong tiêu đề ống, teleconverter dùng luật hãng + DSLR, ống/kính lọc gắn ren → không có ngàm, thêm dấu hiệu FF cho Nikon AF-D/Zeiss, bổ sung luật dòng máy cho D2X, 60Da, K2000, Alpha 7R… | Kết quả dev sau khi sửa: loại 49/50, ngàm 46/50, khung 43/50, mọi giá trị đã gán đều khớp (chỉ là kiểm tra nội bộ). Nguồn của các luật: phần lớn là trang hãng (Canon, Nikon, Sony support, Ricoh, Sigma); ngàm chuyển FT1, LA-EA, MMF mới có nguồn bán lẻ. URL mới kiểm qua tóm tắt kết quả tìm kiếm, chưa đọc toàn văn |
| 07/10/2026 | Khảo sát nguồn đáp án ngoài (chưa tải dữ liệu): **Lensfun** (dữ liệu CC BY-SA 3.0, 59 file XML ~5,2 MB, có ngàm + hệ số crop cho máy và ống); **Wikidata** (CC0, ngàm qua P2935 "connector": khoảng 360 mẫu máy + 596 mẫu ống); **openMVG CameraSensorSizeDatabase** (MIT, chỉ có bề rộng cảm biến → dùng cho khung thân); Kaggle "1000 Cameras" không có ngàm → loại | Chờ Nam duyệt trước khi tải. Độ phủ trên sản phẩm của nhóm chưa đếm được nếu chưa tải |
| 07/10/2026 | **QĐ nội dung 3 – 11:** thân FF có chế độ cắt khung chính hãng (Nikon F/Z, Sony E/A, Canon RF, Pentax K) + ống cùng ngàm không rõ khung → M = 1, mức `compatible_with` kèm cờ `crop_unknown` ("chưa rõ có cắt khung") | Dù ống là FF hay APS-C thì vẫn lắp trực tiếp. Sau khi áp: M = 1 tăng từ 54.638 lên 56.276 cặp, "không biết" giảm từ 3.474 xuống 1.836 |
| 07/10/2026 | **QĐ nội dung 3 – 12:** tải Lensfun, openMVG, Wikidata vào `ai/data/external/` (không lên git), ghi ở `docs/DATA_SOURCES.md`. Sao lưu `ai/data/kg/` sang `kg_v62abf54/` rồi ghi đè bằng đầu ra mới | Nam duyệt. Giấy phép: Lensfun CC BY-SA 3.0, openMVG MIT, Wikidata CC0 |
| 07/10/2026 | Thêm vào `CLAUDE.md`: không gửi thông tin cá nhân (email, tên…) ra bên ngoài trong yêu cầu web | Phiên trước, một lần gọi API Wikidata đã kèm email của Nam trong User-Agent |
| 07/10/2026 | Mở và đọc cả 14 trang nguồn của bảng luật; thay 3 nguồn bán lẻ bằng trang hãng; `kiem_chung = "da_doc_trang"` kèm câu trích | Theo yêu cầu của Nam. Không có luật nào không xác nhận được. Hai chỗ là suy rộng (đã ghi trong TOML): danh sách thân không nhận EF-S trên trang Canon dừng ở 6D; câu về LA-EA của Sony nói về ống DT |
| 07/10/2026 | Đo độ chính xác bằng nguồn ngoài (`eval_external.py`): khớp tên chắc chắn 1.493 sản phẩm. Ngàm đúng 98,1% (Lensfun) / 100% (Wikidata); khung thân 100% / 99,5% (openMVG); loại 87,8% / 83,3%. Bước khớp đã được sửa 3 lần **ở phía đánh giá** (loại tiêu đề phụ kiện; khớp ống phải trùng mọi token tên; lớp "product model" của Wikidata), **không sửa quy tắc** | Các sửa này làm cho đáp án đúng hơn, không đụng tới quy tắc. Quy tắc giữ nguyên để số đo độc lập. Chi tiết ca sai ở CHANGELOG |
