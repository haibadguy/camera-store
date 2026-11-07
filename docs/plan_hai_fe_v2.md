# Kế Hoạch Hoàn Thiện Frontend — Hải (`hai/fe-v2-integration`)

> **Cập nhật ngày:** 02/11/2026  
> **Người thực hiện:** Nguyễn Hồng Hải (Data/AI & Frontend Integration)  
> **Nhánh làm việc duy nhất:** `hai/fe-v2-integration` (đã đồng bộ `origin/main` tại commit `e680ffa`, đã xóa nhánh thừa `hai/fe`).

---

## 1. Định Vị Dự Án & Nguyên Tắc Bất Biến

1. **Định vị: Demo phục vụ nghiên cứu & báo cáo đồ án (Academic / Research Demo)**
   - Giao diện KHÔNG PHẢI sản phẩm thương mại sản xuất (không làm giỏ hàng phức tạp, thanh toán online, trừ kho, hay CRUD admin).
   - Giao diện là **nền tảng trực quan để hội đồng nghiệm thu thuật toán**:
     - *Ràng buộc tương thích phần cứng:* Ma trận ngàm $M$, quy tắc ngàm chính hãng, Mặt nạ QĐ 4-9 chặn ống không lắp được.
     - *Mô hình gợi ý lai & giải thích minh bạch:* LightGCN + đường dẫn tri thức $u \to b \to l$ qua thân máy đã đánh giá.
     - *Độ trễ & Kiến trúc hệ thống:* Chứng minh luồng thực nghiệm React $\to$ Spring Boot $\to$ FastAPI đạt độ trễ $\approx 18\text{ ms}$.
2. **Duy nhất một branch:** Mọi commit chỉ thực hiện trên `hai/fe-v2-integration`.
3. **Bảo toàn kịch bản E2E Playwright (`tools/demo_e2e/demo_e2e.mjs`):**
   - Giữ nguyên vẹn các selector, text, button role bắt buộc:
     - Nút `"Tư vấn thiết bị"` mở luồng tư vấn.
     - Heading `"Bạn đang tìm món đồ tiếp theo?"`.
     - Thẻ chọn nhanh `.demo-user-card` với các heading `"Người dùng 409"`, `"Người dùng 47"`.
     - Form `"Nhập mã người dùng"` với input `#demo-user-id`.
     - Thông báo lỗi đúng hợp đồng 1.3: `"Không tìm thấy người dùng này."`, `"Dịch vụ gợi ý đang tạm dừng, thử lại sau."`, nhãn `"Dữ liệu mẫu"`.
     - Tuyệt đối không dùng các từ cấm trong `BANNED`: `"đang dùng"`, `"lịch sử sử dụng"`, `"ưu tiên"`, `"Gợi ý phù hợp"`, `"Vì sao gợi ý"`.
4. **Kiến trúc luồng dữ liệu:**
   - Chuẩn: `React (Vite) → Spring Boot (/api/...) → FastAPI (/recommend, /items, /users, /compat, /health)`.
   - Tuyệt đối không gọi trực tiếp FastAPI từ React.

---

## 2. Giải Quyết Vấn Đề "Mẫu Số Quá Ít / Thiếu Dữ Liệu Demo"

Phía sau hệ thống có dữ liệu rất lớn (**67.661 người dùng, 27.940 sản phẩm, 72.720 cặp tương thích $M=1$**), nhưng hiện tại giao diện FE đang tạo cảm giác "ít data" vì:
- Chế độ mock chỉ xuất sẵn 2 người dùng (409 và 47).
- Catalog trang chủ chỉ có 6 sản phẩm hardcode tĩnh.
- Người xem dễ hiểu lầm là nhóm chỉ code tay vài trường hợp mẫu để diễn kịch bản.

