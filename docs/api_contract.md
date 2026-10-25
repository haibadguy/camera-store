# Hợp đồng API — dịch vụ mô hình (FastAPI), phiên bản 1.3

- Viết 21/10/2026, nhánh `nam/api-fastapi`. **1.1 (21/10, Nam chốt):** `/recommend` mặc định `exclude=all_history` (bỏ
  toàn bộ lịch sử train + val + test); bỏ giá trị `exclude=train` của 1.0; demo dùng seed 1. **1.2 (21/10, Nam chốt):**
  ở `all_history`, thân máy dùng cho mặt nạ QĐ 4-9 và câu giải thích lấy từ **cả lịch sử** (train + val + test);
  `train_val` giữ nguyên thân train như lúc chấm; thêm `b_star_source`, `/users/{id}/bodies?exclude=`, trường `source`;
  `n_users_with_bodies` của `/health` thành object. **1.3 (26/10, Nam chốt):** câu giải thích ở `all_history` nói
  "bạn **đã đánh giá**" thay "bạn đã mua" (dữ liệu là đánh giá Amazon, không phải lịch sử mua); `train_val` giữ nguyên câu
  cũ để vẫn so được với kết quả đã chấm; mọi trường khác không đổi. Code: `ai/service/` (cách chạy: `ai/README.md`, mục "Dịch vụ mô hình").
- Dùng cho: **Spring Boot** (`backend/`) gọi dịch vụ này; **React** (`frontend/`) chỉ gọi Spring Boot, không gọi thẳng FastAPI.
  Kiến trúc chốt 09/10/2026: React → Spring Boot → FastAPI.
- Mô hình phía sau: **hệ thống cuối = LightGCN + mặt nạ QĐ 4-9 + giải thích theo đường** (STATUS 16/10). Checkpoint
  đã chốt trong `ai/config/n5_final.toml` (mặc định seed 1), **không huấn luyện lại**, không đổi số nào của chương 2.
- Dịch vụ dùng lại đúng code lúc chấm test và đo giải thích (`eval_05.full_rank`, `eval_05.certain_violation_mask`,
  `eval_cakg.mask_scorer`, `09_explain_lightgcn.LGExplainer`, `eval_cakg.sentence`, `eval_cakg.verify_explanation`,
  `03_mount_compat.Rules`). Đã kiểm khớp với kết quả đã lưu: mục 9.

## 1. Quy ước chung

| Mục | Quy ước |
|---|---|
| Địa chỉ mặc định | `http://127.0.0.1:8001` (đổi bằng `--host`, `--port` của `run_service.py`) |
| Phương thức | chỉ `GET`; không có xác thực (chỉ chạy trong máy / mạng nội bộ của demo) |
| Định dạng | JSON, UTF-8. Tên sản phẩm là tiếng Anh gốc của Amazon; nhãn, câu giải thích là tiếng Việt |
| `user_id` | số nguyên 0..67.660 = chỉ số người dùng nội bộ (giá trị trong `ai/data/processed/user_map.json`). **Không** nhận mã người dùng Amazon gốc |
| `item_id` | số nguyên 0..27.939 = `iid` của `item_map.json`; mỗi sản phẩm kèm `asin` (parent_asin của Amazon) |
| Loại sản phẩm `type` | `than` (thân máy), `ong` (ống kính), `phu_kien` (phụ kiện), `khac` (khác: máy ống liền, ...); `type_label` là chữ tiếng Việt |
| Header trả về | `X-Process-Time-Ms`: thời gian xử lý phía máy chủ (ms) |
| Lỗi | luôn cùng một dạng (mục 7) |

## 2. Hạn chế (Spring Boot / React phải biết)

1. **Chỉ phục vụ người dùng có trong dữ liệu** (67.661 người). Chưa có người dùng mới (cold start): `user_id` ngoài
   0..67.660 trả `404 USER_NOT_FOUND`. Spring Boot phải tự ánh xạ tài khoản demo sang một `user_id` có sẵn.
