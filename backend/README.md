# Backend Spring Boot (nội dung 10)

Lớp nghiệp vụ của demo: **React → Spring Boot (thư mục này) → FastAPI (dịch vụ mô hình, `ai/service/`)**. React chỉ gọi
Spring Boot; Spring Boot gọi FastAPI qua HTTP theo hợp đồng `docs/api_contract.md` (bản 1.3).

Hiện trạng (26/10/2026): 5 điểm cuối `/api/...` cho React, cùng tên tham số và cùng dạng dữ liệu với hợp đồng.
**Chưa có database, chưa có đăng nhập** (chờ cô chốt nội dung chương 3): Spring chạy được khi không có PostgreSQL.
Code cũ có sẵn dùng database (`modules/catalog`, `/api/recommendations`, `SeedData`, Flyway) được giữ nguyên, chỉ bật
với profile `db`.

## 1. Cách chạy

Cần: JDK 21 trở lên (máy của Nam: JDK 24), Maven 3.9. Không cần Docker / PostgreSQL.

1. Terminal 1 — dịch vụ mô hình FastAPI, seed 1 (từ thư mục `camera-store`, sẵn sàng sau ~12 s):
   ```powershell
   ai\.venv\Scripts\python.exe ai/service/run_service.py --emb-dir results/service/emb_s1_20261021 --port 8001
   ```
2. Terminal 2 — Spring Boot (`http://localhost:8080`):
   ```powershell
   cd backend
   mvn spring-boot:run
   ```
   Lúc khởi động Spring gọi `/health` của FastAPI một lần và ghi log "Dịch vụ mô hình sẵn sàng ..." (hoặc cảnh báo nếu
   FastAPI chưa chạy; Spring vẫn chạy, `/api/*` trả 503 tới khi FastAPI lên).
3. Thử:
   ```powershell
   curl "http://localhost:8080/api/recommend?user_id=409&k=10"
   ```

Đóng gói thành jar: `mvn package` (chạy cả test) → `target/camera-store-backend-0.1.0.jar`, chạy
`java -jar target/camera-store-backend-0.1.0.jar`.

### Cấu hình (`src/main/resources/application.yml`)

| Khóa | Mặc định | Ý nghĩa |
|---|---|---|
| `model-service.base-url` | `http://127.0.0.1:8001` (biến môi trường `MODEL_SERVICE_URL`) | địa chỉ FastAPI |
| `model-service.connect-timeout` | `1s` | chờ mở kết nối |
| `model-service.read-timeout` | `1s` | chờ phản hồi (hợp đồng mục 8 gợi ý ~1 s; p99 đo được ~21 ms) |
| `cors.allowed-origins` | `http://localhost:5173,http://127.0.0.1:5173` (`CORS_ALLOWED_ORIGINS`) | cổng dev của Vite được gọi `/api/**` |
| `server.port` | `8080` (`PORT`) | cổng Spring |

Đổi khi chạy: `mvn spring-boot:run -Dspring-boot.run.arguments=--model-service.base-url=http://127.0.0.1:8031`
hoặc `java -jar ... --model-service.base-url=...`.

Profile `db` (chưa dùng cho demo): `mvn spring-boot:run -Dspring-boot.run.profiles=db` bật lại DataSource / JPA /
Flyway và code cũ; cần PostgreSQL (`docker compose up -d postgres`).

## 2. Điểm cuối

| Spring (React gọi) | FastAPI (Spring gọi) | Hợp đồng |
|---|---|---|
| `GET /api/recommend?user_id=&k=&exclude=` | `/recommend` | mục 4 |
| `GET /api/items/{id}` | `/items/{id}` | mục 5 |
| `GET /api/users/{id}/bodies?exclude=` | `/users/{id}/bodies` | mục 6.1 |
| `GET /api/compat?body_id=&lens_id=` | `/compat` | mục 6.2 |
| `GET /api/health` | `/health` | mục 3 |

`k`, `exclude` không gửi thì Spring cũng không gửi, FastAPI dùng mặc định (`k = 10`, `exclude = all_history`).
Spring **không kiểm lại** giá trị (k trong 1..50, user_id có trong dữ liệu...): FastAPI là nơi kiểm duy nhất.

### Lỗi (luôn dạng `{"error": {"code", "message", "details"}}`, hợp đồng mục 7)

