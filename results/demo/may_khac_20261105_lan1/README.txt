clone origin/main 947d3cbe30ab4363870a8e7ecbe5951f36e7248c
E:/DATN/thử máy khác/ĐATN/camera-store
Lần 1 (05/11/2026): bản clone origin/main mới tinh ở thư mục có dấu tiếng Việt, dấu cách và chữ Đ, venv Python 3.12 từ
ai/requirements-lock.txt, chỉ giải nén E:\DATN\demo_data.zip (28/10, 5 file), chạy run_demo.ps1 của origin/main.
Kết quả: FastAPI thoát lúc import, thiếu ai/data/processed/user_map.json; run_demo.ps1 in "mã ()" trống.
Lần 2: thêm user_map.json vào clone, chạy check_run_demo.py (script origin/main): FastAPI lên 18,3 s, Spring Boot thoát
"Unable to access jarfile E:\DATN\th? m?y kh?c\?ATN\...jar" (java.exe đọc tham số theo bảng mã ANSI, chữ ử/Đ thành ?);
run_demo.ps1 lại in "mã ()" trống. Log: lan2_*, check_run_demo_mayclone1_20261105_lan2/.
Lần 3: chép run_demo.ps1 đã sửa (jar tương đối, kiểm 6 file) vào clone: check_run_demo 7/7 ĐẠT. Log: lan3_*,
check_run_demo_mayclone1_20261105_lan3/.
Lần 4: bỏ test.txt, user_map.json, sửa 1 byte val.txt: run_demo.ps1 liệt kê đủ 2 THIẾU + 1 SAI rồi dừng
(lan4_thieu_file_console.txt).
Lần 5: test_exitcode.ps1 lấy đúng các hàm của run_demo.ps1, bật Python thoát mã 3: in "FastAPI thoát (mã 3)" và dòng
cuối log lỗi (lan5_thu_ma_thoat_console.txt).