2. **Dữ liệu tĩnh**: lịch sử của người dùng là dữ liệu Amazon đã chia train / val / test, không phải giỏ hàng / đơn
   hàng của web demo. Mua thêm trên web demo **không** làm đổi gợi ý. Mặc định (`exclude=all_history`) gợi ý là "sản
   phẩm tiếp theo sau cả lịch sử": không bao giờ gợi ý sản phẩm người dùng đã có ở train, val hay test.
   - **Thân máy dùng cho mặt nạ và giải thích theo chế độ** (từ 1.2, Nam chốt 21/10): `all_history` (mặc định, demo)
     lấy thân trong **cả lịch sử** train + val + test; `train_val` lấy thân trong train, đúng như lúc chấm test (QĐ 4-9
     định nghĩa trên train). Lý do: ở 1.1 có 2.909 người có item val hoặc test là thân máy (2.066 người không có thân nào
     trong train) mà demo coi như "chưa có thân" dù thân đó đã bị loại khỏi gợi ý (`ai/service/count_history_bodies.py`).
     Số chương 2 (chấm test) không đổi: chúng dùng thân train.
   - **Thêm thân không chỉ làm tăng chặn**: QĐ 4-9 chặn ống mà **mọi** thân đều không lắp được, nên người có thêm thân
     khác ngàm sẽ bị chặn **ít** ống hơn (vd người 178: 1.016 ống ở `train_val`, 772 ống ở `all_history`).
3. **Mặt nạ chỉ chặn ống kính** "chắc chắn không lắp được" (QĐ 4-9): ống mà **mọi** thân của người dùng đều M = 0 và
   không có cặp "không biết". Thân máy, phụ kiện, máy "khác" **không** bị lọc; người không có thân thì không có ống nào
   bị chặn. **Gợi ý thân máy khác hãng / khác ngàm không phải vi phạm** (Nam chốt 21/10): người dùng có thể chuyển hệ
   máy; ràng buộc tương thích chỉ có nghĩa với cặp (thân đã có, ống). Ví dụ thật: người 409 chỉ có Nikon D3100 vẫn được
   gợi ý thân Canon EOS 40D (mục 4.4); Spring Boot / React không được hiển thị đó là lỗi tương thích.
4. `score` là tích vô hướng LightGCN eU[u]·eI[i], **chỉ dùng để xếp thứ tự trong cùng một người**; không phải xác suất,
   không so được giữa hai người.
5. Giải thích chỉ có cho **ống kính** trong top-k của **người có thân** khi có đường u → b → l (thân b của u lắp được
   l, M = 1). Các mục khác có `explanation = null`.
6. Giải thích là **quy tắc sau (post-hoc)**: b* = thân lắp được có e_bᵀe_l lớn nhất, không phải phân rã chính xác điểm
   LightGCN. Vế mục đích c\* ("phù hợp chụp …") là **sự kiện của đồ thị, không phải lý do của gợi ý**: LightGCN không
   dùng cạnh `suitable_for` (`docs/reviews/final_system_explain_plan.md` mục 3, 6).
7. Không có giá, tồn kho, ảnh sản phẩm: lấy từ cơ sở dữ liệu của Spring Boot (khóa nối: `asin`).
8. Một tiến trình, một mô hình: **demo dùng seed 1** (Nam chốt 21/10; cùng seed với ví dụ và Hình 2.6 của chương 2; mặc
   định của `run_service.py`). Chấm trên CPU. Độ trễ đo được: mục 9.

## 3. `GET /health`

Kiểm dịch vụ đã nạp xong. Spring Boot nên gọi lúc khởi động và trước khi gửi yêu cầu khác.

Ví dụ (seed 1, `results/service/check_http_s1_20261021_lan1/summary.json`):

```json
{"status": "ok", "model": "LightGCN + mặt nạ QĐ 4-9", "seed": 1,
 "best_pt_sha256": "d857e24c3d7fff692c39627b54ee30fb1e62044d9ec6fd932642d892285f5fc2",
 "embeddings_sha256": "fbda48a1f84c9fd0047d2a8d06319e1e816dcf20cbe51817f5f86241f97200b4",
 "device": "cpu", "n_users": 67661, "n_items": 27940,
 "n_users_with_bodies": {"train": 10406, "all_history": 12472},
 "startup_s": 2.4, "contract_version": "1.3"}
```

## 4. `GET /recommend?user_id=&k=&exclude=`

