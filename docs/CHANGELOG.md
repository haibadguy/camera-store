# Nhật ký thay đổi so với bản của Hải

Bản gốc để so sánh: commit `62abf54` (Hải, 28/09/2026).
File này ghi lại mọi chỗ Nam sửa trong code hoặc dữ liệu của Hải. Mỗi mục gồm: **sửa gì**, **vì sao**, **ảnh hưởng thế nào** (số cũ → số mới).
Mục mới nhất nằm trên cùng.

---

## 08/10/2026: Sửa lỗi phân loại thân / ống / phụ kiện (`mount_detect.py`), chấm holdout một lần. Nhánh `nam/content3`

**Cách làm (giữ số đo độc lập, QĐ 13)**
- Chỉ xem ca sai của nửa **fix** (`eval_split_report.py --errors`, chỉ in nửa fix). Ngoài ra chỉ xem các sản phẩm **không** nằm trong holdout (lọc theo `eval_split.csv` trước khi in).
- Log tổng của `eval_external.py` có lẫn số của holdout nên trong lúc sửa chỉ ghi ra file nháp, không đọc.
- Chốt quy tắc xong mới chạy lại pipeline vào `ai/data/kg/` và chấm holdout **một lần**.
- Bước khớp tên của phía đánh giá **không sửa**. `eval_external.py` chỉ thêm tham số `--ours / --out-csv / --out-json` để chạy vào thư mục nháp.

**Ca sai loại của nửa fix trước khi sửa: 84 sản phẩm**, chia 2 nhóm:
- **68 ca quy tắc sai thật**, do quy tắc tin danh mục Amazon:
  - 47 ống bán kèm combo bị xếp phụ kiện. Amazon xếp chúng vào "Accessory Kits", "Accessory Bundles", "Filter Sets", thậm chí "Tablets" hay "Microscope Accessories". Ví dụ: "Canon EF 50mm f/1.8 STM Lens with 3pc Filter Kit…", "Fujinon XF33mmF1.4 R LM WR" (danh mục Tablets).
  - 15 thân thành "khác": 11 thân bị xếp "Point & Shoot" (Olympus E-P1, Lumix G3, Sony a6000…), 1 thân trong "Instant Cameras" (Nikon D5500), 3 máy phim SLR (Canon EOS Rebel 2000, Nikon F100, Canon AE-1 Program).
  - 3 thân thành phụ kiện: Leica M8 (thiếu luật dòng máy), Olympus E-5 nằm trong danh mục ống, Sony a7 III bán kèm combo.
  - 2 thân bán kèm ống nằm trong danh mục ống thành "ống": Sony a5100 + 16-50mm, Fujifilm X-T30 + XF18-55mm.
  - 1 máy ống liền thành thân: Fujifilm X-S1 bị luật dòng máy Fuji X bắt nhầm.
- **16 ca đáp án sai**, quy tắc đúng. Bước khớp tên bắt nhầm phụ kiện có nhắc tên máy:
  - pin LP-E6 "Canon EOS 60D EOS 7D EOS 5D Mark II", dây bấm mềm, chân máy, ốp, cốc mắt ngắm A6500, DC coupler Lumix;
  - sách "Introduction To Canon EOS 70D", ống chuyển đổi gắn ren "0.42x … for Canon Rebel SL1";
  - bộ cốc hình ống kính "LenZcup EF Shotglass", vỏ chống nước RX100, ống phụ gắn ngoài ZV-1…

**Sửa gì** (`ai/pipeline/mount_detect.py`)
1. **Loại xét theo tiêu đề trước, danh mục chỉ là dự phòng.** "Chủ thể" là phần tiêu đề trước *for / fits / compatible / with / w/ / + / & / bundle / includes…*. Khác `head()` cũ ở chỗ giữ "(" và " - ".
   - **Thân theo tiêu đề** (`title_body`, áp cho mọi danh mục trừ bảo hành): chủ thể (cắt thêm ở dấu phẩy) phải có đủ:
     - một luật dòng máy;
     - một từ chỉ máy ảnh: camera (trừ "camera lens"), body, DSLR, SLR, mirrorless, rangefinder, DSLM, interchangeable, "xx MP"; hoặc "kit" kèm tiêu cự;
     - không có từ phụ kiện (ACC_WORDS, LENS_NEG, danh sách mới `ACC_BODY`: accessory, replacement, eyepiece, housing, coupler, introduction, guide, book, monopod, shutter release, starter kit, software, upgrade…);
     - không thuộc dòng máy compact (Cyber-shot, PowerShot, Coolpix, FinePix, Lumix FZ/ZS/LX…);
     - không có tiêu cự + khẩu độ đứng trước dòng máy.
   - **Ống theo tiêu đề** (`title_lens`, chỉ áp cho danh mục "khác"; danh mục ống / thân / máy ống liền vẫn dùng luật cũ):
     - chủ thể có tiêu cự + khẩu độ;
     - không có từ phụ kiện: hood, cap, filter… và danh sách mới `LENS_NEG_TITLE` (cover, foot, plate, tripod ring, quick release, *scope, adapt*, 1.4x/2x, replica, shotglass, MP, "digital camera"…);
     - không thuộc dòng máy compact.
