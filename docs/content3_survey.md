# Khảo sát dữ liệu cho nội dung 3: xác định loại sản phẩm và ngàm

Ngày: 07/10/2026 · Nhánh `nam/content3` · Người làm: Nam (Claude hỗ trợ)

> Đây là **khảo sát**, chưa phải pipeline. Mọi số trong file này lấy từ output của các script trong `ai/survey/content3/`, chạy trên 27.940 sản phẩm sau k-core (dữ liệu nhánh `nam/fix-data`). Log nằm ở `ai/data/survey/` (không đưa lên git).
>
> Những chỗ ghi **"Claude xem sơ bộ"** là Claude tự đọc tiêu đề rồi đánh giá. Đó **chưa phải nhãn chuẩn**; Nam cần tự kiểm lại.

## 0. Cách chạy lại

Chạy từ thư mục gốc repo, dùng `ai\.venv\Scripts\python.exe`:

| Bước | Lệnh | Log |
|---|---|---|
| 1. Trích metadata đầy đủ (title, details, features, description…) của 27.940 sản phẩm từ `meta_Electronics.jsonl.gz` (đọc từng dòng, không sửa file gốc) | `extract_full_meta.py ai/data/survey/meta_full_k5.jsonl` | `run_extract.log` |
| 2. Kiểm thử bộ nhận diện ngàm trên 30 tiêu đề mẫu | `test_mountlex.py` | `run_test_mountlex.log` (sai 0/30) |
| 3. Phân loại sản phẩm và gán ngàm theo từng nguồn | `survey2.py ai/data/survey/meta_full_k5.jsonl ai/data/survey/survey2_items.jsonl` | `run_survey2.log` |
| 4. Độ phủ ở mức tương tác và người dùng | `coverage_interactions.py ai/data/survey/survey2_items.jsonl` | `run_coverage.log` |
| 5. Lấy 30 mẫu theo cách phân loại của script 03 cũ | `sample03.py` | `run_sample03.log` |
| 6. Đếm số biến thể (asin con) của mỗi thân/ống | `child_asins.py ai/data/survey/survey2_items.jsonl ai/data/survey/child_asins.json` | `run_child_asins.log` |
| Xem ví dụ | `inspect_items.py ai/data/survey/survey2_items.jsonl <chế độ>` | |

(Các script nằm trong `ai/survey/content3/`. Bước 1 trích ra file có sha256 `62C9D9FA…7794`, giống hệt lần chạy thử trong scratchpad.)

---

## 1. Metadata Amazon có những trường nào cho biết loại và ngàm?

**Lưu ý quan trọng:** file `camera_items_meta.jsonl` mà script 01 sinh ra chỉ giữ 7 trường (`parent_asin, title, brand, categories, average_rating, rating_number, price`). Các trường `details`, `features`, `description` **bị bỏ mất**, nên phải đọc lại từ file gốc (bước 1).

Trong 27.940 sản phẩm, các trường hữu ích:

| Trường | Số sản phẩm có | Cho biết gì | Độ tin |
|---|---:|---|---|
| `categories` (đường dẫn danh mục) | 27.628 | **Loại** sản phẩm: ví dụ `Digital Cameras > DSLR Cameras`, `Lenses > Camera Lenses > SLR Camera Lenses` | Khá, nhưng có nhiễu (xem mục 2) |
| `title` | 27.939 | **Ngàm** khi người bán ghi rõ ("E-mount", "for Canon EF"), hoặc dòng máy ("EOS Rebel T7", "a6000") | Cao nếu ghi rõ |
| `details["Compatible Mountings"]` | 3.464 | Ngàm, dạng có cấu trúc (ví dụ `"Canon EF"`, `"Sony E"`) | **Thấp, nhiễu** (xem dưới) |
| `details["Form Factor"]` | 1.882 | "Mirrorless", "DSLR", "Compact"… | Phụ |
| `details["Lens Type"]` | 3.296 | "Zoom", "Wide Angle", "Telephoto"… | Phụ |
| `features`, `description` | 24.411 / 16.777 | Ngàm (đôi khi) | Nhiễu, chỉ thống kê |