### 4.1. Tham số

| Tham số | Bắt buộc | Mặc định | Ý nghĩa |
|---|---|---|---|
| `user_id` | có | — | 0..67.660 |
| `k` | không | 10 | số sản phẩm trả về, 1..50 |
| `exclude` | không | `all_history` | `all_history`: bỏ **mọi** sản phẩm người dùng đã có (train + val + test) — **dùng cho demo**. `train_val`: bỏ train + item val, item test vẫn là ứng viên — **giống lúc chấm test**, chỉ dùng để kiểm (mục 9) |

### 4.2. Trả về

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id`, `k`, `exclude` | | nhắc lại tham số |
| `has_bodies`, `n_bodies` | bool, int | người dùng có thân máy không, bao nhiêu thân — theo chế độ: cả lịch sử ở `all_history`, train ở `train_val` |
| `items[]` | mảng k phần tử | xếp theo `rank` 1..k |
| `items[].rank` | int | thứ hạng (1 = cao nhất) |
| `items[].item_id`, `asin`, `title`, `type`, `type_label` | | thông tin sản phẩm |
| `items[].score` | float | điểm LightGCN (hạn chế 4) |
| `items[].explanation` | object hoặc `null` | mục 4.3 |
| `mask.rule` | string | `"QĐ 4-9 (mặt nạ 15)"` |
| `mask.n_lenses_blocked` | int | số ống trong ma trận M (1.033 ống) bị mặt nạ chặn với người này (cả catalog) |
| `mask.n_blocked_in_topk_before_mask` | int | **số ống bị mặt nạ chặn khỏi top-k**: có trong top-k nếu không có mặt nạ, bị gỡ ra khi áp mặt nạ |
| `mask.blocked_in_topk_before_mask[]` | mảng | các ống đó (`item_id`, `asin`, `title`, `type`, `type_label`) |

Quy tắc xếp hạng (giống hệt lúc chấm test): điểm giảm dần; hòa điểm thì sản phẩm có π nhỏ hơn đứng trước (π là hoán vị
cố định seed 20261009, `eval_05.tie_keys`); ống bị mặt nạ chặn có điểm −∞ nên không bao giờ vào top-k.

### 4.3. `explanation`

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `text` | string | câu tiếng Việt (mẫu của `eval_cakg.sentence`; tên dài quá 70 ký tự được cắt, thêm "…") |
| `path` | mảng 3 hoặc 4 nút | `[u, b*, l]` hoặc `[u, b*, l, c*]`: `{"kind": "user", "id"}`, `{"kind": "item", "role": "body" \| "lens", item_id, asin, title, type, type_label}`, `{"kind": "usecase", "id", "label"}` |
| `edges` | mảng 2 hoặc 3 chuỗi | loại cạnh giữa hai nút liền nhau: `owns` (u có b\* trong lịch sử đánh giá: cả lịch sử ở `all_history`, train ở `train_val`), ρ (`compatible_with` / `compatible_with_crop_unknown` / `crops_sensor`), `suitable_for` |
| `b_star`, `rho`, `c_star` | | b* (item_id thân), ρ, c* (`phong_canh` / `the_thao_chim` / `chan_dung` / `macro` hoặc `null`) |
| `b_star_score` | float | e_{b\*}ᵀe_l (điểm dùng để chọn b\*) |
| `b_star_source` | string | b\* nằm ở phần nào của lịch sử: `train` / `val` / `test` (chỉ `all_history` mới có `val` / `test`) |
| `candidate_bodies` | mảng int | mọi thân của u (theo chế độ) lắp được l (M = 1); b\* là một trong số đó |
| `verified`, `errors` | bool, mảng | kết quả `eval_cakg.verify_explanation`: mọi sự kiện trong câu đều đúng. Luôn `true` / `[]` trong các lần kiểm (mục 9); nếu `false` thì Spring Boot không nên hiện câu |

**Cách kiểm sự kiện của câu** (`verified`):
- "bạn đã đánh giá <thân>" (`all_history`) / "bạn đã mua <thân>" (`train_val`) (cạnh `owns`): b\* phải là thân máy trong **file lịch sử của người dùng** — `train.txt` ở
  `train_val`; `train.txt` + `val.txt` + `test.txt` ở `all_history`. Đồ thị tri thức chỉ có cạnh `interacted_with` của
  train, nên với thân ở val / test **không** kiểm bằng đồ thị được;
- cạnh lắp được (b\*, l) loại ρ, ngàm của b\* (`has_spec_mount`), cạnh mục đích (l, c\*) `suitable_for`, tiêu cự, khẩu
  độ: kiểm bằng **đồ thị** như cũ (cả hai chế độ);
- b\* không được là máy phim; tên l và b\* trong câu đúng tên sản phẩm.

Ba dạng câu theo ρ. Cụm chỉ cạnh `owns` theo chế độ (từ 1.3): **`all_history` (mặc định, demo): "bạn đã đánh giá"**;
`train_val`: "bạn đã mua" (đúng câu của `eval_cakg.sentence` lúc chấm). Dịch vụ lấy câu của `eval_cakg.sentence` rồi chỉ
thay đúng một cụm " bạn đã mua (ngàm " (kiểm có đúng một lần) bằng " bạn đã đánh giá (ngàm "; kiểm sự kiện chạy trên câu
cuối. Ví dụ dưới viết theo `all_history`:
- `compatible_with`: "… vì ống này lắp trực tiếp được trên … bạn đã đánh giá (ngàm …)";
- `crops_sensor`: thêm "…, nhưng ống thiết kế cho cảm biến nhỏ hơn nên ảnh sẽ bị cắt khung";
- `compatible_with_crop_unknown`: "… lắp được trên …; chưa rõ máy có tự cắt khung với ống này không".

Nếu có c\*: thêm ", và phù hợp chụp <nhãn> (tiêu cự …, khẩu độ tối đa f/…)".

### 4.4. Ví dụ thật

`GET /recommend?user_id=409&k=10` (seed 1, `exclude` mặc định `all_history`, chạy `core.RecommenderCore` 21/10/2026;
rút gọn: chỉ giữ hạng 1, 2, 5). Item val / test của người 409 (một máy ống liền, một bao da) không lọt top-10 và không phải thân máy, nên kết quả giống
bản 1.0, 1.1 (đã chạy lại với bản 1.2). Bản 1.3 (26/10): chỉ `text` đổi "bạn đã mua" → "bạn đã đánh giá", mọi số khác
trùng; bản đầy đủ không rút gọn ở `frontend/src/mock/recommend_409.json` (`ai/service/export_mock.py`).
Người 409 có một thân (Nikon D3100). Không có mặt nạ thì ống Canon EF 24-70mm vào top-10; mặt nạ gỡ nó ra.

```json
{
 "user_id": 409, "k": 10, "exclude": "all_history", "has_bodies": true, "n_bodies": 1,
 "items": [
  {"rank": 1, "item_id": 1154, "asin": "B000EVLS4C", "title": "Canon PSC-55 Deluxe Leather Compact Case for SD430, …",
   "type": "phu_kien", "type_label": "phụ kiện", "score": 7.377339839935303, "explanation": null},
  {"rank": 2, "item_id": 15485, "asin": "B01DZP4UAM",
   "title": "Nikon 55-200mm f/4-5.6G ED IF AF-S DX VR [Vibration Reduction] Nikkor Zoom Lens Bulk packaging (White box, New)",
   "type": "ong", "type_label": "ống kính", "score": 6.998710632324219,
   "explanation": {
    "text": "Gợi ý Nikon 55-200mm f/4-5.6G ED IF AF-S DX VR [Vibration Reduction] Nikkor… vì ống này lắp trực tiếp được trên Nikon D3100 DSLR Camera with 18-55mm f/3.5-5.6 Auto Focus-S Nikkor Zo… bạn đã đánh giá (ngàm nikon_f), và phù hợp chụp thể thao / chim (tiêu cự 55-200 mm, khẩu độ tối đa f/4-5.6).",
    "path": [
     {"kind": "user", "id": 409},
     {"kind": "item", "role": "body", "item_id": 9022, "asin": "B00CIRLDC2", "title": "Nikon D3100 DSLR Camera with 18-55mm …", "type": "than", "type_label": "thân máy"},
     {"kind": "item", "role": "lens", "item_id": 15485, "asin": "B01DZP4UAM", "title": "Nikon 55-200mm f/4-5.6G …", "type": "ong", "type_label": "ống kính"},
     {"kind": "usecase", "id": "the_thao_chim", "label": "thể thao / chim"}],
    "edges": ["owns", "compatible_with", "suitable_for"],
    "b_star": 9022, "rho": "compatible_with", "c_star": "the_thao_chim", "b_star_score": 26.428340911865234,
    "b_star_source": "train",
    "candidate_bodies": [9022], "verified": true, "errors": []}},
  {"rank": 5, "item_id": 1665, "asin": "B000V9CQJI", "title": "Canon EOS 40D 10.1MP Digital SLR Camera with EF 28-135mm …",
   "type": "than", "type_label": "thân máy", "score": 6.5257649421691895, "explanation": null}
 ],
 "mask": {"rule": "QĐ 4-9 (mặt nạ 15)", "n_lenses_blocked": 814, "n_blocked_in_topk_before_mask": 1,
          "blocked_in_topk_before_mask": [
           {"item_id": 13448, "asin": "B00WUI9ITO", "title": "Canon EF 24-70mm f/4.0L is USM Standard Zoom Lens - 6313B002",
            "type": "ong", "type_label": "ống kính"}]}
}
```

(Chuỗi `title` trong `path` ở trên rút gọn bằng "…" cho dễ đọc; API trả tên đầy đủ. Chỉ `text` mới cắt ở 70 ký tự.)

## 5. `GET /items/{item_id}`

| Trường | Ý nghĩa |
|---|---|
| `item_id`, `asin`, `title`, `type`, `type_label` | như trên |
| `mount` | ngàm theo nội dung 3 (`canon_ef`, `nikon_f`, `sony_e`, …); `khong_co` / `khong_ro` / `nhieu`; phụ kiện ngàm chuyển dạng `ngàm_ống>ngàm_thân` |
| `khung` | `ff` / `apsc` / `khac` / `khong_ro` hoặc `null` |
| `may_phim` | thân máy phim (QĐ 16) |
| `mount_uncertain` | ống "không chắc" ngàm (QĐ 4): không có trong M, mặt nạ không chặn, không có giải thích |
| `mount_source`, `categories` | nguồn xác định ngàm; danh mục Amazon |
| `in_matrix` | thân / ống có trong ma trận M (537 thân × 1.033 ống) |
| `focal_mm` | `{"min", "max"}` mm hoặc `null` |
| `max_aperture_f` | khẩu độ tối đa `{"at_min_focal", "at_max_focal"}` (vd f/4 ở 55 mm, f/5.6 ở 200 mm) hoặc `null` |
| `usecases`, `usecases_label` | nhãn mục đích (cạnh `suitable_for`) |
| `n_lenses_m1` | chỉ với thân: số ống M = 1 |

Ví dụ `GET /items/15485`: `mount "nikon_f"`, `khung "apsc"`, `in_matrix true`, `focal_mm {"min": 55.0, "max": 200.0}`,
`max_aperture_f {"at_min_focal": 4.0, "at_max_focal": 5.6}`, `usecases ["the_thao_chim"]`.

## 6. `GET /users/{user_id}/bodies` và `GET /compat?body_id=&lens_id=`

### 6.1. `/users/{user_id}/bodies`

Tham số `exclude` (không bắt buộc, mặc định `all_history`): chọn tập thân như `/recommend` — cả lịch sử
(`all_history`) hoặc chỉ train (`train_val`). Đây đúng là tập thân dùng cho mặt nạ và giải thích của `/recommend` cùng
chế độ. `source` cho biết thân nằm ở train / val / test; `n_history_items` là số sản phẩm trong lịch sử của chế độ đó.

Ví dụ `GET /users/47/bodies` (seed 1): người 47 có Nikon D4S trong train và Nikon D500 ở val. Ở `train_val` chỉ có 1 thân.
Ở `/recommend?user_id=47`, ống hạng 1 (item 13466) được giải thích qua **D500** (`b_star_source "val"`,
`candidate_bodies [12369, 14934]`, `verified true`).

```json
{"user_id": 47, "exclude": "all_history", "n_history_items": 10, "n_bodies": 2,
 "bodies": [
  {"item_id": 12369, "asin": "B00PHRVRXU", "title": "Nikon D4S 16.2 MP CMOS FX Digital SLR with Full 1080p HD Video (Body Only)",
   "mount": "nikon_f", "khung": "ff", "may_phim": false, "in_matrix": true, "n_lenses_m1": 219, "source": "train"},
  {"item_id": 14934, "asin": "B01A7Q0J3Y", "title": "Nikon D500 DX-Format Digital SLR (Body Only), Base",
   "mount": "nikon_f", "khung": "apsc", "may_phim": false, "in_matrix": true, "n_lenses_m1": 219, "source": "val"}],
 "n_lenses_blocked": 814}
