Lần cuối (05/11/2026): bản clone MỚI TINH của nhánh nam/fix-demo-data (commit 46d02ba, cây sạch) ở
E:\DATN\thử máy khác 2\ĐATN\camera-store (dấu tiếng Việt, dấu cách, chữ Đ như máy Quyền D:\ĐATN), venv Python 3.12 từ
ai/requirements-lock.txt, chưa có jar / node_modules, CHỈ giải nén E:\DATN\demo_data_v2.zip (sha256 zip trong
demo_data_v2_sha256.txt). Clone từ repo cục bộ vì nhánh chưa push.
- check_run_demo.py --label mayclone2_20261105_lan1: 7/7 ĐẠT (run_demo.ps1 tự npm ci + mvn package; FastAPI 13,7 s,
  Spring 4,2 s, Vite 0,6 s; tắt sạch). Log: check_run_demo_mayclone2_20261105_lan1/, check_run_demo_console.txt.
- list_runtime_files.py --label mayclone2_20261105: mọi điểm cuối 200, 23 file dữ liệu được đọc, 6 file ngoài git,
  trùng sha256 với zip v2. Log: runtime_files_mayclone2_20261105/.
Hai bản clone thử đã xóa sau khi chép log.
