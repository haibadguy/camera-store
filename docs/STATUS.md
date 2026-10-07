# TRẠNG THÁI ĐỒ ÁN — Camera Recommender

Cập nhật lần cuối: 07/10/2026 (chạy lại bước 01–02) · Người cập nhật: Nam (Claude hỗ trợ kiểm định)

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
| 2 | Thu thập, lọc k-core, chia train/val/test | **Đã kiểm thử** (07/10) | Chạy lại trên máy Nam: số chính khớp, 2 số trong báo cáo sai, dữ liệu gốc có bản ghi lặp y hệt. Xem mục 4 |
| 3 | Entity Linking, ma trận M | Đã triển khai, **cần làm lại một phần** | Độ phủ chỉ 8,9%. Xem mục 4 |
| 4 | Đồ thị tri thức | Đã triển khai, **cần làm lại sau nội dung 3** | 99% sản phẩm không có cạnh tri thức |
| 5 | Baselines và đo lường | Đã triển khai, **có lỗi phải sửa** | Xem mục 4 |
| 6 | Module ràng buộc cứng và mềm | Chưa bắt đầu | |
| 7 | Mô hình gợi ý theo bộ (GNN có quan hệ) | Chưa bắt đầu | |
| 8 | Giải thích (path-based) | Chưa bắt đầu | |
| 9 | Ablation, khảo sát người dùng | Chưa bắt đầu | Cần tìm 20–30 người hiểu nhiếp ảnh từ sớm |
| 10 | API và web demo | Chưa bắt đầu | |

## 4. Kết quả kiểm định bài của Hải (07/10/2026)

### Giữ lại
- Lọc domain camera, k-core (k=5), chia leave-one-out theo thời gian: logic đúng, có seed cố định.
- Kết quả sau k-core: 70.424 người dùng, 28.867 sản phẩm, 622.997 tương tác.
- Bảng ánh xạ ngàm và định nghĩa ma trận M đúng ý cô.

### Lỗi phải sửa
1. **"R-GCN variant" không phải R-GCN:** code dùng `SAGEConv` trong `HeteroConv`. Phải cài R-GCN thật (`RGCNConv`) hoặc KGAT, và gọi đúng tên.
2. **Số liệu mâu thuẫn:** train ghi 482.149 tương tác ở báo cáo 2, nhưng 470.009 ở báo cáo 5 (do `load_train` dùng `set` nên gộp tương tác lặp). Số người dùng tính CVR lúc 2.491, lúc 2.488. Phải thống nhất và giải thích.
3. **Thiếu file trên GitHub:** `compatibility_matrix.npz` và `kg_hetero.pt` không có trong repo, dù cô yêu cầu nộp.
4. **Cách đo:** đang dùng "1 đúng + 99 ngẫu nhiên" (sampled). Nên dùng xếp hạng toàn bộ sản phẩm (full ranking) làm kết quả chính, theo Krichene & Rendle (2020). Báo cáo Recall@K riêng như cô yêu cầu, kèm giải thích vì sao bằng Hit@K khi mỗi người dùng chỉ có một sản phẩm test.
5. **Bảng thông số 139 dòng không ghi nguồn:** cần thêm cột nguồn (URL) và ngày thu thập, ưu tiên các nguồn cô nêu (Kaggle, Wikidata, DPReview). Nhãn mục đích sử dụng phải ghi rõ là quy tắc nhóm tự đặt, kèm căn cứ.
6. **Mẫu kiểm định 50 sản phẩm không có cột nhãn của người chấm.** Con số 94% chưa kiểm chứng được. Đã thấy ít nhất một ca sai: "Canon EF 50mm f/1.8 II" bị khớp thành bản "STM".
7. **Tài liệu có dấu hiệu AI viết** (đường dẫn `file:///d:/`, giọng phóng đại). Phải viết lại bằng giọng của nhóm, đúng mức độ thực tế.
8. **Báo cáo 2 có 2 số sai ở dòng "Sau Domain Filtering"** (phát hiện khi chạy lại 07/10): users trước k-core là **2.502.236** (báo cáo ghi "~2,1M ước tính"); sản phẩm có tương tác trước k-core là **253.208** (báo cáo ghi 72.775 — thực ra là số sản phẩm *sau vòng 1* k-core). Kéo theo TB/user đúng là 1,62 (không phải 1,92). Giải thích ở Phụ lục A "toàn bộ 72.775 items đều thỏa mãn ở vòng 1" cũng sai.
9. **Dữ liệu gốc có bản ghi lặp y hệt** (cùng user, asin, nội dung, timestamp — đã kiểm trong `Electronics.jsonl.gz`). Trong 16.195 dòng lặp (user, item) sau k-core: **13.079 là bản ghi lặp y hệt**, chỉ 3.116 là đánh giá lại ở thời điểm khác. Báo cáo 2 giải thích tất cả là "mua lại" — sai. Hệ quả: 2.396/2.544 user có item test = item val chỉ vì cùng một đánh giá bị lặp; bản ghi lặp cũng được đếm vào bậc k-core. Chưa sửa, chờ Nam quyết (đề xuất: bỏ bản ghi trùng hoàn toàn trước k-core).