2. **Luật dòng máy** (`BODY_SERIES`):
   - thêm máy phim Canon FD (AE-1, AE-1 Program, A-1, AT-1, AV-1, AL-1, FTb, T50/T70/T90, F-1) → `canon_fd`, ff;
   - thêm máy phim Pentax ngàm K (K1000, ME Super, MX, Program A/Plus, ZX-/MZ-/PZ-) → `pentax_k`, ff;
   - thêm Spotmatic → `m42`, ff;
   - thêm máy phim Minolta Maxxum/Dynax → `sony_a`, ff;
   - thêm Leica M8 → `leica_m`, khung `khac` (APS-H, crop 1,33); Leica M2–M7 phim → `leica_m`, ff;
   - "Rebel GII" thêm vào luật máy phim EOS;
   - luật Fuji X không bắt X-S1 (máy ống liền), chỉ bắt X-S10/X-S20;
   - luật Samsung NX không bắt "NX 60mm", "NX 18-55mm" (đó là tên ống). Nếu không sửa, luật thân theo tiêu đề sẽ biến 10 ống Samsung NX thành thân;
   - Olympus OM-1/OM-5: thêm "35mm" vào điều kiện loại máy phim ngàm OM.
3. Ngàm, khung, bảng luật tương thích (`mount_rules.toml`) và `03_mount_compat.py`: **không đổi**.

**Kiểm tra phụ trước khi chốt** (không dùng holdout)
- Đổi loại trên các sản phẩm **ngoài holdout** (so `item_attributes.csv` trước/sau, script nháp): phụ kiện → ống 138, khác → thân 32, phụ kiện → thân 7, ống → thân 2, thân → khác 1 (X-S1). Claude đọc hết từng tiêu đề.
  - 2 lượt sửa đầu còn sai: 10 ống Samsung NX, "Canon Digital Rebel Kit with Case…", "Nikon D3000-D5000 DSLR Starter Kit", "Water Resistant Kit CVR-XT2", phần mềm "V-Log L Upgrade", vòng chân máy, đế tháo nhanh, áo trùm ống, ống ngắm phụ (guidescope), teleconverter 1.4X. Đã chặn hết bằng các luật ở mục 2 và danh sách từ phụ kiện.
  - Bản chốt: Claude xem lại hết, không thấy ca đổi sai.
- Mẫu dev 50 (`label_dev_50_claude.csv`), chỉ tính 36 mẫu **không** thuộc holdout (14 mẫu dev nằm trong holdout): trước = sau = loại 35/36, ngàm 32/36, khung 30/36.

**Ảnh hưởng: độ chính xác so với nguồn ngoài**
- Script: `eval_external.py` rồi `eval_split_report.py --holdout`. Log: `ai/data/survey/run_typefix_report.log`.
- Bản "trước": `ai/data/survey/before_typefix/eval_external_matches.csv`. Đã chạy lại từ mã commit `68ffa56`: mọi cột đúng/sai giống hệt. Chỉ cột tên hiển thị `ten_nguon` khác ở 24 dòng, do thứ tự `set` của Python; từ nay chạy với `PYTHONHASHSEED=0`.
- Khoảng tin cậy 95% (Wilson) ghi trong ngoặc.

| Chỉ số | Fix trước | Fix sau | **Holdout trước** | **Holdout sau** |
|---|---:|---:|---:|---:|
| Loại đúng, Lensfun | 481/548 = 87,8% | 535/548 = 97,6% | 502/571 = 87,9% [85,0–90,3] | **565/571 = 98,9%** [97,7–99,5] |
| Loại đúng, Wikidata | 245/295 = 83,1% | 283/295 = 95,9% | 263/315 = 83,5% [79,0–87,2] | **305/315 = 96,8%** [94,3–98,3] |
| Loại đúng theo sản phẩm (đúng ở mọi nguồn) | 514/598 = 86,0% | 582/598 = 97,3% | 527/612 = 86,1% [83,1–88,6] | **598/612 = 97,7%** [96,2–98,6] |
| Ngàm đúng / gán, Lensfun | 314/319 = 98,4% | 352/357 = 98,6% | 358/366 = 97,8% [95,7–98,9] | 391/402 = 97,3% [95,2–98,5] |
| Ngàm đúng / gán, Wikidata | 212/212 | 239/239 | 238/238 | 266/266 |
| Khung thân đúng / gán, Lensfun | 161/161 | 177/177 | 190/190 | 204/204 |
| Khung thân đúng / gán, openMVG | 93/94 | 106/106 | 121/121 | 132/133 = 99,2% |

