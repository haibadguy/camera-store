# Hướng dẫn chạy đợt `thu` trên Kaggle (làm trên web, không cần khóa API)

Viết 06/11/2026, cập nhật 07/11/2026 (môi trường thư viện dựng bằng `uv`, mục 3a). Đợt `thu` (nhóm chốt 06/11): mỗi
baseline **seed 1, một cấu hình**, chỉ chấm val, để đo số epoch dừng sớm và giờ GPU thật trước khi quyết lưới / số
seed. Kế hoạch: `docs/reviews/v3_eval_plan.md` mục 6.1, 12.1.

Những chỗ ghi **[chưa kiểm chứng]** là mô tả giao diện / giới hạn Kaggle theo hiểu biết chung, chưa thử trên tài khoản
của nhóm. Gặp khác biệt thì ghi lại (ảnh chụp màn hình) để sửa file này.

## 0. Gói đã chuẩn bị (trên máy nhóm)

Thư mục `E:\DATN\kaggle_pkg\<tag>\` (do `kaggle/build_kaggle_package.py` sinh; xem `PACKAGE.md` trong đó):

| File | Dùng để |
|---|---|
| `camera-store-v3-code.zip` | dataset **code**: git bundle của repo (đúng commit) + bundle RecBole-GNN |
| `camera-store-v3-data.zip` | dataset **dữ liệu**: train / val / test, KG, file RecBole; `user_map.json` đã ẩn mã (`u0`, `u1`, ...) |
| `kernel_kiem/kiem_moi_truong.ipynb` | notebook **kiểm môi trường** (mục 3b): chạy trước, vài phút đến ~15 phút GPU [ước tính, chưa đo] |
| `kernel/v3_runner.ipynb` | notebook chạy thật (đã điền commit) |

## 1. Chia việc cho 3 tài khoản

Ô cấu hình đầu notebook có `ACCOUNT`; mỗi người chỉ đổi dòng này.

| Tài khoản | `ACCOUNT` | Việc (seed 1) | Ước tính |
|---|---|---|---|
| Nam | `"nam"` | KGIN, context_hops = 2 (mặc định RecBole) | nặng nhất: 41 s / epoch ở máy nhóm → có thể cần 2 phiên |
| Hải | `"hai"` | SimGCL, λ = 0,01 (giữa lưới đã đăng ký {0,005; 0,01; 0,05}) | 33 s / epoch ở máy nhóm → có thể cần 2 phiên |
| Quyền | `"quyen"` | BPR-MF code nhóm (λ2 = 1e-4), UltraGCN (cấu hình Electronics của tác giả), BPR của RecBole (đối chiếu) | nhẹ, thường 1 phiên |

Số giây / epoch là đo ngắn trên GTX 1660 Ti (kế hoạch mục 8.1); tốc độ T4 chưa đo. Mỗi mô hình chạy mọi seed về sau
trên **cùng loại GPU (T4)**, nên notebook dừng ngay nếu GPU không phải T4.

## 2. Tài khoản Nam: tạo 2 dataset riêng tư (làm 1 lần)

1. Đăng nhập kaggle.com → nút **Create** (dấu +, cột trái) → **New Dataset**.
2. Kéo thả `camera-store-v3-code.zip` vào khung tải lên. Tiêu đề: `camera-store-v3-code`.
   Để chế độ **Private** (mặc định) → **Create**.
3. Làm lại bước 1–2 với `camera-store-v3-data.zip`, tiêu đề `camera-store-v3-data`.
4. Mở từng dataset, xem tab **Data** [chưa kiểm chứng]: Kaggle thường tự giải nén file .zip và giữ cây thư mục
   (thấy `ai/data/processed/...`, `manifest_sha256.json`). Nếu Kaggle giữ nguyên file .zip thì cũng được: notebook tự
   giải nén.
5. Chia sẻ cho Hải và Quyền: trong trang dataset → **Settings** (hoặc nút **Share**) → **Sharing** → thêm tên tài khoản
   Kaggle của Hải, Quyền, quyền **Can view** [chưa kiểm chứng tên nút].

Không bấm "Make Public". Code mới (commit khác) thì tạo **New Version** của dataset code (mục 9), không tạo dataset mới.

## 3. Mỗi người: tạo notebook trong tài khoản của mình

1. Tài khoản phải **xác minh số điện thoại** (Settings → Phone verification) thì mới bật được GPU và Internet.
2. **Create → New Notebook**. Menu **File → Import Notebook** → chọn `v3_runner.ipynb` → Import.
3. Đặt tên notebook `camera-store-v3-runner` (bấm vào tên ở góc trên).
4. Khung bên phải → **Input** → **+ Add Input** → tìm `camera-store-v3-code` → **+**; làm lại với
   `camera-store-v3-data`. (Hải, Quyền: dataset nằm ở mục chia sẻ với mình / "Shared with you".)
5. Khung bên phải → **Settings**:
   - **Accelerator** = `GPU T4 x2` (KHÔNG chọn P100). Notebook chỉ dùng 1 GPU.
   - **Internet** = On (notebook tải `uv`, Python 3.12.10 và thư viện đúng phiên bản như file lock).
   - Language Python, Environment để mặc định ("Pin to original environment" không cần).
6. Ô code đầu tiên: sửa `ACCOUNT = "nam"` thành `"hai"` / `"quyen"` cho đúng người. Không sửa gì khác.

## 3a. Môi trường thư viện (notebook tự làm, không cần thao tác)

Ô **Thư viện** cài `uv` (bản `UV_VERSION`) bằng pip của Kaggle, rồi tạo venv **Python 3.12.10** (cùng bản với
`ai/.venv` và venv RecBole ở máy nhóm) cho từng môi trường mà `JOBS` cần:

| Môi trường | Thư mục | Cài gì |
|---|---|---|
| `nhom` (code `ai/pipeline/`) | `/tmp/env_nhom` | `kaggle/requirements-kaggle.txt` (torch 2.14.1+cu126, PyG 2.8.0.post1, numpy 2.5.3, scipy 1.18.1), gói phụ thuộc ghim theo `ai/requirements-lock.txt` |
| `recbole` (RecBole, RecBole-GNN) | `/tmp/env_recbole` | đúng file `ai/recbole/requirements-recbole-lock.txt` (numpy 1.26.4, scipy 1.11.4, recbole 1.2.1, torch 2.14.1+cu126 ...), `--no-deps` như ở máy nhóm |

- Vì sao không dùng Python của Kaggle: ảnh Kaggle (Python 3.13 tại 11/2026) không có `ensurepip` nên
  `python -m venv` lỗi, và numpy 1.26.4 / scipy 1.11.4 không có bản cho Python 3.13.
- Sau khi cài, notebook so `pip freeze` của từng venv với file lock: gói nào lệch phiên bản thì dừng. Bản freeze lưu ở
  `logs/pip_freeze_<môi trường>_*.txt`.
- Khác máy nhóm (bắt buộc vì Kaggle chạy Linux): torch bản Linux có thêm các gói `nvidia-*` và `triton`; phiên bản
  các gói này do torch 2.14.1 quy định, ghi trong `summary.json` → `env.env_<môi trường>.not_in_lock`.
- Dung lượng: torch + gói `nvidia-*` chiếm khoảng vài GB trong `/tmp` (không nằm trong `/kaggle/working`, không vào
  Output) [chưa đo trên Kaggle].

## 3b. Chạy notebook kiểm môi trường trước (một lần cho mỗi gói mới)

`kiem_moi_truong.ipynb` là **cùng mã** với notebook chạy thật, chỉ khác `ACCOUNT = "kiem"`: dựng 2 venv như mục 3a,
kiểm phiên bản, rồi chạy **mọi việc của 3 tài khoản, mỗi việc 1 epoch + 1 lần chấm val** (KGIN, SimGCL, BPR-MF,
UltraGCN, BPR RecBole) để chắc cài đặt, import, đọc dữ liệu, huấn luyện, chấm, lưu checkpoint đều chạy được trên Linux.

1. **Create → New Notebook** → **File → Import Notebook** → chọn `kernel_kiem/kiem_moi_truong.ipynb`.
   Đặt tên `camera-store-v3-kiem-moi-truong`.
2. Thêm 2 dataset như mục 3 bước 4; Settings như mục 3 bước 5 (GPU T4, Internet On). Không sửa ô nào.
3. **Save Version → Save & Run All**.
4. Xem log phiên bản: ô cuối phải in `KIỂM MÔI TRƯỜNG: ĐẠT`. Nếu dừng với `TRƯỢT` hoặc lỗi ở ô nào: tải Output
   (`out/kiem_moi_truong/logs/`) gửi vào nhóm, **chưa chạy bản thật**.
5. Số liệu của lần kiểm (1 epoch) chỉ để kiểm, không dùng trong báo cáo. Ghi lại `env_setup_minutes` và số phút từng
   việc trong bảng `done` để ước tính giờ.

## 4. Chạy

1. Góc trên phải → **Save Version** → chọn **Save & Run All (Commit)** → **Save**.
   Notebook chạy nền trên máy Kaggle; đóng trình duyệt cũng được.
2. Theo dõi: trang notebook → **Versions** (hoặc Your Work → notebook) → bấm phiên bản đang chạy → xem log.
   Ô cuối in bảng `done`: mỗi việc có `status` = `xong` / `lỗi (mã ...)` / `ngắt ở mốc 8.5 giờ ...`.
3. Hạn mức [chưa kiểm chứng]: khoảng 30 giờ GPU / tuần / tài khoản; xem số giờ còn lại ở khung Settings → Quota.
   Notebook tự ngắt việc đang chạy ở mốc `JOB_DEADLINE_H = 8.5` giờ (thận trọng, vì giới hạn mỗi phiên chưa kiểm
   chứng; nếu xác nhận được là 12 giờ thì báo nhóm để nâng mốc) và vẫn lưu kết quả để chạy tiếp.

## 5. Lấy kết quả

1. Mở phiên bản đã chạy xong → tab **Output** → thư mục `out/<RUN_LABEL>/` (vd `out/thu_s1_nam/`) gồm `results/`
   (config, history, `last.pt` / `last_state.pth`, `result.json`), `logs/`, `summary.json` (sha256 mọi file).
2. **Download** (tải cả thư mục / "Download All") → gửi vào nhóm. Thư mục được đặt vào `results/kaggle/<RUN_LABEL>/`
   của repo ở máy nhóm (giữ nguyên tên) rồi kiểm: so sha256 với `summary.json`, đọc đường cong val.
3. Ghi vào bảng lần chạy: ngày, tài khoản, số phiên bản notebook, commit (trong `summary.json` → `env.commit`).

## 6. Chạy tiếp khi bị ngắt ở mốc giờ (`status` = "ngắt ở mốc ...")

1. Mở notebook → **Edit**.
2. **+ Add Input** → **Your Work** (hoặc Notebooks) → chọn chính notebook `camera-store-v3-runner` (output phiên bản vừa
   chạy) → **+**.
3. Ô cấu hình: đặt `RESUME = True`. **Giữ nguyên** `ACCOUNT` và `RUN_LABEL`.
4. **Save Version → Save & Run All**. Việc đã có `result.json` được bỏ qua; việc dở chạy tiếp từ lần chấm val gần nhất
   (đã kiểm ở máy nhóm: chạy tiếp cho đúng cùng quá trình, xem CHANGELOG 06/11).
5. Output phiên bản mới chứa toàn bộ kết quả (cả phần của phiên bản trước) và log cũ trong `logs/truoc/`.

Chạy tiếp phải dùng **cùng commit** với phiên bản trước (notebook kiểm `env.commit`); đổi sang notebook / code mới thì
bắt đầu lại với `RUN_LABEL` mới.

## 7. Chia sẻ notebook cho giảng viên hướng dẫn

- Cách chắc chắn: trang notebook → **Share** → **Add collaborators** → tên tài khoản Kaggle của GVHD, quyền
  **Can view**. GVHD xem được code, log từng phiên bản và output; dataset vẫn riêng tư.
- Để notebook **Public** khi dataset riêng tư: [chưa kiểm chứng] Kaggle có cho không và người xem thấy gì; chưa làm.

## 8. Nếu lỗi

- `cần GPU T4`: chưa chọn Accelerator = GPU T4 x2.
- Lỗi ở ô **Thư viện** (không tải được `uv` / Python 3.12.10 / thư viện, hoặc `phiên bản lệch`): kiểm Internet = On,
  chụp 30 dòng cuối gửi vào nhóm. Không tự đổi phiên bản thư viện (kết quả phải chạy trên đúng phiên bản trong file lock).
- `torch không thấy GPU`: chưa chọn Accelerator, hoặc GPU không được bản torch 2.14.1+cu126 hỗ trợ (P100).
- `sha256 lệch` / `không tìm thấy đúng một ...`: dataset tải lên thiếu file hoặc trùng; kiểm tab Data của dataset.
- Việc báo `lỗi (mã ...)`: notebook in 30 dòng cuối log của việc đó; gửi vào nhóm kèm file log trong Output.

## 9. Thay gói cũ bằng gói mới (commit mới)

1. Dataset code: trang `camera-store-v3-code` → **New Version** → tải `camera-store-v3-code.zip` của gói mới →
   **Create**. Dataset dữ liệu chỉ cần **New Version** khi `PACKAGE.md` của gói mới báo dữ liệu khác gói trước.
2. Chạy notebook kiểm của gói mới trước (mục 3b; lần đầu thì tạo mới, các lần sau Import đè như bước 3).
3. Notebook chạy thật: mở `camera-store-v3-runner` → **Edit** → **File → Import Notebook** → chọn `v3_runner.ipynb` của
   gói mới (thay toàn bộ ô; `EXPECT_COMMIT` mới đã điền sẵn) → sửa lại `ACCOUNT` cho đúng người.
4. Khung **Input**: dataset đã thêm tự dùng bản mới nhất [chưa kiểm chứng]; nếu thấy chữ "new version available" thì
   bấm cập nhật. Notebook kiểm commit, lệch thì dừng ở ô **Code**.
5. **Save Version → Save & Run All**.
