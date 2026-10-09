# Camera Store — đồ án tốt nghiệp

**Đề tài:** Hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh trong thương mại điện tử bằng mô hình gợi ý lai có ràng buộc và giải thích được. GVHD: TS. Đỗ Thị Liên. Nhóm: Nam, Hải, Quyền.

Dữ liệu: Amazon Reviews 2023, nhóm Electronics. Trạng thái dự án, quyết định và hạn chế: **`docs/STATUS.md`** (nguồn sự thật). Lịch sử sửa so với bản của Hải: `docs/CHANGELOG.md`.

## Kiến trúc demo

React (`frontend/`) → Spring Boot (`backend/`, nghiệp vụ) → FastAPI (dịch vụ mô hình, nội dung 10, chưa viết). Quyết định giữ Spring Boot: `docs/STATUS.md`, nhật ký 10/10/2026. Hiện `backend/` và `frontend/` là khung có từ trước, chưa nối với mô hình.

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

Cần: Git, Node.js (LTS), JDK 17 hoặc 21, Maven (hoặc tích hợp trong IDE), Docker Desktop. Chỉ làm bước 1–2 một lần đầu.

1. Clone: `git clone https://github.com/haibadguy/camera-store.git`, rồi `cd camera-store`.
2. Cài thư viện frontend:
   ```powershell
   cd frontend
   npm install
   cd ..
   ```
3. Bật Docker Desktop (đợi *Engine Running*), rồi khởi động database mỗi lần bắt đầu làm việc, từ thư mục gốc repo:
   ```powershell
   docker compose up -d postgres redis
   ```
4. Terminal 1, backend Spring Boot (`http://localhost:8080`):
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
