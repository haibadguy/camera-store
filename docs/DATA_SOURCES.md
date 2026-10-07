# Nguồn dữ liệu

Mọi dữ liệu bên ngoài mà nhóm dùng. Dữ liệu **không đưa lên git** (`.gitignore`: `ai/data/raw/`, `ai/data/external/`). Muốn tái lập thì tải lại theo đúng phiên bản ghi dưới đây.

> **Nguyên tắc:** các nguồn ở mục 2 **chỉ làm đáp án đối chiếu** khi đo độ chính xác của nội dung 3 (QĐ 10). Chúng **không** được dùng trong quy tắc (`ai/pipeline/mount_detect.py`, `ai/config/mount_rules.toml`), để quy tắc và đáp án độc lập với nhau.

## 1. Dữ liệu chính

| | |
|---|---|
| Tên | Amazon Reviews 2023, nhóm Electronics |
| Trang | https://amazon-reviews-2023.github.io/ |
| File | `ai/data/raw/Electronics.jsonl.gz` (6.474.438.619 B), `ai/data/raw/meta_Electronics.jsonl.gz` (1.312.900.427 B). sha256 ghi ở `docs/CHANGELOG.md` |
| Phiên bản | Last-Modified trên server: 16/01/2025 |
| Dùng cho | Toàn bộ pipeline (nội dung 2–5) |

## 2. Nguồn đáp án cho nội dung 3 (tải ngày 07/10/2026)

### 2.1. Lensfun
| | |
|---|---|
| Là gì | Cơ sở dữ liệu mở về máy ảnh và ống kính, dùng để sửa méo ảnh |
| Trang | https://github.com/lensfun/lensfun |
| Giấy phép | **Dữ liệu: CC BY-SA 3.0** (thư mục `data/`); mã nguồn thư viện LGPL-3.0. Trích từ README của repo: "The lens database is licensed under the Creative Commons Attribution-Share Alike 3.0 license (CC BY-SA 3.0)" |
| Phiên bản | commit `bbd4332a9ec566fd9aa548c9e0d8ced238c56261` (nhánh master, tải ngày 07/10/2026) |
| File | `ai/data/external/lensfun/*.xml` (56 file XML + 2 file schema, khoảng 5,1 MB), `COMMIT_SHA.txt`, `LICENSE_README.md` |
| Nội dung | 1.057 máy ảnh (có `mount` và `cropfactor`), 1.569 ống kính (có một hoặc nhiều `mount`) |
| Dùng để chấm | **Loại** (thân thay ống / máy ống liền / ống), **ngàm** thân và ống, **khung** của thân (suy từ `cropfactor`: ≤ 1,1 → ff; 1,45–1,75 → apsc; còn lại → khac) |
| Hạn chế đã thấy | (1) `cropfactor` và đôi khi cả `mount` của **ống** là của **máy dùng để hiệu chỉnh**, không phải của ống. Vd "Canon EF 75-300mm F4-5.6 III" ghi `mount = Canon EF-S`, hiệu chỉnh trên EOS 60D (`slr-canon.xml`, dòng 8014–8018). Vì vậy **không chấm khung của ống** bằng Lensfun. (2) Tên máy là tên EXIF, không phải tên bán ở Mỹ (vd "EOS 600D" thay vì "Rebel T3i"), nên một số máy không khớp được |
| Ghi công | Nếu công bố số liệu suy ra từ nguồn này: "Dữ liệu Lensfun (https://github.com/lensfun/lensfun), CC BY-SA 3.0". Không đưa bản sao dữ liệu lên repo. Nếu sau này phát hành dữ liệu suy ra từ Lensfun thì phải dùng cùng giấy phép (share-alike) |

### 2.2. openMVG Camera Sensor Size Database
| | |
|---|---|
| Trang | https://github.com/openMVG/CameraSensorSizeDatabase |
| Giấy phép | **MIT** (file `LICENSE`, "Copyright (c) 2014 Camera Sensor Size Database authors") |
| Phiên bản | commit `07da7acbf97348405cf859ce76a00ac642ba1fc5` (tải ngày 07/10/2026) |
| File | `ai/data/external/openmvg/sensor_database.csv` (3.639 dòng: hãng, model, bề rộng cảm biến mm), `sensor_database_detailed.csv`, `LICENSE`, `README.md` |
| Dùng để chấm | **Khung của thân**: bề rộng ≥ 34 mm → ff; 26–34 → khac (APS-H); 20–26 → apsc; còn lại → khac |
| Hạn chế | Không có ngàm. Không phân biệt máy thay ống với máy ống liền |

### 2.3. Wikidata
| | |
|---|---|
| Trang | https://query.wikidata.org/ (SPARQL) |
| Giấy phép | **CC0** (dữ liệu có cấu trúc của Wikidata) |
| Truy vấn | `ai/data/external/wikidata/query_mount_models.rq`: các item thuộc lớp camera model / digital camera model / product model / product line / lens model / camera lens có thuộc tính **P2935 (connector)** trỏ tới một chuẩn kỹ thuật (Q317623, tức một ngàm) |
| Thời điểm | `2026-10-07T15:29:24Z` (`RETRIEVED_AT.txt`) |
| File | `ai/data/external/wikidata/mount_models.json` (1.132 dòng, 987 item) |
| Dùng để chấm | **Loại** và **ngàm** (thân và ống) |
| Hạn chế | Không có khổ cảm biến. Thân Canon APS-C thường ghi cả "EF" và "EF-S" → quy về `canon_efs`. Một số ống nằm ở lớp "product model" → script nhận ra ống khi tên có tiêu cự và khẩu độ |

### 2.4. Các trang nguồn của bảng luật `ai/config/mount_rules.toml`
- 14 trang, chủ yếu là trang hãng: Canon, Nikon, Sony, Ricoh/Pentax, Sigma, Olympus. Danh sách URL và câu trích nằm trong `[sources.*]` của file TOML.
- Bản sao văn bản đã đọc: `ai/data/external/rule_sources/`.
- Tất cả được mở và đọc ngày 07/10/2026, bằng curl hoặc trình duyệt tích hợp.
- Trang B&H (bán lẻ) bật kiểm tra chống bot nên **không đọc**. Ba nguồn bán lẻ đã được thay bằng trang hãng.

## 3. Cách tải lại

```bash
# Lensfun (đúng commit)
SHA=bbd4332a9ec566fd9aa548c9e0d8ced238c56261
# tải từng file trong data/db/ tại commit đó: https://raw.githubusercontent.com/lensfun/lensfun/$SHA/data/db/<file>

# openMVG
SHA2=07da7acbf97348405cf859ce76a00ac642ba1fc5
# https://raw.githubusercontent.com/openMVG/CameraSensorSizeDatabase/$SHA2/sensor_database.csv

# Wikidata: chạy lại query_mount_models.rq ở https://query.wikidata.org/sparql (kết quả có thể khác vì Wikidata luôn được sửa)
```

Khi gọi web, User-Agent chỉ ghi tên dự án chung chung, **không** kèm thông tin cá nhân (quy tắc trong `CLAUDE.md`).

## 4. Script dùng các nguồn này
- `ai/survey/content3/eval_external.py`: đo độ chính xác của quy tắc. Kết quả ở `ai/data/survey/eval_external_*.{csv,json}`, `run_eval_external.log`.
