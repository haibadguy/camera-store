# Chạy huấn luyện v3 trên Kaggle — cách đóng gói (chưa tải lên, chưa chạy)

Viết 06/11/2026 theo nhận xét cô 06/11 ("đưa code lên Kaggle ..., cố định seed, ghi log, lưu phiên bản; tính giờ chạy
trước; gửi cô link notebook"). Kế hoạch chạy và ngân sách giờ: `docs/reviews/v3_eval_plan.md`.

## 1. Ví dụ

Muốn chạy LightGCN λ = 1e-3, seed 2, tối đa 1.000 epoch trên Kaggle:

1. Commit code trên nhánh, cây git sạch.
2. `ai\.venv\Scripts\python.exe kaggle/build_kaggle_package.py --out E:\DATN\kaggle_pkg --tag v3_20261106`
   → tạo `E:\DATN\kaggle_pkg\v3_20261106\` gồm 2 dataset + 1 notebook (xem mục 2).
3. (Nam, khi đồng ý) tải 2 dataset lên dưới dạng **riêng tư**, đẩy notebook.
4. Trên Kaggle: mở notebook, sửa ô cấu hình
   `JOBS = [("lightgcn_l2-1e-03_s2", "ai/pipeline/05b_lightgcn_train.py", ["--l2", "1e-3", "--seed", "2", "--max-epoch", "1000"])]`,
   `RUN_LABEL = "kaggle_v3_lan1"`, chọn GPU T4, Internet bật → **Save Version → Save & Run All**.
5. Phiên bản notebook lưu: commit, sha256 dữ liệu, `pip freeze`, log từng việc, `result.json`, `best.pt`, `last.pt`
   ở `/kaggle/working/out/<RUN_LABEL>/`. Tải về bằng `kaggle kernels output <tài khoản>/camera-store-v3-runner -p ...`.
6. Chấm test **ở máy nhóm** bằng script chấm test (không chấm test trên Kaggle).

## 2. Gói gồm gì

| Thành phần | Nội dung | Vì sao |
|---|---|---|
| `camera-store-v3-code` (dataset riêng tư) | `camera-store.bundle` (git bundle đến commit), `COMMIT.txt` | Notebook `git clone` bundle rồi `git checkout` đúng commit; `eval_05.git_state()` ghi được commit thật vào `config.json` của mỗi lần chạy |
| `camera-store-v3-data` (dataset riêng tư) | `ai/data/processed/` (train / val / test, map, âm mẫu 1+99) và `ai/data/kg/` (đồ thị, M, chỉ mục) đúng đường dẫn trong repo; `manifest_sha256.json` | Notebook chép vào repo rồi kiểm sha256 từng file, lệch thì dừng |
| `kernel/v3_runner.ipynb` | sinh từ `kaggle/v3_runner.py` | Notebook mẫu: môi trường → code → thư viện → dữ liệu → chạy tiếp (tùy chọn) → chạy việc → gom kết quả |

- **Không symlink dữ liệu**: `eval_05.inputs_sha256()` gọi `Path.resolve().relative_to(ROOT)`, symlink sang
  `/kaggle/input` sẽ lỗi; notebook chép file (≈ 190 MB) vào `/kaggle/working/camera-store/ai/data/`.
- **Mã người dùng**: `user_map.json` trong gói thay mã người đánh giá Amazon bằng `u0, u1, ...` (code huấn luyện chỉ
  dùng số phần tử). Tắt bằng `--keep-user-ids` nếu Nam quyết.
- **Seed**: mỗi script nhận `--seed` và tự đặt seed torch / numpy như ở máy nhóm; notebook đặt `PYTHONHASHSEED=0`.
  GPU không tất định (đã thấy ở máy nhóm, STATUS hạn chế nội dung 5 điểm 9): cùng seed trên Kaggle và trên máy nhóm
  **không** cho số trùng từng chữ số.
- **Log**: mỗi việc một file `logs/<việc>_<RUN_LABEL>_<thời điểm>.log` (không ghi đè) + log của chính script.
- **Phiên bản**: mỗi lần Save Version là một phiên bản cố định của notebook và output; ghi số phiên bản vào
  `docs/reviews/v3_eval_plan.md` (bảng lần chạy) khi dùng số của nó.
- **Phiên giới hạn giờ**: `train_05.run` lưu `last.pt` ở mỗi lần chấm val; chạy tiếp ở phiên bản sau bằng ô
  `RESUME_FROM` (thêm output phiên bản trước làm input, giữ nguyên `RUN_LABEL` và `JOBS`).

## 3. Chưa kiểm chứng (phải thử một lần ngắn trước khi chạy thật)

- Ảnh Kaggle có Python ≥ 3.11 (cần `tomllib`) và có bản `torch==2.14.1+cu126` cho Python đó.
- GPU: T4 (sm_75, cùng thế hệ Turing với GTX 1660 Ti) nên dùng; P100 (sm_60) có thể không được bản torch mới hỗ trợ.
- Hạn mức GPU mỗi tuần và giờ tối đa mỗi phiên: xem trang tài khoản Kaggle của Nam (trong kế hoạch tạm lấy 30 giờ /
  tuần, 12 giờ / phiên — **chưa kiểm chứng**).
- Tốc độ T4 so với GTX 1660 Ti: chưa đo. Ước tính giờ trong kế hoạch dùng số đo ở máy nhóm.
- RecBole trên Kaggle: cần thêm `ai/recbole/requirements-recbole.txt` (venv riêng ở máy nhóm, xem
  `ai/recbole/README.md`); chưa đưa vào notebook.
