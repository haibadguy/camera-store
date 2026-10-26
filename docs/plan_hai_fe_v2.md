# Plan Hải — FE v2 Integration

## Thông tin branch

- Branch: `hai/fe-v2-integration`
- Tạo từ: `quyen/fron-p1`
- Nền: `main` tại commit `680e5ef` và frontend demo của Quyền tại commit `d6a4c90`
- Mục tiêu: hoàn thiện luồng demo recommendation để có thể merge vào `main`

## Phạm vi

- Giữ lại giao diện demo hiện tại của Quyền.
- Thay dữ liệu tĩnh bằng API thật qua Spring Boot.
- Đảm bảo kiến trúc đúng: `React → Spring Boot → FastAPI`.
- Xử lý loading, lỗi API, timeout và user không hợp lệ.
- Đối chiếu response với `docs/api_contract.md` v1.2.
- Không huấn luyện lại model, không đổi checkpoint, seed hoặc kết quả đã chốt.

## Tiến trình

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Tạo branch từ `quyen/fron-p1` | Đã hoàn thành | Giữ `main` mới nhất và FE của Quyền |
| Đọc và chốt API contract v1.2 | Đã hoàn thành | Dùng `docs/api_contract.md` làm nguồn sự thật |
| Rà soát cấu trúc frontend hiện tại | Đã hoàn thành | Xác định `RecommendationDemo.tsx` là điểm thay mock data |
| Tạo API client/service cho Spring Boot | Đã hoàn thành | Thêm `frontend/src/services/recommendationService.ts` |
| Kết nối Spring Boot tới FastAPI | Đã hoàn thành | Proxy `/api/recommendations` tới FastAPI `/recommend` |
| Kết nối màn hình recommendation với backend | Đã hoàn thành | Gọi `GET /api/recommendations?user_id=&k=10&exclude=all_history` |
| Xử lý loading/error/timeout | Đã hoàn thành | Có loading, lỗi HTTP/schema, timeout 10 giây và nút thử lại |
| Kiểm thử user `409` và `47` | Bị chặn môi trường | Thiếu `results/service/emb_s1_20261021/embeddings.npz`, chưa thể khởi động FastAPI |
| Kiểm thử user không hợp lệ | Đã chuẩn bị | API client hiển thị lỗi HTTP/schema rõ ràng |
| Chạy `npm run build` | Đã hoàn thành | `tsc -b && vite build` đạt, 31 modules |
| Smoke test `React → Spring Boot → FastAPI` | Bị chặn môi trường | Docker engine chưa chạy; FastAPI thiếu embedding runtime |
| Cập nhật tài liệu và changelog | Đã hoàn thành một phần | Đã cập nhật plan và changelog; chờ số liệu smoke test |
| Rà soát cảm giác thị giác và câu chữ | Đã hoàn thành | Giảm nhãn kỹ thuật trên mặt tiền, dùng bố cục editorial tiết chế; đã kiểm tra nhanh trên trình duyệt |
| Hủy request cũ khi đổi hồ sơ/rời màn hình | Đã hoàn thành | Dùng `AbortController`, tránh race condition giữa các lần chọn |
| Kiểm tra CORS local | Đã hoàn thành | Cho phép cả hostname `localhost` và địa chỉ `127.0.0.1` của Vite |

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
