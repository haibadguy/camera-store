# Kế hoạch đo lần thứ 3 của nội dung 3 (đăng ký trước)

- Viết ngày 08/10/2026, nhánh `nam/content4`, **trước khi đo**. Phiên viết kế hoạch không chạy đánh giá trên holdout và không xem kết quả holdout.
- Mốc thời gian: commit chứa file này cùng `eval_external.py` mới. Phép đo (bước N3.7b) chỉ được chạy sau commit đó.
- Mọi thay đổi kế hoạch trước khi đo: ghi vào mục 9 ("Sửa đổi kế hoạch") và commit riêng. Sau khi đo thì không sửa kế hoạch nữa.
- Căn cứ: Red Team lần 1 (`docs/reviews/redteam_n3_lan1.md`, các điểm S1, S2, N4, T6, mục 5 câu 6).

## 1. Phiên bản được đo

| Thành phần | Phiên bản | Kiểm lại trước khi đo |
|---|---|---|
| Quy tắc (nội dung 3) | commit `ea6abb0` | `ai/data/kg/item_attributes.csv`: git blob `659b53d1…` (trùng `ea6abb0`), sha256 `3b05f535…7b621` |
| Thành viên của M | `ai/data/kg/body_index.json`, `lens_index.json` (537 thân, 1.033 ống) | sha256 `dfffbc20…`, `f774c8e5…` |
| Tập chia fix / holdout | `ai/survey/content3/eval_split.csv` (QĐ 13) | sha256 `fecee371…53c0b` |
| Mẫu dev 50 | `ai/survey/content3/label_dev_50.csv` | sha256 `6f6b1979…` |
| Bộ đánh giá | `ai/survey/content3/eval_external.py` ở commit của kế hoạch này, chế độ `--bo-danh-gia lan3` | |
| Nguồn ngoài | Lensfun 56 file XML; openMVG; Wikidata | sha256 ở log dưới |
| Bản cũ của Hải (baseline) | `ai/data/kg_v62abf54/linked_products.csv` | sha256 `c74e2c42…` |
| Môi trường | `ai/.venv` theo `ai/requirements-lock.txt`, `PYTHONHASHSEED=0` | |

Mọi mã băm đầy đủ: `ai/data/survey/run_lan3_prereg_check_20261008.log` (script `ai/survey/content3/lan3_prereg_check.py`). Bước N3.7b chạy lại script này; lệch bất kỳ dòng nào thì **dừng, không đo**.

## 2. Những gì đã biết về holdout trước lần đo này (để đọc số cho đúng)

Holdout **không còn sạch**. Lần đo 3 vì vậy là một phép đo lại có điều chỉnh, không phải phép đo độc lập. Cụ thể:

1. **14 mẫu dev nằm trong holdout** (đã kiểm bằng script, log ở trên). Ngày 07/10 Claude chấm dev 50 rồi sửa luật theo đó. Danh sách 14 ASIN: `B00004ZD2X B000051TOG B00009VT1T B0001G6UB6 B000GBV8LI B0026FCKA0 B004J3Y9U6 B0054WT9IS B005MUHJ4I B0064I7NC0 B00Q7GLGGS B00R5MILES B01LWC5IMC B07HNS84K7`.
2. **Ngày 07/10, trước khi chia đôi**, Claude đã đọc ca sai trên cả 1.493 sản phẩm; lần sửa loại ngày 08/10 nhắm đúng các mẫu lỗi đó (Red Team S1.2).
3. **Một luật đã sửa theo đúng một ca sai của holdout:** B00L2PN5L8 (ống EF-S 55-250 bị xếp thân), commit `e8b39e6`.
4. **Các sửa N4 lấy từ chính ca sai của holdout.** CHANGELOG mục "Phân loại ca sai của holdout" (08/10) liệt kê: kính dán Galaxy S8 (lỗi "plus"), sách "Expanded Guides", cốc mắt ngắm D7000 / G9, ốp máy, ống bị khớp thành thân Nikon F4 / F2, Zeiss ZE (`khac_ngam`). Trên nửa fix, các sửa N4 **không đổi ô chấm nào** (mục 7). Nghĩa là gần như mọi thay đổi do N4 sẽ rơi vào đúng những ca holdout đã xem, và đều theo chiều có lợi cho quy tắc.
5. **Sửa S2 không thể tác động lên holdout.** Holdout chỉ gồm sản phẩm đã qua bộ lọc phụ kiện cũ. S2 chỉ **thu hẹp** bộ lọc (mục 3), nên chỉ thêm sản phẩm mới, mà sản phẩm mới thì nằm ngoài 1.493 sản phẩm đã chia. Vậy trên holdout, "sửa cả hai chiều" thực tế chỉ còn chiều có lợi (N4). Xem câu hỏi H1 ở mục 8.
6. Người đọc và phân loại ca sai trước đây là người viết luật (Claude), không phải người chấm độc lập.