Bảng nhầm loại của holdout sau sửa (đáp án → quy tắc): thân → phụ kiện 5, thân → khác 2, thân → ống 1, ống → thân 1, khác → phụ kiện 2, khác → thân 1.
- **Chưa xem từng ca sai của holdout**, nên chưa biết bao nhiêu trong 14 ca là đáp án sai. Ở nửa fix, 16/16 ca còn lại đều là đáp án sai.
- Ngàm theo Lensfun ở holdout: số được gán tăng 366 → 402 (thêm thân/ống vừa được nhận đúng loại), số sai tăng 8 → 11. Chưa xem 3 ca sai mới.

**Ảnh hưởng: số sản phẩm và ma trận M** (`ai/data/kg/mount_compat_log.txt`)

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Thân (`than`) | 488 | **544** |
| Ống (`ong`) | 1.143 | **1.337** |
| Máy ống liền / khác (`khac`) | 1.802 | 1.758 |
| Phụ kiện | 24.507 | 24.301 |
| Thân có 1 ngàm (hàng của M) | 482 | **538** |
| Ống có 1 ngàm / "không chắc" QĐ 4 / vào M | 999 / 113 / 886 | **1.167 / 130 / 1.037** |
| Kích thước M | 482 × 886 | **538 × 1.037** |
| Cặp M = 1 | 56.276 | **75.690** |
| … trong đó cờ "chưa rõ có cắt khung" (QĐ 11) | 1.638 | 2.186 |
| Cặp "không biết" | 1.836 | 2.960 |

**Còn chưa chắc / phải làm theo**
- **Máy phim trong M (cần Nam quyết).** Sau sửa có 17 thân máy phim (Nikon F 7, Canon EF 8, Canon FD 2); trước chỉ có 2.
  - Bảng luật đang coi chúng là thân FF. Nên ống DX trên thân Nikon phim bị xếp `crops_sensor` (M = 1): **462 cặp**, trước sửa 53. Luật QĐ 11 còn cho thêm **294 cặp** M = 1 có cờ, trước sửa 36.
  - Nhưng máy phim **không có chế độ cắt khung**: ống DX sẽ tối góc. Thân cơ như FM-10 còn không chỉnh được khẩu độ với ống G (không có vòng khẩu).
  - Canon EF phim + EF-S → `incompatible`: đúng.
- Hai ống mới được nhận loại có ngàm chưa chuẩn (lỗi bước gán ngàm, không thuộc lần sửa này):
  - "Sigma 150-600mm … (for Canon EOS) & MC-11 Mount Converter" bị gán `sony_e`;
  - "Lightdow 420-800mm … + T Mount Ring for Nikon" bị gán `t_mount`, trong khi QĐ 9 nói phải theo ngàm của vòng.
- Kết quả holdout là **lần chấm duy nhất**. Nếu sửa thêm quy tắc thì holdout không còn độc lập.
- Script 04 / `common_05.py` vẫn chưa đọc được đầu ra mới (như mục dưới).

---

## 08/10/2026: Gỡ các file nội dung 3–4 cũ của Hải khỏi `ai/data/kg/`; đưa đầu ra mới lên git. Nhánh `nam/content3`

**Sửa gì**
- `git rm` 8 file cũ trong `ai/data/kg/`: `linked_products.csv`, `compatible_item_edges.csv`, `compatibility_stats.json`, `kg_stats.json`, `mount_mapping.json`, `validation_log.txt`, `validation_samples_50.csv`, `unlinked_audit_samples_50.csv`.
  - Trước khi gỡ, đã kiểm sha256: cả 8 file giống hệt bản sao lưu ở `ai/data/kg_v62abf54/` (bản này không lên git).
  - Muốn xem lại bản của Hải thì lấy từ commit `62abf54`.
- Đưa lên git đầu ra nội dung 3 mới: `compatibility_matrix.npz` (M), `unknown_mask.npz` (ma trận "không biết"), `item_attributes.csv`, `compat_pairs.csv`.
  - `.gitignore` vẫn chặn `ai/data/kg/*.npz`, nhưng thêm ngoại lệ `!` cho đúng 2 file `.npz` này.
- Dữ liệu gốc (`ai/data/raw/`) và dữ liệu nguồn ngoài (`ai/data/external/`) vẫn **không** lên git.

**Vì sao**
- Các file cũ được sinh từ cách khớp model cũ (257 sản phẩm có ngàm) và mã sản phẩm cũ, nên không còn đúng với dữ liệu sau gộp lặp.
- Cô yêu cầu nộp ma trận M (lỗi 3 trong STATUS).

**Ảnh hưởng / phải làm theo**
- `04_build_knowledge_graph.py` đọc `linked_products.csv`, `compatibility_matrix.npz` theo định dạng cũ, `body_index.json`, `lens_index.json`, nên **hiện không chạy được**. Phải sửa để đọc `item_attributes.csv` và `compat_pairs.csv`.
- `common_05.py` đọc `compatible_item_edges.csv` (đã gỡ), nên các baseline nội dung 5 cũng phải sửa theo.

