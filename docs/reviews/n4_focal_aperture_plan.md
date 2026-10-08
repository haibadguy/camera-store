# Kế hoạch đo độ chính xác bước đọc tiêu cự / khẩu độ từ tiêu đề ống (nội dung 4, việc 2) — đăng ký trước

- Viết ngày 08/10/2026, nhánh `nam/content4`, **trước khi xem bất kỳ kết quả nào của holdout**.
- Mốc thời gian: commit chứa file này. Bộ đọc chỉ được sửa sau commit đó, chỉ theo nửa fix (mục 5). Holdout chỉ chạy một lần, sau commit sửa bộ đọc.
- Mọi thay đổi kế hoạch trước khi chạy holdout: ghi vào mục 9 ("Sửa đổi kế hoạch") và commit riêng. Sau khi chạy holdout thì không sửa kế hoạch nữa.
- Làm theo khuôn kế hoạch lần đo 3 của nội dung 3 (`docs/reviews/n3_eval_lan3_plan.md`).

## 1. Ví dụ trước

Tiêu đề Amazon: "Sony SEL85F18 85mm F/1.8-22 Medium-Telephoto Fixed Prime Camera Lens".
- Bộ đọc hiện tại đọc khẩu độ thành (1.8, 22), tức coi như zoom có khẩu độ thay đổi từ f/1.8 đến f/22. Thật ra "1.8-22" là dải khẩu độ từ mở lớn nhất (f/1.8) đến khép nhỏ nhất (f/22).
- Nút khẩu độ của đồ thị lấy theo a1 = 1.8 → khoảng `≤2.0`: **vẫn đúng**.
- Nhưng luật chân dung dùng khẩu độ ở đầu tele (a2 nếu có) = 22 > 2.8 → ống mất nhãn chân dung: **sai**.

Vì vậy phải đo cả hai mức: **đúng con số** (mm, số f) và **đúng khoảng của nút** (thứ đồ thị dùng).

## 2. Đối tượng được đo

| Thành phần | Phiên bản | Mã băm (sha256) |
|---|---|---|
| Bộ đọc trước khi sửa (`cu`) | `eval_external.lens_sig(eval_external.head_main(tiêu đề))`, file `ai/survey/content3/eval_external.py` không đổi | `8941054e…3bc9` |
| Bộ đọc mới (`moi`) | `ai/pipeline/lens_specs.py`, `read_title()`. Ở commit của kế hoạch này, `READER_VERSION = "v0"`: chép nguyên từ `eval_external`, kiểm trên 1.339 ống cho kết quả giống hệt bộ `cu` (0 ống khác) | |
| Ống được đo | `item_type = ong` trong `ai/data/kg/item_attributes.csv` (quy tắc `ea6abb0`): **1.339 ống**, bộ đọc đọc được tiêu cự + khẩu độ ở 1.287 | `3b05f535…7b621` |
| Đáp án | `ai/survey/content4/fa_answer_key.csv` (1.153 ô), sinh bằng `ai/survey/content4/fa_match.py` | `3b2dea00…885c` |
| Tập chia | `ai/survey/content4/fa_split.csv` (657 ống) | `372f9c3f…cb02` |
| Lensfun | 56 file XML, commit `bbd4332a` (như nội dung 3) | |
| Wikidata P2151 | `ai/data/external/wikidata/focal_length_20261008.json`, tải 2026-10-08T15:11:09Z bằng `ai/survey/content4/fetch_wikidata_focal.py` (1.223 dòng, 821 item) | `42feaf8d…63fc1` |
| Bootstrap | `ai/survey/content3/bootstrap_ci.py` (không đổi) | `22d701f8…cb8a` |
| Script đo | `ai/survey/content4/fa_eval.py` ở commit của kế hoạch này | |

`fa_match.py` chạy 2 lần cho đáp án và tập chia giống hệt (sha256 trên). Log: `ai/data/survey/run_c4_fa_match_20261008.log`, `ai/data/survey/n4_fa/run_c4_fa_match_20261008_lan2.log`.

## 3. Đáp án: khớp không dùng thuộc tính cần đo

Định nghĩa đầy đủ ở docstring của `fa_match.py`. Tóm tắt:

- **Chấm tiêu cự:** khóa = (hãng, khẩu độ đọc từ tiêu đề). Nguồn: Lensfun (tiêu cự đọc từ tên ống chuẩn của Lensfun) và Wikidata (tiêu cự = các giá trị P2151, không đọc từ tên; 1 giá trị = ống một tiêu cự, 2 giá trị = zoom; item có từ 3 giá trị bị bỏ).
- **Chấm khẩu độ:** khóa = (hãng, tiêu cự đọc từ tiêu đề). Nguồn: chỉ Lensfun (Wikidata P6790 chỉ có ở 2 ống).
- **Khóa đọc bằng regex cố định của `eval_external`**, không bằng bộ đọc đang được đo. Nhờ vậy sửa bộ đọc không làm đổi tập khớp hay đáp án.
- **Token chữ trùng hai chiều.** Token chữ = token chỉ gồm chữ a-z, bỏ tên hãng, "mm", "f" và danh sách từ mô tả chung `GENERIC` (lens, zoom, wide, black…).
  - (1) Mọi token chữ của tên nguồn có trong tiêu đề.
  - (2) Mọi token chữ của tiêu đề thuộc bộ từ của nguồn (hợp token chữ của mọi tên ống cùng nguồn, cùng hãng) có trong tên nguồn.
  - Ví dụ: tiêu đề "Canon EF 75-300mm f/4-5.6 III USM" không khớp với "Canon EF 75-300mm f/4-5.6 III" của nguồn, vì "usm" thuộc bộ từ Canon của Lensfun mà tên nguồn không có (chiều 2).
- **Chỉ giữ khi các ứng viên còn lại cho đúng một giá trị** (một tiêu cự, hoặc một khẩu độ).
- `GENERIC` được chốt bằng cách đọc bộ từ của tên ống trong Lensfun và Wikidata, **không** đọc tiêu đề hay kết quả khớp.

Kết quả khớp (log `run_c4_fa_match_20261008.log`):

| Phép đo / nguồn | Có ứng viên cùng khóa | Bị loại do token chữ | Nhiều hơn một giá trị | **Khớp** |
|---|---:|---:|---:|---:|
| Tiêu cự / Lensfun | 1.141 | 556 | 216 | **369** |
| Tiêu cự / Wikidata | 844 | 402 | 123 | **319** |
| Khẩu độ / Lensfun | 1.108 | 599 | 44 | **465** |

111 ống không có tên hãng trong phần chủ thể tiêu đề nên không khớp được. **657 / 1.339 ống (49,1%) có ít nhất một đáp án.**

## 4. Chia fix / holdout

- **Một lần chia cho cả hai phép đo.** Lý do: nếu ống X thuộc fix ở phép đo tiêu cự nhưng thuộc holdout ở phép đo khẩu độ, thì đọc ca lệch tiêu cự của X là đã xem tiêu đề của một ống holdout.
- **Chia theo nhóm, không theo listing.** Các ống có chung ít nhất một mục nguồn ứng viên gộp thành một nhóm (union-find; ví dụ nhiều listing của cùng một ống Canon). Cả nhóm nằm cùng một nửa. 387 nhóm, nhóm lớn nhất 13 ống.
- **Phân tầng** theo (có đáp án tiêu cự?, có đáp án khẩu độ?, zoom / một tiêu cự theo đáp án tiêu cự). Seed `20261010`. Mỗi tầng: nửa đầu (làm tròn xuống) → fix, còn lại → holdout.

| Tầng | fix | holdout |
|---|---:|---:|
| chỉ khẩu độ (`-A_khong_ro`) | 51 | 53 |
| chỉ tiêu cự, một tiêu cự | 31 | 26 |
| chỉ tiêu cự, zoom | 31 | 36 |
| cả hai, một tiêu cự | 101 | 90 |
| cả hai, zoom | 118 | 120 |
| **Tổng** | **332** | **325** |

| Phép đo | Nguồn | fix: ô (cụm) | holdout: ô (cụm) |
|---|---|---:|---:|
| Tiêu cự | Lensfun | 167 (113) | 202 (114) |
| Tiêu cự | Wikidata | 179 (92) | 140 (88) |
| Tiêu cự | theo ống | 271 ống | **270 ống** |
| Khẩu độ | Lensfun | 237 (163) | **228 (154)** |

Điều kiện dừng của Nam (holdout dưới 50 ống cho một chỉ số): **không xảy ra** (nhỏ nhất là Wikidata 140 ô).

## 5. Chỉ số

Đơn vị = ô (phép đo, nguồn, ống). Bộ đọc không đọc ra = **sai** (không bỏ khỏi mẫu số).