### Phát hiện chính: `Compatible Mountings` không đáng tin nếu dùng một mình

Ví dụ thật:

- **Máy ảnh compact (không thay được ống kính) vẫn bị ghi ngàm.** Trong 1.580 máy ảnh ống liền/máy quay, có **493** sản phẩm có `Compatible Mountings` ghi đúng 1 ngàm (215 ghi "Micro Four Thirds", 100 ghi "Nikon 1", 76 ghi "Sony E"…). Ví dụ:
  - `B004NTO2I0` Panasonic Lumix DMC-FH27 (compact) → ghi "Micro Four Thirds"
  - `B00B8KXKDU` Nikon COOLPIX S31 (compact) → ghi "Nikon 1"
  - `B001G60DXG` Canon PowerShot SD990IS (compact) → ghi "Canon EF"
- **Thân máy/ống kính thật cũng bị ghi sai:**
  - `B00GC3PQ76` Nikon D3200 (DSLR, ngàm F) → ghi "Nikon 1"
  - `B01M74YO0G` Sony a6500 (ngàm E) → ghi "Sony A"
  - `B084BKXDLD` Canon RF24-105mm (ngàm RF) → ghi "Canon EF"
  - `B0086UXTP4` Rokinon 8mm "for Sony E-mount" → ghi "Fujifilm X"

Khi cả tiêu đề lẫn `Compatible Mountings` đều cho đúng 1 ngàm, hai nguồn **lệch nhau ở 39/812 ống kính (4,8%) và 22/407 thân máy (5,4%)** (`run_survey2.log`, cột `rec&CM` / `rec==CM`). Claude xem sơ bộ toàn bộ các ca lệch: trong gần hết các ca, tiêu đề đúng và `Compatible Mountings` sai (như các ví dụ trên).

→ Có vẻ người bán điền trường này theo "hệ máy của hãng" chứ không theo ngàm thật.

### Đếm số sản phẩm có ngàm rõ ràng theo từng nguồn

"Rõ ràng" = nguồn đó cho **đúng 1 ngàm**. Các nguồn:

- **T**: tiêu đề nói rõ tên ngàm hoặc tiền tố dòng ống kính chỉ thuộc 1 ngàm. Ví dụ "E-mount", "Canon EF-S", "RF24-105mm", "Fujinon XF", "AF-S NIKKOR", "M.Zuiko".
- **SER** (chỉ thân máy): suy từ dòng máy trong tiêu đề. Ví dụ "EOS Rebel" → Canon EF, "a6000" → Sony E, "Nikon D3200" → Nikon F, "X-T2" → Fujifilm X. Gồm khoảng 20 luật theo dòng máy (`survey2.py`, biến `SERIES`).
- **SLR** (chỉ ống kính): hãng + "DSLR/SLR". Ví dụ "for Canon APS-C Digital SLR" → Canon EF, vì máy DSLR của Canon chỉ dùng ngàm EF.
- **CM**: `details["Compatible Mountings"]`.
- **TX**: features + description.

Bảng từ `run_survey2.log`:

| Loại (theo categories + lọc tiêu đề) | Số SP | CM | T | SLR | SER | TX | **Quy tắc đề xuất** (T→SER/SLR, không dùng CM) | Đề xuất + CM dự phòng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Thân máy thay ống kính (DSLR/Mirrorless) | 531 | 472 | 182 | – | 436 | 239 | **445** (83,8%) | 506 |
| Ống kính | 1.128 | 911 | 708 | 418 | – | 568 | **967** (85,7%) | 1.065 |
| Nằm trong danh mục ống kính nhưng là phụ kiện (ống chuyển đổi, teleconverter, hood…) | 117 | 34 | 17 | 38 | – | 26 | 51 | 62 |
| Nằm trong danh mục ống kính, tiêu đề không có tiêu cự + khẩu độ | 125 | 79 | 40 | 19 | – | 42 | 51 | 86 |
| Nằm trong danh mục thân máy nhưng tiêu đề là phụ kiện | 7 | 3 | 0 | – | 4 | 0 | 4 | 4 |
| Máy ảnh ống liền, máy quay | 1.580 | **493** | 19 | – | – | 41 | 19 | 500 |
| Phụ kiện và khác | 24.452 | 487 | 1.053 | – | – | 1.180 | 1.053 | 1.208 |
| **Tổng** | **27.940** | 2.479 | 2.019 | 475 | 440 | 2.096 | 2.590 | 3.431 |