### Chiến lược khắc phục:
1. **Minh bạch hóa quy mô Dataset thật:** Đặt một thanh số liệu tổng quan (Dataset Scale Badge) ngay đầu trang: *67.661 Người dùng • 27.940 Thiết bị • 72.720 Cặp ngàm tương thích ($M=1$) • 595.515 Tương tác (Amazon Electronics 2023)*.
2. **Mở rộng từ 2 lên 5 Hồ sơ Người dùng đại diện (Curated Profiles):**
   - **User 409 (Nikon D3100):** 1 thân máy APS-C phổ thông $\to$ bị chặn 814 ống kính không cùng ngàm.
   - **User 47 (Nikon D4S, D500):** Người dùng có cả thân Full-frame lẫn APS-C $\to$ giải thích đa dạng qua thân D500.
   - **User 178:** Người chơi **đa hệ máy** (sở hữu thân của nhiều hãng khác nhau).
   - **User 0:** Người mới hoàn toàn (**chưa từng đánh giá thân máy nào**) $\to$ không bị chặn ống nào.
   - **User 1476:** Người có thân máy ngoài ma trận $M$ $\to$ demo ca xử lý ngoại lệ theo QĐ 4-9.
3. **Mở rộng kho sản phẩm Catalog từ 6 lên 24–30 sản phẩm thực tế:** Đủ các thân máy chính (Sony, Canon, Nikon, Fujifilm), các dải tiêu cự ống kính (Wide, Standard, Tele, Macro) và phụ kiện lấy từ danh mục Amazon thật.

---

## 3. Lộ Trình Triển Khai Chi Tiết (Phase 2)

```
[Phase 1: ĐÃ XONG TRÊN MAIN]
Nối React → Spring Boot → FastAPI (Contract 1.3, E2E Check Demo 12/12 ĐẠT)
       ↓
[Phase 2: NHIỆM VỤ CỦA HẢI TRÊN hai/fe-v2-integration]
├── Task 1: Tra cứu tương thích Thân máy – Ống kính (/api/compat) [✔ ĐÃ HOÀN THÀNH]
├── Task 2: Mở rộng dữ liệu hiển thị & Minh bạch quy mô Dataset [✔ ĐÃ HOÀN THÀNH]
│   ├── 2.1: Thêm thanh thông số quy mô Dataset (Data Scale Banner)
│   ├── 2.2: Mở rộng 5 hồ sơ người dùng tiêu biểu (409, 47, 178, 0, 1476)
│   └── 2.3: Nâng kho Catalog từ 6 lên 28 sản phẩm minh họa có nguồn cục bộ
├── Task 3: Chỉ báo trạng thái kết nối hệ thống (Health & Mode Indicator) [✔ ĐÃ HOÀN THÀNH]
│   └── Gọi /api/health → hiển thị badge 🟢 Live API FastAPI Seed 1 vs 🟡 Dữ liệu mẫu
├── Task 4: Cá nhân hóa Catalog theo Profile đang chọn (Personalized Storefront) [✔ ĐÃ HOÀN THÀNH]
│   └── Chọn Profile trên Header → gắn badge tương thích trực tiếp lên sản phẩm Catalog
├── Task 5: Tái cấu trúc Clean Code & Khóa chất lượng E2E [✔ ĐÃ HOÀN THÀNH]
│   ├── Tách App.tsx thành các component con độc lập
│   └── Kiểm tra Playwright tools/demo_e2e/demo_e2e.mjs pass 100%
├── Task 6: Dọn AI slop và khóa phạm vi demo [✔ ĐÃ HOÀN THÀNH]
│   ├── Khử bỏ claim thương mại bịa đặt ("Còn hàng", "Bảo hành 24 tháng")
│   ├── Thay ép kiểu as any bằng Union Types và Type Guards
│   └── Ghi rõ catalog chỉ là minh họa, luồng chính là Recommendation
└── Task 7: Chuẩn hóa Research Demo, Khắc phục Harness Cleanup & Nghiệm thu End-to-End [ĐANG THỰC HIỆN]
    ├── Redesign UI theo hướng trung tính (shadcn/ui, Vercel Commerce), hỗ trợ bàn phím & ARIA
    ├── Khắc phục triệt để race condition psutil.NoSuchProcess trong check_service.py / check_demo.py
    └── Chạy bộ kiểm thử nghiêm ngặt check_demo.py (1.000–2.000 requests, p50 ~18ms) đạt 100%
```

---

### Chi Tiết Từng Task

