# Hướng dẫn chạy đợt `thu` trên Kaggle (làm trên web, không cần khóa API)

Viết 06/11/2026. Đợt `thu` = HỎI 10 (Nam chốt 06/11): mỗi baseline **seed 1, một cấu hình**, chỉ chấm val, để đo số
epoch dừng sớm và giờ GPU thật trước khi quyết lưới / số seed. Kế hoạch: `docs/reviews/v3_eval_plan.md` mục 6.1, 12.1.

Những chỗ ghi **[chưa kiểm chứng]** là mô tả giao diện / giới hạn Kaggle theo hiểu biết chung, chưa thử trên tài khoản
của nhóm. Gặp khác biệt thì ghi lại (ảnh chụp màn hình) để sửa file này.

## 0. Gói đã chuẩn bị (trên máy nhóm)

Thư mục `E:\DATN\kaggle_pkg\<tag>\` (do `kaggle/build_kaggle_package.py` sinh; xem `PACKAGE.md` trong đó):

| File | Dùng để |
|---|---|
| `camera-store-v3-code.zip` | dataset **code**: git bundle của repo (đúng commit) + bundle RecBole-GNN |
| `camera-store-v3-data.zip` | dataset **dữ liệu**: train / val / test, KG, file RecBole; `user_map.json` đã ẩn mã (`u0`, `u1`, ...) |
| `kernel/v3_runner.ipynb` | notebook (đã điền commit) |

## 1. Chia việc cho 3 tài khoản (HỎI 7)

Ô cấu hình đầu notebook có `ACCOUNT`; mỗi người chỉ đổi dòng này.

| Tài khoản | `ACCOUNT` | Việc (seed 1) | Ước tính |
|---|---|---|---|
| Nam | `"nam"` | KGIN, context_hops = 2 (mặc định RecBole) | nặng nhất: 41 s / epoch ở máy nhóm → có thể cần 2 phiên |
| Hải | `"hai"` | SimGCL, λ = 0,01 (giữa lưới đã đăng ký {0,005; 0,01; 0,05}) | 33 s / epoch ở máy nhóm → có thể cần 2 phiên |
| Quyền | `"quyen"` | BPR-MF code nhóm (λ2 = 1e-4), UltraGCN (cấu hình Electronics của tác giả), BPR của RecBole (đối chiếu) | nhẹ, thường 1 phiên |

Số giây / epoch là đo ngắn trên GTX 1660 Ti (kế hoạch mục 8.1); tốc độ T4 chưa đo. Mỗi mô hình chạy mọi seed về sau
trên **cùng loại GPU (T4)**, nên notebook dừng ngay nếu GPU không phải T4.

## 2. Nam: tạo 2 dataset riêng tư (làm 1 lần)

1. Đăng nhập kaggle.com → nút **Create** (dấu +, cột trái) → **New Dataset**.
2. Kéo thả `camera-store-v3-code.zip` vào khung tải lên. Tiêu đề: `camera-store-v3-code`.
   Để chế độ **Private** (mặc định) → **Create**.
3. Làm lại bước 1–2 với `camera-store-v3-data.zip`, tiêu đề `camera-store-v3-data`.
4. Mở từng dataset, xem tab **Data** [chưa kiểm chứng]: Kaggle thường tự giải nén file .zip và giữ cây thư mục
   (thấy `ai/data/processed/...`, `manifest_sha256.json`). Nếu Kaggle giữ nguyên file .zip thì cũng được: notebook tự
   giải nén.
5. Chia sẻ cho Hải và Quyền: trong trang dataset → **Settings** (hoặc nút **Share**) → **Sharing** → thêm tên tài khoản
   Kaggle của Hải, Quyền, quyền **Can view** [chưa kiểm chứng tên nút].

Không bấm "Make Public". Code mới (commit khác) thì tạo **New Version** của dataset code, không tạo dataset mới.

## 3. Mỗi người: tạo notebook trong tài khoản của mình

1. Tài khoản phải **xác minh số điện thoại** (Settings → Phone verification) thì mới bật được GPU và Internet.
2. **Create → New Notebook**. Menu **File → Import Notebook** → chọn `v3_runner.ipynb` → Import.
3. Đặt tên notebook `camera-store-v3-runner` (bấm vào tên ở góc trên).
4. Khung bên phải → **Input** → **+ Add Input** → tìm `camera-store-v3-code` → **+**; làm lại với
   `camera-store-v3-data`. (Hải, Quyền: dataset nằm ở mục chia sẻ với mình / "Shared with you".)
5. Khung bên phải → **Settings**:
   - **Accelerator** = `GPU T4 x2` (KHÔNG chọn P100). Notebook chỉ dùng 1 GPU.
   - **Internet** = On (để cài đúng torch / RecBole như file lock).
   - Language Python, Environment để mặc định ("Pin to original environment" không cần).
6. Ô code đầu tiên: sửa `ACCOUNT = "nam"` thành `"hai"` / `"quyen"` cho đúng người. Không sửa gì khác.

## 4. Chạy

1. Góc trên phải → **Save Version** → chọn **Save & Run All (Commit)** → **Save**.
   Notebook chạy nền trên máy Kaggle; đóng trình duyệt cũng được.
2. Theo dõi: trang notebook → **Versions** (hoặc Your Work → notebook) → bấm phiên bản đang chạy → xem log.
   Ô cuối in bảng `done`: mỗi việc có `status` = `xong` / `lỗi (mã ...)` / `ngắt ở mốc 8.5 giờ ...`.
3. Hạn mức [chưa kiểm chứng]: khoảng 30 giờ GPU / tuần / tài khoản; xem số giờ còn lại ở khung Settings → Quota.
   Notebook tự ngắt việc đang chạy ở mốc `JOB_DEADLINE_H = 8.5` giờ (thận trọng, vì giới hạn mỗi phiên chưa kiểm
   chứng; nếu xác nhận được là 12 giờ thì báo Nam/Claude để nâng mốc) và vẫn lưu kết quả để chạy tiếp.

## 5. Lấy kết quả

1. Mở phiên bản đã chạy xong → tab **Output** → thư mục `out/<RUN_LABEL>/` (vd `out/thu_s1_nam/`) gồm `results/`
   (config, history, `last.pt` / `last_state.pth`, `result.json`), `logs/`, `summary.json` (sha256 mọi file).
2. **Download** (tải cả thư mục / "Download All") → gửi Nam. Nam đặt vào
   `E:\DATN\camera-store\results\kaggle\<RUN_LABEL>\` (giữ nguyên tên) và báo Claude kiểm (so sha256 với `summary.json`,
   đọc đường cong val).
3. Ghi vào bảng lần chạy: ngày, tài khoản, số phiên bản notebook, commit (trong `summary.json` → `env.commit`).

## 6. Chạy tiếp khi bị ngắt ở mốc giờ (`status` = "ngắt ở mốc ...")

1. Mở notebook → **Edit**.
2. **+ Add Input** → **Your Work** (hoặc Notebooks) → chọn chính notebook `camera-store-v3-runner` (output phiên bản vừa
   chạy) → **+**.
3. Ô cấu hình: đặt `RESUME = True`. **Giữ nguyên** `ACCOUNT` và `RUN_LABEL`.
4. **Save Version → Save & Run All**. Việc đã có `result.json` được bỏ qua; việc dở chạy tiếp từ lần chấm val gần nhất
   (đã kiểm ở máy nhóm: chạy tiếp cho đúng cùng quá trình, xem CHANGELOG 06/11).
5. Output phiên bản mới chứa toàn bộ kết quả (cả phần của phiên bản trước) và log cũ trong `logs/truoc/`.

## 7. Chia sẻ notebook cho cô (HỎI 8)

- Cách chắc chắn: trang notebook → **Share** → **Add collaborators** → tên tài khoản Kaggle của cô, quyền **Can view**.
  Cô xem được code, log từng phiên bản và output; dataset vẫn riêng tư.
- Để notebook **Public** khi dataset riêng tư: [chưa kiểm chứng] Kaggle có cho không và người xem thấy gì; chưa làm.

## 8. Nếu lỗi

- `cần GPU T4`: chưa chọn Accelerator = GPU T4 x2.
- Lỗi khi `pip install` (không tải được / không có bản cho Python của Kaggle): chụp 30 dòng cuối gửi Nam. Không tự đổi
  phiên bản thư viện (kết quả phải chạy trên đúng phiên bản trong file lock).
- `sha256 lệch` / `không tìm thấy đúng một ...`: dataset tải lên thiếu file hoặc trùng; kiểm tab Data của dataset.
- Việc báo `lỗi (mã ...)`: notebook in 30 dòng cuối log của việc đó; gửi Nam kèm file log trong Output.