| Mã | Chỉ số | Định nghĩa | Vai trò |
|---|---|---|---|
| T1 | tiêu cự đúng mm | (f1, f2) đọc được = đáp án | chính |
| **T2** | **tiêu cự đúng khoảng nút** | tập khoảng tiêu cự mà ống phủ = tập của đáp án. 6 khoảng tiêu cự thật (QĐ 4-1): `<24`, `[24, 35]`, `(35, 70]`, `(70, 135]`, `(135, 300]`, `>300`; zoom nối mọi khoảng giao với [f1, f2] (`lens_specs.focal_nodes`) | **chính, thứ đồ thị dùng** |
| K1 | khẩu độ đúng số f | (a1, a2) đọc được = đáp án | chính |
| **K2** | **khẩu độ đúng khoảng nút** | khoảng của a1 = khoảng của a1 đáp án. 5 khoảng: `≤1.4`, `(1.4, 2.0]`, `(2.0, 2.8]`, `(2.8, 4]`, `>4` (`lens_specs.aperture_node`) | **chính, thứ đồ thị dùng** |
| K3 | a1 đúng | | phụ |
| K4 | khẩu độ đầu tele đúng | (a2, không có thì a1) = của đáp án. Luật chân dung dùng số này | phụ |

- Tiêu cự báo **theo từng nguồn** (Lensfun, Wikidata) và **theo ống**: ống đúng khi đúng ở mọi nguồn có đáp án. Khẩu độ chỉ có Lensfun.
- **Khoảng tin cậy 95%:** bootstrap theo cụm (`bootstrap_ci.cluster_ci`, B = 10.000, seed 20261009, phân vị 2,5–97,5 %). Cụm của ô = (nguồn, `cum_nguon`), tức mục nguồn nhỏ nhất mà ống khớp vào. Cụm của ống = cụm Lensfun nếu có, không thì Wikidata.
- **Số chính:** bộ đọc `moi` trên holdout, T1, T2, K1, K2. In kèm bộ đọc `cu` trên cùng holdout để thấy phần thay đổi do sửa.
- Script còn in (thông tin, không phải chỉ số): số ống có đáp án từ cả hai nguồn và số ống hai đáp án trùng nhau; số đáp án bất thường (khẩu độ a2 ≥ 11, tiêu cự f2 ≤ f1).

## 6. Những gì đã biết trước khi đo (để đọc số cho đúng)

1. **Khảo sát ngày 08/10 (`survey_kg_counts.py`) đã xem ca lệch trên toàn tập**, với cách khớp lỏng hơn (token chữ chỉ một chiều, không bỏ ống "nhiều giá trị" theo cách hiện tại): tiêu cự khớp 301 / trùng 202, khẩu độ khớp 554 / trùng 528. Claude đã đọc lướt các ca lệch đó, kể cả ca thuộc holdout hiện tại. Lỗi đọc đã biết từ đó: "Tokina 12mm - 24mm" chỉ đọc được 12. Holdout vì vậy **không hoàn toàn sạch**.
2. **Lỗi đã biết thứ hai:** "F/1.8-22" bị hiểu thành khoảng khẩu độ (SEL85F18 mất nhãn chân dung). Nam yêu cầu sửa lỗi này.
3. **Khi viết kế hoạch, một lệnh tìm tiêu đề có dạng lỗi đã biết trên mọi ống đã in 10 tiêu đề, 2 tiêu đề thuộc holdout:** B01IPC1EOU (Irix 15mm f/2.4-22) và B071LTFPDQ (Nikon AF-S Fisheye 8-15mm f/3.5-4.5E … F/4.5-29). Chỉ thấy tiêu đề, không thấy đáp án hay kết quả chấm. Hai ống này sẽ chịu tác động của việc sửa lỗi "F/1.8-22", theo hướng có lợi cho bộ đọc mới nếu cách sửa đúng. 8 tiêu đề còn lại không khớp được nguồn nào (gồm SEL85F18 và Tokina 12-24), nên không có trong tập đo.
4. **Số của nửa fix với bộ đọc trước khi sửa** (đã chạy khi viết script; log `ai/data/survey/n4_fa/run_fa_eval_fix_v0_20261008_lan2.log`; chưa xem từng ca lệch):

