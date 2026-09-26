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
