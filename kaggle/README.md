# Chạy huấn luyện v3 trên Kaggle — cách đóng gói

Viết 06/11/2026, cập nhật 07/11/2026. Cách làm trên web (tạo dataset, notebook, chạy, lấy kết quả, chạy tiếp, thay gói
mới): `kaggle/HUONG_DAN_KAGGLE.md`. Kế hoạch chạy và ngân sách giờ: `docs/reviews/v3_eval_plan.md`.

## 1. Ví dụ

Muốn chạy LightGCN λ = 1e-3, seed 2, tối đa 1.000 epoch trên Kaggle:

1. Commit code trên nhánh, cây git sạch.
2. `ai\.venv\Scripts\python.exe kaggle/build_kaggle_package.py --out E:\DATN\kaggle_pkg --tag <tag>`
   → tạo `E:\DATN\kaggle_pkg\<tag>\` gồm 2 dataset (thư mục + .zip) + 1 notebook + `PACKAGE.md`.
3. Tải 2 dataset lên dưới dạng **riêng tư**, import notebook (`HUONG_DAN_KAGGLE.md` mục 2–3).
4. Trên Kaggle, ô cấu hình: thêm việc vào `PRESETS`, mỗi việc là `(tên, môi trường, script, tham số)`, vd
   `("lightgcn_l2-1e-03_s2", "nhom", "ai/pipeline/05b_lightgcn_train.py", ["--l2", "1e-3", "--seed", "2", "--max-epoch", "1000"])`;
   chọn GPU T4, Internet bật → **Save Version → Save & Run All**.
5. Phiên bản notebook lưu: commit, sha256 dữ liệu, `pip freeze` của từng venv, log từng việc, `result.json`, checkpoint
   ở `/kaggle/working/out/<RUN_LABEL>/`.
6. Chấm test **ở máy nhóm** bằng script chấm test (không chấm test trên Kaggle).

## 2. Gói gồm gì

| Thành phần | Nội dung | Vì sao |
|---|---|---|
| `camera-store-v3-code` (dataset riêng tư) | `camera-store.bundle` (git bundle đến commit), `COMMIT.txt`, `recbole_gnn.bundle` + `RECBOLE_GNN_COMMIT.txt` | Notebook `git clone` bundle rồi `git checkout` đúng commit; `eval_05.git_state()` ghi được commit thật vào `config.json` của mỗi lần chạy. RecBole-GNN (SimGCL) không phải gói pip nên đi kèm dạng bundle, kiểm đúng commit |
| `camera-store-v3-data` (dataset riêng tư) | `ai/data/processed/`, `ai/data/kg/`, `ai/data/recbole/camera_loo/` đúng đường dẫn trong repo; `manifest_sha256.json` | Notebook chép vào repo rồi kiểm sha256 từng file, lệch thì dừng |
| `kernel/v3_runner.ipynb` | sinh từ `kaggle/v3_runner.py` | Môi trường → code → thư viện → dữ liệu → chạy tiếp (tùy chọn) → chạy việc → gom kết quả |

- **Thư viện**: hai venv Python 3.12.10 do `uv` tạo (`nhom`: `kaggle/requirements-kaggle.txt` + ràng buộc
  `ai/requirements-lock.txt`; `recbole`: `ai/recbole/requirements-recbole-lock.txt`), kiểm phiên bản với file lock.
  Python sẵn có của Kaggle không chạy việc huấn luyện nào. Chi tiết và chỗ khác máy nhóm: `HUONG_DAN_KAGGLE.md` mục 3a.
- **Không symlink dữ liệu**: `eval_05.inputs_sha256()` gọi `Path.resolve().relative_to(ROOT)`, symlink sang
  `/kaggle/input` sẽ lỗi; notebook chép file (≈ 140 MB) vào `/kaggle/working/camera-store/ai/data/`.
- **Mã người dùng**: `user_map.json` trong gói thay mã người đánh giá Amazon bằng `u0, u1, ...` (code huấn luyện chỉ
  dùng số phần tử). Tắt bằng `--keep-user-ids` khi nhóm cần.
- **Seed**: mỗi script nhận `--seed` và tự đặt seed torch / numpy như ở máy nhóm; notebook đặt `PYTHONHASHSEED=0`.
  GPU không tất định (đã thấy ở máy nhóm, STATUS hạn chế nội dung 5 điểm 9): cùng seed trên Kaggle và trên máy nhóm
  **không** cho số trùng từng chữ số.
- **Log**: mỗi việc một file `logs/<việc>_<RUN_LABEL>_<thời điểm>.log` (không ghi đè) + log của chính script.
- **Phiên bản**: mỗi lần Save Version là một phiên bản cố định của notebook và output; ghi số phiên bản vào
  `docs/reviews/v3_eval_plan.md` (bảng lần chạy) khi dùng số của nó.
- **Phiên giới hạn giờ**: việc đang chạy bị ngắt ở mốc `JOB_DEADLINE_H`; chạy tiếp ở phiên bản sau bằng `RESUME = True`
  (`HUONG_DAN_KAGGLE.md` mục 6).

## 3. Chưa kiểm chứng

- Giao diện, hạn mức GPU mỗi tuần và giờ tối đa mỗi phiên của Kaggle (xem các chỗ **[chưa kiểm chứng]** trong
  `HUONG_DAN_KAGGLE.md`).
- Tốc độ T4 so với GTX 1660 Ti: chưa đo. Ước tính giờ trong kế hoạch dùng số đo ở máy nhóm.