Đọc bảng:

- Với **thân máy**, tiêu đề hiếm khi ghi ngàm (182/531), nhưng **dòng máy** cho ngàm ở 436/531.
- Với **ống kính**, tiêu đề ghi rõ ngàm ở 708/1.128. Thêm luật "hãng + SLR" thì đạt 967.
- Cột CM của máy ảnh ống liền (493) là **ngàm sai**, vì loại máy này không có ngàm.
- 1.053 phụ kiện có ngàm trong tiêu đề, chủ yếu là hood (232), ngàm chuyển (114), bộ phụ kiện (108), nắp ống kính (82), ống nối macro (47).

### 23 ví dụ thật (`inspect_items.py … asin=…`)

| # | ASIN | Tiêu đề (rút gọn) | CM | Nguồn cho ngàm | Kết quả |
|---|---|---|---|---|---|
| 1 | B003U8Q7TC | Sony Alpha SEL1855 **E-mount** 18-55mm | Sony E | T | Sony E |
| 2 | B073S8FYTH | Fujinon **XF**50mmF2 R WR | Fujifilm X | T (tiền tố XF) | Fujifilm X |
| 3 | B010RAAOIK | Nikon **AF-S** DX NIKKOR 16-80mm … for Nikon DSLR | Nikon F | T + SLR | Nikon F |
| 4 | B084BKXDLD | Canon **RF**24-105mm F4-7.1 | Canon EF ✗ | T | Canon RF (CM sai) |
| 5 | B06ZZNK3Y9 | Sony **E** 55-210mm … for Sony E-Mount | Sony A ✗ | T | Sony E (CM sai) |
| 6 | B00UZM0G0W | Sigma 24mm f/1.4 Art for **Nikon F** | Nikon 1 ✗ | T | Nikon F (CM sai) |
| 7 | B0086UXTP4 | Rokinon 8mm for **Sony E-mount** | Fujifilm X ✗ | T | Sony E (CM sai) |
| 8 | B014MC1HUI | Tamron 18-200mm for **Canon** APS-C **Digital SLR** | Canon EF | SLR | Canon EF |
| 9 | B08M2VQ2TG | **Pentax DA** 35mm f/2.4 for Pentax Digital SLR | Pentax KAF | SLR | Pentax K |
| 10 | B0001M47FG | Olympus 11-22mm Zuiko for **4/3 Cameras** | – | SLR | Four Thirds |
| 11 | B01C9AE8T2 | Tamron SP 90mm Macro for Nikon Cameras | Nikon DX | chỉ CM | không rõ / Nikon F nếu dùng CM |
| 12 | B00A35X8ZG | Sigma 35mm F1.4 Art for Nikon | Nikon F (FX) | chỉ CM | không rõ / Nikon F nếu dùng CM |
| 13 | B00D6BOXOY | Samyang 85mm F1.4 for **Sony Alpha** | – | – | **không rõ** ("Alpha" có thể là A hoặc E) |
| 14 | B00005V8S9 | Tamron AF 75-300mm (Model 672DN) | – | – | **không rõ** (chỉ có mã model) |
| 15 | B000EXV0QQ | Tamron SP AF17-50mm for Nikon-D DSLR | Canon EF, Nikon, Pentax, Sony | SLR | Nikon F. CM liệt kê 4 ngàm vì 1 `parent_asin` gộp nhiều bản ngàm (rủi ro R2) |
| 16 | B00GC3PQ76 | Nikon **D3200** DSLR … | Nikon 1 ✗ | SER | Nikon F (CM sai) |
| 17 | B01M74YO0G | Sony **a6500** Mirrorless … | Sony A ✗ | SER | Sony E (CM sai) |
| 18 | B00T90FR3W | Canon **EOS M3** Body | Canon EF ✗ | SER | Canon EF-M (CM sai) |
| 19 | B0092MD6QW | Fujifilm **X-E1** … 18-55mm | Fujifilm X | SER | Fujifilm X |
| 20 | B07H3JVDJC | Nikon **Z6** … with FTZ Mount Adapter | Nikon F | SER | Nikon Z (CM ghi ngàm của adapter đi kèm) |
| 21 | B004NTO2I0 | Panasonic Lumix DMC-FH27 (compact) | Micro Four Thirds ✗ | – | không có ngàm (đúng) |
| 22 | B00B8KXKDU | Nikon COOLPIX S31 (compact) | Nikon 1 ✗ | – | không có ngàm (đúng) |
| 23 | B001G60DXG | Canon PowerShot SD990IS (compact) | Canon EF ✗ | – | không có ngàm (đúng) |