### Kết quả chạy lại bước 01–02 trên máy Nam (07/10/2026)
- Dữ liệu gốc: `Electronics.jsonl.gz` 6.474.438.619 B (sha256 `17b2c5f3…4a28`), `meta_Electronics.jsonl.gz` 1.312.900.427 B (sha256 `a4a196a1…790d`), Last-Modified trên server 16/01/2025.
- Khớp với Hải: 43.886.944 review, 1.610.012 meta, 253.260 sản phẩm camera, 4.042.112 tương tác camera, cả 14 vòng k-core, 70.424 users / 28.867 items / 622.997 tương tác, sparsity 99,969%, phân vị bậc user, phân bố sao, train 482.149 (470.009 nếu gộp lặp), các số trùng train/val/test (1.290 / 1.166 / 2.544).
- Script 02 chạy 2 lần cho file đầu ra giống hệt (sha256) → seed 42 tái lập được.
- RAM đỉnh script 01: 2,03 GiB → không cần sửa đọc từng phần. Thời gian: 01 ≈ 6,4 phút, 02 ≈ 83 giây.
- Log: `ai/data/processed/run01_nam.log`, `run02_nam.log`, `prekcore_stats_nam.json`.
- Chưa kiểm: 18.286.191 users thô (script không đếm), Bảng 2.3 (1.414 body / 1.462 lens), mục 5 của báo cáo 2.

### Vấn đề cốt lõi
- 99% sản phẩm trong dữ liệu là phụ kiện. Chỉ 257/28.867 sản phẩm (0,9%) được xác định ngàm.
- Vì vậy LightGCN chỉ gợi ý sai ngàm khoảng 3%: vấn đề mà đề tài muốn giải quyết gần như không xuất hiện trong thí nghiệm, và đồ thị tri thức gần như rỗng.
- Nguyên nhân: ngàm được suy ra bằng cách khớp đúng tên model với bảng 139 dòng, quá chặt.

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
- [ ] Có bỏ bản ghi lặp y hệt (user, item, timestamp) trước k-core không? Nếu có thì mọi số từ bước 2 trở đi sẽ đổi (lỗi 9, mục 4)

## 7. Nhật ký quyết định

| Ngày | Quyết định | Lý do |
|---|---|---|
| 07/10/2026 | Không làm lại từ đầu, giữ khung của Hải và sửa | Khung code và nội dung 2 dùng được |
| 07/10/2026 | Dựng môi trường `ai/.venv` (Python 3.12.10, torch 2.14.1+cu126, PyG 2.8.0.post1) trên nhánh `nam/setup`; thêm `CLAUDE.md` | Chạy thử: `torch.cuda.is_available()` = True, GPU GTX 1660 Ti, `RGCNConv` chạy được trên GPU. RecBole 1.2.0 import gói gốc được nhưng import `recbole.quick_start` lỗi thiếu `ray` — pipeline hiện không dùng RecBole |
| 07/10/2026 | Chốt `ai/requirements-lock.txt` (pip freeze) làm môi trường chuẩn; thêm mục "An toàn" vào `CLAUDE.md` | Để kết quả tái lập được trên đúng phiên bản thư viện; repo dùng chung với Hải nên chỉ làm trên nhánh riêng |
| 07/10/2026 | Nội dung 2 nâng lên "Đã kiểm thử"; giữ nguyên code 01/02 (không sửa) | Chạy lại ra đúng số chính của Hải, RAM đỉnh 2,03 GiB vừa máy. Phát hiện 2 số sai trong báo cáo và vấn đề bản ghi lặp y hệt — ghi ở mục 4, lỗi 8–9, chờ Nam quyết có lọc trùng hay không |