---

## 07/10/2026: Ghi đè `ai/data/kg/` bằng đầu ra nội dung 3 mới; QĐ 11; đo độ chính xác bằng nguồn ngoài. Nhánh `nam/content3`

**Sửa gì**
1. **Sao lưu rồi ghi đè `ai/data/kg/`.**
   - Bản cũ chép sang `ai/data/kg_v62abf54/` (10 file, kiểm sha256 khớp từng file; không đưa lên git).
   - Chạy `03_mount_compat.py --out-dir ai/data/kg --overwrite`. Các file bị thay: `body_index.json`, `lens_index.json`. File mới: `item_attributes.csv`, `compat_pairs.csv`, `compatibility_matrix.npz`, `unknown_mask.npz`, `mount_compat_stats.json`, `mount_compat_log.txt`.
   - **Các file cũ của Hải vẫn nằm trong `ai/data/kg/` và nay đã cũ**, vì pipeline mới không ghi đè chúng: `linked_products.csv`, `compatible_item_edges.csv`, `compatibility_stats.json`, `kg_stats.json`, `mount_mapping.json`, `validation_*`, `unlinked_audit_samples_50.csv`. Script 04 cũ vẫn đọc các file này.
2. **QĐ 11** (`ai/config/mount_rules.toml`, luật `same_mount_ff_body_lens_khung_unknown_autocrop`):
   - Áp cho thân FF ở các ngàm có chế độ cắt khung chính hãng (Nikon F/Z, Sony E/A, Canon RF, Pentax K), gắn ống cùng ngàm nhưng không rõ khung.
   - Kết quả: M = 1, mức `compatible_with`, kèm cờ `crop_unknown = 1` ("chưa rõ có cắt khung").
   - `compat_pairs.csv` có thêm cột `crop_unknown`.
3. **Nguồn của luật:**
   - Mở và đọc cả 14 trang; mỗi nguồn ghi URL, câu trích nguyên văn, `kiem_chung = "da_doc_trang"`.
   - Ba nguồn bán lẻ (B&H) được thay bằng trang hãng: thông cáo Nikon FT1 (2011), trang hỗ trợ Sony về ống DT (có câu nói ngàm chuyển LA-EA), thông cáo Olympus về E-P2 (nói MMF-1).
   - Trang Sigma xác nhận ống DC bản Canon dùng **ngàm EF**. Điểm "chưa đối chiếu" của QĐ 8 nay đã có nguồn.

**Ảnh hưởng** (`ai/data/kg/mount_compat_log.txt`)

| Chỉ số | Trước QĐ 11 (`kg_new`) | Sau QĐ 11 (`kg`) |
|---|---:|---:|
| Kích thước M | 482 × 886 | 482 × 886 |
| Cặp M = 1 | 54.638 | **56.276** |
| … trong đó cờ "chưa rõ có cắt khung" | – | 1.638 |
| Cặp "không biết" | 3.474 | **1.836** |

**Độ chính xác so với nguồn ngoài** (`ai/survey/content3/eval_external.py`, log `ai/data/survey/run_eval_external.log`; nguồn ở `docs/DATA_SOURCES.md`)

Cách đọc bảng:
- Mỗi nguồn chỉ chấm trên các sản phẩm khớp tên chắc chắn.
- "Gán" là số sản phẩm mà quy tắc đưa ra 1 ngàm / 1 khung.
- "Để trống" là quy tắc trả "không rõ".

| Nguồn | Khớp được | Loại đúng | Ngàm: đúng / gán (để trống) | Khung thân: đúng / gán (để trống) |
|---|---:|---:|---:|---:|
| Lensfun | 1.119 (551 thân/máy, 568 ống) | 983/1.119 (87,8%) | 672/685 = **98,1%** (12) | 351/351 = **100%** (1) |
| openMVG | 635 máy | – | – | 214/215 = **99,5%** (2) |
| Wikidata | 610 (297 thân, 313 ống) | 508/610 (83,3%) | 450/450 = **100%** (2) | – |

Tổng cộng 1.493 sản phẩm khác nhau khớp được ít nhất một nguồn.

Các ca sai, Claude đã đọc từng ca:
- **Ngàm, 13 ca lệch với Lensfun: không ca nào là lỗi quy tắc.**
  - 7 ca: Lensfun ghi ngàm "EF-S" cho ống EF 75-300 III, vì ghi theo máy dùng để hiệu chỉnh.
  - 6 ca: khớp nhầm sang bản ngàm khác mà Lensfun chỉ có một bản, vd Sony FE 50mm f/1.4 ZA bị khớp với "Sony 50mm f/1.4" ngàm A; Samyang AF 85mm bản RF với bản E; Voigtlander 15mm bản Leica M với bản E; Zeiss ZE.
