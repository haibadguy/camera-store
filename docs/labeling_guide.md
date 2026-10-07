# Hướng dẫn chấm tay: loại sản phẩm và ngàm

Dùng cho: `ai/survey/content3/label_dev_50.csv` (50 mẫu dev), sau này là 200 mẫu test.
Người chấm: Nam (chấm một mình, theo quyết định ngày 07/10/2026).

## Quy tắc chung

1. **Chấm mù.** Không mở `ai/data/survey/label_dev_50_rule.csv` (kết quả của quy tắc) trước khi chấm xong cả 50 dòng.
2. Mỗi dòng: đọc tiêu đề và danh mục, mở link Amazon nếu cần. Nếu link hỏng, chấm theo tiêu đề và ghi `link hỏng` vào `ghi_chu`.
3. Điền 4 cột: `loai`, `ngam`, `khung`, `ghi_chu`. **Chỉ dùng các giá trị trong bảng dưới.** Viết thường, không dấu.
4. Chấm theo **sản phẩm chính** của trang, tức thứ đứng đầu tiêu đề, trước các chữ "with / + / & / bundle".
5. Không chắc thì vẫn chọn đáp án hợp lý nhất, rồi ghi `?` cùng lý do vào `ghi_chu`.

## Cột `loai`

| Giá trị | Nghĩa | Ví dụ (ngoài 50 mẫu dev) |
|---|---|---|
| `than` | Thân máy **thay được ống kính** (DSLR, mirrorless), kể cả khi bán kèm ống kit hay phụ kiện | B00GC3PQ76 "Nikon D3200 … with 18-55mm and 55-200mm" |
| `ong` | Ống kính **gắn vào ngàm** máy, kể cả ống lấy nét tay, ống cine, ống mirror | B003U8Q7TC "Sony SEL1855 E-mount 18-55mm" |
| `phu_kien` | Phụ kiện máy ảnh: teleconverter, ngàm chuyển, ống gắn ren phía trước (wide/tele converter), hood, nắp, kính lọc, pin, túi, đèn, chân máy… | B01IALYGE6 "Sony FE 1.4x Teleconverter" |
| `khac` | Máy ảnh **không thay được ống kính** (compact, bridge, chụp lấy liền, máy quay, action cam, flycam, máy dạng ống kính gắn điện thoại); và thứ không phải đồ nhiếp ảnh (gói bảo hành, máy in…) | B001G60DXG "Canon PowerShot SD990IS" |

## Cột `ngam`: ngàm vật lý

| Giá trị | Ngàm | Ghi chú |
|---|---|---|
| `canon_ef` | Canon EF | Thân: DSLR Canon **không** nhận ống EF-S, gồm full-frame (5D, 6D, 1Ds…), APS-H (1D Mark I–IV) và các máy APS-C đời đầu 10D, D30, D60. Ống: ống EF, kể cả ống hãng thứ ba "for Canon" có vòng ảnh APS-C (vd Sigma DC) |
| `canon_efs` | Canon EF-S | Thân: DSLR Canon APS-C nhận được EF-S (Rebel / xxxD, xxD từ 20D, 7D…). Ống: chỉ các ống Canon ghi **EF-S** |
| `canon_efm` | Canon EF-M | Dòng EOS M |
| `canon_rf` | Canon RF (gồm cả RF-S) | Phân biệt RF và RF-S bằng cột `khung` |
| `canon_fd` | Canon FD (máy phim) | |
| `nikon_f` | Nikon F (gồm FX và DX) | Phân biệt bằng `khung` |
| `nikon_z` | Nikon Z | |
| `nikon_1` | Nikon 1 | |
| `sony_e` | Sony E (gồm FE và E APS-C) | Phân biệt bằng `khung` |
| `sony_a` | Sony / Minolta A (gồm DT) | |
| `fuji_x` | Fujifilm X | |
| `fuji_g` | Fujifilm G (GFX) | |
| `mft` | Micro Four Thirds | |
| `four_thirds` | Four Thirds (Olympus E-1/E-3/E-5/E-3xx…E-6xx, ống "Zuiko Digital" không có "M.") | |
| `pentax_k` | Pentax K | |
| `pentax_q` | Pentax Q | |
| `l_mount` | L-Mount (Leica SL/CL/TL, Panasonic S, Sigma fp) | |
| `leica_m` | Leica M | |
| `samsung_nx` | Samsung NX | |
| `sigma_sa` | Sigma SA | |
| `m42`, `t_mount`, `c_mount` | Ngàm ren M42, T-mount, C-mount | |
| `khac_ngam` | Ngàm khác | Ghi tên ngàm vào `ghi_chu` |
| `khong_co` | Sản phẩm không có ngàm, hoặc không phụ thuộc ngàm | Máy compact, túi, pin, ống gắn ren phía trước… |
| `khong_ro` | Có ngàm, nhưng trang không cho biết là ngàm nào | Ghi lý do vào `ghi_chu` |
| `nhieu` | Trang bán **nhiều bản ngàm**, hoặc phụ kiện hợp với nhiều ngàm | Liệt kê các ngàm vào `ghi_chu` |
| `A>B` | Ngàm chuyển: ống ngàm A lên thân ngàm B | Vd `canon_ef>mft` |

## Cột `khung`: khổ cảm biến (thân) hoặc vòng ảnh (ống)

