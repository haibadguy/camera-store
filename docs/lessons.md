# Lessons Learned (Bài Học Kinh Nghiệm)

File này dùng để ghi lại các sự cố kỹ thuật, kinh nghiệm xử lý lỗi khó và các bài học trong quá trình phát triển dự án.

## Cấu trúc chuẩn của một bài học kinh nghiệm:
```markdown
## [Vấn đề] Mô tả ngắn gọn sự cố
- **Nguyên nhân (Cause)**: Lý do kỹ thuật gây ra lỗi
- **Cách khắc phục (Fix)**: Cách thức xử lý và sửa đổi mã nguồn
- **Cách phòng ngừa (Prevention)**: Nguyên tắc áp dụng để không lặp lại lỗi
```

---

## 1. [Encoding] Lỗi hiển thị font chữ (Mojibake UTF-8) trên tài liệu Markdown
- **Nguyên nhân (Cause)**: Các file markdown bị lưu sai encoding (UTF-8 bị lưu đè bằng Latin-1/Windows-1252), dẫn đến các ký tự tiếng Việt có dấu bị vỡ thành ký tự rác.
- **Cách khắc phục (Fix)**: Chuyển đổi toàn bộ tài liệu sang chuẩn UTF-8 đồng nhất và kiểm tra định kỳ.
- **Cách phòng ngừa (Prevention)**: Cấu hình VS Code / IDE luôn mở và lưu file với định dạng `UTF-8 without BOM`.

## 2. [Cổng kết nối] Lệch cổng Backend giữa tài liệu và cấu hình
- **Nguyên nhân (Cause)**: Một số tài liệu cũ còn sót lại cổng 3000 từ giai đoạn trước, trong khi Spring Boot chạy mặc định ở cổng 8080.
- **Cách khắc phục (Fix)**: Thống nhất một cổng duy nhất `8080` trên toàn bộ tài liệu, `application.yml` và `docker-compose.yml`.
- **Cách phòng ngừa (Prevention)**: Luôn kiểm tra file `FOUNDATION_BASELINE.md` làm bản móng kỹ thuật chuẩn.