- **Khung, 1 ca sai với openMVG: lỗi quy tắc thật.** Fujifilm X-S1 là máy bridge 2011, nhưng luật dòng máy `x-s\d` coi là thân X-mount.
- **Loại, khoảng 100–140 ca sai mỗi nguồn: phần lớn là lỗi quy tắc thật.** Quy tắc tin danh mục Amazon:
  - ống kính bán kèm combo nằm ở "Accessory Kits" / "Accessory Bundles" bị xếp `phu_kien` (Lensfun: 59 + 18 ca);
  - thân máy bị Amazon xếp vào "Point & Shoot" / "Instant Cameras" bị xếp `khac` (vd Olympus PEN E-P1, Pentax K-01, Nikon D3300);
  - máy phim SLR (danh mục Film Cameras) bị xếp `khac`;
  - còn một ít là lỗi khớp: chữ "f4" trong khẩu độ bị khớp với máy phim "Nikon F4"; "Canon VIXIA HF R50" bị khớp với "EOS R50".
- **Hệ quả:** độ chính xác khi quy tắc **đã gán** ngàm hoặc khung rất cao, nhưng **độ phủ** bị giới hạn bởi lỗi phân loại. Các ống, thân bị xếp nhầm thành phụ kiện / khác thì không vào M.

**Chưa làm / phải làm theo**
- **Chưa sửa lỗi phân loại** vừa tìm được. Nếu sửa theo chính tập đánh giá này thì số đo lần sau không còn độc lập. Cần Nam quyết cách làm.
- Script 04 và `common_05.py` (CVR) chưa đọc đầu ra mới (xem mục bên dưới).

---

## 07/10/2026: Nội dung 3 bản mới — `03_mount_compat.py` (xác định ngàm tách khỏi khớp model). Nhánh `nam/content3`

**Sửa gì**
- **Thêm** (không sửa file của Hải):
  - `ai/pipeline/03_mount_compat.py`: pipeline chính;
  - `ai/pipeline/mount_detect.py`: bộ nhận diện loại / ngàm / khung;
  - `ai/config/mount_rules.toml`: bảng luật tương thích, mỗi luật có nguồn hoặc lý do.
- `03_entity_linking_matrix.py` của Hải **giữ nguyên**. Từ nay nó chỉ còn vai trò khớp model để lấy thông số (bước 3d). Ma trận M **không** lấy từ nó nữa.
- Cách mới, ví dụ trước:
  - "Sigma 30mm DC DN for Sony E-mount" → đọc chữ "E-mount" → ngàm `sony_e`; chữ "DC" → khung `apsc`. Cách cũ bỏ sót ống này vì nó không có trong bảng 139 model.
  - "Nikon D3200" → luật dòng máy → `nikon_f`, `apsc`.
  - Cặp (D750, ống DX) → mức `crops_sensor`, M = 1.
- Loại sản phẩm lấy từ danh mục, có lọc thêm bằng tiêu đề. Bản cũ coi 801 máy compact là "thân máy"; bản mới xếp chúng vào `khac`.
- Ma trận M có 5 mức (QĐ 2, 8): `compatible_with`, `crops_sensor` (M = 1); `requires_adapter`, `incompatible`, `unknown` (M = 0). Cặp `unknown` lưu ở ma trận riêng `unknown_mask.npz`.
- 113 ống hãng thứ ba có nhiều asin con được đánh dấu "không chắc" (QĐ 4): không vào M, vẫn có trong `item_attributes.csv` và `compat_pairs.csv`.

**Vì sao**
- Bản cũ chỉ gán được ngàm cho 257/28.867 sản phẩm (0,9%), vì phải khớp đúng tên model với bảng 139 dòng.
- Bản cũ có 1.414 "thân máy" thì hơn một nửa là máy compact không có ngàm.
- Bằng chứng ở `docs/content3_survey.md`.

**Ảnh hưởng** (số mới từ `03_mount_compat.py --out-dir ai/data/kg_new`, log ở `ai/data/kg_new/mount_compat_log.txt`)

| Chỉ số | Bản cũ (62abf54, dữ liệu cũ) | Bản mới (dữ liệu sau gộp lặp) |
|---|---:|---:|
| "Thân máy" theo phân loại | 1.414 | 488 (`than`); thêm 1.802 `khac` (compact, máy quay…) |
| "Ống kính" theo phân loại | 1.462 | 1.143 (`ong`) |
| Thân có ngàm (vào M) | (257 thân + ống) | **482** |
| Ống có ngàm | | 999, trong đó 886 vào M và 113 "không chắc" |
| Kích thước M | (theo bảng cũ) | 482 × 886 |
| Cặp M = 1 | | 54.638 (12,79%) |
| Cặp "không biết" | không có mức này | 3.474 (0,81%) |
| User có thân trong M ở train và item test là ống trong M | (chưa tính) | 951. Ống test so với thân đã có: 661 `compatible_with`, 9 `crops_sensor`, 10 `requires_adapter`, 23 `unknown`, 248 `incompatible` (`ai/survey/content3/scenario_kgnew.py`) |

