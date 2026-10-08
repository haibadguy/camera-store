# Nội dung 4 — Đề xuất thiết kế đồ thị tri thức G = (V, E, R)

Ngày 08/10/2026, nhánh `nam/content4`. **Chưa viết code pipeline.** Nam đã chốt 8 câu [HỎI] ngày 08/10/2026 (xem **mục 9**). Khi mục 9 khác với các mục 1–8 thì **tin mục 9**.

Số liệu trong file do các script khảo sát sinh ra (chạy trên đầu ra nội dung 3 trong `ai/data/kg/`):

| Script | Log |
|---|---|
| `ai/survey/content4/survey_specs.py` | `ai/data/survey/run_c4_survey_specs.log` |
| `ai/survey/content4/survey_kg_counts.py` | `ai/data/survey/run_c4_survey_counts.log` |
| `ai/survey/content4/survey_usecase_draft.py` | `ai/data/survey/run_c4_usecase_draft.log` |

## 1. Ví dụ trước

Một người dùng `u` trong tập train đã mua thân **Canon EOS Rebel T7i** (iid 13343) và ống **Canon EF 50mm f/1.8 STM** (iid 7056). Trong đồ thị, các cạnh liên quan:

```
u ──interacted_with──▶ T7i                    (từ train.txt)
u ──interacted_with──▶ EF 50mm f/1.8 STM      (từ train.txt)
T7i ──compatible_with──▶ EF 50mm f/1.8 STM    (nội dung 3, luật canon_ef_efs_on_efs_body)
T7i ──compatible_with──▶ EF 70-200mm f/2.8L   (nội dung 3)
T7i ──has_spec──▶ [ngàm canon_efs]            T7i ──has_spec──▶ [khổ APS-C]
EF 50mm ──has_spec──▶ [ngàm canon_ef]         EF 50mm ──has_spec──▶ [khổ full-frame]
EF 50mm ──has_spec──▶ [tiêu cự 36–70mm]       EF 50mm ──has_spec──▶ [khẩu độ ≤ f/2.0]
EF 70-200 ──suitable_for──▶ [chân dung], [thể thao/chim]   (luật mục đích, mục 4)
```

Nhờ đường đi `u → T7i → compatible_with → EF 70-200`, mô hình (nội dung 7) và phần giải thích (nội dung 8) có thể nói: "gợi ý EF 70-200 vì lắp được trên T7i bạn đang có".

Lưu ý rút ra từ chính ví dụ này: ống EF 50mm là ống full-frame, tiêu cự quy đổi là 50mm. Nhưng khi lắp trên T7i (APS-C, hệ số 1,6) thì góc nhìn tương đương 80mm, rất hợp chụp chân dung. **Mục đích sử dụng phụ thuộc cả thân lẫn ống**, còn đồ thị chỉ gắn nhãn cho ống theo khổ ống được thiết kế. Đây là một hạn chế phải nêu (xem [HỎI 4]).

## 2. Loại nút (V)

| Loại nút | Số lượng | Lấy từ | Đã đo độ chính xác? |
|---|---:|---|---|
| `user` | 67.661 | `user_map.json` (nội dung 2) | — |
| `item` | 27.940 (thân 544, ống 1.337, phụ kiện 24.301, máy ống liền / khác 1.758) | `item_map.json` + `item_type` của nội dung 3 | Loại: 98,9% / 96,8% trên holdout (nội dung 3) |
| `mount` (ngàm) | 23 | cột `mount` của `item_attributes.csv` | Ngàm: 97,3% / 100% (nội dung 3) |
| `sensor_format` (khổ cảm biến) | 7: ff, apsc, aps_h, four_thirds, one_inch, medium, small | cột `khung` + ngàm (vd mft → four_thirds, nikon_1 → one_inch, fuji_g → medium) | Thân: 100% / 99,2%. **Ống: chưa đo** (hạn chế 4 của nội dung 3) |
| `focal_range` (tiêu cự) | 6 khoảng (mục 3) | tiêu đề ống | **Chưa**, đo ở việc 2 (mục 5) |
| `aperture_class` (khẩu độ tối đa) | 5 khoảng (mục 3) | tiêu đề ống | **Chưa**, đo ở việc 2 (mục 5) |
| `usecase` (mục đích sử dụng) | 4: chân dung, phong cảnh, thể thao/chim, macro (vlog đã bỏ, QĐ 4-11) | luật nhóm đặt (mục 4, `ai/config/usecase_rules.toml`) | Không đo được: đây là quy tắc, không phải sự thật |
| ~~dải ISO~~ | 0 | **không có nguồn đáng tin**, xem mục 3.3 | — |

