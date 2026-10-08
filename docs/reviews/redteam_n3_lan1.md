Mình kiểm công cụ web trước, rồi đọc tài liệu trong Project.

WebSearch hoạt động. WebFetch sẽ kiểm ngay khi mở URL nguồn đầu tiên. Giờ đọc tài liệu.

Giờ đọc code.

Đã đọc xong tài liệu, code và 3 log. Giờ mở từng URL nguồn trong `mount_rules.toml` (13 URL khác nhau cho 14 mục nguồn).

WebFetch hoạt động và trả về toàn văn trang. 4 trang Canon đầu đã kiểm. Tiếp các trang Nikon.

Nikon xong. Tiếp Sony, Olympus, Ricoh, Sigma.

Trang Olympus bị chặn robots. Thử bản lưu trên Wayback Machine, và kiểm thêm 2 ngàm chuyển chính hãng mà bảng luật có thể thiếu.

Đã kiểm xong 13 URL (12 mở được, Olympus bị chặn). Giờ tổng hợp.

**Kiểm công cụ:** WebSearch và WebFetch đều chạy được. WebFetch trả về văn bản trang đã chuyển sang markdown, không phải HTML gốc. Mình chỉ đọc code, tài liệu và 3 log, không chạy pipeline.

Dưới đây là phản biện. Mỗi vấn đề có mã (S = nghiêm trọng, T = trung bình, N = nhỏ) để tra trong bảng tóm tắt cuối bài. Bằng chứng code ghi theo tên hàm hoặc biến, vì file trong Project không có số dòng.

---

## 1. Lỗi logic trong code

**T1. `body_series()` chạy trên toàn tiêu đề, không phải chủ thể. Luật máy phim EOS lại đứng trước luật Canon APS-C** · trung bình · *lỗi logic chắc chắn, số ca bị ảnh hưởng cần kiểm*
- `classify_item` lấy ngàm của thân bằng `body_series(title)`, tức đọc cả phần "for …", "with …". Nhánh `body_cat` cũng dùng `not body_series(title)` để loại ống.
- Đã có một ca chứng minh: B00L2PN5L8 "Canon EF-S 55-250mm … for Canon EOS 7D, 60D…" thành thân (`run_holdout_errors.log`).
- Trong `BODY_SERIES`, luật `[phim] EOS` dùng mẫu `\beos\b.*\b(?:film|35mm)\b` và đứng **trước** luật APS-C. Một tiêu đề bộ máy kiểu "Canon EOS Rebel T7 … + 35mm f/1.8" sẽ thành `canon_ef`, ff, `may_phim=True`. Theo QĐ 16, mọi cặp của thân đó thành "không biết", nên thân mất hết ràng buộc.
- Cờ `may_phim` còn bật khi chủ thể có chữ "film", vd "screen protector film" nếu đứng trước các từ cắt.
- **Cần kiểm:** in 17 thân `may_phim=True` kèm tiêu đề và `evidence`, nhất là 8 thân Canon EF.
- **Hướng sửa:** chạy luật dòng máy trên `subject()`. Luật phim EOS chỉ khớp tên máy phim cụ thể, bỏ mẫu `.*35mm`.

**T2. Regex khung ống sai với mã SEL/SAL của Sony** · trung bình · *SEL: chắc chắn. SAL: nghi ngờ mạnh*
- `LENS_APSC` có `\bselp?\d{2,4}(?!g?m)`. Với "sel2470gm", `\d{2,4}` lùi về "247", lookahead gặp "0" nên vẫn khớp → apsc. "sel50f18f" (FE 50mm F1.8) cũng ra apsc.
- Trang Sony mà chính bảng luật dẫn lấy FE 24-70 mm F2.8 GM (SEL2470GM) làm ví dụ ống full-frame, và ghi tên ống full-frame bắt đầu bằng FE. Mã SEL không phân biệt được khổ.
- `LENS_FF` có `\bsal\d` → FF. Nhưng ống DT (APS-C) ngàm A cũng mang mã SAL, vd SAL1855. Điểm này dựa vào hiểu biết của mình về cách Sony đặt tên, cần đối chiếu.
- **Ảnh hưởng:** M không đổi, vì `compatible_with` và `crops_sensor` đều cho M = 1. Nhưng mức tương thích và cạnh đồ thị sai. Khung ống lại chưa đo bằng nguồn ngoài (hạn chế 4), nên lỗi này không lộ ra.
- **Hướng sửa:** bỏ SEL/SAL khỏi dấu hiệu khung, chỉ dùng chữ "FE"/"E"/"DT". In các ống có `evidence` chứa "khung: sel" hoặc "khung: sal" để đếm số ca.