---

## 2. Script 03 cũ phân loại thân máy / ống kính thế nào, đúng sai ra sao?

### Quy tắc của script 03 (`03_entity_linking_matrix.py`, dòng 304–312)

- **Thân máy** nếu chuỗi categories chứa một trong: "dslr cameras", "mirrorless cameras", "digital cameras", "point & shoot".
- Ngược lại là **ống kính** nếu chứa "camera lenses", "slr camera lenses" hoặc "lenses".
- Không đọc tiêu đề.

Kết quả:
- Trên dữ liệu cũ (28.867 sản phẩm): 1.414 thân máy / 1.462 ống kính (theo báo cáo của Hải; chưa chạy lại).
- Trên dữ liệu mới (27.940 sản phẩm), Claude tái hiện đúng quy tắc trên: **1.364 thân máy / 1.434 ống kính** (`sample03.py`).

### Lỗi có tính hệ thống (đếm theo đường dẫn categories, dữ liệu mới)

- **"Thân máy" có 1.364 sản phẩm, nhưng chỉ 494 là máy thay được ống kính** (315 DSLR + 179 Mirrorless). Phần còn lại:
  - 801 máy Point & Shoot, 19 máy chụp lấy liền, 6 máy phim compact: các máy này **không có ngàm**;
  - 44 sản phẩm chỉ ghi "Digital Cameras", chưa rõ loại.
  - Nguyên nhân: từ khóa "digital cameras" và "point & shoot" kéo cả máy compact vào.
- **"Ống kính" có 1.434 sản phẩm, trong đó 49 rõ ràng không phải ống kính máy ảnh:**
  - phụ kiện kính thiên văn (Barlow Lenses) 17, kính hiển vi 11;
  - kính lọc Canon ("Lenses & Filters > Filters") 6 + 5;
  - ống kính máy quay 6, bộ combo 4.
  - Nguyên nhân: từ khóa "lenses" quá rộng.
- **Ngay trong `Lenses > Camera Lenses` vẫn có phụ kiện:** hood, ống chuyển đổi gắn ren phía trước ("0.43x wide angle"), teleconverter, thậm chí cốc giữ nhiệt hình ống kính. Bộ lọc tiêu đề trong `survey2.py` tách ra được 117 sản phẩm loại này.

### 30 mẫu (15 thân + 15 ống, `random.Random(42)`, `run_sample03.log`). Claude xem sơ bộ

| | Đúng loại "máy ảnh / ống kính" | Đúng theo nghĩa cần cho ma trận M (thân **thay được ống kính** / ống kính **gắn vào ngàm**) |
|---|---|---|
| 15 "thân máy" | 15/15 đều là máy ảnh | **9/15**. 6 sai là máy ống liền: B06 Olympus Stylus Tough, B07 Sony TX200V, B10 Canon PowerShot A40, B11 Sony TX5, B12 Konica Minolta Dimage A200, B13 Kodak Easyshare |
| 15 "ống kính" | 13/15 | **12/15**. Sai: L01 dây chống trôi zoom, L03 cốc giữ nhiệt hình ống kính, L07 ống chuyển đổi 2x gắn ren 52mm |

Ghi thêm:
- L08 (Olympus 14-54mm Zuiko) và L14 (Olympus 50-200mm Zuiko Digital) là ngàm **Four Thirds**. Bảng thông số 139 dòng và `NATIVE_MOUNT_RULES` của script 03 chỉ có 8 ngàm, không có Four Thirds, nên hai ống kính này không thể gán đúng.
- 30 mẫu là cỡ nhỏ, chỉ để minh họa. Con số đáng tin hơn là phần đếm theo categories ở trên: khoảng 60% "thân máy" của script 03 (826/1.364 trên dữ liệu mới) là máy không thay được ống kính.