```

### 6.2. `/compat?body_id=&lens_id=` — mức tương thích (5 mức) và luật quyết định

Mức xếp bằng bộ áp luật của nội dung 3 (`03_mount_compat.Rules`, `ai/config/mount_rules.toml` v0.5): duyệt luật theo
thứ tự, luật đầu tiên khớp quyết định; không luật nào khớp → `incompatible`. Lúc khởi động dịch vụ tự kiểm: 107.452 cặp
của `compat_pairs.csv` trùng kết quả bộ áp luật; M = 1: 72.720 cặp, "không biết": 5.846 cặp.

| `level` | Nghĩa | M |
|---|---|---|
| `compatible_with` | lắp trực tiếp, đủ khung hình | 1 |
| `crops_sensor` | lắp trực tiếp, ống cho cảm biến nhỏ hơn nên ảnh bị cắt khung | 1 |
| `requires_adapter` | cần ngàm chuyển chính hãng | 0 |
| `incompatible` | không lắp được | 0 |
| `unknown` | không biết (không dùng cho mặt nạ và CVR) | 0 |

| Trường | Ý nghĩa |
|---|---|
| `body`, `lens` | thông tin ngắn hai sản phẩm |
| `body_mount`, `lens_mount`, `body_khung`, `lens_khung`, `body_film`, `lens_uncertain` | thuộc tính dùng để áp luật |
| `level`, `level_label` | mức (bảng trên); `null` nếu thân hoặc ống không có đúng một ngàm (kèm `reason`) |
| `rule_id`, `rule_note` | luật quyết định và ghi chú của luật trong `mount_rules.toml`; `rule_id = null` khi rơi vào mức mặc định |
| `crop_unknown` | M = 1 nhưng chưa rõ máy có tự cắt khung (QĐ 11) |
| `in_matrix`, `m` | cặp có trong M không; giá trị M (0 / 1), `null` nếu không có trong M |
| `qd49_if_only_this_body` | nếu người dùng chỉ có thân này thì mặt nạ QĐ 4-9 làm gì với ống: `chan` / `khong_chan` / `khong_cham_duoc` |

Ví dụ `GET /compat?body_id=9022&lens_id=13448` (Nikon D3100 + Canon EF 24-70mm, chính ống bị chặn ở mục 4.4):
`level "incompatible"`, `rule_id null`, `rule_note "không luật nào khớp -> mức mặc định 'incompatible' (khác ngàm, không
có ngàm chuyển chính hãng trong bảng luật)"`, `in_matrix true`, `m 0`, `qd49_if_only_this_body "chan"`.