**T3. Luật "hãng + SLR" suy rộng sang máy phim SLR** · trung bình · *logic chắc chắn, số ca cần kiểm*
- `BRAND_SLR` gán `minolta|sony + SLR → sony_a` và `olympus + SLR → four_thirds`. Regex `SLR` cũng khớp "slr" và "reflex" chung chung.
- Hệ quả: ống cổ "Minolta MD … for Minolta SLR" thành ngàm A (thực tế là ngàm MD/SR). Ống "Olympus OM Zuiko … SLR" thành Four Thirds (ngàm OM không có trong `MOUNT_PATTERNS`).
- Khảo sát lại viết "máy DSLR của Canon chỉ dùng ngàm EF", trong khi Canon có cả EF-S.
- **Cần kiểm:** các ống `mount_source=hang_slr` (270 ống) có chữ md, mc, rokkor, om, fd, film hoặc manual.

**T4. QĐ 16 xếp "không biết" cả những cặp chắc chắn không lắp được** · trung bình · *hệ quả chắc chắn; đây là quyết định của Nam nên chỉ đề xuất*
- Luật `film_body_unknown` áp cho mọi ngàm. Vd thân Nikon F phim + ống Canon EF, trước là `incompatible`, nay là `unknown`.
- Theo QĐ 4-9, cặp `unknown` làm ống "không chấm được". Người dùng có máy phim sẽ rơi khỏi CVR nhiều hơn mức cần.
- **Đề xuất:** chỉ áp luật phim cho cặp cùng ngàm. Cặp khác ngàm giữ `incompatible`.
  - Lợi ích: không mất các ràng buộc chắc chắn.
  - Rủi ro: gần như không có, vì khác ngàm thì máy phim hay máy số đều không lắp được.
- Câu trích Sigma trong TOML đã cắt mất cụm không dùng cho máy phim 35mm hoặc APS vì bị tối góc. Cụm này có thể làm căn cứ hãng cho QĐ 16 với ống APS-C.

**N1. Thiếu ngàm chuyển chính hãng** · nhỏ · *Pentax: chắc chắn. Fuji: nghi ngờ*
- Ricoh có thông cáo 11/09/2012 về Adapter Q, cho dùng ống ngàm K trên dòng PENTAX Q, chỉ lấy nét tay. Bảng luật không có luật này. Dữ liệu có 5 thân `pentax_q` và 45 ống `pentax_k`.
- Fujifilm M Mount Adapter (ống Leica M trên thân X): mình chỉ thấy bài báo TechRadar nói Fuji đã chính thức công bố ngàm chuyển này cho X-Pro1, chưa mở được trang hãng.
- M không đổi (đều M = 0), chỉ thiếu cạnh `requires_adapter`.

**N2. Danh sách hãng thứ ba `THIRD_PARTY` chưa đủ** · nhỏ · *chắc chắn*
- Ví dụ: `mitakon`, `zhongyi` có trong `MAKERS` của `eval_external.py` nhưng không có trong `THIRD_PARTY`. Ống nhiều biến thể của các hãng này không bị đánh dấu "không chắc" (QĐ 4).

**N3. Lỗi vặt khác** · nhỏ · *chắc chắn*
- `load_child_counts` chỉ kiểm `set(d) <= items`: cache cũ (tính trên tập người dùng khác) vẫn được dùng.
- `COMPACT_LINE` có "finepix", nên FinePix S1–S5 Pro (ngàm Nikon F) không bao giờ thành "thân theo tiêu đề".

---

## 2. Luật trong `mount_rules.toml`: kiểm 13 URL (14 mục nguồn)

| Nguồn | Mở được | Câu trích | Căn cứ cho luật |
|---|---|---|---|
| canon_efs | Có | Khớp | Trang cập nhật lần cuối 23/02/2015. Danh sách thân không nhận EF-S kết thúc ở EOS 6D, 10D, D60, D30. Trang nói ống EF-S có cấu tạo cơ khí không gắn lên thân không tương thích. Ghi chú TOML "phần sau ống chạm gương" không có trên trang. Luật `canon_ef_efs_on_efs_body` cũng suy rộng: danh sách thân **tương thích** dừng ở đời 2015, nhưng TOML không ghi điều này |
| canon_ef_eos_r | Có | Khớp | Đủ |
| canon_rfs | Có | Khớp | Đủ |
| canon_ef_eos_m | Có | Khớp (dấu "…" thay cho một đoạn nối) | Đủ |
| nikon_dx_fx | Có | **Ghép sai thứ tự** | Hai câu nằm ở hai mục khác nhau. Câu "dùng lẫn được" thuộc mục ống FX trên thân DX và đứng trước. TOML ghép chúng bằng "…" như một đoạn liền. Bài viết nói về DSLR. Ghi chú "DX hãng thứ ba có thể phải chọn tay" không có trên trang |
| nikon_z_area | Có | Khớp | Chỉ là sách hướng dẫn **Zf**. Áp cho mọi thân Z FX là suy rộng, TOML không ghi |
| nikon_ftz | Có | Khớp (bị cắt đuôi) | Trang liệt kê các ống không dùng được với FTZ II, trong đó có ống non-AI. Luật áp `requires_adapter` cho mọi ống F, hơi rộng (nhỏ) |
| nikon_ft1 | Có | Khớp | Đủ, có chú thích hạn chế lấy nét |
| sony_e_apsc | Có | Khớp | Trang lưu ý một số chế độ quay như 4K chỉ cho đặt Off (nhỏ). Trang này còn bác bỏ regex SEL (T2) |
| sony_dt | Có | Khớp | Đủ |
| sony_la_ea | Có | Khớp | Đã ghi là suy rộng (đúng) |
| olympus_mmf | **Không**: WebFetch bị robots chặn | Không kiểm được | Chỉ thấy các trang đăng lại thông cáo, không dùng làm bằng chứng. Nam cần mở bằng trình duyệt và lưu bản sao |
| pentax_k1_crop | Có | **Không nguyên văn** | Trang ghi "DA★-", TOML ghi "DA-". Trang còn nói 3 ống DA★200, DA★300, DA 560 phủ được khổ full-frame. Áp cho ống APS-C hãng thứ ba là suy rộng |
| sigma_dc | Có | Khớp, nhưng cắt mất cụm về máy phim | Trang chỉ nói về một ống (17-50 F2.8, đã ngừng bán). Áp cho mọi ống APS-C hãng thứ ba ngàm EF (Tamron Di II, Tokina DX) là suy rộng |

