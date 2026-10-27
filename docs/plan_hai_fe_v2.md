# Plan Hải — FE v2 Integration

## Thông tin branch

- Branch: `hai/fe-v2-integration`
- Tạo từ: `quyen/fron-p1`
- Nền: `origin/main` tại commit `1619323` và frontend demo của Quyền tại commit `d6a4c90`
- Mục tiêu: hoàn thiện luồng demo recommendation để có thể merge vào `main`

## Phạm vi

- Giữ lại giao diện demo hiện tại của Quyền.
- Dùng dữ liệu mock thật đã xuất từ FastAPI để demo ổn định; vẫn giữ tùy chọn gọi API v1.3 qua Spring Boot.
- Đảm bảo kiến trúc đúng: `React → Spring Boot → FastAPI`.
- Xử lý loading, lỗi API, timeout và user không hợp lệ.
- Đối chiếu response với `docs/api_contract.md` v1.3.
- Không huấn luyện lại model, không đổi checkpoint, seed hoặc kết quả đã chốt.

## Tiến trình

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Tạo branch từ `quyen/fron-p1` | Đã hoàn thành | Giữ `main` mới nhất và FE của Quyền |
| Đọc và chốt API contract v1.3 | Đã hoàn thành | Dùng `docs/api_contract.md` làm nguồn sự thật |
| Rà soát cấu trúc frontend hiện tại | Đã hoàn thành | Xác định `RecommendationDemo.tsx` là điểm thay mock data |
| Tạo API client/service cho Spring Boot | Đã hoàn thành | Thêm `frontend/src/services/recommendationService.ts` |
| Kết nối Spring Boot tới FastAPI | Đã hoàn thành | Dùng `AdvisorController` của main với `/api/recommend` và các endpoint v1.3 |
| Kết nối màn hình recommendation với nguồn dữ liệu | Đã hoàn thành | Mặc định đọc mock thật; bật `VITE_RECOMMENDATION_SOURCE=api` để gọi `/api/recommend` |
| Xử lý loading/error/timeout | Đã hoàn thành | Có loading, lỗi HTTP/schema, timeout 10 giây và nút thử lại |
| Kiểm thử user `409` và `47` | Đã hoàn thành | Đã kiểm tra trên browser với mock thật; user 409 hiển thị 814 ống kính bị lọc |
| Kiểm thử user không hợp lệ | Đã chuẩn bị | API client hiển thị lỗi HTTP/schema rõ ràng |
| Chạy `npm run build` | Đã hoàn thành | `tsc -b && vite build` đạt, 59 modules |
| Smoke test `React → Spring Boot → FastAPI` | Bị chặn môi trường | Docker engine chưa chạy; FastAPI thiếu embedding runtime |
| Cập nhật tài liệu và changelog | Đã hoàn thành một phần | Đã cập nhật plan và changelog; chờ số liệu smoke test |
| Rà soát cảm giác thị giác và câu chữ | Đã hoàn thành | Giảm nhãn kỹ thuật trên mặt tiền, dùng bố cục editorial tiết chế; đã kiểm tra nhanh trên trình duyệt |
| Hủy request cũ khi đổi hồ sơ/rời màn hình | Đã hoàn thành | Dùng `AbortController`, tránh race condition giữa các lần chọn |
| Kiểm tra CORS local | Đã hoàn thành | Cho phép cả hostname `localhost` và địa chỉ `127.0.0.1` của Vite |
| Đồng bộ mock thật từ main | Đã hoàn thành | Thêm recommendation, lịch sử thân máy và chi tiết item từ `frontend/src/mock/` |
| Rà soát chữ kỹ thuật trên UI | Đã hoàn thành | Không còn `item_id`, `QĐ 4-9`, `contract`, `API 1.2` trên mặt tiền |

## Tiêu chí hoàn thành

- Frontend gọi Spring Boot, không gọi trực tiếp FastAPI.
- Recommendation và explanation hiển thị đúng với response API.
- Có trạng thái loading và thông báo lỗi phù hợp.
- Build frontend thành công.
- Smoke test end-to-end đạt với user hợp lệ.
- Kiểm tra được trường hợp user không hợp lệ hoặc API lỗi.
- Không commit thư mục `report_figures/` nếu không thuộc phạm vi công việc.
- Cập nhật `docs/CHANGELOG.md` và `docs/STATUS.md` bằng kết quả đã kiểm chứng.
- Smoke test end-to-end phải được chạy sau khi khôi phục đúng embedding runtime và khởi động được Docker/PostgreSQL.

## Phối hợp

- Quyền: cung cấp/duy trì giao diện frontend hiện tại.
- Hải: thực hiện phần FE v2 integration trên branch này.
- Nam: hoàn thiện Spring Boot client/controller và endpoint trung gian nếu cần.