| Trường hợp | HTTP | `code` |
|---|---|---|
| FastAPI trả lỗi 4xx (`USER_NOT_FOUND`, `ITEM_NOT_FOUND`, `NOT_A_BODY`, `NOT_A_LENS`, `INVALID_PARAM`) | giữ nguyên | giữ nguyên, thân lỗi chuyển tiếp nguyên dạng |
| Spring tự bắt: thiếu tham số, sai kiểu (`user_id=abc`) | 422 | `INVALID_PARAM` (cùng dạng `details.errors[].loc/msg` như FastAPI) |
| Đường dẫn không có / sai phương thức | 404 / 405 | `NOT_FOUND` / `HTTP_ERROR` |
| **FastAPI không chạy** (không kết nối được) | 503 | `MODEL_SERVICE_UNAVAILABLE` (message nêu địa chỉ đang gọi) |
| FastAPI quá thời gian chờ | 504 | `MODEL_SERVICE_TIMEOUT` |
| FastAPI lỗi 5xx | 502 | `MODEL_SERVICE_ERROR` ("Dịch vụ gợi ý tạm lỗi", không lộ chi tiết; `details.upstream_code` để dò) |
| FastAPI trả dữ liệu không đọc được | 502 | `MODEL_SERVICE_BAD_RESPONSE` |
| Lỗi khác trong Spring | 500 | `INTERNAL_ERROR` |

Hiển thị câu giải thích: hợp đồng mục 4.3 nói nếu `verified = false` thì không nên hiện câu. Spring chuyển tiếp
nguyên `explanation` (trong mọi lần kiểm `verified` luôn `true`); phía React nên kiểm `verified` trước khi hiện.

## 3. Cấu trúc code

```
src/main/java/com/camerastore/
  CameraStoreApplication.java
  config/ModelServiceProperties.java   khối model-service của application.yml
  config/CorsConfig.java               CORS cho Vite
  common/ApiErrorResponse.java         định dạng lỗi chung
  common/ApiException.java             lỗi mang sẵn mã HTTP + thân lỗi
  common/GlobalExceptionHandler.java   đổi mọi lỗi sang định dạng chung
  modules/advisor/
    AdvisorController.java             điểm cuối /api/...
    AdvisorService.java                nghiệp vụ (hiện chỉ chọn điểm cuối + tham số)
    ModelServiceClient.java            gọi FastAPI qua HTTP, timeout, đổi lỗi
    ModelServiceStartupCheck.java      gọi /health lúc khởi động
    dto/                               record Java khớp từng trường của hợp đồng
```

## 4. Một yêu cầu của người 409 đi qua những lớp nào

Ví dụ: React muốn hiện 10 gợi ý cho người dùng 409 (có một thân Nikon D3100). Trình duyệt gửi

```
GET http://localhost:8080/api/recommend?user_id=409&k=10
```

**Bước 1 — Controller (`AdvisorController.recommend`): nhận yêu cầu HTTP.**
Spring thấy đường dẫn `/api/recommend` khớp hàm `recommend`, đọc tham số trong URL thành biến Java:
`user_id=409` → `long userId = 409`, `k=10` → `Integer k = 10`, `exclude` không có → `null`. Nếu URL sai
(vd `user_id=abc`) thì dừng ở đây: `GlobalExceptionHandler` trả 422 `INVALID_PARAM`, không gọi FastAPI.
Controller không tính gì, chỉ chuyển cho Service. Trước đó bộ lọc CORS đã kiểm: yêu cầu đến từ trang
`http://localhost:5173` (Vite) nên được phép; trang khác bị chặn 403.

**Bước 2 — Service (`AdvisorService.recommend`): nghiệp vụ.**
Quyết định gọi điểm cuối nào của FastAPI và với tham số gì: `/recommend` với `{user_id: 409, k: 10, exclude: null}`.
Hiện Service chỉ làm vậy vì chưa có database. Đây là chỗ sau này thêm nghiệp vụ thật: đổi tài khoản đăng nhập demo
thành một `user_id` có sẵn (FastAPI chỉ biết 67.661 người trong dữ liệu), nối giá / ảnh / tồn kho theo `asin`, trả danh
sách dự phòng khi FastAPI lỗi.

**Bước 3 — Client (`ModelServiceClient.get`): gọi FastAPI qua HTTP.**
Ghép địa chỉ từ `application.yml` thành `http://127.0.0.1:8001/recommend?user_id=409&k=10` (tham số `null` bị bỏ, nên
FastAPI dùng mặc định `exclude=all_history`), gửi GET, chờ tối đa 1 s. Ba khả năng:
- FastAPI trả **200**: đọc JSON thành DTO (bước 4);
- FastAPI trả **lỗi 4xx** (vd `user_id=99999` → 404 `USER_NOT_FOUND`): ném `ApiException` mang đúng mã 404 và thân
  lỗi đó; `GlobalExceptionHandler` trả nguyên cho React;