---

## 3. Đề xuất thiết kế mới cho nội dung 3

Theo hướng ở `STATUS.md` mục 4: **tách việc xác định ngàm khỏi việc khớp model.**

### Ví dụ trước

Có 3 sản phẩm:
- A = "Canon EOS Rebel T7 DSLR + EF-S 18-55mm"
- B = "Sigma 30mm F1.4 DC DN for **Sony E-mount**"
- C = "Canon EF 50mm f/1.8 STM"

- **Cách cũ:** phải khớp đúng từng model với bảng 139 dòng. "Rebel T7" có trong bảng thì A có ngàm. "Sigma 30mm F1.4 DC DN" không có trong bảng thì B **không có ngàm**, dù tiêu đề ghi rõ "Sony E-mount".
- **Cách mới:**
  - B: đọc thẳng chữ "E-mount" trong tiêu đề → Sony E.
  - A: thấy "EOS Rebel" → Canon EF (Canon chỉ dùng 1 ngàm cho dòng Rebel).
  - C: thấy "Canon EF" → Canon EF.
  - Kết quả: M[A, C] = 1 (cùng ngàm EF), M[A, B] = 0.
  - Thông số chi tiết (cảm biến, tiêu cự…) vẫn lấy bằng cách khớp model như cũ. Khớp không được thì chỉ thiếu thông số, **không mất ngàm**.

### Các bước

**3a. Xác định loại sản phẩm** (`item_type`): `body_ilc` (thân thay được ống kính), `camera_fixed` (ống liền), `lens`, `lens_accessory` (teleconverter, ống chuyển đổi…), `accessory`.
- Nguồn chính: `categories`.
- Lọc nhiễu bằng từ khóa ở **phần đầu tiêu đề**, tức đoạn trước "with / + / & / bundle". Ví dụ "Canon 5D Mark IV Body **+ Battery Grip**" vẫn là thân máy.
- Ống kính phải có tiêu cự và khẩu độ trong tiêu đề (vd "50mm f/1.8").

**3b. Xác định ngàm** cho `body_ilc` và `lens`. Mỗi sản phẩm lưu lại **ngàm + nguồn + đoạn chữ làm bằng chứng**. Thứ tự ưu tiên:
1. Tiêu đề ghi rõ ngàm, hoặc tiền tố dòng ống kính chỉ thuộc 1 ngàm (T).
2. Thân máy: suy từ dòng máy (SER). Ống kính: hãng + DSLR/SLR (SLR).
3. `Compatible Mountings` chỉ dùng làm dự phòng. **[HỎI 1]**
4. Nếu ra ≥ 2 ngàm, hoặc không ra ngàm nào → "không rõ". Sản phẩm "không rõ" không vào ma trận M.

**3c. Ma trận M theo ngàm.**
- M[b, l] = 1 nếu ngàm của ống l lắp trực tiếp được vào ngàm của thân b (native).
- Bảng quy tắc ngàm mở rộng từ 8 lên khoảng 17 ngàm có trong dữ liệu (thêm Four Thirds, Sony A, Canon EF-M, Pentax K, Samsung NX, Nikon 1…).
- Ngàm chuyển (adapter) vẫn để ngoài phạm vi như bản cũ.

**3d. Khớp model với bảng thông số:** giữ như cũ, chỉ để lấy thông số. Bảng 139 dòng vẫn phải thêm cột nguồn (lỗi 5).

Đầu ra dự kiến: `item_attributes.csv` gồm `parent_asin, item_type, mount, mount_source, evidence, spec_id`.

### Ước tính độ phủ (`run_coverage.log`, quy tắc đề xuất **không** dùng CM; trong ngoặc là khi có CM dự phòng)