**T5. Tóm lại phần nguồn** · trung bình · *chắc chắn*
- STATUS (hạn chế 8) ghi "hai chỗ suy rộng". Thực tế có ít nhất **6 chỗ**: Zf → mọi Z FX; Sigma 17-50 → mọi ống DC/Di II/DX; K-1 DA → ống APS-C hãng thứ ba; danh sách thân EF-S đời 2015; LA-EA; danh sách thân không nhận EF-S.
- Có 3 khẳng định trong ghi chú không có nguồn: "chạm gương"; "DSLR Canon FF không tự cắt khung"; "DX hãng thứ ba phải chọn tay".
- Có 2 câu trích không nguyên văn: Nikon DX/FX (ghép sai thứ tự) và Ricoh (thiếu ★).
- Nguồn nội dung 3 chưa theo chuẩn QĐ 4-15 của nội dung 4: chưa có sha256 cho bản sao, chưa có script kiểm câu trích.
- **Hướng sửa:** áp QĐ 4-15 cho `rule_sources/`, sửa 2 câu trích, ghi đủ các chỗ suy rộng, và lưu bản sao trang Olympus.

---

## 3. Cách đo có thật sự độc lập không

**S1. Holdout không "sạch" như STATUS mô tả** · nghiêm trọng · *các sự kiện dưới đây chắc chắn, vì lấy từ chính CHANGELOG và STATUS; mức ảnh hưởng tới con số thì chưa biết*
1. **14 mẫu dev nằm trong holdout.** Ngày 07/10 Claude chấm dev 50 rồi sửa luật theo các lỗi tìm được (nhật ký QĐ). CHANGELOG 08/10 ghi "14 mẫu dev nằm trong holdout". Vậy người viết luật đã xem và sửa luật dựa trên 14 sản phẩm của holdout.
2. **Đã đọc ca sai trên toàn bộ 1.493 sản phẩm trước khi chia đôi.** CHANGELOG 07/10 ghi Claude đọc "khoảng 100–140 ca sai mỗi nguồn" và nhận ra mẫu lỗi "tin danh mục Amazon", "Point & Shoot", "Film Cameras". Lần sửa 08/10 nhắm đúng các mẫu lỗi đó. Câu "holdout chưa xem" chỉ đúng từ 08/10.
3. **Ba lần sửa bước khớp tên đều một chiều.** Cả ba làm trên toàn tập, đều sau khi xem ca lệch, và đều loại bỏ những ca bất lợi cho quy tắc. Không có lần nào tìm ca mà quy tắc và đáp án cùng sai. STATUS (hạn chế 1) có nêu việc sửa, nhưng chưa nêu thiên lệch một chiều này.
4. **Người phân loại "đáp án sai / quy tắc sai" chính là người viết luật.**
- **Hướng sửa (đề xuất cho Nam):**
  - (a) Loại 14 mẫu dev khỏi holdout và báo lại số.
  - (b) Ghi trung thực mốc 07/10 trong báo cáo.
  - (c) Chạy bước khớp tên bản trước 3 lần sửa trên holdout, với quy tắc hiện tại, để biết số nhạy đến đâu.
  - (d) Lập một tập kiểm tra mới chưa ai xem: lấy ngẫu nhiên khoảng 100 thân/ống **trong M**, do Hải hoặc Quyền chấm mù.
    - Lợi ích: có số độc lập thật.
    - Rủi ro: tốn 1–2 giờ của một thành viên, và vẫn chỉ có một người chấm.

**S2. Đo loại "ống" gần như tự khẳng định lại chính nó; máy phim không bao giờ được chấm** · nghiêm trọng · *chắc chắn theo code*
- `match_lens` chỉ khớp khi phần đầu tiêu đề có tiêu cự + khẩu độ (`lens_sig`). Quy tắc xếp "ống" cũng dựa vào đúng dấu hiệu đó (`LENS_POS`).
- Vì vậy "ống → ống 315/316" chủ yếu kiểm phần lọc từ phụ kiện. Ống thiếu tiêu cự hoặc khẩu độ trong tiêu đề không bao giờ vào tập chấm. Recall của loại ống chưa được đo.
- `ACC_EVAL` có các từ `film`, `mount`, `lcd`, `screen`, `flash`, `light`, `card`. Hệ quả:
  - mọi tiêu đề "…35mm Film Camera" bị loại khỏi đánh giá, nên việc **nhận diện máy phim (QĐ 16) chưa được đo**;
  - ống có chữ "E-Mount" ở phần đầu và thân có chữ "LCD" ở phần đầu cũng bị loại.