- **không gọi được**: FastAPI tắt → 503 `MODEL_SERVICE_UNAVAILABLE`; quá 1 s → 504 `MODEL_SERVICE_TIMEOUT`;
  FastAPI lỗi 5xx → 502 `MODEL_SERVICE_ERROR`.

**Bước 4 — DTO (`dto/RecommendResponse`): dữ liệu có kiểu.**
JSON của FastAPI được đọc vào các record Java: `RecommendResponse` (user_id, k, has_bodies, n_bodies, items, mask),
mỗi phần tử `RecommendedItem` (rank, item_id, title, type, score, explanation), `Explanation` (text, path, b_star,
rho, ...), `Mask`. Với người 409: `items[0]` là bao da Canon (item 1154, phụ kiện, `explanation = null`); `items[1]`
là ống Nikon 55-200mm (item 15485) có giải thích qua thân D3100 (`b_star = 9022`, câu "… bạn đã đánh giá (ngàm
nikon_f) …"); `mask.n_lenses_blocked = 814`, `mask.blocked_in_topk_before_mask` = ống Canon EF 24-70mm (item 13448)
bị mặt nạ gỡ khỏi top-10. Tên trường Java viết camelCase (`hasBodies`), ra JSON là snake_case (`has_bodies`) nhờ
`spring.jackson.property-naming-strategy: SNAKE_CASE`, nên React nhận đúng tên trong hợp đồng.

**Bước 5 — trả về.** Controller trả DTO, Spring ghi lại thành JSON gửi trình duyệt. Nội dung **trùng** với gọi thẳng
FastAPI (đã kiểm, mục 5).

Tóm lại: **Controller** nhận và đọc URL → **Service** quyết định gọi gì → **Client** gọi FastAPI, lo timeout và đổi lỗi
→ **DTO** là "khuôn" dữ liệu theo hợp đồng → JSON về React. Lỗi ở bất kỳ bước nào đều đổi thành cùng một dạng
`{"error": {...}}` nhờ `GlobalExceptionHandler`.

Vì sao có DTO thay vì chuyển nguyên chuỗi JSON: (1) code Java đọc được từng trường có kiểu (sau này Service cần
`items[].asin` để nối giá, `explanation.verified` để quyết định hiện câu); (2) DTO là bản hợp đồng viết bằng Java: nếu
FastAPI đổi tên / bỏ trường, test so nội dung sẽ báo lệch. Cái giá: phải giữ DTO khớp hợp đồng. Hai chỗ đặc biệt:
`path` có ba loại nút với trường khác nhau (và `id` lúc là số, lúc là chuỗi) nên bỏ trường null khi ghi; `n_lenses_m1`
(chỉ thân máy có) và `reason` của `/compat` cũng bỏ khi null, đúng như FastAPI.

## 5. Kiểm

- **Test tự động** (`mvn test`, 33 test, `src/test/java/.../advisor/`): FastAPI giả lập (`FakeModelService`, máy chủ
  HTTP thật trên cổng ngẫu nhiên) trả phản hồi thật đã lưu (`src/test/resources/fastapi/`, nguồn ghi trong README ở
  đó). Kiểm: 14 phản hồi thành công qua Spring trùng nội dung phản hồi FastAPI (recommend 409 / 47, bodies, 3 items, 4
  compat, health) và Spring gửi đúng tham số; 3 lỗi 4xx chuyển tiếp nguyên dạng; 5xx / hết giờ / dữ liệu hỏng → 502 /
  504 / 502; lỗi tham số phía Spring → 422 không gọi FastAPI; 404 / 405; CORS; FastAPI không chạy → 503 ở cả 5 điểm
  cuối. Log lần chạy: `results/backend/mvn_test_20261026_lan1.log`.
- **Kiểm thật** (`ai/service/check_backend.py`): bật FastAPI seed 1 + Spring (jar), gọi qua Spring, so với
  `frontend/src/mock/*.json` và với gọi thẳng FastAPI. Chạy:
  ```powershell
  ai\.venv\Scripts\python.exe ai/service/check_backend.py --label <nhãn>
  ```
  Kết quả `results/backend/check_backend_<nhãn>/` (log, log FastAPI, log Spring, `summary.json`). Lần
  `s1_20261026_lan2` (commit `e94b0c7`): ĐẠT — 28/28 phản hồi trùng mock và trùng FastAPI, health + 4 compat + 3 lỗi
  trùng FastAPI, CORS đúng, tắt FastAPI → 503.