| Chỉ số | Bản cũ (dữ liệu cũ) | Đề xuất |
|---|---:|---:|
| Thân máy có ngàm | (257 thân + ống) | **445** (506) |
| Ống kính có ngàm | | **967** (1.065) |
| Tỷ lệ trên toàn bộ sản phẩm | 0,9% | **5,05%** (5,62%) |
| Tỷ lệ trên thân thay được ống + ống kính thật (531 + 1.128) | – | **85,1%** |
| Tương tác vào sản phẩm có ngàm (trên 595.515) | – | **8,83%** (9,47%) |
| Người dùng có ≥ 1 thân máy biết ngàm trong train | – | **9.866** (10.311) / 67.661 |
| … trong đó item test là ống kính biết ngàm (kịch bản "gợi ý ống kính cho người đã có thân") | – | **1.065** (1.177) |

Ghi chú:
- Cột "bản cũ" lấy từ STATUS.md, tính trên dữ liệu cũ; chưa chạy lại script 03 trên dữ liệu mới (vì script đó ghi đè `ai/data/kg/`).
- Toàn hệ thống vẫn có khoảng 95% sản phẩm là phụ kiện. Đây là giới hạn của dữ liệu, không phải của quy tắc.

### Rủi ro

- **R1. `Compatible Mountings` nhiễu.** Đã nêu ở mục 1. Nếu dùng làm dự phòng thì thêm khoảng 159 sản phẩm, nhưng không biết bao nhiêu trong số đó sai.
- **R2. Một `parent_asin` gộp nhiều bản ngàm.**
  - Metadata Amazon chỉ có ở mức `parent_asin`. Ví dụ ống Sigma bản Canon và bản Nikon có thể chung một trang.
  - `run_child_asins.log`: trong 967 ống kính có ngàm, **171 (17,7%)** có > 1 asin con trong review; riêng **104** là ống của hãng thứ ba (Sigma, Tamron, Rokinon…), nhóm hay bán nhiều bản ngàm.
  - Với nhóm này, ngàm ghi trong tiêu đề có thể không đúng với bản người dùng thật sự mua. Script 01 đã bỏ asin con nên hiện không kiểm được.
  - Thân máy: 175/445 (39,3%) có > 1 asin con, nhưng nhiều khả năng là bản kit hoặc màu khác nhau, cùng ngàm (chưa kiểm).
- **R3. Danh mục nhiễu** (mục 2). Bộ lọc tiêu đề giảm được nhiễu nhưng chưa đo độ chính xác.
- **R4. Ca biên của regex:**
  - "for Sony Alpha" có thể là ngàm A hoặc E;
  - "for Canon" không nói rõ EF hay RF;
  - Four Thirds dễ lẫn với Micro Four Thirds;
  - Canon EF và EF-S đang bị gộp **[HỎI 2]**.
- **R5. Hành vi thật của người dùng (quan trọng cho đánh giá).** Trong 1.065 người dùng của kịch bản trên:
  - **729** mua ống cùng ngàm với thân đã có;
  - **10** mua ống khác ngàm nhưng lắp được qua ngàm chuyển chính hãng (EF→RF, F→Z…);
  - **326 (30,6%)** mua ống khác ngàm hẳn. Ví dụ user 13149 có Nikon D7200 nhưng mua ống Panasonic Micro Four Thirds. Có thể họ có thân máy khác mà không viết review, mua tặng, hoặc dùng adapter của hãng thứ ba.
  - Hệ quả: nếu ràng buộc cứng loại mọi ống khác ngàm thì 30,6% item test trong kịch bản này **không bao giờ trúng được**. Cần chốt cách đánh giá **[HỎI 5]**.

### Cách đo độ chính xác bằng mẫu Nam chấm tay

1. **Tách hai tập mẫu, cố định seed.**
   - Tập **dev** 50 mẫu: dùng để sửa quy tắc.
   - Tập **test** 200 mẫu: chỉ chấm và tính số **sau khi đã chốt quy tắc**, không sửa quy tắc theo tập này. Mục đích là tránh "học tủ" (sửa quy tắc cho khớp đúng mẫu đang chấm).