- Số sản phẩm bị loại nằm trong `run_eval_external.log` (mục `bo_qua_tieu_de_phu_kien`), log này chưa có trong Project.

**S3. Con số ngàm 97–100% chưa chắc đại diện cho các đường suy luận yếu; chưa đo độ chính xác của việc vào M** · nghiêm trọng · *nghi ngờ, cần kiểm*
- 332/1.166 ống (28%) lấy ngàm bằng suy luận: `hang_slr` 270, `dong_may_nhac_toi` 58, `vong_t` 4 (`mount_compat_log.txt`).
- Đáp án ngàm của ống chỉ có khi mọi bản trong nguồn cùng một ngàm. Ống hãng thứ ba thường có nhiều bản, nên phần lớn không có đáp án. Nhiều khả năng số đúng chủ yếu đến từ ống chính hãng có ghi rõ ngàm trong tiêu đề.
- Chưa đo **precision của việc vào M**: trong 538 hàng và 1.036 cột của M, bao nhiêu thực ra là phụ kiện? Phép đo hiện tại đi từ phía đáp án nên không thấy được loại lỗi này.
- **Cần kiểm:** ghép `eval_external_matches.csv` với `item_attributes.csv` theo `mount_source`, rồi tách số đúng / số được chấm của holdout cho từng nguồn ngàm.

**T6. Khoảng tin cậy Wilson** · trung bình
- Mình tự tính lại 4 khoảng trong CHANGELOG: khớp đến 0,1 điểm.
- Nhưng không có script nào tạo ra các khoảng này, trái quy tắc "mọi số do script tạo".
- Wilson giả định mẫu độc lập, trong khi có nhiều listing cùng một model: riêng holdout có 7 listing của Canon EF 75-300 III. Khoảng tin cậy vì thế hẹp hơn thực tế. Nên gộp theo model (cụm) hoặc dùng bootstrap theo cụm.

**T7. Câu "quy tắc chỉ sai ở 4 sản phẩm" là nói quá** · trung bình · *chắc chắn*
- Câu này nằm ngay ô nội dung 3 ở mục 3 của STATUS.
- "4/612" trộn mẫu số: DMC-S1 chỉ khớp openMVG, không có đáp án loại, nên không thuộc 612.
- Chỉ các ca lệch với đáp án được đọc, và người đọc là người viết luật.
- Nên viết lại thành: "trong 14 ca lệch về loại, đọc thủ công thấy 3 ca do quy tắc".

**N4. Lỗi bước khớp tên phía đánh giá** · nhỏ · *chắc chắn; các lỗi này làm quy tắc bị chấm oan*
- `head_main` cắt ở chữ "plus", nên tiêu đề "Galaxy S8 Plus … Screen Protector" lọt qua bộ lọc phụ kiện.
- `\bguide\b` không khớp "Guides"; "eye cup", "jacket" không có trong danh sách.
- Khớp thân chạy trước khớp ống, nên token "f4", "f2" bị khớp thành thân Nikon F4, F2.
- Ngàm `khac_ngam` (Lensfun ghi ngàm mà bước ánh xạ không đổi được) bị tính là sai, thay vì loại khỏi phép chấm.

---

## 4. Đối chiếu số liệu STATUS, CHANGELOG và log

**Khớp với log trong Project:**
- Ma trận M: 538 × 1.036; M = 1: 73.050; cờ "chưa rõ có cắt khung": 1.892; "không biết": 19.932, trong đó luật máy phim 17.612.
- Số cặp theo mức: `compatible_with` 70.854, `crops_sensor` 2.196, `requires_adapter` 16.005.
- Ống "không chắc": 130; ống `t_mount`: 1; số sản phẩm theo loại: 24.301 / 544 / 1.758 / 1.337.
- Mình đã tự cộng: tổng các mức và tổng các luật đều bằng 557.368.
- Mọi số holdout và fix của lần đo thứ hai.
- Danh sách 14 ca sai loại, 11 ô sai ngàm và 1 ô sai khung: khớp từng ASIN với log.
- Các số 07/10 trong CHANGELOG khớp nội bộ với log lần hai: 1.119 = 548 + 571, 983 = 481 + 502, 672/685 = 314/319 + 358/366.

**Chưa có bằng chứng trong Project (cần bổ sung log):**