#### Task 1: Tích hợp công cụ Tra Cứu Tương Thích Thân Máy – Ống Kính (`/api/compat`) [✔ ĐÃ HOÀN THÀNH]
- **Đã làm:**
  - Bổ sung types (`CompatResponse`, `CompatItemBrief`, `CompatLevel`) và hàm `fetchCompatibility` trong `recommendationService.ts`.
  - Tạo `frontend/src/mock/compat_pairs.json` gồm 5 cặp mẫu chuẩn.
  - Xây dựng component `CompatibilityChecker.tsx` hiển thị trực quan mức tương thích, thông số ngàm/sensor, trạng thái ma trận $M$ và luật quyết định.
  - Tích hợp view `"compat"` và nút "Kiểm tra tương thích" trên Navigation bar của `App.tsx`.
- **Kết quả:** `npm run build` đạt 61 modules, không lỗi.

#### Task 2: Mở rộng dữ liệu hiển thị & Minh bạch quy mô Dataset [✔ ĐÃ HOÀN THÀNH]
- **Mục tiêu:** Xóa bỏ cảm giác "ít data", khẳng định quy mô thật 67k users trước hội đồng.
- **Nội dung:**
  1. *Data Scale Banner:* Gắn dải thông số quy mô đề tài ở đầu Catalog và đầu trang Tư vấn.
  2. *5 Curated Profiles:* Bổ sung các thẻ chọn nhanh cho User 178, User 0, User 1476 bên cạnh User 409, 47 trong `RecommendationDemo.tsx` (có mock data tương ứng cho chế độ offline).
  3. *Mở rộng Catalog:* Thay mảng 6 sản phẩm hardcode bằng 28 sản phẩm đại diện (thân máy, ống kính, phụ kiện). Đây là catalog thương mại minh họa, không tuyên bố là danh sách item recommendation.
- **Kiểm chứng:** Giao diện dày dặn, lọc mượt mà theo thương hiệu/ngàm, chọn được 5 ca người dùng khác nhau.

#### Task 3: Chỉ báo trạng thái kết nối hệ thống (Health Check Indicator) [✔ ĐÃ HOÀN THÀNH]
- **Mục tiêu:** Nhận biết ngay hệ thống đang chạy Live API hay Mock data khi demo.
- **Nội dung:**
  - Gọi `/api/health` của Spring Boot.
  - Gắn badge trạng thái nhỏ gọn ở góc topbar:
    - 🟢 `AI Engine: Live (FastAPI Seed 1 · Latency ~18ms)`
    - 🟡 `Chế độ: Dữ liệu mẫu (Offline Mode)`
- **Kiểm chứng:** Đổi `VITE_RECOMMENDATION_SOURCE=api` và `mock`, kiểm tra badge đổi màu chính xác.

#### Task 4: Cá nhân hóa Catalog theo Profile đang chọn (Personalized Storefront) [✔ ĐÃ HOÀN THÀNH]
- **Mục tiêu:** Gắn kết trải nghiệm duyệt sản phẩm với thuật toán gợi ý và ma trận tương thích.
- **Nội dung:**
  - Thanh chọn hồ sơ trong catalog: `Không đối chiếu` | `User 409 (Nikon D3100)` | `User 47 (Nikon D4S, D500)`.
  - Khi một User được chọn:
    - Các ống kính trong Catalog lắp được trên thân của họ sẽ có badge xanh: *"Tương thích với máy của bạn"*.
    - Các ống kính bị chặn theo ma trận $M$ sẽ có nhãn cảnh báo đỏ: *"Không tương thích với thân máy của bạn"*.
- **Kiểm chứng:** Đổi qua lại giữa các user, danh sách sản phẩm trong Catalog phản ánh đúng trạng thái tương thích.

#### Task 5: Tái cấu trúc Clean Code & Khóa chất lượng E2E [✔ ĐÃ HOÀN THÀNH] [✔ E2E ĐẠT]
- **Mục tiêu:** Mã nguồn sạch sẽ, dễ bảo trì, vượt qua 100% kiểm thử tự động.
- **Nội dung:**
  - Tách phần catalog thành `CatalogFilterSidebar.tsx`, `CatalogProductGrid.tsx`, `CatalogProductCard.tsx`, `CatalogDetailModal.tsx` và `CatalogProfileSelector.tsx`; `App.tsx` giữ orchestration và trạng thái trang. Dữ liệu catalog nằm riêng tại `frontend/src/catalog/catalogData.ts`.
  - Kiểm tra `npm run build` không warning/error.
  - Đối chiếu toàn bộ selector và text với `tools/demo_e2e/demo_e2e.mjs` để đảm bảo test tự động không bị gãy.
  - Cập nhật kết quả vào `docs/CHANGELOG.md` và `docs/STATUS.md`.