2. **Lấy mẫu test theo tầng**, từ 1.908 sản phẩm nằm trong danh mục thân/ống:
   - 100 sản phẩm quy tắc **đã gán ngàm**, chia theo nguồn (T / SER / SLR), để đo **độ chính xác** (precision);
   - 50 sản phẩm quy tắc **không gán được**, để đo **bỏ sót** (recall);
   - 50 sản phẩm thuộc nhóm biên (phụ kiện trong danh mục ống kính, ống không có tiêu cự, máy "Digital Cameras" chung chung), để đo **phân loại loại sản phẩm**;
   - nên có cả các ống kính hãng thứ ba nhiều biến thể (R2).
3. **Chấm "mù":** file CSV cho Nam chỉ có ASIN, link `amazon.com/dp/<ASIN>`, tiêu đề, danh mục. **Không hiện kết quả của quy tắc**, để người chấm không bị dắt theo. Nam điền:
   - `type_gold` (thân thay ống / máy ống liền / ống kính / phụ kiện ống / phụ kiện / không rõ);
   - `mount_gold` (chọn từ danh sách ngàm);
   - `chắc / không chắc`;
   - ghi chú.
   Kèm 1 trang hướng dẫn chấm có ví dụ.
4. **Hai người chấm độc lập** cùng 200 mẫu (Nam + 1 người nữa). Tính mức đồng thuận Cohen's kappa; chỗ bất đồng thì hai người bàn rồi chốt nhãn cuối.
5. **Số báo cáo**, kèm khoảng tin cậy 95% (Wilson):
   - precision ngàm = số gán đúng / số được gán. Ví dụ minh họa: đúng 96/100 thì precision 96%, khoảng tin cậy xấp xỉ 90–98%;
   - tỷ lệ bỏ sót;
   - độ chính xác phân loại loại sản phẩm;
   - tách số theo nguồn (T / SER / SLR / CM).

---

## 4. Quyết định của Nam (07/10/2026)

Các quyết định này thay cho phần đề xuất ở mục 3 khi hai bên khác nhau.

| # | Câu hỏi | Quyết định | Lý do / căn cứ |
|---|---|---|---|
| 1 | Dùng `Compatible Mountings`? | **Không dùng trong bản chính**, chỉ lưu để phân tích | Nhiễu (mục 1): 493 máy compact vẫn có ngàm; lệch tiêu đề 4,8% ống / 5,4% thân |
| 2 | Gộp hay tách EF/EF-S? | **Tách, áp dụng cho mọi hãng.** Mỗi cặp (thân, ống) xếp 1 trong 4 mức (xem dưới). M = 1 khi lắp trực tiếp | Gộp thì sai ở các ca như ống EF-S trên thân 5D |
| 3 | M có phụ kiện không? | **Chỉ thân × ống.** Phụ kiện có ngàm thì lưu ngàm làm thuộc tính, đánh dấu là phụ kiện | Đúng phạm vi cô yêu cầu |
| 4 | 104 ống kính nhiều biến thể | Đánh dấu **"không chắc"**: loại khỏi M và khỏi CVR, vẫn giữ trong đồ thị | Không biết người dùng mua bản ngàm nào |
| 5 | 30,6% ca mua khác ngàm | **Giữ nguyên tập test**; báo kết quả tách 2 nhóm: item test cùng ngàm / khác ngàm với thân đã biết. Ghi rõ hạn chế: chỉ biết các thân máy người dùng có viết đánh giá | Bỏ ca khó khỏi test là chọn dữ liệu theo nhãn |
| 6 | Người chấm | **Nam chấm một mình**: 50 dev + 200 test | Không tính được kappa → ghi là hạn chế |

**4 mức tương thích (quyết định số 2).** Ví dụ trước, định nghĩa sau:

| Cặp (thân, ống) | Mức | M |
|---|---|---|
| Canon 5D (EF, full-frame) + Canon EF 50mm | `compatible_with`: lắp trực tiếp, đủ khung hình | 1 |
| Canon R10 (RF, APS-C) + RF-S 18-150mm | `compatible_with` | 1 |
| Nikon D750 (FX) + ống Nikon DX | `crops_sensor`: lắp trực tiếp nhưng ảnh bị cắt về APS-C | 1 |
| Sony a7 III (FE) + ống Sony E (APS-C); Canon R5 + RF-S | `crops_sensor` | 1 |
| Canon R6 + ống EF/EF-S; Nikon Z6 + ống F; Olympus E-M1 + ống Four Thirds | `requires_adapter`: cần ngàm chuyển chính hãng | 0 |
| Canon 5D + ống EF-S; Canon 80D + ống EF-M | không lắp được | 0 |

