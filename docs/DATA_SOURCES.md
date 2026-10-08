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

### 2.4. Các trang nguồn của bảng luật `ai/config/mount_rules.toml` và bảng mã `ai/config/sony_lens_codes.toml`
Từ 08/10/2026 (bảng luật v0.5, theo Red Team T5) áp **chuẩn QĐ nội dung 4 – 15**: mỗi trang có bản sao HTML + bản văn bản, sha256 của cả hai ghi trong TOML; mỗi luật có danh sách căn cứ (nguồn + câu trích nguyên văn, liền một đoạn); script `ai/survey/content3/check_rule_sources.py` kiểm sha256, kiểm bản sao có phần nội dung bài (không phải trang lỗi / trang chặn) và kiểm từng câu trích. Lần kiểm 08/10: 16 nguồn + 13 mã Sony đều OK, mọi căn cứ OK (log `ai/data/survey/run_check_rule_sources_20261008_rt1b_lan2.log`).

- Thư mục (không lên git):
  - `ai/data/external/rule_sources/qd415/`: bản chính (curl hoặc Wayback thô `id_`), văn bản `.txt` tạo bằng `ai/survey/content4/html_to_text.py`;
  - `ai/data/external/rule_sources/qd415/sony_jp/`: trang thông số 13 ống Sony trên sony.jp (Shift_JIS);
  - `ai/data/external/rule_sources_manual/`: bản Nam lưu bằng trình duyệt (Olympus);
  - `ai/data/external/rule_sources/*.html|.txt`: bản đọc ngày 07/10 (giữ nguyên, không dùng nữa).
- **Bản 07/10 có 6 file không dùng được**: 4 file là trang lỗi "Access Denied" của Canon Europe (`canon_ef_eos_r`, `canon_ef_eos_m`) và Sony (`sony_e_apsc`, `sony_dt`); `olympus_mmf.html` là trang chặn bot "Just a moment…"; `sony_la_ea.html` gần rỗng. Tức là câu trích của các nguồn này trong bản luật 07/10 không có bản sao hợp lệ làm bằng chứng (cách đọc hôm đó không còn ghi lại được).

| Nguồn (khóa TOML) | Cách lưu | Bản chính (tính từ `ai/data/external/`) |
|---|---|---|
| `canon_efs`, `canon_rfs`, `nikon_dx_fx`, `nikon_z_area`, `nikon_ftz`, `nikon_ft1`, `pentax_k1_crop`, `sigma_dc` | curl ngày 07/10/2026 (chép nguyên file sang `qd415/`, thêm hậu tố ngày) | `rule_sources/qd415/*_20261007.html` |
| `canon_ef_eos_r`, `canon_ef_eos_m` | curl bản Wayback thô `id_` (20260420101801, 20260521110121) ngày 08/10/2026; trang hãng trả 403 với curl | `rule_sources/qd415/canon_ef_eos_*_wb2026*.html` |
| `sony_e_apsc`, `sony_dt` | curl bản Wayback thô `id_` (20231204224307, 20231002215307) ngày 08/10/2026; sony.ca / sony.com trả 403. Bản Wayback mới nhất có HTTP 200 là năm 2023. `sony_dt` dùng cho cả luật LA-EA (v0.4 tách thành `sony_la_ea` cùng URL, nay gộp) | `rule_sources/qd415/sony_*_wb2023*.html` |
| `olympus_mmf` | **Nam lưu bằng trình duyệt ngày 08/10/2026**. File gốc Nam để ở `usecase_sources/manual/OLYMPUS _ News Release_ … Live Viewfinder.html` (không phải `rule_sources_manual/` như dự kiến); Claude chép sang, sha256 giống hệt. Bản curl 07/10 cùng URL (`rule_sources/qd415/olympus_mmf_curl_20261007.html`) giữ làm bản phụ | `rule_sources_manual/olympus_mmf.html` |
| `pentax_adapter_q` (mới, Red Team N1) | curl ngày 08/10/2026 | `rule_sources/qd415/pentax_adapter_q_20261008.html` |
| `fuji_m_adapter`, `fuji_m_adapter_compat` (mới, Red Team N1) | curl ngày 08/10/2026 | `rule_sources/qd415/fuji_m_adapter*_20261008.html` |
| 13 mã ống Sony (`sony_lens_codes.toml`) | curl ngày 08/10/2026 trang `https://www.sony.jp/ichigan/products/<MÃ>/spec.html` (3 ống G ngàm A ở `/archive/`). Các trang Sony tiếng Anh (sony.com, .ca, .co.uk, .ie, sony-asia.com, .com.tw, electronics.sony.com) trả 403 | `rule_sources/qd415/sony_jp/<MÃ>_spec_20261008.html` |

- Trang B&H (bán lẻ) bật kiểm tra chống bot nên **không đọc**. Ba nguồn bán lẻ đã được thay bằng trang hãng (07/10).
- 3 khẳng định trước đây có trong ghi chú luật nhưng **không tìm được trang hãng** (tìm ngày 08/10/2026, chỉ thấy bài diễn đàn Canon Community): "phần sau ống EF-S chạm gương", "DSLR Canon full-frame không tự cắt khung", "ống DX hãng thứ ba phải chọn tay chế độ cắt". Nay ghi là "nhận định nhóm, chưa có nguồn" (trường `nhan_dinh_nhom`), không dùng làm căn cứ.