Ví dụ `GET /compat?body_id=19071&lens_id=9696` (Sony a6000 + Sony 50mm f/1.8): `level "compatible_with"`,
`rule_id "same_mount_body_apsc_lens_unknown_khung"`, `m 1`, `qd49_if_only_this_body "khong_chan"`.

## 7. Định dạng lỗi chung

Mọi lỗi trả cùng một dạng:

```json
{"error": {"code": "USER_NOT_FOUND",
           "message": "Không có người dùng 99999 trong dữ liệu (chỉ phục vụ user_id 0..67660; chưa hỗ trợ người dùng mới).",
           "details": {"user_id": 99999}}}
```

| HTTP | `code` | Khi nào |
|---|---|---|
| 404 | `USER_NOT_FOUND` | `user_id` ngoài 0..67.660 |
| 404 | `ITEM_NOT_FOUND` | `item_id` / `body_id` / `lens_id` ngoài 0..27.939 |
| 400 | `NOT_A_BODY` | `body_id` không phải thân máy (`details.type` cho biết loại thật) |
| 400 | `NOT_A_LENS` | `lens_id` không phải ống kính |
| 422 | `INVALID_PARAM` | thiếu tham số, sai kiểu, `k` ngoài 1..50, `exclude` (của `/recommend` hoặc `/users/{id}/bodies`) khác `all_history` / `train_val` (`details.errors[]`: `loc`, `msg`) |
| 404 | `NOT_FOUND` | đường dẫn không tồn tại |
| 500 | `INTERNAL_ERROR` | lỗi trong dịch vụ (Spring Boot nên báo "dịch vụ gợi ý tạm lỗi", không hiện chi tiết cho người dùng) |