**Đã kiểm chứng / chưa**
- Kiểm trên 50 mẫu dev do Claude tự chấm (`check_dev.py`): loại đúng 49/50, ngàm 46/50, khung 43/50. Mọi giá trị quy tắc **đã gán** đều khớp nhãn; các chỗ lệch là quy tắc để "không rõ" (vd chỉ ghi "for Canon"). **Đây không phải số đánh giá chính thức**, vì người chấm và người viết quy tắc là một.
- Chưa đối chiếu với nguồn thông số bên ngoài (chờ Nam duyệt tải về, QĐ 10).

**Phải làm theo**
- **Chưa ghi vào `ai/data/kg/`.** Đầu ra mới đang ở `ai/data/kg_new/`, chờ Nam đồng ý ghi đè.
- Script 04 đọc `linked_products.csv` (đầu ra cũ) → phải sửa để đọc `item_attributes.csv` và `compat_pairs.csv`. Bỏ `assert after == 257`.
- `common_05.py` (CVR): chỉ tính các ống có trong `lens_index.json`, và bỏ các cặp có trong `unknown_mask.npz` (QĐ 4, 8).

---

## 07/10/2026: Bỏ số ghi cứng trong `common_05.py` và `04_build_knowledge_graph.py`. Nhánh `nam/content3`

**Sửa gì**
- `ai/pipeline/common_05.py`: `N_USERS` và `N_ITEMS` không còn ghi cứng `70424` / `28867`. Nay đọc từ `ai/data/processed/user_map.json` và `item_map.json` rồi lấy `len()`, giống cách `04_build_knowledge_graph.py` đã làm. Sửa luôn docstring đầu file (bỏ "70,424 users", "2,491 users").
- `ai/pipeline/04_build_knowledge_graph.py`, phần ghi `kg_stats.json` (mục `notes`):
  - `full_kcore_interactions`: trước ghi cứng `622997`, nay đọc `filtered_interactions` trong `ai/data/processed/filtering_stats.json`.
  - `val_interactions`, `test_interactions`: trước ghi cứng `70424`, nay đếm số dòng của `val.txt` / `test.txt` (hàm mới `count_lines`).

**Vì sao**
- Sau khi gộp tương tác lặp (mục bên dưới), số người dùng và sản phẩm đã đổi. Ví dụ: nếu để `N_ITEMS = 28867` trong khi chỉ còn 27.940 sản phẩm, LightGCN sẽ tạo thừa 927 embedding sản phẩm "ma", còn bộ lấy mẫu âm có thể bốc trúng mã sản phẩm không tồn tại.
- Lấy số từ file đầu ra của bước 2 thì lần sau dữ liệu đổi cũng không phải sửa tay.

**Ảnh hưởng (kiểm bằng lệnh Python chạy ngày 07/10/2026)**

| Hằng số | Cũ (ghi cứng) | Mới (đọc từ file) |
|---|---:|---:|
| `common_05.N_USERS` | 70.424 | 67.661 |
| `common_05.N_ITEMS` | 28.867 | 27.940 |
| `kg_stats.notes.full_kcore_interactions` | 622.997 | 595.515 |
| `kg_stats.notes.val_interactions` / `test_interactions` | 70.424 / 70.424 | 67.661 / 67.661 |

**Chưa làm / phải sửa tiếp**
- **Chưa chạy lại toàn bộ script 04**, vì script 04 cần đầu ra của script 03 (nội dung 3), mà nội dung 3 đang được thiết kế lại.
- Script 04 còn một chỗ ghi cứng nữa: `assert after == 257` (số sản phẩm đã gán ngàm theo bản cũ). Chỗ này phụ thuộc kết quả nội dung 3 nên chưa sửa; khi làm lại nội dung 3 phải bỏ hoặc thay.

---

## 07/10/2026: Bước 01–02 (lọc dữ liệu, chia train/val/test). Nhánh `nam/fix-data`

### 1. Những điểm đã kiểm chứng là đúng (không sửa)

Nam tải lại dữ liệu gốc và chạy lại `01_filter_camera_domain.py` và `02_split_time_aware.py` **bằng code của Hải, chưa sửa gì**. Các số sau khớp đúng với báo cáo 2:

- 43.886.944 đánh giá và 1.610.012 sản phẩm trong Electronics.
- 253.260 sản phẩm camera sau khi lọc metadata; 4.042.112 tương tác camera.
- Cả 14 vòng k-core, từng con số một.
- Sau k-core: 70.424 người dùng, 28.867 sản phẩm, 622.997 tương tác, độ thưa 99,969%, trung bình 8,85 tương tác/người.
- Phân vị số tương tác mỗi người (5 / 5 / 7 / 9 / 15 / 20 / 188), phân bố số sao.
- Train 482.149 tương tác, val và test mỗi tập 70.424.
- Số người dùng có item trùng giữa các tập: val–train 1.290, test–train 1.166, test–val 2.544.
- Script 02 chạy 2 lần cho ra file giống hệt nhau (kiểm bằng sha256), nên seed 42 tái lập được.