| Giá trị | Khi nào | Dấu hiệu |
|---|---|---|
| `ff` | Full-frame 35mm | Ống: EF, RF, FE, Nikon FX / AF-S không ghi DX, Sigma **DG**, Tamron **Di** / **Di III**, Tokina **FX**, Pentax **FA / D FA**, Sony A không ghi DT. Thân: 5D, 6D, R5, a7, D750, K-1… |
| `apsc` | APS-C | Ống: **EF-S, RF-S, DX, DT**, Sony E không ghi FE, Fujifilm XF/XC, Pentax **DA**, EF-M, Samsung NX, Sigma **DC**, Tamron **Di II** / **Di III-A**, Tokina **DX**, tiêu đề ghi "APS-C". Thân: Rebel, xxD, 7D, R7, R10, a6000, D3xxx/D5xxx/D7xxx/D500, X-T… |
| `khac` | Khổ khác: MFT, Four Thirds, Nikon 1, GFX (medium format), Pentax Q, APS-H | Ghi khổ vào `ghi_chu` nếu không suy ra được từ ngàm |
| `khong_ro` | Không biết | |
| (để trống) | Khi `ngam` là `khong_co` | |

**Ví dụ khung:**
- B010FAU86K "Canon EF-S 55-250mm" → `ong`, `canon_efs`, `apsc`
- B00K893ZVE "Canon EOS Rebel SL1 + EF-S 18-55mm" → `than`, `canon_efs`, `apsc`
- B000NP1C5O "Canon EOS 1D Mark III" → `than`, `canon_ef`, `khac`, ghi_chu `APS-H`

## Ca khó

| Tình huống | Cách chấm | Ví dụ |
|---|---|---|
| **Bundle thân + ống kit + phụ kiện** | `than`, ghi ngàm của thân | B01MAWGVZ4 "Sony a6000 + 16-50mm & 55-210mm + bag…" → `than`, `sony_e`, `apsc` |
| **Máy compact / bridge**, kể cả khi Amazon ghi "Compatible Mountings" | `khac`, `khong_co` | B001G60DXG Canon PowerShot → `khac`, `khong_co` (Amazon ghi "Canon EF", sai) |
| **Ngàm chuyển** (adapter, speed booster) | `phu_kien`, ngàm ghi dạng `A>B` | B014C118K8 "Metabones Canon EF to Micro Four Thirds Speed Booster" → `phu_kien`, `canon_ef>mft` |
| **Teleconverter** (lắp giữa thân và ống) | `phu_kien`, ghi ngàm của nó | B01IALYGE6 "Sony FE 1.4x Teleconverter" → `phu_kien`, `sony_e`, `ff` |
| **Ống gắn ren phía trước** ("0.43x wide angle", "2x telephoto 58mm") | `phu_kien`, `khong_co` (gắn bằng ren kính lọc, không qua ngàm); ghi cỡ ren vào `ghi_chu` | B00YDCQCGM "52MM 0.43x Wide Angle Conversion Lens … for Nikon D3200" → `phu_kien`, `khong_co`, ghi_chu `ren 52mm` |
| **Hood / nắp ống** | `phu_kien`. Nếu chỉ hợp **một ống của một ngàm** thì ghi ngàm đó; nếu ống đó có nhiều bản ngàm thì ghi `nhieu`; nếu loại phổ thông thì ghi `khong_co` | B0038LDYHY "Tamron Lenshood for SP AF10-24mm Di-II" → `phu_kien`, `nhieu` (ống Tamron 10-24 có bản Canon / Nikon / Sony / Pentax) |
| **Ống hãng thứ ba có ô chọn ngàm trên trang** | `ong`, `nhieu`, liệt kê ngàm vào `ghi_chu`. Nếu trang không có ô chọn mà tiêu đề ghi rõ 1 ngàm thì ghi ngàm đó | B000EXV0QQ "Tamron SP AF17-50mm … for Nikon-D" → xem trang: có nhiều bản ngàm thì `nhieu` |
| **"for Sony Alpha"** (có thể A hoặc E) | Xem trang hoặc mã model. Không xác định được thì `khong_ro` | B00D6BOXOY "Samyang 85mm F1.4 for Sony Alpha" |
| **"for Canon" / "for Nikon"** không nói rõ ngàm | Nếu tiêu đề có "DSLR / SLR" hoặc model DSLR → `canon_ef` / `nikon_f`. Còn lại xem trang; không rõ thì `khong_ro` | B014MC1HUI "Tamron 18-200mm for Canon APS-C Digital SLR" → `ong`, `canon_ef`, `apsc` |
| **Ống mirror / tele rẻ ngàm T kèm vòng T** | `ong`, ghi ngàm của vòng T đi kèm (vd `canon_ef`), ghi_chu `T-mount + vòng T` | |
| **Máy phim thay được ống kính** | `than`, ghi ngàm (vd `canon_fd`, `nikon_f`), `khung` = `ff` | |

## Chưa chắc, cần Nam xác nhận

1. **Thêm cột `khung`.** Nam yêu cầu 3 cột (`loai`, `ngam`, `ghi_chu`). Tôi thêm `khung` vì quyết định 2 (`crops_sensor`, EF/EF-S, DX/FX…) cần biết ống và thân là full-frame hay APS-C. Nếu Nam muốn bỏ, có thể gộp vào `ngam` (vd `nikon_f_dx`).
2. **Ống hãng thứ ba "for Canon" vòng ảnh APS-C** (Sigma DC, Tamron Di II): tôi ghi `canon_ef` + `apsc` vì theo tôi biết các ống này dùng ngàm EF, không phải EF-S. **Điều này chưa đối chiếu tài liệu hãng.** Hệ quả cho bảng luật: ống này lắp vật lý được lên thân Canon full-frame nhưng ảnh bị tối góc, mà phần lớn DSLR Canon full-frame không có chế độ tự cắt khung. Vậy cặp này thuộc mức `crops_sensor` hay "không lắp được"? Cần Nam quyết khi viết file cấu hình luật.
3. **Ống ngàm T kèm vòng T:** ghi theo vòng T (như trên) hay ghi `t_mount`?