Hệ quả cho báo cáo: số của lần 3 **luôn phải in kèm** số của bộ đánh giá `lan2` trên cùng tập, để thấy phần chênh do sửa bộ đánh giá.

## 3. Danh sách sửa bộ đánh giá (chỉ các điểm Red Team nêu)

Ví dụ trước: tiêu đề "Sony FE 50mm F1.8 Standard Lens **E-Mount**" bị bản cũ loại khỏi đánh giá vì có chữ "mount" (từ phụ kiện). Bản mới chỉ loại khi có **cụm** phụ kiện cụ thể như "suction cup mount", "shoe mount", nên ống này được chấm.

Chiều tác động dự kiến: **có lợi** = số đúng của quy tắc có thể tăng; **bất lợi** = có thể giảm; tính trên tập được chấm.

| # | Điểm Red Team | Sửa trong `eval_external.py` (chế độ `lan3`) | Chiều tác động dự kiến | Trên nửa fix |
|---|---|---|---|---|
| a | S2: 7 từ quá rộng trong `ACC_EVAL` | Bỏ `film, mount, lcd, screen, flash, light, card`; thay bằng cụm cụ thể (`ACC_EVAL_LAN3_PHRASES`), vd "screen protector film", "instant film", "suction cup mount", "focusing screen", "speedlite flash", "ring light", "sd card", "card reader". **Mỗi cụm đều chứa đúng từ cũ**, nên tiêu đề nào bản cũ cho qua thì bản mới cũng cho qua | **Bất lợi hoặc trung tính, chỉ ngoài 1.493:** thêm vào đánh giá máy phim ("…35mm Film Camera"), ống có "E-Mount", thân có "LCD", "Touch Screen", "Dual Card Slot"… Máy phim (QĐ 16) lần đầu được chấm; phụ kiện lọt bộ lọc sẽ bị tính là quy tắc sai. **Trên holdout 747: không đổi gì** (mục 2.5) | 0 sản phẩm đổi |
| b1 | N4: `head_main` cắt ở "plus" | Bộ lọc phụ kiện dùng `head_main(…, plus=False)`: không cắt ở "plus". Bước khớp ống giữ nguyên | **Có lợi:** loại "Galaxy S8 Plus … Screen Protector". Có thể loại nhầm vài bộ máy "… plus <phụ kiện>" (trung tính) | 0 |
| b2 | N4: "guide" không khớp số nhiều | `guide` → `guides?` | **Có lợi:** loại sách "Expanded Guides" | 0 |
| b3 | N4: thiếu "eye cup", "jacket" | Thêm `eye[\s-]cups?`, `jackets?` | **Có lợi:** loại cốc mắt ngắm, áo / ốp máy | 0 |
| b4 | N4: "f4", "f2" bị khớp thành thân Nikon F4 / F2 | Token kiểu khẩu độ (`f\d{1,2}(\.\d+)?`) đứng **ngay sau** một token có chữ số hoặc "mm" thì không được khớp làm tên thân. Vd "70-210mm F4", "12-28 F4", "58mm F2" bị chặn; "Nikon F4 35mm SLR" vẫn khớp | **Có lợi:** bỏ khớp thân sai. Ống bị chặn có thể được khớp lại thành ống và chấm (đúng hoặc sai) | 0 |
| b5 | N4: `khac_ngam` tính là sai | Đáp án ngàm `khac_ngam` (ngàm ngoài bảng mã của nhóm) → không chấm, ghi `ngam_dung = dap_an_khac_ngam`, đếm riêng | **Có lợi.** Lưu ý: danh sách ngàm Lensfun rơi vào `khac_ngam` gồm cả ngàm có thật nhưng nhóm không có mã (Mamiya 645, Contax/Yashica, Minolta MD, Olympus OM, DKL, Samsung NX mini…) và một lỗi gõ của Lensfun ("Pentak K"). Nếu quy tắc gán mã của nhóm cho ống ngàm MD / OM thì đó là **lỗi thật**, nhưng nay không còn được chấm. Sẽ báo số ô bị bỏ | 1 ô (Pentax 645D; trước đó vốn đã "để trống", điểm không đổi) |