#### Task 6: Dọn AI slop và khóa phạm vi demo [✔ ĐÃ HOÀN THÀNH]
- Đổi các nhãn marketing, tồn kho, bảo hành và đổi trả thành thông tin minh họa; phân biệt rõ catalog filter với recommendation model.
- Thêm citation/giới hạn cho compatibility và smoke test catalog vào `tools/demo_e2e/demo_e2e.mjs`.
- Thay cast `as any` ở bộ sắp xếp bằng union type và type guard.
- Kiểm chứng: `npm run build` đạt 67 modules; E2E catalog đạt 28 card, profile 409, compatibility badge và wizard.


#### Task 7: Chuẩn hóa Research Demo, Khắc phục Harness Cleanup & Nghiệm thu End-to-End [ĐANG THỰC HIỆN]
- **Mục tiêu:**
  - Hoàn thiện giao diện demo nghiên cứu: loại bỏ hoàn toàn các cliches "AI slop" bề mặt (gradient sặc sỡ, banner phô trương số liệu ở trang mua sắm, card không có ngữ nghĩa).
  - Tối ưu hóa Accessibility: chuẩn hóa nút bấm bàn phím, modal dialog ARIA (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`), ảnh có `alt`.
  - Khắc phục lỗi race condition `psutil.NoSuchProcess` trong test harness `ai/service/check_service.py` và `check_demo.py` khi dọn dẹp các tiến trình con.
  - Chạy lại toàn bộ kịch bản E2E Playwright và đo độ trễ HTTP qua Spring Boot (1.000–2.000 requests), xuất file bằng chứng `summary.json` sạch sẽ.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - [ ] `cd frontend && npm run build`: 67 modules, 0 lỗi TypeScript, 0 cảnh báo.
  - [ ] `git diff --check`: không có lỗi khoảng trắng thừa.
  - [ ] `git grep "as any"` / `"as unknown"` trong frontend: 0 kết quả.
  - [ ] `tools/demo_e2e/demo_e2e.mjs` pass 100% tất cả các màn hình (catalog, wizard, profile 409, 47, 178, 1476, 0, lỗi input, FastAPI down).
  - [ ] Không còn lỗi crash cleanup của `psutil.NoSuchProcess`.

---

## 4. Bảng Tiêu Chuẩn Đối Chiếu Chống AI Slop (Tham chiếu quốc tế & Quy chuẩn Đồ án)

| Phân hệ / Tầng | Công cụ tham chiếu | Tiêu chí chống Slop | Triển khai trong Đồ án Camera Store |
| :--- | :--- | :--- | :--- |
| **Code & AST** | `dmmulroy/anti-slop`, `cm2435/slopcop` | Cấm ép kiểu mù (`as any`, `as unknown as T`), cấm `catch {}` rỗng, cấm abstraction rỗng. | 100% Clean Types trong `recommendationService.ts` và `catalogData.ts`. Controller Spring Boot bọc `ApiResponse<T>`. |
| **UI & Design** | `hahahahahahahahah6/css-slop-detector`, `molveau/skills` | Tránh gradient sặc sỡ, bo góc quá lố, hero dashboard rỗng ruột; đảm bảo phím tab/enter và ARIA modal. | UI chuyển sang phong cách neutral slate/navy tinh gọn; Modal có đầy đủ ARIA role/labelled-by; thẻ sản phẩm click bằng button chuẩn. |
| **Copywriting & Claims** | `hardikpandya/stop-slop`, `FeedHive/ai-slop-detector` | Không dùng từ ngữ sáo rỗng ("AI đột phá", "lựa chọn tối ưu"); không bịa tồn kho/bảo hành; đúng thuật ngữ dữ liệu. | Catalog dán nhãn "Dữ liệu thương mại minh họa · không bán hàng". Dữ liệu Amazon là "bạn đã đánh giá", không gọi là "bạn đã mua". |
| **Thực nghiệm & CI** | `peakoss/anti-slop` | Không dùng detector làm cổng pass/fail; đo bằng test E2E thực tế và latency thực nghiệm. | Chứng minh bằng 37/37 Spring unit test, Playwright E2E 12/12 testcases, latency p50 ~18ms trên 1.000–2.000 request thật. |