| Chỉ số | Lensfun | Wikidata | Theo ống |
|---|---|---|---|
| T1 mm | 141/167 = 84,4% | 129/179 = 72,1% | 198/271 = 73,1% |
| T2 khoảng nút | 143/167 = 85,6% | 131/179 = 73,2% | 202/271 = 74,5% |
| K1 số f | 223/237 = 94,1% | — | — |
| K2 khoảng nút | 225/237 = 94,9% | — | — |

   Ở nửa fix, Lensfun và Wikidata cùng có đáp án tiêu cự cho 75 ống; 72 ống hai đáp án trùng nhau.
5. Người đọc và phân loại ca lệch (Claude) cũng là người sửa bộ đọc. Không có người chấm thứ hai.

## 7. Quy trình

**Bước A, nửa fix** (sau commit kế hoạch):
1. `fa_eval.py --half fix --liet-ke`: in mọi ô sai ở ít nhất một chỉ số chính.
2. Phân loại từng ô vào `ai/survey/content4/n4_fa_fix_errors.csv`, cột `phan_loai`:
   - `dap_an_sai`: khớp nhầm ống khác, hoặc đáp án của nguồn sai;
   - `doc_sai`: bộ đọc đọc sai tiêu đề;
   - `ca_hai`: cả hai cùng sai;
   - `khong_ro`.
   
   Kèm lý do ngắn; người phân loại = Claude. Đếm bằng script.
3. **Chỉ sửa `ai/pipeline/lens_specs.py`**, theo các ca `doc_sai` / `ca_hai` của nửa fix và 2 lỗi đã biết (mục 6.1–6.2). Mỗi chỗ sửa ghi lý do và ca fix làm căn cứ, tăng `READER_VERSION`. Lỗi "12mm - 24mm" không có ống nào trong tập đo, nên sửa hay không cũng không đổi số đo; chỉ đổi đồ thị và số nhãn mục đích.
4. **Không đổi:** `fa_match.py`, đáp án, tập chia, `GENERIC`, định nghĩa khoảng, `fa_eval.py` (trừ lỗi chạy). Nếu thấy cần sửa thứ ngoài bộ đọc thì **dừng, báo Nam**.
5. Chạy lại nửa fix, ghi log tên mới. Commit.

**Bước B, holdout — chạy một lần:**
1. `fa_eval.py --half holdout --out-csv ai/data/survey/n4_fa/fa_holdout_<ngày>.csv`, không `--liet-ke`. Script chấm cả `cu` và `moi`.
2. Ghi số (T1, T2, K1, K2, phụ K3, K4; khoảng tin cậy) vào STATUS / CHANGELOG và commit **trước** khi mở file CSV của holdout.
3. Sau đó mới đọc các ô sai của holdout, **chỉ để phân loại cho báo cáo** (CSV `n4_fa_holdout_errors.csv`, người phân loại = Claude). Không sửa bộ đọc theo holdout.
4. Nếu thấy lỗi script **sau khi** đã chạy holdout: **dừng và báo Nam, không tự chạy lại.**

## 8. Hạn chế đã biết của cách đo

1. **Chỉ chấm được 657 / 1.339 ống** (49,1%): các ống có tên model khớp được rõ với Lensfun / Wikidata, thường là ống chính hãng phổ biến, dễ đọc hơn. Ống không có tên hãng trong tiêu đề (111) không bao giờ vào tập đo.
2. **Đáp án Lensfun đọc tiêu cự / khẩu độ từ tên ống của Lensfun** bằng cùng họ regex với bộ đọc `cu`. Tên Lensfun có dạng chuẩn ("Canon EF 16-35mm f/2.8L USM"), và kiểm trên nửa fix không thấy đáp án bất thường nào. Tuy vậy, lỗi regex xảy ra ở cả hai phía sẽ không bị phát hiện. Wikidata (P2151) không có vấn đề này cho tiêu cự.
3. **Khóa khớp đọc bằng regex cũ.** Ống mà regex cũ đọc sai thuộc tính dùng làm khóa sẽ không khớp được, hoặc khớp nhầm (vd khẩu độ "1.8-22" làm ống không khớp được khi chấm tiêu cự). Ca khó vì vậy bị thiếu trong tập đo.
4. **Khớp nhầm vẫn có thể xảy ra** dù đã siết token hai chiều: nguồn không có đúng ống đó mà có một ống khác cùng hãng, cùng khóa, tên không có token phân biệt. Phân loại `dap_an_sai` để thấy mức độ.
5. Holdout không hoàn toàn sạch (mục 6.1, 6.3).

## 9. Sửa đổi kế hoạch

(chưa có)
