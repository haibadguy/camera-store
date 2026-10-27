# Camera Store — đồ án tốt nghiệp

**Đề tài:** Hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh trong thương mại điện tử bằng mô hình gợi ý lai có ràng buộc và giải thích được. GVHD: TS. Đỗ Thị Liên. Nhóm: Nam, Hải, Quyền.

Dữ liệu: Amazon Reviews 2023, nhóm Electronics. Trạng thái dự án, quyết định và hạn chế: **`docs/STATUS.md`** (nguồn sự thật). Lịch sử sửa so với bản của Hải: `docs/CHANGELOG.md`.

## Kiến trúc demo

React (`frontend/`) → Spring Boot (`backend/`, nghiệp vụ) → FastAPI (dịch vụ mô hình `ai/service/`, nội dung 10). Quyết định giữ Spring Boot: `docs/STATUS.md`, nhật ký 09/10/2026. Hiện (28/10) Spring Boot gọi FastAPI theo `docs/api_contract.md` 1.3 (cách chạy: `backend/README.md`; chưa có database / đăng nhập); React gọi Spring khi đặt `VITE_RECOMMENDATION_SOURCE=api` (`run_demo.ps1` luôn đặt); chạy Vite tay thì mặc định đọc dữ liệu giả `frontend/src/mock/` và trang hiện nhãn "Dữ liệu mẫu". Chạy cả ba bằng một lệnh: mục "Chạy demo trên máy khác".

## Thư mục chính

| Thư mục | Nội dung |
|---|---|
| `backend/` | Spring Boot API, JPA entities, Flyway migrations |
| `frontend/` | React + Vite (TypeScript, TailwindCSS) |
| `ai/pipeline/` | Code nội dung 1–5 (script `01`…`05`, `common_05.py`, `eval_05.py`, ...) |
| `ai/config/` | Luật và cấu hình: `mount_rules.toml`, `usecase_rules.toml`, `n5_final.toml` |
| `ai/data/raw/` | Dữ liệu gốc (không sửa, không lên git) |
| `ai/data/processed/` | Đầu ra script 01–02 (k-core, train/val/test) |
| `ai/data/kg/` | Đầu ra script 03–04 (ma trận tương thích M, đồ thị tri thức `kg_hetero.pt`) |
| `ai/survey/` | Script khảo sát, kiểm chứng, đo cho báo cáo; log ở `ai/data/survey/` |
| `results/n5/` | Kết quả nội dung 5 (val, test cuối) |
| `docs/` | `STATUS.md`, `CHANGELOG.md`, thiết kế, kế hoạch đánh giá `docs/reviews/` |

## Môi trường

Windows 11, Python 3.12, GPU CUDA 12.6. Luôn dùng venv `ai/.venv`; môi trường chuẩn để tái lập kết quả là `ai/requirements-lock.txt` (`ai/requirements.txt` chỉ ghi phiên bản tối thiểu).

```powershell
py -3.12 -m venv ai\.venv
ai\.venv\Scripts\python.exe -m pip install -r ai/requirements-lock.txt
```

## Thứ tự chạy (từ thư mục gốc repo)

Đặt `Electronics.jsonl.gz` và `meta_Electronics.jsonl.gz` vào `ai/data/raw/`.

```powershell
# 1. Lọc nhóm camera, gộp tương tác lặp, k-core (k = 5)  -> ai/data/processed/
ai\.venv\Scripts\python.exe ai/pipeline/01_filter_camera_domain.py
# 2. Chia train/val/test theo thời gian                   -> ai/data/processed/
ai\.venv\Scripts\python.exe ai/pipeline/02_split_time_aware.py
# 3. Ngàm, khung, ma trận tương thích M (thêm --overwrite nếu ai/data/kg đã có file)  -> ai/data/kg/
ai\.venv\Scripts\python.exe ai/pipeline/03_mount_compat.py --out-dir ai/data/kg
# 4. Đồ thị tri thức + 8 kiểm tra (--run-label đặt tên log, không ghi đè log cũ)       -> ai/data/kg/
ai\.venv\Scripts\python.exe ai/pipeline/04_build_knowledge_graph.py --run-label <nhãn>
# 5a. Dò siêu tham số trên val (LightGCN, R-GCN; chạy tiếp được nếu bị ngắt)           -> results/n5/val_sweep_<nhãn>/
ai\.venv\Scripts\python.exe ai/pipeline/05_val_sweep.py --label <nhãn>
# 5b. Cấu hình chốt: ai/config/n5_final.toml (đã chốt 09/10/2026, không sửa sau khi chấm test)
# 5c. Chấm test đúng một lần, Popularity, MountAware, LightGCN, R-GCN (3 seed cho hai mô hình huấn luyện) (thử --split val trước; --out phải là thư mục mới)
ai\.venv\Scripts\python.exe ai/pipeline/05_test_final.py --split val  --out results/n5/<nhãn mới>
ai\.venv\Scripts\python.exe ai/pipeline/05_test_final.py --split test --out results/n5/<nhãn mới>
```