Dữ liệu gốc dùng để kiểm (tải từ trang chính thức, ngày sửa trên server là 16/01/2025):

| File | Kích thước (byte) | sha256 |
|---|---|---|
| `Electronics.jsonl.gz` | 6.474.438.619 | `17b2c5f3736d4c0cb874859076436ebd4513f4c2396c528440a63204084e6a28` |
| `meta_Electronics.jsonl.gz` | 1.312.900.427 | `a4a196a1c8e443e0942d8a5c79b5a5d2d68e29d483f2badec1126690b4b2790d` |

### 2. Những chỗ báo cáo 2 (`ai/docs/02_DATA_PREPROCESSING.md`) ghi sai

Code tính đúng. Sai nằm ở chỗ báo cáo ghi số không do script in ra, hoặc diễn giải sai.

| Chỗ trong báo cáo | Báo cáo ghi | Số đúng | Vì sao sai |
|---|---|---|---|
| Bảng 2.1, dòng "Sau Domain Filtering", cột Users | ~2,1 triệu (ước tính) | **2.502.236** | Script cũ không đếm số này, nên báo cáo phải ước tính. Nay script đã đếm. |
| Bảng 2.1, cột "Items có tương tác" | 72.775 | **253.208** | 72.775 là số sản phẩm **sau vòng 1 của k-core** (xem dòng "Vòng 1" trong log), không phải số sản phẩm có ít nhất 1 tương tác. |
| Bảng 2.1, TB tương tác/người | 1,92 | **1,62** | Hệ quả của 2 dòng trên: 4.042.112 / 2.502.236. |
| Bảng 2.1, độ thưa | 99,997% | **99,9994%** | Cũng là hệ quả của 2 dòng trên. |
| Phụ lục A, ghi chú vòng 1 | "toàn bộ 72.775 items tạm thời đều thỏa mãn" | Vòng 1 giảm sản phẩm từ 253.208 xuống 72.775 | Cùng nguyên nhân với dòng 72.775 ở trên. |
| Mục 2.2, giải thích 16.195 tương tác lặp | "người dùng tương tác lại ở các thời điểm khác nhau", "mua lặp lại" | **13.079 dòng là bản sao y hệt**, chỉ 3.116 dòng là đánh giá lại thật | Xem mục 3 bên dưới. |

Ví dụ một bản sao y hệt trong file gốc: user `AHSRW3FML7LW3G5LZK5REGJGDNLQ`, sản phẩm `B01E3QM34W`, timestamp `1489165051000`. File gốc có **2 dòng giống nhau hoàn toàn**: cùng asin, cùng tiêu đề "Five Stars", cùng nội dung "Works great but film is pricy." Đây không phải mua lại, mà là dữ liệu Amazon bị lặp dòng. Khi kiểm cả 9.461 nhóm bị lặp trong file gốc, có 9.460 nhóm trùng y hệt cả asin lẫn nội dung.

### 3. Sửa code: gộp tương tác lặp trong `ai/pipeline/01_filter_camera_domain.py`

**Sửa gì**
- Thêm hàm `step_2b_dedup_user_item`, chạy sau bước lọc tương tác và **trước k-core**.
- Mỗi cặp (user, parent_asin) chỉ giữ **1 dòng có timestamp sớm nhất**. Nếu hai dòng trùng timestamp thì giữ dòng có số sao thấp hơn. Trong dữ liệu sau k-core của bản cũ không có trường hợp nào trùng timestamp mà khác số sao.
- Log in ra số dòng bị bỏ, chia làm hai loại:
  - **bản sao y hệt:** trùng cả user, sản phẩm, timestamp và số sao với một dòng khác;
  - **đánh giá lại:** cùng user và sản phẩm nhưng khác timestamp hoặc số sao.
- `filtering_stats.json` có thêm các trường: `raw_camera_users`, `raw_camera_items_with_interaction`, `dedup_removed_total`, `dedup_removed_exact_copy`, `dedup_removed_re_review`, `dedup_interactions`.
- Phần còn lại của script 01 và toàn bộ script 02 **không đổi**.

**Vì sao**
1. **Bài toán là gợi ý sản phẩm người dùng chưa có.** Một sản phẩm đã mua rồi thì không cần gợi ý lại, nên mỗi cặp user–sản phẩm chỉ cần tính một lần.
2. **Bản ghi lặp làm rò rỉ dữ liệu sang val/test.**
   - Ví dụ: đánh giá cuối của một người bị lặp 2 dòng. Khi đó dòng thứ nhất rơi vào val, dòng thứ hai rơi vào test, tức là val và test là cùng một sản phẩm.
   - Bản cũ có 2.544 người dùng bị như vậy, trong đó 2.396 người chỉ vì bản sao y hệt.
   - Ngoài ra, bản sao còn được đếm vào điều kiện "≥ 5 tương tác" của k-core. Vì vậy một người chỉ có 3 sản phẩm khác nhau, cộng thêm 2 dòng lặp, vẫn lọt qua k-core.