Ngoài danh sách (không sửa, ghi để biết):
- "manual" vẫn loại mọi tiêu đề có "Manual Focus", nên "Pentax K1000 Manual Focus SLR Film Camera" **vẫn bị loại** dù đã bỏ "film". Mục tiêu "để máy phim không bị loại" của S2 chỉ đạt một phần.
- Các từ phụ kiện khác cũng không bắt số nhiều (cases, covers, straps…). Chỉ sửa "guide" vì Red Team nêu.
- Phần còn lại của S2 (khớp ống dùng chính tiêu cự + khẩu độ nên đo loại "ống" gần như tự khẳng định): **chưa sửa**, giữ là hạn chế.
- Lỗi khớp "VIXIA HF R50 → EOS R50", "XH A1 → A-1": không thuộc N4, không sửa.

Hai chế độ cũ vẫn chạy được bằng tham số:
- `lan2`: giống hệt mã ở `ea6abb0` (kiểm trên nửa fix: giống từng ô, mục 7).
- `truoc_0710`: bản **trước** 3 lần sửa khớp tên ngày 07/10. **Mã gốc không còn trong git** (commit đầu tiên của `eval_external.py`, `e18dd91`, đã có cả 3 lần sửa), nên đây là bản **dựng lại theo mô tả** ở STATUS (hạn chế 1): (a) không lọc tiêu đề phụ kiện; (b) khớp ống chỉ cần hãng + tiêu cự + khẩu độ; (c) lớp "product model" của Wikidata luôn coi là máy ảnh. Không có log nào để đối chiếu bản dựng lại với bản gốc.

## 4. Tập đo

| Tên | Định nghĩa | Ghi chú |
|---|---|---|
| **H747** | 747 sản phẩm holdout (`eval_split.csv`), lọc **trước khi khớp** (`--half holdout`) | Sản phẩm nào của H747 không khớp được ở bộ đánh giá đang chạy thì không được chấm; báo số này |
| **H733** | H747 bỏ 14 mẫu dev (mục 2.1) | Lọc theo `parent_asin` sau khi khớp |
| (đề xuất) **N** | Sản phẩm **ngoài** 1.493, nay khớp được nhờ S2 (lan3) hoặc nhờ bỏ bộ lọc (truoc_0710) | **Chờ Nam (H1).** Không độc lập: luật đã được chỉnh khi xem sản phẩm ngoài holdout (17 thân phim, K1000…) |

Không dùng nửa fix trong số báo cáo.

## 5. Các phép đo sẽ chạy ở N3.7b

Quy ước chung:
- Chạy với `PYTHONHASHSEED=0`. Mỗi lần chạy ghi log và file đầu ra **tên mới** trong `ai/data/survey/n3_lan3/` (vd `run_eval_holdout_lan3_<ngày>.log`, `holdout_lan3.csv`).
- Script cho các phép đo (3)–(6) được viết và **commit trước khi chạy trên holdout**, chỉ thử trên nửa fix.
- Thứ tự: kiểm mã băm (mục 1) → (1) → (2) → (3) → (4) → (5) → (6).
- Mỗi tỉ lệ ghi rõ tử số / mẫu số và kèm khoảng tin cậy của phép đo (6).

**(1) Lần đo 3.** `eval_external.py --bo-danh-gia lan3 --half holdout`, rồi `eval_split_report.py --holdout`, báo trên H747 và H733. Chỉ số giống lần đo 2: theo từng nguồn (Lensfun, openMVG, Wikidata) gồm loại đúng / chấm; ngàm đúng / gán, số để trống, số `khac_ngam` bị bỏ (mới); khung thân đúng / gán; loại đúng theo sản phẩm (đúng ở mọi nguồn có đáp án loại); bảng nhầm loại.

**(2) Độ nhạy theo bộ đánh giá**, cùng quy tắc `ea6abb0`, trên H747 và H733:
- `truoc_0710` (bản dựng lại, trước 3 lần sửa 07/10);
- `lan2` (bản của lần đo 1, 2), để tách phần chênh do sửa bộ đánh giá (lan2 → lan3) khỏi phần chênh do sửa quy tắc (lần đo 2 → lan2 trên quy tắc `ea6abb0`).
- Hạn chế đã biết: lần sửa (a) ngày 07/10 chủ yếu **loại** sản phẩm khỏi đánh giá; những sản phẩm đó nằm ngoài 1.493 nên H747 không thấy được ảnh hưởng của (a). Ảnh hưởng thấy được trên H747 chủ yếu của (b) và (c).

**(3) Độ chính xác ngàm theo `mount_source`.** Ghép kết quả (1) với `item_attributes.csv` theo `parent_asin`. Với mỗi giá trị `tieu_de`, `dong_may`, `hang_slr`, `dong_may_nhac_toi`, `vong_t`: đúng / gán, để trống; tách theo Lensfun và Wikidata. Nhóm có dưới 10 ô chấm thì chỉ báo số đếm, không báo phần trăm.