Hai quan hệ `crops_sensor` và `requires_adapter` lưu riêng làm cạnh của đồ thị tri thức. Bảng luật sẽ viết thành file cấu hình dễ đọc; mỗi luật ghi nguồn hoặc lý do, ưu tiên tài liệu chính thức của hãng. Chỗ chưa chắc thì đánh dấu và hỏi Nam. **Phiên 07/10 chưa viết file này.**

**Hệ quả đã làm trong phiên 07/10:**
- File chấm mù `ai/survey/content3/label_dev_50.csv`, tạo bởi `make_label_dev.py` với seed 20261007. Mẫu chia 12 tầng: thân 14, ống 22, phụ kiện/khác 14.
- Kết quả quy tắc khảo sát của 50 mẫu nằm riêng ở `ai/data/survey/label_dev_50_rule.csv` (không đưa lên git; chạy lại script sẽ tạo lại giống hệt). Lưu ý: quy tắc khảo sát vẫn **gộp** EF/EF-S và FX/DX, nên khi so phải so ở mức họ ngàm, hoặc dùng quy tắc mới.
- Hướng dẫn chấm: `docs/labeling_guide.md`. Có thêm cột `khung` (ff/apsc/khac) để phân biệt mức `crops_sensor`; Nam đã duyệt.

**Chốt thêm (07/10/2026, chi tiết ở nhật ký STATUS.md, QĐ 7–9):**
- giữ cột `khung`;
- ống APS-C hãng thứ ba "for Canon" trên thân Canon full-frame xếp "không chắc": M có thêm giá trị "không biết", lưu bằng ma trận đánh dấu riêng, và các cặp này bị loại khỏi ràng buộc cứng và CVR. Trên thân Canon APS-C thì vẫn là `compatible_with`;
- ống ngàm T ghi theo ngàm của vòng T đi kèm; tiêu đề không rõ vòng nào thì ghi `khong_chac`.

## 5. Câu hỏi đã gửi Nam (đã trả lời ở mục 4)

1. **[HỎI 1]** Có dùng `Compatible Mountings` làm dự phòng không?
   - Có: thêm 61 thân + 98 ống, và thêm 112 người dùng cho kịch bản. Nhưng trường này đã thấy sai nhiều.
   - Đề xuất: **không dùng** cho bản chính. Chỉ dùng để đối chiếu, và báo số "có CM" như một phân tích phụ.
2. **[HỎI 2]** Canon EF và EF-S: gộp (như hiện tại) hay tách?
   - Ống EF-S không lắp được thân full-frame (5D, 6D…).
   - Tách thì đúng hơn nhưng cần biết thân nào là full-frame, tức thêm một luật theo dòng máy.
3. **[HỎI 3]** Ma trận M chỉ gồm thân × ống (như cô yêu cầu), hay mở rộng sang phụ kiện phụ thuộc ngàm (hood, nắp, ngàm chuyển, teleconverter: khoảng 1.050 sản phẩm có ngàm trong tiêu đề)?
4. **[HỎI 4]** Ống kính hãng thứ ba có nhiều biến thể (104 sản phẩm): giữ ngàm theo tiêu đề, hay đánh dấu "không chắc" và loại khỏi ràng buộc cứng? Có muốn đọc lại file review để xem asin con không? Mất khoảng 2–3 phút đọc file. Nhưng metadata của asin con thì không có sẵn.
5. **[HỎI 5]** Với 30,6% ca "mua ống khác ngàm" trong kịch bản đánh giá: giữ nguyên trong tập test và nói rõ trần recall của mô hình có ràng buộc cứng; hay báo kết quả tách hai nhóm (cùng ngàm / khác ngàm)? Có thể cần hỏi ý cô.
6. **[HỎI 6]** Người chấm thứ hai là ai (Hải hay Quyền)? Cỡ mẫu 50 dev + 200 test có ổn không?