Tổng khoảng 95.650 nút. Mỗi `item` có thêm vector đặc trưng: one-hot loại (4 chiều) và các số đọc được (tiêu cự min/max, khẩu độ ở hai đầu), để trống thì ghi 0 kèm cờ "không có".

## 3. Thuộc tính kỹ thuật: nguồn của từng cái

### 3.1. Ngàm và khổ cảm biến
Lấy nguyên từ nội dung 3, không thêm quy tắc mới.
- Thân có 1 ngàm: 538, thuộc 20 ngàm khác nhau. Khung: ff 105, apsc 329, khác 103, không rõ 1.
- Ống có 1 ngàm: 1.166 (trong đó 130 "không chắc" theo QĐ 4). Khung: ff 463, apsc 345, khác 140, không rõ 218.
- Phụ kiện có 1 ngàm: 954 (nắp, hood, teleconverter…). Ngàm chuyển dạng "A > B": 155.

### 3.2. Tiêu cự và khẩu độ (chỉ cho ống)
- **Nguồn:** tiêu đề Amazon. Đọc ở phần chủ thể của tiêu đề (trước "with / + / for…") được cả tiêu cự lẫn khẩu độ ở **1.285 / 1.337** ống. Trong đó 623 zoom, 662 ống một tiêu cự.
- **Không dùng** trường `details` của Amazon làm nguồn:
  - "Maximum Aperture" chỉ có 6 ống;
  - "Focal Length Description" có 873 ống, nhưng có chỗ ghi tiêu cự quy đổi chứ không phải tiêu cự thật. Ví dụ Sony DT 11-18mm ghi "16.5–27 mm", Sony 50mm DT ghi "75 mm";
  - có chỗ ghi nhầm khẩu độ vào ô tiêu cự (Sigma 24-70 ghi "F 2.8").
- **Nút tiêu cự = khoảng tiêu cự quy đổi 35mm.** Mốc theo cách chia của Canon (wide-angle tới ~35mm, dưới ~24mm là ultra-wide, từ 400mm trở lên là super-tele): `<24`, `24–35`, `36–70`, `71–135`, `136–300`, `>300`.
  - Ống zoom nối tới mọi khoảng mà nó phủ.
  - Quy đổi bằng hệ số crop theo khổ ống: ff 1,0; apsc 1,5 (Canon 1,6); four_thirds 2,0; nikon_1 2,7. Ống không rõ khổ (218 ống) thì tính với cả 1,0 và 1,6, chỉ nối các khoảng mà cả hai cách tính cùng cho ra.
  - Tiêu cự thật (chưa quy đổi) vẫn giữ trong vector đặc trưng, để phần giải thích nói được con số cụ thể.
- **Nút khẩu độ:** lấy số f nhỏ nhất (với zoom khẩu độ thay đổi thì lấy ở đầu rộng). Các khoảng: `≤1.4`, `≤2.0`, `≤2.8`, `≤4`, `>4`. Mỗi ống chỉ thuộc 1 khoảng.

### 3.3. Dải ISO — không có nguồn đáng tin
- **Amazon:** `details` có "Expanded ISO Minimum / Maximum" cho 424 / 544 thân. Nhưng dữ liệu không nhất quán:
  - Cùng một máy mà các listing ghi khác nhau. 31 / 247 dòng máy có hơn một giá trị. Ví dụ Rebel T7i có listing ghi 12800, có listing 25600, có listing 51200; 5D Mark IV có listing 25600, có listing 102400.
  - Trường mang tên "Expanded" (ISO mở rộng), nhưng lúc thì người bán ghi ISO gốc, lúc ghi ISO mở rộng.