| Số liệu | Log cần bổ sung |
|---|---|
| Holdout và fix "trước sửa": 87,9 / 83,5 / 86,1%; 502/571… | `run_typefix_report.log` (lần 1) + `before_typefix/eval_external_matches*.csv` |
| Kết quả 07/10: 98,1% / 100% / 87,8% / 83,3%; số ca bị bỏ qua | `run_eval_external.log` |
| M trung gian: 482 × 886; 54.638; 56.276; 3.474; 1.836; 75.690; 2.186; 2.960 | `ai/data/kg_new/mount_compat_log.txt` + log sau lần sửa loại thứ nhất |
| 17 thân phim = Nikon F 7 + Canon EF 8 + Canon FD 2; 462 và 294 cặp | Chưa có log nào. Cần truy vấn `item_attributes.csv` / `compat_pairs.csv` và lưu kết quả |
| 84 ca sai ở nửa fix (68 / 16; 47 / 15 / 3 / 2 / 1) | Đầu ra `eval_split_report.py --errors` |
| Đổi loại ngoài holdout 138 / 32 / 7 / 2 / 1 | Log của script nháp |
| Dev 49/50 …; 35/36 …; "14 mẫu dev trong holdout" | Log của `check_dev.py` |
| sha256 `FECEE371…`; "lần 1 = lần 2 từng ô" | Log tính hash hoặc diff |
| 951 người dùng (661 / 9 / 10 / 23 / 248) | Log của `scenario_kgnew.py` |
| Các số khảo sát trong STATUS mục 4: 1.364, 826, 493, 4,8%, 445 + 967, 8,83%, 326… | `run_survey2.log`, `run_coverage.log`, `run_sample03.log`, `run_child_asins.log` |
| Khoảng tin cậy Wilson | Chưa có script nào tạo ra |

**Chỗ mâu thuẫn hoặc đã cũ trong tài liệu:**
- Hạn chế 6(b) ghi "14 ca sai ở holdout chưa xem", nhưng 6(e) nói đã xem.
- Mục 4 "Hướng sửa (chờ chốt)" và khảo sát mục 3 vẫn tả cách chấm tay 200 mẫu, đã bị QĐ 10 thay.
- "Vấn đề cốt lõi 257/28.867" chưa cập nhật theo số mới.
- Hạn chế 8 ghi "hai chỗ suy rộng", thực tế ít nhất 6 (T5).

---

## 5. Câu hỏi hội đồng dễ hỏi mà hiện chưa có câu trả lời tốt

1. M đúng bao nhiêu phần trăm **ở mức cặp (thân, ống)**? Hiện chỉ có độ chính xác của từng thuộc tính, đo trên tập khớp tên.
2. Holdout có thật chưa ai nhìn không? (S1)
3. Ống được suy ngàm từ "hãng + DSLR" hoặc từ tên máy được nhắc tới thì đúng bao nhiêu? (S3)
4. Ai quyết định một ca là "đáp án sai"? Nếu là người viết luật thì vì sao tin được?
5. Vì sao chỉ tính ngàm chuyển chính hãng, trong khi 30,6% người dùng trong kịch bản mua ống khác ngàm (có thể dùng Sigma MC-11, Metabones)?
6. Vì sao chọn luật thủ công thay vì học máy cho Entity Linking? Hiện chưa có baseline trên cùng holdout, vd cách khớp model cũ, hoặc trường `Compatible Mountings`.
7. Vì sao cặp máy phim Nikon F + ống Canon EF lại là "không biết"? (T4)
8. Khung ống chưa được đo, vậy dựa vào đâu để xếp `crops_sensor`? (T2)
9. 7 listing của cùng một ống có phải 7 mẫu độc lập không? (T6)
10. Bao nhiêu thân và ống thật bị bỏ sót (recall)? Mới có con số 85,1% của khảo sát, tính trước khi sửa lỗi phân loại.

---

## Bảng tóm tắt

| Mã | Mức | Vấn đề | Chắc chắn / nghi ngờ |
|---|---|---|---|
| S1 | Nghiêm trọng | Holdout bị rò: 14 mẫu dev, đọc ca sai toàn tập ngày 07/10, 3 lần sửa khớp tên một chiều, người viết luật tự phân loại ca sai | Sự kiện chắc chắn; ảnh hưởng cần kiểm |
| S2 | Nghiêm trọng | Đo loại ống gần như vòng lặp; `ACC_EVAL` loại máy phim và tiêu đề có "mount"/"LCD" | Chắc chắn |
| S3 | Nghiêm trọng | Chưa tách độ chính xác theo nguồn ngàm (28% ống là suy luận); chưa đo precision của việc vào M | Nghi ngờ, cần kiểm |
| T1 | Trung bình | `body_series` đọc toàn tiêu đề; luật phim EOS (`.*35mm`) đứng trước luật APS-C | Logic chắc chắn; số ca cần kiểm |
| T2 | Trung bình | Regex SEL (lùi khớp) và SAL làm sai khung ống | SEL chắc chắn; SAL nghi ngờ mạnh |
| T3 | Trung bình | "Hãng + SLR" gán nhầm ống máy phim (Minolta MD, Olympus OM) | Logic chắc chắn; số ca cần kiểm |
| T4 | Trung bình | QĐ 16 xếp "không biết" cả cặp khác ngàm | Chắc chắn (đề xuất cho Nam) |
| T5 | Trung bình | Nguồn: 2 câu trích không nguyên văn, ít nhất 6 chỗ suy rộng, 3 khẳng định không nguồn, Olympus chưa mở được, chưa có sha256 | Chắc chắn |
| T6 | Trung bình | Khoảng tin cậy Wilson không do script, giả định độc lập bị vi phạm | Chắc chắn |
| T7 | Trung bình | "Quy tắc chỉ sai 4/612" là nói quá, trộn mẫu số | Chắc chắn |
| N1 | Nhỏ | Thiếu Pentax Adapter Q (đã xác nhận); Fujifilm M Mount Adapter (cần nguồn hãng) | Pentax chắc chắn; Fuji nghi ngờ |
| N2 | Nhỏ | `THIRD_PARTY` thiếu hãng (vd mitakon, zhongyi) | Chắc chắn |
| N3 | Nhỏ | Cache asin con kiểm lỏng; "finepix" chặn FinePix S Pro | Chắc chắn |
| N4 | Nhỏ | Lỗi khớp tên phía đánh giá ("plus", số nhiều, f4/f2, `khac_ngam`) | Chắc chắn |
| — | Nhỏ | Tài liệu cũ hoặc mâu thuẫn (6b/6e, mục 4, 257/28.867) | Chắc chắn |

