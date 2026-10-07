# Nhật ký thay đổi so với bản của Hải

Bản gốc để so sánh: commit `62abf54` (Hải, 28/09/2026).
File này ghi lại mọi chỗ Nam sửa trong code hoặc dữ liệu của Hải. Mỗi mục gồm: **sửa gì**, **vì sao**, **ảnh hưởng thế nào** (số cũ → số mới).
Mục mới nhất nằm trên cùng.

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