- **Wikidata:** không có thuộc tính ISO. Tra danh sách thuộc tính bằng `wbsearchentities` ngày 08/10: chỉ ra ISO standard, ISNI…
- **Lensfun, openMVG:** không có ISO.
- **DPReview:** không có dữ liệu mở. Muốn dùng phải cào trang, mà điều khoản trang không cho phép, nên không dùng.
- **Đề xuất:** không đưa ISO vào đồ thị và ghi là hạn chế. Xem [HỎI 2].

## 4. Mục đích sử dụng (quy tắc nhóm đặt ra)

**Ghi rõ trong báo cáo: đây là quy tắc do nhóm tự đặt, dựa trên khuyến nghị của tài liệu nhiếp ảnh, không phải nhãn thật.** Luật chỉ áp cho ống kính, dựa trên tiêu cự quy đổi (`lo`–`hi`) và khẩu độ.

> **Cập nhật 08/10/2026 (việc 1 đã làm, tin phần này hơn bảng nháp bên dưới).** Luật chốt nằm ở `ai/config/usecase_rules.toml` (v0.2), đếm bằng `ai/survey/content4/count_usecase.py` (log `ai/data/survey/run_c4_usecase_count.log`). Mỗi câu trích được script kiểm trên bản sao đã lưu (OK cả 4 luật).
>
> | Nhãn | Luật chốt | Căn cứ đọc toàn văn (bản sao đã lưu) | Số ống (/1.285) |
> |---|---|---|---:|
> | Phong cảnh | `lo_eq` ≤ 35 | Canon EU beginner's guide, Canon EU wildlife, Canon USA lens guide, Canon USA wide-angle, Canon EU landscape | 556 |
> | Thể thao / chim | `hi_eq` ≥ 300 | Canon EU beginner's guide, Canon USA wildlife, Canon EU wildlife | 285 |
> | Chân dung | phủ một tiêu cự quy đổi trong [85, 135] **và** khẩu độ đầu tele ≤ f/2.8 | Canon EU portrait ("around 85mm or longer"), Nikon 85mm f/1.8G. Mốc trên 135 và ngưỡng f/2.8: **quyết định nhóm** | 144 |
> | Macro | ống một tiêu cự có chữ Macro / Makro / Micro-Nikkor | Canon EU beginner's guide (≥ 0,5x), Nikon "Macro Lenses" (1:2 hoặc 1:1). Dấu hiệu thay thế bằng tiêu đề: **quyết định nhóm** | 86 |
> | ~~Vlog~~ | **bỏ** (QĐ 4-11) | Canon EU vlogging tips, Canon EU best vlogging kit: ở mức ống chỉ yêu cầu góc rộng → trùng phong cảnh | — |
>
> Không nhãn nào: 311. **Hai nguồn trong bảng nháp dưới đây không dùng được:** trang Nikon 105mm f/2D không có chữ "portrait"; trang Canon USA "Visual power in wide-angle imagery" không có câu "quay selfie cầm tay cần 24mm" (câu đó lấy từ tóm tắt kết quả tìm kiếm, không có trong trang).

Bảng nháp ban đầu (giữ làm dấu vết):