### 2.5. Các trang nguồn của luật mục đích sử dụng `ai/config/usecase_rules.toml` (nội dung 4, 08/10/2026)
- 12 trang của Canon và Nikon. URL, câu trích, sha256 của bản HTML và bản văn bản nằm trong `[sources.*]` của file TOML. Script `ai/survey/content4/count_usecase.py` kiểm sha256, kiểm bản sao có phần nội dung bài, và kiểm từng câu trích (cả 4 luật đều OK).
- Thư mục gốc: `ai/data/external/usecase_sources/` (không lên git). Bản văn bản `.txt` trích từ `.html` bằng `ai/survey/content4/html_to_text.py`.
- 08/10/2026: `html_to_text.py` nay đọc bảng mã theo thẻ meta charset (cho trang sony.jp). Đã kiểm trên 12 bản sao của mục này: bản cũ và bản mới cho văn bản giống hệt 12/12 (log `ai/data/survey/run_c4_html_to_text_check_20261008.log`). **Phát hiện phụ (có từ trước):** 5 file `.txt` ở thư mục gốc (`canon_us_wide_angle`, `canon_us_wildlife`, `nikon_85_f18g`, `nikon_macro`, `nikon_105_f2d`) không tái tạo được bằng `html_to_text.py` (cả bản cũ lẫn mới), tức đã được tạo bằng cách khác. File trên đĩa vẫn khớp sha256 trong TOML và mọi câu trích vẫn OK.

| Nguồn (khóa TOML) | Cách lưu | Bản chính |
|---|---|---|
| `canon_eu_beginner`, `canon_eu_landscape`, `canon_eu_wildlife`, `canon_eu_portrait`, `canon_eu_vlogging`, `canon_eu_best_vlogging` | **Nam lưu bằng trình duyệt ngày 08/10/2026** (Ctrl+S, trang web hoàn chỉnh). Trang chặn curl (HTTP 403) | `manual/canon_eu_*.html` (file gốc tên theo tiêu đề trang vẫn giữ trong `manual/`) |
| `canon_us_lens_guide` | **Nam lưu bằng trình duyệt ngày 08/10/2026** (đã tắt VPN) từ bản Wayback `https://web.archive.org/web/20260904221559/https://www.usa.canon.com/lens-buying-guide` — đúng bản Claude đã đọc. Trang hãng chặn truy cập từ Việt Nam; bản thô `id_` tải bằng curl thiếu nội dung do JavaScript sinh | `manual/canon_us_lens_guide_wb20260904.html` |
| `canon_us_wildlife`, `canon_us_wide_angle` | curl bản Wayback thô (`id_`) ngày 08/10/2026; trang hãng chặn truy cập từ Việt Nam | `canon_us_wildlife_wb20260517.html`, `canon_us_wide_angle_wb20260306.html` |
| `nikon_85_f18g`, `nikon_macro`, `nikon_105_f2d` (không dùng) | curl ngày 08/10/2026 | `nikon_*.html` |

- **Bản phụ công khai (Wayback, chỉ để đối chiếu, không dùng kiểm câu trích):** Claude gửi Save Page Now ngày 08/10/2026 cho 6 trang Canon Europe; tải bản thô về `wayback_20261008/` (sha256 ở `wayback_20261008/sha256.tsv`), cả 6 đều có phần nội dung bài:
  - beginner's guide: https://web.archive.org/web/20261008062749/https://www.canon-europe.com/get-inspired/tips-and-techniques/beginners-guide-lenses/
  - landscape: https://web.archive.org/web/20261008062826/https://www.canon-europe.com/get-inspired/tips-and-techniques/landscape-photography-lenses/
  - wildlife: https://web.archive.org/web/20261008062907/https://www.canon-europe.com/get-inspired/tips-and-techniques/best-wildlife-lenses/
  - portrait: https://web.archive.org/web/20261008063012/https://www.canon-europe.com/get-inspired/tips-and-techniques/portrait-lenses-tips-tricks/
  - vlogging tips: https://web.archive.org/web/20261008063138/https://www.canon-europe.com/get-inspired/tips-and-techniques/how-to-start-vlogging/
  - best vlogging kit: https://web.archive.org/web/20261008063223/https://www.canon-europe.com/get-inspired/tips-and-techniques/best-vlogging-cameras/
  - Bản chụp thứ 7 (Canon USA lens guide) bị dừng giữa chừng → bỏ qua.
- **Khác biệt phiên bản:** trang chân dung bản lưu 08/10/2026 ghi "around 85mm or longer"; bản Wayback 25/02/2024 (`canon_eu_portrait_wb20240225.html`) ghi "a focal length over 85mm". Trích theo bản 08/10/2026.
- **Nguồn bỏ:** trang Nikon 105mm f/2D (không có chữ "portrait"). Các bản Wayback cũ hơn tải trước đó (`*_wb202604*.html`, `*_wb20260511.html`, `canon_us_lens_buying_guide_wb20260904.html` — bản thô thiếu nội dung do JavaScript sinh) không dùng.

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
- `ai/survey/content4/count_usecase.py`: kiểm bản sao và câu trích của luật mục đích sử dụng, đếm số ống mỗi nhãn. Log `ai/data/survey/run_c4_usecase_count.log` (lần chạy lại 08/10 tối: `run_c4_usecase_count_20261008_rt1b.log`).
- `ai/survey/content3/check_rule_sources.py`: kiểm bản sao và câu trích của bảng luật ngàm và bảng mã ống Sony; kiểm mọi mã SEL/SAL cần tra trong dữ liệu đều có trong bảng. Log `ai/data/survey/run_check_rule_sources_*.log`.
