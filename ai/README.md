# AI Recommendation & Knowledge Graph System (Camera Store)

Hệ thống tư vấn & gợi ý cá nhân hóa thiết bị nhiếp ảnh dựa trên ràng buộc tương thích vật lý (Constraint-aware) và Đồ thị tri thức (Explainable Knowledge Graph).

---

## Cấu trúc thư mục (Directory Structure)

```text
ai/
├── README.md                      # Hướng dẫn tổng quan
├── requirements.txt               # Thư viện Python cần thiết
│
├── docs/                          # Báo cáo kỹ thuật chi tiết từng mục (Nộp giảng viên)
│   ├── 01_PIPELINE_ARCHITECTURE.md# Mục 1: Pipeline tổng quát
│   ├── 02_DATA_PREPROCESSING.md   # Mục 2: Tiền xử lý, lọc k-core & phân chia dữ liệu
│   ├── 03_ENTITY_LINKING_MATRIX.md# Mục 3: Khớp nối thực thể & Ma trận tương thích M
│   ├── 04_KNOWLEDGE_GRAPH.md      # Mục 4: Xây dựng Đồ thị tri thức PyG HeteroData
│   └── 05_BASELINE_BENCHMARK.md   # Mục 5: Kết quả thực nghiệm đối chứng (NDCG, Recall, CVR)
│
├── data/                          # Quản lý dữ liệu qua các giai đoạn
│   ├── raw/                       # Dữ liệu thô từ Amazon Reviews 2023 (.jsonl.gz)
│   ├── specs/                     # Thông số kỹ thuật chuẩn (Body, Lens, Mount, Sensor)
│   ├── processed/                 # Dữ liệu sau lọc k-core (train.txt, val.txt, test.txt)
│   └── kg/                        # Ma trận M (.npz), bảng ngàm (.csv), đồ thị PyG (.pt)
│
├── pipeline/                      # Các script thực thi theo thứ tự logic
│   ├── 01_filter_camera_domain.py # Lọc domain Camera & k-core filtering
│   ├── 02_split_time_aware.py     # Phân chia train/val/test theo chuẩn Leave-one-out
│   ├── 03_entity_linking.py       # Entity Linking (Regex + Fuzzy + Sentence-Transformers)
│   ├── 04_build_mount_matrix.py   # Tạo ma trận tương thích cứng M (Sparse CSR)
│   └── 05_build_knowledge_graph.py# Tạo đồ thị dị thể HeteroData G=(V,E,R)
│
├── models/                        # Mã nguồn mô hình & đo lường
│   ├── baselines/                 # Popularity (Rule-based), LightGCN, RGCN
│   ├── metrics.py                 # Bộ đo: Recall@K, NDCG@K, Hit@K, CVR@K
│   └── trainer.py                 # Loop huấn luyện BPR loss, early stopping
│
├── experiments/                   # Quản lý kết quả thử nghiệm & log
│   ├── logs/                      # Log từng epoch
│   └── baseline_benchmark.csv     # Bảng số liệu benchmark tổng hợp
│
└── checkpoints/                   # Lưu model weights (.pt)
```

---

## Hướng dẫn cài đặt & Thực thi từng bước

```bash
# 1. Cài đặt môi trường
pip install -r requirements.txt

# 2. Bước 1 -> 2: Lọc dữ liệu Amazon & chia tập
python pipeline/01_filter_camera_domain.py
python pipeline/02_split_time_aware.py

# 3. Bước 3: Entity Linking & Tạo ma trận tương thích M
python pipeline/03_entity_linking.py
python pipeline/04_build_mount_matrix.py

# 4. Bước 4: Tạo đồ thị tri thức PyTorch Geometric
python pipeline/05_build_knowledge_graph.py

# 5. Bước 5: Chạy benchmark các baseline & xuất báo cáo
python -m models.baselines.run_benchmark
```

---

## Dịch vụ mô hình (FastAPI, nội dung 10) — thêm 21/10/2026

> Phần trên là cấu trúc cũ của bản 62abf54, nhiều đường dẫn không còn đúng; trạng thái thật xem `docs/STATUS.md`.

Thư mục `ai/service/`: dịch vụ HTTP cho **hệ thống cuối = LightGCN + mặt nạ QĐ 4-9 + giải thích theo đường**.
Hợp đồng API (cho Spring Boot / React): `docs/api_contract.md`. Kiến trúc demo: React → Spring Boot → FastAPI.

| File | Việc |
|---|---|
| `export_embeddings.py` | chạy **một lần**: nạp `best.pt` đã chốt (`ai/config/n5_final.toml`, kiểm sha256), lan truyền LightGCN, ghi `results/service/emb_s<seed>_<nhãn>/embeddings.npz` + `meta.json` |
| `core.py` | lõi: dùng lại `eval_05.full_rank`, `certain_violation_mask`, `eval_cakg.mask_scorer`, `09_explain_lightgcn.LGExplainer`, `eval_cakg.sentence`, `verify_explanation`, `03_mount_compat.Rules` (không viết lại logic) |
| `app.py` | lớp HTTP (FastAPI): `/health`, `/recommend`, `/items/{id}`, `/users/{id}/bodies`, `/compat`, định dạng lỗi chung |
| `run_service.py` | bật dịch vụ (uvicorn), mỗi lần chạy một log tên mới trong `results/service/logs/` |
| `check_service.py` | kiểm khớp với kết quả đã lưu, kiểm hợp đồng, đo độ trễ qua HTTP |

Chạy (từ thư mục `camera-store`, chỉ cần CPU; thư viện trong `ai/requirements-lock.txt`):

```bash
ai\.venv\Scripts\python.exe ai/service/export_embeddings.py --seed 1 --label 20261021
ai\.venv\Scripts\python.exe ai/service/run_service.py --emb-dir results/service/emb_s1_20261021 --port 8001
curl "http://127.0.0.1:8001/recommend?user_id=409&k=10"
ai\.venv\Scripts\python.exe ai/service/check_service.py --emb-dir results/service/emb_s1_20261021 --label <nhãn>
```

`embeddings.npz` (~24 MB / seed) không lên git: chạy lại `export_embeddings.py` để tạo (cần `best.pt` của nội dung 5).