Huấn luyện từng mô hình riêng: `05b_lightgcn_train.py --l2 <λ> --seed <s> --run-dir <thư mục>`, `05c_rgcn_train.py --lr <lr> --seed <s> --run-dir <thư mục>`, `05a_popularity.py --split val --out <thư mục>`.

## Kết quả nằm ở đâu

- Số test cuối nội dung 5: `results/n5/test_final_20261009/summary_test_20261009_125536.{json,md}`; bảng đọc nhanh ở `docs/STATUS.md` mục 3.
- Đồ thị và ma trận M: `ai/data/kg/` (`kg_stats.json`, `mount_compat_stats.json`, log kiểm tra `kg_validation_log_*.txt`).
- Dữ liệu sau lọc: `ai/data/processed/` (`filtering_stats.json`, `train.txt`, `val.txt`, `test.txt`).
- Log mỗi lần chạy ghi ra file tên mới kèm ngày/nhãn, không ghi đè.

## Chạy backend và frontend (khung demo)

Cần: Git, Node.js (LTS), JDK 21 trở lên, Maven (hoặc tích hợp trong IDE); Docker Desktop chỉ cần khi làm database. Chỉ làm bước 1–2 một lần đầu.

1. Clone: `git clone https://github.com/haibadguy/camera-store.git`, rồi `cd camera-store`.
2. Cài thư viện frontend:
   ```powershell
   cd frontend
   npm install
   cd ..
   ```
3. Terminal 0, dịch vụ mô hình FastAPI seed 1 (`http://127.0.0.1:8001`, cần `ai/.venv`, xem `ai/README.md`):
   ```powershell
   ai\.venv\Scripts\python.exe ai/service/run_service.py --emb-dir results/service/emb_s1_20261021 --port 8001
   ```
   (Database chưa dùng: backend hiện chạy không cần PostgreSQL. Khi làm database: bật Docker Desktop rồi
   `docker compose up -d postgres redis`.)
4. Terminal 1, backend Spring Boot (`http://localhost:8080`, chi tiết `backend/README.md`):
   ```powershell
   cd backend
   mvn spring-boot:run
   ```
5. Terminal 2, frontend React + Vite (`http://localhost:5173`):
   ```powershell
   cd frontend
   npm run dev
   ```

Cơ sở dữ liệu của demo: PostgreSQL 17, Redis 7 (Docker). Tài liệu cũ về kiến trúc, kế hoạch, setup: `docs/setup.md`, `docs/plan.md`, `docs/architecture.md` (một phần đã lỗi thời, xem `docs/STATUS.md`).

## Chạy demo trên máy khác

Demo = FastAPI (dịch vụ mô hình, seed 1) → Spring Boot → React (Vite), bật cả ba bằng `run_demo.ps1` (Windows,
PowerShell). Đã thử trên máy của Nam 28/10/2026, cả khi repo nằm ở đường dẫn có dấu cách; **chưa thử trên máy thứ hai**.
Lần đầu cần mạng (pip, `npm ci`, Maven); sau khi đã có `backend/target/*.jar` thì chạy demo không cần mạng.

**1. Cài phần mềm**

| Cần | Phiên bản | Ghi chú |
|---|---|---|
| Python | **3.12** (đúng 3.12; `run_demo.ps1` dừng nếu venv khác 3.12) | tải ở python.org, có kèm `py` |
| JDK | 21 trở lên (máy Nam: 24) | `java -version` |
| Maven | 3.9 | `mvn -v` |
| Node.js | LTS (máy Nam: 24.11) | `node --version` |