## 8. Gợi ý cho Spring Boot

- Gọi `/health` lúc khởi động; dịch vụ cần khoảng 10–12 s để lên (nạp dữ liệu ~2 s, phần còn lại là khởi động Python,
  đo trong `check_service.py`).
- Đặt thời gian chờ ~1 s cho `/recommend` (p99 đo được ~21 ms, mục 9); hết giờ hoặc 5xx thì hiện danh sách dự phòng.
- Nối với bảng sản phẩm của Spring Boot bằng `asin`.

## 9. Đã kiểm (21/10/2026; bản 1.3: 26/10/2026)

Script `ai/service/check_service.py`, `ai/service/diag_mismatch.py`; kết quả trong `results/service/`.

**Bản 1.3 (26/10, commit `5c28e2d`)** — chỉ đổi cụm "bạn đã mua" → "bạn đã đánh giá" ở `all_history`:
- `train_val` qua HTTP, 3 seed (`check_http_s{1,2,3}_20261026_lan5`): phần khớp kết quả đã lưu (nhóm A, B, từng người)
  và hợp đồng trong `summary.json` **y hệt `lan4`** (so bằng script: hai object bằng nhau); 40/40 người trùng top-10,
  14 + 61 / 9 + 65 / 12 + 67 câu trùng từng chữ với câu đã lưu ("bạn đã mua"), 16/16 hợp đồng;