**(4) Độ chính xác của việc vào M.** Phần tử của M: 537 thân trong `body_index.json` và 1.033 ống trong `lens_index.json`.
- Với các phần tử của M thuộc H747 và có đáp án loại: tỉ lệ đáp án đúng là thân (với hàng của M) / ống (với cột của M), theo từng nguồn và theo sản phẩm.
- Độ phủ, báo cả ba số: số phần tử M thuộc H747; số trong đó có đáp án loại; chia cho 1.570 (toàn bộ M) và chia cho số phần tử M thuộc H747.

**(5) Baseline trên cùng H747 / H733**, cùng cách chấm như (1):
- **B1, bản của Hải** (`kg_v62abf54/linked_products.csv`, 257 sản phẩm), ánh xạ theo `parent_asin`. Loại: `Body` → thân, `Lens` → ống. Ngàm: `Canon EF` → `canon_ef`, `Canon RF` → `canon_rf`, `Nikon F` → `nikon_f`, `Nikon Z` → `nikon_z`, `Sony E` → `sony_e`, `Fujifilm X` → `fuji_x`, `Micro Four Thirds` → `mft`, `L-Mount` → `l_mount`. Sản phẩm không có trong file = "không gán". Bản của Hải không tách EF / EF-S nên ngàm chấm 2 mức: chặt (EF ≠ EF-S) và theo họ (EF, EF-S gộp).
- **B2, trường Compatible Mountings** (cột `cm_raw` của `item_attributes.csv`), đọc bằng `mountlex.cm_mounts` (bản khảo sát 07/10). Đúng 1 ngàm rõ thì gán, còn lại "không gán". Ánh xạ: `Canon RF` → `canon_rf`, `Canon EF-M` → `canon_efm`, `Canon EF` → họ EF (mountlex gộp EF / EF-S, nên chỉ chấm theo họ), `Canon FD` → `canon_fd`, `Nikon Z` → `nikon_z`, `Nikon F` → `nikon_f`, `Nikon 1` → `nikon_1`, `Sony E` → `sony_e`, `Sony A` → `sony_a`, `Fujifilm X` → `fuji_x`, `Fujifilm G` → `fuji_g`, `Micro Four Thirds` → `mft`, `Four Thirds` → `four_thirds`, `L-Mount` → `l_mount`, `Leica M` → `leica_m`, `Pentax K` → `pentax_k`, `Pentax Q` → `pentax_q`, `Samsung NX` → `samsung_nx`, `Sigma SA` → `sigma_sa`, `M42` → `m42`, `T-Mount` → `t_mount`, `C-Mount` → không gán. B2 không cho loại, chỉ chấm ngàm. Lưu ý: B2 dùng chung bộ từ điển ngàm với quy tắc, chỉ khác trường dữ liệu.
- **Cách so ngàm cho mọi phương pháp** (kể cả quy tắc): xét sản phẩm H747 có đáp án ngàm (không tính `khac_ngam`), **không phụ thuộc loại mà quy tắc gán**. Mỗi phương pháp báo: độ phủ (gán 1 ngàm / có đáp án) và độ chính xác (đúng / gán), mức chặt và mức họ.
- Chưa kiểm: `parent_asin` của dữ liệu cũ (28.867 sản phẩm) có trùng hết với dữ liệu mới không; sẽ báo số sản phẩm H747 không có trong `processed_v62abf54/item_map.json`.

**(6) Khoảng tin cậy bootstrap theo cụm**, thay cho Wilson.
- Cụm = (nguồn, `cum_nguon`). `cum_nguon` là mã mục nguồn mà sản phẩm khớp vào (Lensfun: file + thứ tự máy / ống; Wikidata: URI; openMVG: số dòng), lấy mã nhỏ nhất nếu khớp nhiều mục. Vd 7 listing của Canon EF 75-300 III khớp cùng một mục Lensfun nên là **một** cụm.
- Chỉ số "theo sản phẩm" (gộp nguồn): cụm lấy theo Lensfun, không có thì Wikidata, rồi openMVG.
- Lấy lại các cụm có hoàn lại, B = 10.000 lần, seed 20261009, khoảng phân vị 2,5 % – 97,5 %. Lần lấy nào có mẫu số 0 thì bỏ và báo số lần bị bỏ.
- Script `ai/survey/content3/bootstrap_ci.py` (viết ở N3.7b, thử trên nửa fix trước).

## 6. Cam kết sau khi đo

