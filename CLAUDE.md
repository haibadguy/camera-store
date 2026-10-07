# CLAUDE.md

Hướng dẫn cho Claude khi làm việc trong repo đồ án này. Trả lời bằng **tiếng Việt**, ngắn gọn, dễ hiểu.

## 1. Bối cảnh

> **`docs/STATUS.md` là nguồn sự thật về trạng thái dự án.** Đọc file đó đầu mỗi phiên. Khi STATUS.md mâu thuẫn với tài liệu khác (kể cả `AGENTS.md`, `docs/FOUNDATION_BASELINE.md`, `docs/plan.md`...) hay với trí nhớ của cuộc chat, tin STATUS.md.

Tóm tắt (tại 07/10/2026 — chi tiết và bản mới nhất xem STATUS.md):

- **Đề tài:** Hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh trong TMĐT bằng mô hình gợi ý lai có ràng buộc và giải thích được. GVHD: TS. Đỗ Thị Liên.
- **Nhóm:** Nam (nhóm trưởng, phải nắm toàn bộ), Hải (Data/AI), Quyền (Frontend). Người dùng Claude thường là Nam.
- **Lộ trình:** 10 nội dung theo mail của cô ngày 22/09/2026. Cô dặn: làm đến đâu phải hiểu đến đó.
- **Hướng cũ đã bỏ:** bản đề xuất 16/09 (Spring Boot, chấm điểm theo quy tắc). Phần Spring Boot/React trong `AGENTS.md` và `docs/` cũ không còn là hướng chính.
- **Dữ liệu:** Amazon Reviews 2023, nhóm Electronics. Code AI nằm trong `ai/pipeline/`.
- **Tình hình:** nội dung 1–5 đã có code (của Hải, commit `62abf54`) nhưng có lỗi phải sửa (R-GCN gọi sai tên, số liệu mâu thuẫn, cách đo sampled thay vì full ranking, độ phủ ngàm chỉ 0,9%...). Nội dung 6–10 chưa bắt đầu.

## 2. Nguyên tắc

1. **Chính xác là ưu tiên số một.** Thà chậm mà đúng.
2. **Không đoán.** Thiếu thông tin thì hỏi Nam, không tự bịa giả định.
3. **Mọi kết luận phải có bằng chứng từ việc chạy code thật.** Chưa chạy thì nói rõ là "chưa kiểm chứng".
4. **Số liệu chỉ lấy từ output của script.** Không ước lượng, không chép số từ tài liệu cũ mà không chạy lại. Khi báo số, ghi rõ script nào sinh ra.
5. **Giải thích để Nam hiểu và tự trình bày lại được:** đưa **ví dụ trước, công thức sau**. Dùng ví dụ nhỏ, cụ thể (vài người dùng, vài sản phẩm), rồi mới tổng quát hóa.

## 3. Quy trình

- Làm việc trên nhánh riêng, không push khi Nam chưa đồng ý.
- **Cuối mỗi phiên:**
  1. Cập nhật `docs/STATUS.md`: bảng trạng thái (đúng thang Kế hoạch / Đã triển khai / Đã kiểm thử / Đã đánh giá, chỉ nâng mức khi có bằng chứng) và **nhật ký quyết định**.
  2. Tóm tắt ngắn cho Nam: **đã làm gì**, **kết quả** (kèm số liệu và nguồn), **còn chưa chắc gì**.

## 4. Môi trường

- Windows 11, GPU GTX 1660 Ti 6 GB (driver hỗ trợ CUDA 12.6), RAM 16 GB.
- **RAM thường chỉ trống khoảng 5–6 GB** → dữ liệu lớn phải đọc từng phần (chunk / streaming), không nạp cả file vào bộ nhớ.
- Python 3.12. Máy có cả Python 3.14 là bản mặc định của `py`, nên **luôn dùng venv** `ai/.venv`:
  - Chạy: `ai\.venv\Scripts\python.exe <script>`
  - Tạo lại: `py -3.12 -m venv ai\.venv`, rồi cài torch từ `https://download.pytorch.org/whl/cu126`, sau đó `pip install -r ai/requirements.txt`.
- Dự án và dữ liệu đặt ở ổ E.