---

**Bàn giao**
- **Đã làm:** đọc toàn bộ tài liệu, code và 3 log của commit d339dda. Mở 12/13 URL nguồn, đối chiếu câu trích. Tự cộng lại các số của M và tự tính lại 4 khoảng Wilson.
- **Kết quả:** 3 vấn đề nghiêm trọng, đều về độ độc lập và độ đại diện của phép đo, không phải về con số trong log (số trong log khớp). 7 vấn đề trung bình, 5 vấn đề nhỏ.
- **Còn chưa chắc:**
  - số ca thực sự dính T1, T2, T3: cần chạy các truy vấn đã nêu trong Claude Code;
  - trang Olympus chưa kiểm được;
  - nguồn hãng cho Fujifilm M Mount Adapter.
- **Có cần cập nhật STATUS.md:** có.
  - Sửa câu "4 sản phẩm" ở mục 3.
  - Sửa hạn chế 6(b) và hạn chế 8.
  - Thêm hạn chế về 14 mẫu dev trong holdout và việc đọc ca sai toàn tập ngày 07/10.
  - Giữ nội dung 3 ở mức "Đã kiểm thử" cho tới khi xử lý S1–S3.

Sources:
- [Canon Asia – What Is an EF-S Lens?](https://asia.canon/en/support/8202262300)
- [Canon Europe – Mount Adapter EF-EOS R](https://www.canon-europe.com/lenses/eos-r-adapters/mount-adapter-ef-eos-r/)
- [Canon SNAPSHOT – RF-S vs RF](https://snapshot.asia.canon/en/article/whats-the-difference-between-rf-s-and-rf-lenses)
- [Canon Europe – Mount Adapter EF-EOS M](https://www.canon-europe.com/lenses/mount-adapter-ef-eos-m-lens/)
- [Nikon USA – The DX and FX Formats](https://www.nikonusa.com/learn-and-explore/c/products-and-innovation/the-dx-and-fx-formats)
- [Nikon Zf Reference Guide – Image Area](https://onlinemanual.nikonimglib.com/zf/en/image_area_quality_and_size_31.html)
- [Nikon – FTZ II](https://imaging.nikon.com/imaging/lineup/accessory/camera/ftz_2/)
- [Nikon – FT1 press release 2011](https://www.nikon.com/company/news/2011/0921_acc_03/)
- [Sony Canada – APS-C/full frame (E-mount)](https://www.sony.ca/en/electronics/support/articles/00268906)
- [Sony Canada – DT lens on full-frame](https://www.sony.ca/en/electronics/support/articles/00029993)
- [Ricoh – K-1 Features 4](https://www.ricoh-imaging.co.jp/english/products/k-1/feature/04.html)
- [Sigma – 17-50mm F2.8 EX DC OS HSM](https://www.sigma-global.com/en/lenses/17_50_28)
- [Ricoh – Adapter Q for K-mount Lenses](https://www.ricoh-imaging.co.jp/english/news/2012/20120911_5.html)
- [TechRadar – Fuji M-mount adapter](https://www.techradar.com/news/photography-video-capture/cameras/fuji-officially-announces-m-mount-adapter-1081718)
---

## Phụ lục: chẩn đoán của Claude Code (08/10/2026, nhánh `nam/content4`)

Chỉ chẩn đoán, **không sửa** code, luật hay dữ liệu. Chỉ đọc `ai/data/kg/` (không ghi đè).
Script ở `ai/survey/redteam_n3/`, log ở `ai/data/survey/run_redteam_n3_*.log` (log không lên git).

### T4. Cặp "không biết" do luật phim mà luật thường cho "không lắp được"

Script `t4_film_unknown.py`, log `run_redteam_n3_t4.log`. Dùng chính lớp `Rules` của `03_mount_compat.py`, tính lại mức của mỗi cặp với `bfilm=False`.
Kiểm lại: 17 thân phim (Canon EF 8, Nikon F 7, Canon FD 2), 17.612 cặp `film_body_unknown` (ống vào M) — khớp `mount_compat_log.txt`.

| Ống | Cặp đang "unknown" do luật phim | Luật thường cho `incompatible` | Cùng ngàm (luật thường) |
|---|---:|---:|---|
| Vào M | 17.612 | **14.123 (80,2%)**, đều là cặp khác ngàm | 3.489: `compatible_with` 2.319, `crops_sensor` 462, `unknown` 708 |
| "Không chắc" (QĐ 4) | 2.210 | 1.684 (76,2%), đều là cặp khác ngàm | 526 |

- 14.123 = 13.795 (mặc định, không luật nào khớp) + 328 (`canon_efs_on_ef_body`: ống EF-S trên thân EF phim).
- **Không có cặp khác ngàm nào** mà luật thường cho `requires_adapter` hay mức khác: mọi cặp khác ngàm đều `incompatible`.
- Ví dụ: Nikon N70 (B00001ZUNN, `nikon_f`) + Canon EF 28-80mm (B00004THCX) → nay `unknown`, luật thường `incompatible`.
- Mỗi thân Nikon F phim mất 817 cặp `incompatible`; Canon EF phim 792; Canon FD 1.034.
- Nếu làm theo đề xuất (luật phim chỉ áp cho cặp cùng ngàm): M không đổi (cả hai mức đều M = 0), số cặp "không biết" của ống vào M giảm 19.932 → 5.809 (tính từ hai số trên, chưa chạy lại pipeline).
- **Kết luận: Red Team đúng.**

### N2. `THIRD_PARTY` thiếu hãng

Script `n2_n3_thirdparty_finepix.py`, log `run_redteam_n3_n2n3.log`.
- `MAKERS` có 37 từ khóa, 20 từ không có trong `THIRD_PARTY`: 18 là hãng máy ảnh (canon, nikon, sony…) và **2 hãng thứ ba: mitakon, zhongyi**.
- Ống 1 ngàm có > 1 asin con: 204, trong đó **74 không bị đánh dấu "không chắc"** (vẫn vào M).
- Số ống trong 74 ống đó mang tên mitakon / zhongyi: **0**. Cả dữ liệu chỉ có 1 ống Zhongyi Mitakon (B00O5IQC46, 1 asin con).
- Trong 74 ống, theo từ đầu tiêu đề: 70 ống chính hãng (Nikon, Canon, Panasonic, Fujinon, OM, Olympus, Sony, Fujifilm, Pentax). Ống chính hãng chỉ có 1 ngàm, nên QĐ 4 không cần áp.
- **4 ống hãng thứ ba không có trong cả `MAKERS` lẫn `THIRD_PARTY`**:
  - Brightin Star 23mm F5.6 (B0BP64H129, `nikon_z`, 7 asin con);
  - Brightin Star 50mm F1.4 (B0BQ6WX3V5, `canon_efm`, 9 asin con);
  - AstrHori 50mm F1.4 (B09P4QQTRG, `sony_e`, 2 asin con);
  - SIRUI 50mm F1.8 Anamorphic (B0857XT4GW, `sony_e`, 2 asin con).
  - Chưa kiểm các asin con có thật là khác ngàm không.
- **Kết luận: Red Team đúng một phần.** Danh sách thiếu hãng là đúng, nhưng 2 hãng được nêu làm ví dụ ảnh hưởng 0 ống. Lỗ hổng thật là 4 ống của Brightin Star, AstrHori, SIRUI.

### N3. FinePix S Pro bị `COMPACT_LINE` chặn

Cùng script và log trên. Vá tạm `COMPACT_LINE` **trong bộ nhớ** (bỏ "finepix") rồi gọi lại `classify_item`; không sửa file.
- Có 10 sản phẩm có "S1–S5 Pro" kèm Fuji/FinePix trong tiêu đề: **2 thân** và 8 phụ kiện (dây bấm mềm, remote, GPS…).
  - Fujifilm FinePix S2 Pro (B00006JK36);
  - Fujifilm FinePix S5 Pro (B000OUBPV4).
- Với cả 2 thân, `title_body` = False, và thành True nếu bỏ "finepix". Vậy đúng là `COMPACT_LINE` chặn bước "thân theo tiêu đề".
- Nhưng cả 2 vẫn ra **`than` / `nikon_f`** nhờ nhánh danh mục (DSLR Cameras → `body_series`). Bỏ "finepix" thì loại và ngàm không đổi. 8 phụ kiện cũng không đổi.
- **Số ca bị ảnh hưởng: 0/10.**
- **Kết luận: Red Team đúng về logic, nhưng hiện không ảnh hưởng ca nào.** Lỗi chỉ lộ ra nếu có thân S Pro nằm ngoài danh mục DSLR.

### Mục 4. Bảng "Chưa có bằng chứng": log có trên máy không

Script `evidence_logs.py`, log `run_redteam_n3_evidence.log`. Quét 29 file log / tóm tắt trong `ai/data/`, không chạy lại gì. Mọi đường dẫn dưới đây tính từ `ai/data/`.

| Số liệu | Có log trên máy? | File |
|---|---|---|
| Holdout / fix trước sửa: 502/571, 263/315, 527/612, 358/366; fix 481/548, 245/295, 514/598 | **Có** | `survey/run_typefix_report.log`; nửa fix có thêm trong `survey/run_fix_errors_before.log`. Hai file `before_typefix/eval_external_matches*.csv` có trên máy |
| Kết quả 07/10: 983/1.119, 672/685, 351/351, 214/215, 508/610, 450/450; bỏ qua 236 / 133 / 190 | **Có, nhưng chỉ ở dạng JSON** | `survey/before_typefix/eval_external_summary.json` (07/10 22:43). **`run_eval_external.log` đã bị lần chạy 08/10 ghi đè**, nay chứa số sau sửa (1.100/1.119…) |
| M trung gian: 482 × 886, 54.638, 3.474 | **Có** | `kg_new/mount_compat_log.txt`, `run03_mount_compat_kgnew.log` |
| M trung gian: 56.276, 1.836 (và 1.638) | **Có** | `survey/before_typefix/mount_compat_log.txt` |
| M trung gian: 538 × 1.037, 1.167 ống, 75.690, 2.186, 2.960 | **Không** | `kg/mount_compat_log.txt` đã bị lần chạy QĐ 16 ghi đè. Có thể dựng lại từ commit `f7e4174` (`compat_pairs.csv` có trên git), chưa làm |
| 17 thân phim | **Có** | `kg/mount_compat_log.txt`, `kg/run03_mount_compat.log` |
| 7 + 8 + 2; 462; 294 | **Trước đây không có. Nay có** (log mới của phiên này, tính trên `kg` hiện tại, khớp số trong CHANGELOG) | `survey/run_redteam_n3_t4.log` |
| Trước sửa: 53 và 36 cặp | **Không** | — |
| 84 ca sai nửa fix | **Có** (514/598; log có đúng 84 ASIN sai loại) | `survey/run_fix_errors_before.log` |
| Phân nhóm 68 / 16; 47 / 15 / 3 / 2 / 1 | **Không** (Claude phân loại tay) | — |
| Đổi loại ngoài holdout 138 / 32 / 7 / 2 / 1 | **Không** | — |
| Dev 49/50, 46/50, 43/50; 35/36, 32/36, 30/36; "14 mẫu dev trong holdout" | **Không** (không có `run_check_dev.log`; chỉ có `check_dev.py` và `label_dev_50_claude.csv`) | — |
| sha256 `FECEE371…`; "lần 1 = lần 2 từng ô" | **Không** (các file để kiểm lại thì có: `eval_split.csv`, `eval_external_matches.csv` và bản `_lan1`) | — |
| 951 người dùng (661 / 9 / 10 / 23 / 248) | **Có**, nhưng tính trên M cũ 482 × 886 (07/10 22:24), chưa chạy lại theo M hiện tại | `survey/run_scenario_kgnew.log` |
| 1.364 / 1.434 | **Có** | `survey/run_sample03.log` |
| 493 | **Có** | `survey/run_survey2.log` |
| 445 + 967, 5,05%; 8,83%; 1.065, 729 | **Có** | `survey/run_coverage.log` |
| 104/967; 175/445 | **Có** | `survey/run_child_asins.log` |
| 4,8% (39/812), 5,4% (22/407) | **Không có nguyên văn**. Log có các thành phần: ống 812 / 773, thân 407 / 385 | `survey/run_survey2.log` |
| 85,1% | **Không có nguyên văn**. Tính tay: 1.412 / (531 + 1.128) = 85,1%, với 531 và 1.128 lấy từ `survey/run_survey2.log` | — |
| 494, 826, 801 (đếm theo danh mục) | **Không** | — |
| 326 (30,6%) | **Không**. Log ghi "khác ngàm: 336"; theo `content3_survey.md`, 336 = 326 + 10 ca qua ngàm chuyển, nhưng chưa có log tách hai nhóm | `survey/run_coverage.log` (chỉ có 336) |
| Khoảng tin cậy Wilson | **Không**: không file `.py` nào trong `ai/` có chữ "wilson" | — |

**Kết luận mục 4: Red Team đúng một phần.**
- Nhận xét "chưa có trong Project" là đúng với các file Red Team được xem.
- Nhưng trên máy, khoảng một nửa số liệu đã có log: holdout trước sửa, M trung gian 07/10, 951 người dùng, phần lớn số khảo sát.
- Thiếu log thật ở các chỗ sau:
  - M sau lần sửa loại thứ nhất (75.690…);
  - phân nhóm ca sai làm tay;
  - đổi loại ngoài holdout;
  - dev 50;
  - sha256 và việc so lần 1 với lần 2;
  - 494 / 826 / 326;
  - Wilson.
- Phát hiện thêm: `run_eval_external.log` đã bị ghi đè. Số 07/10 chỉ còn trong file JSON tóm tắt.