1. Không sửa quy tắc hay bộ đánh giá theo kết quả lần 3. Nếu sửa thì holdout không còn dùng để đo được nữa, và phải nói rõ trong báo cáo.
2. Ghi đủ số của (1)–(6) vào CHANGELOG và STATUS **trước** khi xem ca sai của lần 3.
3. Số chính trong báo cáo (**đề xuất, chờ Nam chốt, H2**): lần đo 3 trên **H733**, bộ đánh giá `lan3`, kèm khoảng bootstrap. Luôn in cạnh số của `lan2` và `truoc_0710` trên cùng tập, và nhắc mục 2.
4. Số của lần đo 2 vẫn giữ trong tài liệu. Không thay hay xóa.
5. Nếu script lỗi giữa chừng: chỉ sửa lỗi chạy (không đổi logic chấm), chạy lại, ghi rõ trong log và CHANGELOG.

## 7. Kiểm thử đã làm khi viết kế hoạch (chỉ nửa fix và ví dụ dựng tay)

- **Ví dụ dựng tay:** `ai/survey/content3/test_eval_external.py`, 86/86 ca đúng (log `ai/data/survey/run_test_eval_external_20261008_lan3plan_lan2.log`). Gồm: máy phim, "E-Mount", "LCD", "Built-in Flash", "Dual Card Slot", "Low Light", "Touch Screen" không còn bị loại; 10 tiêu đề phụ kiện vẫn bị loại; "Galaxy S8 Plus … Screen Protector", "Expanded Guides", "Eye Cup", "Jacket" nay bị loại; chặn F4 / F2 ở 4 tiêu đề ống, vẫn khớp "Nikon F4 35mm SLR", "Nikon F2 Photomic"; bản `truoc_0710` khớp "Canon EF 75-300mm" với ống RF; `cum_nguon` không phụ thuộc thứ tự; mọi cụm S2 khớp được đều chứa từ cũ. Lần chạy đầu có 1 ca sai do **kỳ vọng viết sai** (tiêu đề có "Replacement" đã bị `head_for` cắt), đã sửa kỳ vọng (log lần đầu: `run_test_eval_external_20261008_lan3plan.log`).
- **Nửa fix** (`--half fix`, 746 sản phẩm; file và log trong `ai/data/survey/n3_lan3_chuanbi/`; so bằng `ai/survey/content3/compare_eval_modes.py`, script này dừng nếu gặp sản phẩm không thuộc nửa fix):

| So sánh | Kết quả |
|---|---|
| Mã cũ `ea6abb0` ↔ chế độ `lan2` | **Giống hệt** mọi ô (1.160 dòng), kể cả cột `ten_nguon` |
| `lan2` → `lan3` | 0 sản phẩm thêm / bớt; 1 ô đổi: B00YI5667E (Pentax 645D, Lensfun ngàm `khac_ngam`) `bo_trong` → `dap_an_khac_ngam`. Số đúng không đổi: Lensfun loại 535/548, ngàm 352/357, khung 177/177; Wikidata loại 283/295, ngàm 239/239; openMVG khung 106/106 |
| `lan2` → `truoc_0710` | Khớp 1.160 → 1.228 dòng (+69, −1); 96 dòng đổi đáp án hoặc ô chấm. Lensfun: loại 535/548 → 558/571, ngàm 352/357 → 310/312; Wikidata: loại 283/295 → 321/340, ngàm 239/239 → 226/242 |

Log: `run_eval_fix_{ma_ea6abb0,lan2,lan3,truoc_0710}_20261008.log`, `run_compare_fix_ea6abb0_vs_lan2_20261008.log`, `run_compare_fix_lan2_vs_lan3_20261008.log`, `run_compare_fix_lan2_vs_truoc0710_20261008.log`.

## 8. Câu hỏi chờ Nam (trước khi đo)

- **H1. Sản phẩm mới khớp được ngoài 1.493 (tập N).** Sửa S2 (và bản `truoc_0710`) chỉ có tác dụng trên những sản phẩm này. Đề xuất: báo riêng, ghi rõ "không độc lập", không gộp vào số chính. Nếu không báo thì nói rõ S2 không đo được trên holdout.
- **H2. Số chính của báo cáo:** H733 + `lan3` (đề xuất), hay H747?
- **H3. `khac_ngam`:** làm đúng như danh sách (bỏ mọi ô `khac_ngam`), hay chỉ bỏ ô có ngàm không rõ ("Generic", lỗi gõ "Pentak K") mà vẫn chấm ngàm có thật nhóm không có mã (Minolta MD, Olympus OM…)? Kế hoạch hiện tại theo danh sách: bỏ mọi ô.

## 9. Sửa đổi kế hoạch

(chưa có)