3. **Giữ lặp làm sai kết quả đánh giá.**
   - Hàm `full_catalog_cvr` (`ai/pipeline/common_05.py`, dòng 182–186) loại các item đã có trong train bằng cách gán điểm −∞. Đánh giá xếp hạng toàn bộ (full ranking), cách đo dự định dùng làm kết quả chính, theo chuẩn cũng loại như vậy.
   - Hệ quả: nếu item test đã nằm trong train, mô hình không thể đoán trúng, và kết quả bị kéo xuống một cách oan uổng.
   - Lưu ý: hàm `sampled_eval` (1 + 99) **không** loại item train. Ở đó item test trùng train lại có thể làm kết quả đẹp lên giả.
   - Bản cũ có 1.166 người dùng có item test nằm trong train.

**Ảnh hưởng (số cũ → số mới)**

Số mới lấy từ `filtering_stats.json`, log của script 01 và 02, và script so sánh chạy ngày 07/10/2026.

| Chỉ số | Bản cũ (62abf54) | Bản mới |
|---|---:|---:|
| Tương tác camera đọc từ file gốc | 4.042.112 | 4.042.112 |
| Người dùng / sản phẩm có tương tác, trước k-core | 2.502.236 / 253.208 | 2.502.236 / 253.208 (không đổi) |
| Dòng bị bỏ khi gộp | 0 | **51.199** (45.684 bản sao y hệt + 5.515 đánh giá lại) |
| Tương tác đưa vào k-core | 4.042.112 | **3.990.913** |
| Vòng 1 k-core (tương tác / người dùng / sản phẩm) | 826.275 / 99.317 / 72.775 | 799.073 / 96.648 / 72.081 |
| Số vòng đến khi hội tụ | 14 | 14 |
| **Người dùng sau k-core** | 70.424 | **67.661** |
| **Sản phẩm sau k-core** | 28.867 | **27.940** |
| **Tương tác sau k-core** | 622.997 | **595.515** |
| Độ thưa | 99,969% | 99,968% |
| TB tương tác/người (trung vị / P90 / max) | 8,85 (7 / 15 / 188) | 8,80 (7 / 15 / 184) |
| **Train** (đếm từng dòng) | 482.149 | **460.193** |
| Train (gộp lặp từng người, như `load_train`) | 470.009 | 460.193 (hai cách đếm giờ bằng nhau) |
| Val / Test | 70.424 / 70.424 | 67.661 / 67.661 |
| Dòng lặp (user, item) trong `camera_interactions_k5.csv` | 16.195 | **0** |
| Người dùng có val = test | 2.544 | **0** |
| Người dùng có test nằm trong train | 1.166 | **0** |
| Người dùng có val nằm trong train | 1.290 | **0** |
| RAM đỉnh khi chạy script 01 | 2,03 GiB | 2,02 GiB |

Ghi chú: còn **4 người dùng** có hai sản phẩm *khác nhau* cùng timestamp ở ranh giới train/val/test, nên thứ tự giữa hai sản phẩm đó do thuật toán sắp xếp quyết định. Kết quả vẫn tái lập được vì cùng đầu vào cho cùng đầu ra. Số này quá nhỏ nên chưa sửa.

### 4. Thay đổi phụ
- `.gitignore`: thêm `ai/data/processed_*/`.
- Đầu ra của bản cũ được sao lưu ở `ai/data/processed_v62abf54/` (không đưa lên git) để còn đối chiếu.

### 5. Việc cần làm tiếp vì số người dùng và sản phẩm đã đổi

Mã số người dùng và sản phẩm (`user_map.json`, `item_map.json`) đã thay đổi, nên **mọi kết quả của bước 03–05 trên dữ liệu cũ không còn dùng được**. Phải chạy lại các bước này. Những chỗ đang ghi cứng số cũ (chưa sửa):
- `ai/pipeline/common_05.py` dòng 36–37: `N_USERS = 70424`, `N_ITEMS = 28867`.
- `ai/pipeline/04_build_knowledge_graph.py` dòng 432–433: `val_interactions` / `test_interactions` = 70424.
- Các file trong `ai/data/kg/` (ví dụ `compatible_item_edges.csv`, `kg_stats.json`) đang dùng mã sản phẩm cũ.
- Báo cáo `ai/docs/02_DATA_PREPROCESSING.md` cần cập nhật theo số mới và sửa các chỗ sai ở mục 2.

### 6. Chưa kiểm chứng
- 18.286.191 người dùng thô của Electronics: script không đếm. Số này khớp với con số 18,3M ghi trên trang dataset, nhưng nhóm chưa tự đếm.
- Bảng 2.3 trong báo cáo 2 (1.414 thân máy / 1.462 ống kính) và mục 5 của báo cáo 2.