- `all_history` qua HTTP: trong 1.050 yêu cầu mỗi seed, 0 câu sai cụm (thiếu "bạn đã đánh giá" hoặc còn "bạn đã mua"),
  0 câu không qua kiểm sự kiện, 0 sản phẩm trong lịch sử;
- `all_history`, mọi 67.661 người seed 1 (`check_history_s1_20261026_lan2`): 0 lỗi sự kiện, 0 câu sai cụm, 0 b\* ngoài
  lịch sử, 0 ống vi phạm QĐ 4-9; mọi số đếm khác trùng `check_history_s1_20261021_lan1` (22.739 câu, ...);
- độ trễ `lan5` chậm hơn `lan4` (seed 1 phía khách p50 / p99 21,56 / 26,89 ms so với 14,77 / 20,41 ms; seed 2 max
  151,52 ms) dù code chỉ thêm một phép thay chuỗi mỗi câu; lúc đo máy chỉ còn ~2,9 GB RAM trống. **Chưa tìm nguyên
  nhân**; bảng độ trễ dưới giữ số `lan4`.

**Khớp với kết quả đã lưu qua HTTP** (`exclude=train_val`, k = 10; bản 1.2: commit `ea3a16a`,
`check_http_s{1,2,3}_20261021_lan4`; bản 1.1: `lan3` trên `ead4acd`; bản 1.0: `lan1` trên `8f47897`, `lan2` trên `37b7fd8`;
cả 4 lần cùng số): ở cả 3 seed, nhóm A (20 người ngẫu nhiên, seed 20261021) và nhóm B (20 người có câu
giải thích đã lưu) đều **40/40 người trùng top-10 đúng thứ tự**; câu giải thích trùng hết (seed 1 / 2 / 3: 14 / 9 / 12
câu ở nhóm A, chỉ 3 / 20 người nhóm A có câu; 61 / 65 / 67 câu ở nhóm B), b\*, ρ, c\* trùng; 0 câu không qua kiểm sự
kiện. Hợp đồng: 16/16 trường hợp (mã lỗi, định dạng lỗi chung, trường chính) đúng.

