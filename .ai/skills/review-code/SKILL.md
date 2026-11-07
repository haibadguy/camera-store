# Skill: Review Code / Fix Bug

## Khi nào sử dụng
- Đánh giá (review) một pull request hoặc đoạn mã nguồn mới.
- Khắc phục (fix) lỗi hoặc sự cố phát sinh trong hệ thống.

## Các bước thực hiện

### 1. Đọc bối cảnh
- Đọc kỹ `docs/coding-style.md` và `docs/architecture.md`.
- Nếu là bug: đọc mô tả lỗi, xác định thông báo exception và cách tái hiện.

### 2. Tiêu chuẩn Review Code
Kiểm tra các vấn đề cốt lõi:
- [ ] Có tuân thủ `docs/coding-style.md` và kiến trúc Modular Monolith không?
- [ ] Có vi phạm anti-pattern (Controller gọi thẳng Repository, logic nghiệp vụ nằm ở Controller) không?
- [ ] Controller có bọc response trong `ApiResponse<T>` không?
- [ ] DTO có đầy đủ Jakarta Bean Validation không?
- [ ] Có nguy cơ lỗi vòng lặp import (circular dependency) không?
- [ ] Nếu là tính năng gợi ý: có xử lý constraint filtering và fallback khi cold-start không?

### 2a. Kiểm tra chống AI Slop & Chất lượng thực chất (không suy đoán tác giả)
Thực hiện đối chiếu theo 4 khía cạnh kỹ thuật:

1. **Mã nguồn & AST (Tham chiếu `dmmulroy/anti-slop`, `slopcop`):**
   - [ ] Bỏ code chết, placeholder, abstraction rỗng không có người gọi.
   - [ ] Không ép kiểu né type-check (`as any`, `as unknown as T`); dùng Union Types và Type Guards rõ ràng.
   - [ ] Không nuốt lỗi âm thầm (`catch {}` rỗng), không fallback ngầm che giấu lỗi downstream.

2. **Giao diện & Accessibility (Tham chiếu `css-slop-detector`, `molveau/skills`):**
   - [ ] Không dùng hiệu ứng phô trương thừa thãi (gradient neon, bo góc quá đà, dashboard hào nhoáng rỗng ruột) chỉ để tạo vẻ ngoài phức tạp.
   - [ ] Phần tử tương tác phải chuẩn ngữ nghĩa: dùng `<button>`/`<a>` (không gán `onClick` lên `<div>`/`<h3>` trần); hỗ trợ bàn phím (tab, enter).
   - [ ] Dialog/Modal có đầy đủ ARIA: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, nút đóng có `aria-label`.
   - [ ] Đầy đủ các trạng thái thực tế: Thường, Loading, Rỗng (Empty), Lỗi (Error). Ảnh có `alt` mô tả.

3. **Từ ngữ, Tuyên bố & Dữ liệu (Tham chiếu `stop-slop`, `FeedHive`, `ameobius-ai`):**
   - [ ] Không bịa đặt claim thương mại: tồn kho ("Còn hàng"), chính sách đổi trả, bảo hành khi không có dữ liệu thật.
   - [ ] Phân định rõ: Catalog chỉ là dữ liệu minh họa thương mại, không phải kết quả của mô hình Recommendation.
   - [ ] Đúng ngữ nghĩa dữ liệu đồ án: Dữ liệu Amazon Reviews là *"bạn đã đánh giá"*, không phải *"bạn đã mua"* hay *"lịch sử sử dụng"*.
   - [ ] Tránh buzzwords sáo rỗng ("AI đột phá", "lựa chọn tối ưu", "thuật toán siêu việt").

4. **Kiểm định thực nghiệm (Tham chiếu `peakoss/anti-slop`):**
   - [ ] Có test hoặc kiểm tra tái lập cụ thể cho hành vi thay đổi; kết quả được nêu đúng phạm vi, không tuyên bố đã kiểm tra điều chưa chạy.
   - [ ] Heuristic/detector chỉ là tín hiệu mở ra review thủ công, **không dùng điểm số detector làm cổng pass/fail**.

### 3. Xử lý lỗi (Fix Bug)
- Xác định nguyên nhân gốc rễ (Root Cause).
- Sửa mã nguồn và chạy lại test để đảm bảo không phát sinh lỗi hồi quy (regression).
- Nếu là lỗi đặc biệt hoặc phức tạp: ghi chú bài học vào `docs/lessons.md`.

### 4. Sau khi hoàn thành
- Chạy `cd backend && mvn clean compile` hoặc `cd frontend && npm run build` để kiểm tra tính toàn vẹn.
- Cập nhật checklist tương ứng nếu có.