| Nhãn | Luật nháp | Căn cứ (ứng viên, **chưa đọc toàn văn**; sẽ mở từng trang, trích câu và lưu bản sao như nội dung 3) |
|---|---|---|
| Chân dung | phủ một tiêu cự trong 70–135mm **và** khẩu độ ở đầu tele ≤ f/2.8 | Nikon USA, các trang ống 85mm/105mm/135mm gọi đây là "portrait lens" ([85mm f/1.8G](https://www.nikonusa.com/p/af-s-nikkor-85mm-f18g/2201/overview), [105mm f/2D](https://www.nikonusa.com/p/af-dc-nikkor-105mm-f2d/1932/overview)); [Canon Europe – Beginner's guide to lenses](https://www.canon-europe.com/get-inspired/tips-and-techniques/beginners-guide-lenses/) |
| Phong cảnh | `lo` ≤ 35mm | [Canon Europe – landscape lenses](https://www.canon-europe.com/get-inspired/tips-and-techniques/landscape-photography-lenses/) (wide-angle tới khoảng 35mm); [Canon USA – Lens buying guide](https://www.usa.canon.com/lens-buying-guide) |
| Thể thao / chim | `hi` ≥ 300mm | [Canon USA – Lenses for wildlife](https://www.usa.canon.com/learning/training-articles/training-articles-list/canon-lenses-for-wildlife-photography) (ít nhất 300mm); [Canon Europe – best wildlife lenses](https://www.canon-europe.com/get-inspired/tips-and-techniques/best-wildlife-lenses/) (chim có thể cần 500–800mm) |
| Vlog | `lo` ≤ 24mm | [Canon USA – Visual power in wide-angle imagery](https://www.usa.canon.com/learning/training-articles/training-articles-list/visual-power-in-wide-angle-imagery) (quay selfie cầm tay cần 24mm hoặc rộng hơn); [Canon Europe – vlogging tips](https://www.canon-europe.com/get-inspired/tips-and-techniques/how-to-start-vlogging/) |

Đếm thử theo luật nháp (`survey_usecase_draft.py`, trên 1.285 ống):

| Nhãn | Số ống |
|---|---:|
| Phong cảnh | 556 |
| Vlog | 306 |
| Thể thao / chim | 285 |
| Chân dung | 229 |
| Không nhãn nào | 324 |

Ngoài ra, 209 ống không rõ khổ cho nhãn khác nhau giữa hệ số 1,0 và 1,6; với các ống này chỉ giữ phần nhãn chung.

**Vấn đề thấy ngay:**
- Mọi ống "vlog" đều là ống "phong cảnh", vì 24 < 35. Nhãn vlog vì vậy gần như không thêm thông tin.
- Thân máy không có nhãn mục đích nào: Amazon không có trường đáng tin về màn hình xoay, cổng mic, tốc độ chụp liên tiếp… để gán.

Xem [HỎI 3].

## 5. Loại quan hệ (R) và cạnh (E)

| Quan hệ | Đầu → cuối | Số cạnh (ước tính) | Nguồn |
|---|---|---:|---|
| `interacted_with` | user → item | **460.193** | chỉ `train.txt`; không dùng val/test |
| `compatible_with` | thân → ống | 70.854 | `compat_pairs.csv`, mức compatible_with, ống chắc chắn |
| `crops_sensor` | thân → ống | 2.196 | như trên, mức crops_sensor |
| `requires_adapter` | thân → ống | 16.005 | như trên, mức requires_adapter (ngàm chuyển chính hãng) |
| `has_spec` | item → mount | ≈ 2.970 (thân 538 + ống 1.166 + phụ kiện 954 + ngàm chuyển 155 × 2 đầu) | nội dung 3 |
| `has_spec` | item → sensor_format | ≈ 1.485 (thân 537 + ống 948) | nội dung 3 |
| `has_spec` | item → focal_range | ≈ 2.000 (zoom nối nhiều khoảng) | tiêu đề, mục 3.2 |
| `has_spec` | item → aperture_class | ≈ 1.285 | tiêu đề, mục 3.2 |
| `suitable_for` | item → usecase | ≈ 1.380 | luật mục 4 |

- Các cặp mức "không biết" (19.932 cặp, gồm 17.612 cặp có thân máy phim theo QĐ 16) **không có cạnh**.
- Cặp của 130 ống "không chắc" (QĐ 4): xem [HỎI 5].
- `ToUndirected()` thêm cạnh ngược `rev_*` để thông tin truyền được cả hai chiều khi huấn luyện GNN. Bảng số chỉ đếm cạnh xuôi.
- `suitable_for` không có trong danh sách quan hệ cô nêu. Cần thêm quan hệ này vì cô có nêu thực thể "mục đích sử dụng", mà thực thể đó cần một quan hệ để nối vào đồ thị.
- **Đầu ra:**
  - `ai/data/kg/kg_hetero.pt` (PyG `HeteroData`);
  - danh sách cạnh dạng CSV cho từng quan hệ, để mở bằng mắt;
  - `kg_node_index.json` (mã nút → tên dễ đọc);
  - `kg_stats.json`, `kg_validation_log.txt`.

## 6. Cách kiểm tra

**A. Toàn vẹn (script 04 tự chạy; sai một điều kiện là dừng):**
1. Mọi chỉ số nút nằm trong khoảng cho phép; không có cạnh lặp trong cùng một quan hệ.
2. Tập cạnh `interacted_with` **đúng bằng** tập cặp (u, i) của `train.txt`: 460.193 cạnh, giao với val và test đều bằng 0.
3. Cạnh thân–ống khớp từng cặp với `compat_pairs.csv`:
   - số cạnh `compatible_with` + `crops_sensor` = nnz(M) = 73.050 (nếu không đưa ống "không chắc" vào);
   - ba quan hệ thân–ống không trùng cặp nào;
   - không cặp nào thuộc `unknown_mask`.
4. `compatible_with` / `crops_sensor` chỉ nối thân và ống cùng họ ngàm, theo các luật trong `mount_rules.toml`. `requires_adapter` chỉ nối các cặp ngàm có ngàm chuyển trong bảng luật. Kiểm lại bằng cách tra ngàm của hai đầu cạnh.
5. Mỗi thân/ống có 1 ngàm có đúng 1 cạnh `has_spec → mount`, và ngàm của cạnh trùng cột `mount`.
6. Thân máy phim (17) không có cạnh `compatible_with`, `crops_sensor` hay `requires_adapter` nào.
7. Đọc lại `.pt` bằng `torch.load`, chạy thử 1 lớp `RGCNConv` trên GPU, để chắc định dạng PyG dùng được ở nội dung 7.
8. Chạy script 2 lần, sha256 của các file đầu ra phải giống nhau.

**B. Đọc bằng mắt:** in 10 cạnh ngẫu nhiên (seed cố định) của mỗi quan hệ, kèm tiêu đề sản phẩm.

**C. Độ chính xác tiêu cự / khẩu độ, đo bằng nguồn ngoài như nội dung 3:**
- **Nguồn đáp án:**
  - Lensfun: tên ống chuẩn có tiêu cự và khẩu độ;
  - Wikidata: P2151 (focal length) có ở 619 ống. P6790 (f-number) chỉ có ở 2 ống, nên khẩu độ chỉ chấm được bằng Lensfun.
- **Phải tránh vòng lặp.** Bước khớp ống của `eval_external.py` dùng chính tiêu cự và khẩu độ để khớp, nên nếu dùng lại thì kết quả luôn đúng 100%. Cách mới:
  - Muốn chấm **tiêu cự**: khớp bằng hãng, các token chữ trong tên và khẩu độ, **không dùng tiêu cự**. Chỉ giữ khi có đúng một tiêu cự ứng viên.
  - Muốn chấm khẩu độ thì làm ngược lại (khớp bằng tiêu cự, không dùng khẩu độ).
- **Thử sơ bộ** (`survey_kg_counts.py`, chưa chia fix/holdout):
  - tiêu cự: khớp được 301 ống, trùng 202;
  - khẩu độ: khớp được 554 ống, trùng 528.

  Ở phần tiêu cự có nhiều ca lệch. Xem qua thì phần lớn là do **bước khớp nhận nhầm**: Lensfun không có đúng ống đó nên khớp sang một ống khác có tên gần giống. Nhưng cũng có lỗi thật của cách đọc tiêu đề, ví dụ "Tokina 12mm - 24mm" chỉ đọc được "12".
- **Kết luận: chưa có số đo.** Ở việc 2 sẽ:
  - siết bước khớp: token chữ của tiêu đề và của tên nguồn phải trùng nhau theo cả hai chiều;
  - chia fix / holdout như QĐ 13;
  - đọc ca sai của nửa fix, ghi rõ ca nào do đáp án sai, ca nào do quy tắc sai;
  - chấm holdout một lần.

## 7. Sửa `common_05.py` (để nội dung 5 đọc được đầu ra mới)

- `load_item_type()`:
  - đọc `item_attributes.csv` thay vì `argmax` của `kg_hetero.pt`;
  - mã: 0 thân, 1 ống, 2 phụ kiện, 3 khác (thêm mã 3).
- `load_body_to_lenses()`: đọc từ cạnh `compatible_with` + `crops_sensor` (tức M = 1).
- **Định nghĩa CVR** (đề xuất, [HỎI 6]). Một ống trong top-K bị tính là vi phạm khi:
  - ống nằm trong M, tức có 1 ngàm và không thuộc nhóm "không chắc";
  - **với mọi thân** người dùng đã có trong train: cặp (thân, ống) có M = 0 và **không** thuộc nhóm "không biết".

  Như vậy cặp `requires_adapter` vẫn bị tính là vi phạm (theo QĐ 2, M = 0). Người dùng chỉ có thân máy phim thì không bị tính.
  - Bản hiện tại tính mọi ống không nằm trong tập hợp lệ là vi phạm. Tức là cả ống "không chắc" và ống mức "không biết" đều bị tính, trái với QĐ 4, 8, 16.
- **`05c_rgcn_train.py` sẽ không chạy được** với sơ đồ mới: code này ghi cứng nút `mount` và `usecase` trong `forward`. Việc này thuộc nội dung 5 và 7 (phải cài R-GCN thật, lỗi 1), không sửa ở đây.

## 8. Các câu [HỎI]

1. **Nút tiêu cự:** dùng khoảng **quy đổi 35mm** (đề xuất), hay khoảng tiêu cự thật? Mốc `<24 / 24–35 / 36–70 / 71–135 / 136–300 / >300` được không?
2. **ISO:** đồng ý không đưa ISO vào đồ thị và ghi là hạn chế? Còn hai cách khác:
   - (a) tự chép tay ISO gốc từ trang hãng cho khoảng 30–50 dòng máy phổ biến nhất (mất công, nhưng có nguồn rõ);
   - (b) dùng trường Amazon, chỉ giữ dòng máy có các listing ghi giống nhau. Không khuyên dùng, vì không đo được độ chính xác.
3. **Mục đích sử dụng:**
   - Giữ 4 nhãn chân dung / phong cảnh / thể thao-chim / vlog?
   - Vlog đang trùng hẳn với phong cảnh, vậy bỏ nhãn vlog, hay định nghĩa khác? Ví dụ chỉ tính ống có `lo` ≤ 24mm **và** nặng dưới X gram (Amazon có trường "Item Weight" ở 96% ống, nhưng chưa kiểm độ đúng).
   - Có thêm "macro" không? Tiêu đề ghi "Macro" / "Micro-Nikkor", nhưng một số zoom Sigma ghi "Macro" mà không phải macro 1:1.
4. **Nhãn mục đích gắn theo khổ ống được thiết kế** (ống FF 50mm không phải "chân dung", dù trên thân APS-C thì tương đương 80mm). Chấp nhận và ghi hạn chế, để nội dung 6/8 tự tính theo thân của người dùng?
5. **130 ống "không chắc" (QĐ 4):** trong đồ thị giữ nút và các cạnh `has_spec`, nhưng **không** nối cạnh tương thích (đề xuất, vì ngàm không chắc)? Hay nối cạnh tương thích kèm cờ? Nếu nối thì thêm 8.950 + 255 + 2.362 cạnh.
6. **Định nghĩa CVR mới ở mục 7:** đồng ý không?
7. **Phụ kiện có ngàm** (954) và **ngàm chuyển** (155): có đưa cạnh `has_spec → mount` vào đồ thị không? Đề xuất là có: nhờ đó gợi ý được hood, teleconverter, ngàm chuyển đúng ngàm.
8. **Quan hệ `suitable_for`:** đặt tên như vậy được không?

## 9. Quyết định của Nam (08/10/2026) — chưa viết code

| # | Quyết định | Thay đổi so với đề xuất ở mục 1–8 |
|---|---|---|
| 1 | **Nút tiêu cự theo tiêu cự thật** (mm ghi trên ống), giữ các mốc `<24 / 24–35 / 36–70 / 71–135 / 136–300 / >300`. Ống zoom nối mọi khoảng nó đi qua. Tiêu cự quy đổi 35mm **chỉ dùng trong luật mục đích** | Đề xuất cũ dùng khoảng quy đổi cho nút. Hệ quả: nút tiêu cự không còn phụ thuộc khổ ống, nên 218 ống không rõ khổ vẫn có cạnh tiêu cự. Ví dụ ống MFT 50mm nằm ở khoảng 36–70, dù góc nhìn tương đương 100mm |
| 2 | **Bỏ ISO**, ghi hạn chế kèm lý do (mục 3.3): Amazon không nhất quán; Wikidata, Lensfun, openMVG không có ISO; DPReview không có dữ liệu mở | Như đề xuất |
| 3 | **5 nhãn mục đích:** chân dung, phong cảnh, thể thao/chim, vlog, **macro**. **Vlog phải định nghĩa lại cho khác phong cảnh, dựa trên nguồn; không có căn cứ thì bỏ nhãn vlog.** Luật macro cũng phải có nguồn | Thêm macro; luật vlog nháp (`lo` ≤ 24mm) bị bỏ |
| 4 | Nhãn mục đích gắn theo **khổ mà ống được thiết kế cho**. Chấp nhận, ghi hạn chế (ví dụ ống FF 50mm trên thân APS-C) | Như đề xuất |
| 5 | **130 ống "không chắc" ngàm (QĐ 4):** giữ nút và các cạnh `has_spec`, **không** nối `compatible_with` / `crops_sensor` / `requires_adapter` | Như đề xuất |
| 6 | **CVR mới:** loại cặp "không biết" và ống "không chắc" khỏi **cả tử số lẫn mẫu số** | Đề xuất cũ giữ mẫu số = K. **Đã chốt 08/10 (QĐ 4-9):** mẫu số = số ống "chấm được" trong top-K, không tính phụ kiện; gộp kiểu micro (tổng vi phạm / tổng ống chấm được); người dùng có top-K không chứa ống nào chấm được thì bỏ khỏi phép tính (không tính 0); báo kèm số người dùng được tính |
| 7 | **Phụ kiện có ngàm (954) và ngàm chuyển (155):** nối `has_spec → mount`, **có đánh dấu** | Như đề xuất, thêm đánh dấu. **Đã chốt 08/10 (QĐ 4-10):** cạnh từ phụ kiện có cờ "nguồn là phụ kiện"; ngàm chuyển có hai cạnh `has_spec`, một tới ngàm phía ống, một tới ngàm phía thân, mỗi cạnh ghi rõ phía |
| 8 | Tên quan hệ **`suitable_for`** | Như đề xuất |

**Quyết định thêm của Nam (08/10/2026, sau khi duyệt việc 1):**

| # | Quyết định |
|---|---|
| 9 (sửa) | Ống "chấm được" trong CVR: xét các thân người dùng có trong train. Chấm được khi ống nằm trong M, không "không chắc", và phán chắc được: (a) có ít nhất một thân với M = 1 → không vi phạm; (b) mọi thân đều M = 0 và không cặp nào "không biết" → vi phạm. Còn lại (không thân nào M = 1, có ít nhất một cặp "không biết") → không chấm được. Người dùng không có thân nào trong train thì bỏ |
| 11 | Bỏ nhãn vlog |
| 12 | Mốc dưới chân dung giữ 85 theo nguồn |
| 13 | Giữ mốc trên 135 và ngưỡng f/2.8 của chân dung, ghi là quyết định nhóm |
| 14 | Macro = ống một tiêu cự có chữ Macro / Makro / Micro-Nikkor; chấp nhận sai đã biết |
| 15 | Mọi nguồn phải có bản sao lưu (kèm ngày, sha256); câu trích lấy từ đúng bản đã lưu; mỗi luật cần ít nhất một câu trích OK |

**2 nguồn cũ ở mục 4 không dùng được:** trang Nikon 105mm f/2D (không có chữ "portrait") và trang Canon USA "Visual power in wide-angle imagery" (không có câu "selfie cầm tay cần 24mm").

**Việc phiên sau** (theo thứ tự):
1. ~~**Đọc toàn văn các trang nguồn cho luật mục đích** (mục 4).~~ **Đã làm 08/10/2026**, xem bảng cập nhật ở mục 4. Trích câu, lưu bản sao, ghi vào file cấu hình luật như đã làm với `mount_rules.toml`. Tìm căn cứ cho vlog (khác phong cảnh) và macro; không có căn cứ cho vlog thì bỏ nhãn vlog.
2. **Đo độ chính xác tiêu cự / khẩu độ** bằng Lensfun (và Wikidata P2151 cho tiêu cự):
   - khớp không dùng chính thuộc tính cần đo;
   - siết bước khớp;
   - chia fix / holdout; chỉ đọc ca sai của nửa fix; chấm holdout một lần.
3. **Sửa `04_build_knowledge_graph.py` và `common_05.py`** theo mục 5, 7 và các quyết định trên.
4. **Xây đồ thị và chạy các kiểm tra ở mục 6.** Ghi CHANGELOG, STATUS, DATA_SOURCES.