Tạo venv từ file lock (lần đầu; torch bản CUDA 12.6 khá nặng, vẫn chạy được trên máy không có GPU vì dịch vụ chạy CPU):

```powershell
py -3.12 -m venv ai\.venv
ai\.venv\Scripts\python.exe -m pip install -r ai/requirements-lock.txt
```

**2. Lấy 5 file dữ liệu không có trong git** (Nam gửi; tổng 28,5 MiB). Đặt đúng đường dẫn dưới đây (tính từ thư mục
`camera-store`). Danh sách đo bằng `ai/service/list_runtime_files.py` (mọi file dịch vụ đọc khi chạy, kết quả
`results/demo/runtime_files_20261028_lan1/files.json`); các file khác dịch vụ cần đều đã có trong git.

| File | Kích thước (byte) | sha256 |
|---|---:|---|
| `results/service/emb_s1_20261021/embeddings.npz` | 24.474.350 | `fbda48a1f84c9fd0047d2a8d06319e1e816dcf20cbe51817f5f86241f97200b4` |
| `ai/data/processed/train.txt` | 3.015.661 | `ebd29b03a4866cfca243edc1ee31539f16be19b756bfbd4c388e3f20ca06a5c5` |
| `ai/data/processed/val.txt` | 846.700 | `e8a47d06bd6e6977fe7eebc485cbf07eb75e7e9bdb651da955e8fd7f85a3a900` |
| `ai/data/processed/test.txt` | 850.792 | `410fc46cea72cdc5115a3e0413036456d1d1d59b8bcb7c63da6edd026e4da8ea` |
| `ai/data/processed/item_map.json` | 659.453 | `c7ccd84b3fbcc5cf7cab85171fdf187dea8deccf3d36aaceb4877f06cfdaa63c` |

`embeddings.npz` là vector LightGCN seed 1 tính sẵn từ checkpoint đã chốt (`meta.json` cùng thư mục có trong git và ghi
sha256 của nó). Kiểm sau khi chép: `Get-FileHash <file> -Algorithm SHA256`; `run_demo.ps1` tự kiểm cả 5 file và dừng
nếu thiếu hoặc sai. Nếu không có file từ Nam: chạy lại bước 1–2 của "Thứ tự chạy" (cần dữ liệu gốc Amazon) để có
`ai/data/processed/`, rồi `ai/service/export_embeddings.py --seed 1` (cần `best.pt` của nội dung 5, xem `ai/README.md`).

**3. Chạy**

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
```

Script kiểm máy (Python 3.12, JDK ≥ 21, sha256 của 5 file, cổng đang bị chiếm hoặc nằm trong khoảng Windows giữ riêng),
`npm ci` nếu chưa có `frontend/node_modules`, đóng gói Spring **chỉ khi chưa có jar** (hoặc khi thêm `-Build`, cần sau
khi đổi code backend), rồi bật FastAPI (cổng 8001, ~15–20 s), Spring (8080, heap tối đa 512 MB, chỉ nghe 127.0.0.1),
Vite (5173, chế độ api). Mở `http://127.0.0.1:5173`, bấm **"Tư vấn thiết bị"**, chọn người 409 / 47 hoặc nhập mã người
dùng khác (0–67.660, vd 178 nhiều hệ máy, 1476 có thân ngoài bảng tương thích, 0 chưa có thân). Bấm thử một lượt trước
khi trình bày. Nhấn Enter trong cửa sổ PowerShell để tắt cả ba. Log mỗi lần chạy: `results/demo/run_demo_logs/<ngày_giờ>/`.
Tùy chọn: `-Build`, `-SpringHeap 768m`, `-FastApiPort` / `-SpringPort` / `-VitePort`.

Kiểm tự động cả chuỗi (trình duyệt Edge có sẵn của Windows, Playwright; lần đầu `npm install` trong `tools/demo_e2e/`):
`ai\.venv\Scripts\python.exe ai/service/check_demo.py --label <nhãn>` → `results/demo/check_demo_<nhãn>/` (ảnh màn
hình, `summary.json`).