**Khớp trên mọi người, không qua HTTP** (`check_all_s{1,2,3}_20261021_lan1`, chạy trên bản 1.0; chế độ `train_val` ở bản
1.1, 1.2 bỏ đúng cùng tập sản phẩm (train + val) và dùng cùng thân train nên kết quả này vẫn áp dụng): top-10 trùng 67.660 / 67.660 / 67.661 trên
67.661 người; câu trùng 20.548 / 20.138 / 20.393 (tất cả). 2 người lệch (u 59388 seed 1, u 65200 seed 2) chỉ **đổi chỗ
hai hạng kề nhau**, tập top-10 vẫn trùng: hai sản phẩm chênh 4,8e-7 và 9,5e-7 điểm, tức một bước làm tròn float32; lúc
chấm test GPU nhân theo lô 1.024 người cho thứ tự ngược với nhân một hàng trên CPU (`diag_mismatch_20261021_lan1`).

**Chế độ mặc định `all_history`, thân cả lịch sử (bản 1.2), mọi 67.661 người, seed 1** (không qua HTTP,
`check_history_s1_20261021_lan1`, commit `ea3a16a`):
- phải bằng 0 và **đều bằng 0**: lỗi sự kiện của câu; b\* không phải thân trong lịch sử (kiểm độc lập với
  `verify_explanation`); ống trong top-10 vi phạm QĐ 4-9 với thân cả lịch sử (trên 76.986 ống); sản phẩm trả về nằm
  trong lịch sử;
- so với dùng thân train (cùng `all_history`): người có thân 10.406 → 12.472 (thêm 2.066); **2.062 người được thêm mặt
  nạ** (trước 0 ống bị chặn, nay > 0), **344 người bị chặn ít ống hơn** (có thêm thân khác ngàm); top-10 đổi ở 493
  người; câu giải thích 20.503 → 22.739, trong đó 2.650 câu có b\* ở val / test; **902 người thêm câu** (890 người trước
  không có câu nào), 0 người bớt câu.

Qua HTTP (`lan4`): trong 1.050 yêu cầu `all_history` mỗi seed, **0** sản phẩm trả về nằm trong train, val hay test.

**Độ trễ qua HTTP** (1.000 yêu cầu `/recommend?k=10`, `exclude` mặc định `all_history`, sau 50 khởi động, gửi lần lượt;
máy của Nam, dịch vụ chạy CPU, không dùng GPU; `lan4`, commit `ea3a16a`, bản 1.2):

| Seed | phía khách p50 / p95 / p99 / max (ms) | phía máy chủ p50 / p95 / p99 (ms) |
|---|---|---|
| **1 (demo)** | 14,77 / 18,71 / 20,41 / 22,86 | 13,53 / 17,42 / 18,72 |
| 2 | 15,25 / 19,68 / 21,57 / 50,51 | 14,01 / 18,28 / 19,85 |
| 3 | 15,44 / 19,22 / 20,51 / 21,28 | 14,18 / 17,89 / 19,08 |

(Seed 2 có một yêu cầu chậm bất thường ở cả `lan3` (78,67 ms) và `lan4` (50,51 ms); chưa tìm nguyên nhân, p99 không bị
ảnh hưởng. Bản 1.1, `lan3`: p50 phía khách 15,04–15,69 ms; bản 1.0, `lan2`: 15,93–16,25 ms.)

Bộ nhớ dịch vụ ~1.017 MiB (bản 1.2 giữ thêm mặt nạ và lịch sử của chế độ `all_history`; bản 1.1 ~933 MiB); nạp dữ liệu ~2,3 s, sẵn sàng sau ~12 s kể cả khởi động Python. Phần lớn thời gian xử lý là hai
lần `eval_05.full_rank` (trước và sau mặt nạ, mỗi lần ~6,6 ms đo trong tiến trình): sắp xếp ổn định cả catalog để giữ
đúng quy tắc hòa π. Số này **không so được** với độ trễ 0,40 ms (CPU) ở `09_explain_lightgcn.py`: phép đo đó dùng
`torch.topk` một lần, không quy tắc hòa π, không HTTP.
