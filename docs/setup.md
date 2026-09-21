# Camera Store Setup Guide

Tài liệu này dành cho cả 3 thành viên trong nhóm. Dự án sử dụng kiến trúc Modular Monolith với Spring Boot 3, PostgreSQL 17, Redis 7, React 19 và Python 3.11.

## 1. Mô hình chạy thống nhất

```text
React SPA (Frontend :5173) -> REST API -> Spring Boot modular monolith (Backend :8080)
                                           |-> JPA/Flyway -> PostgreSQL (:5432)
                                           |-> Redis (Cache layer :6379)
                                           |-> ai/recommendation (Python ML pipeline)
```

- Docker Compose quản lý PostgreSQL và Redis local.
- Backend chạy trực tiếp bằng Maven trên máy local (Port: 8080).
- Frontend chạy trực tiếp bằng Vite trên máy local (Port: 5173).
- Python chạy script offline để huấn luyện mô hình và xuất artifact JSON/PKL.

## 2. Công cụ cần cài trên Windows
Cài các công cụ sau trên máy của mỗi thành viên:

- Git: https://git-scm.com/download/win
- Node.js LTS (v20+): https://nodejs.org/
- Java JDK 21: https://www.oracle.com/java/technologies/downloads/#java21
- Apache Maven (v3.9+): https://maven.apache.org/download.cgi
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Python 3.11+: https://www.python.org/downloads/

Kiểm tra trên PowerShell:
```powershell
git --version
node --version
npm --version
java -version
mvn -version
docker --version
docker compose version
python --version
```

## 3. Nhận source code bằng Git
```powershell
git clone https://github.com/haibadguy/camera-store.git
cd camera-store
```

## 4. Khởi động Database & Redis bằng Docker
Mở Docker Desktop, sau đó ở thư mục gốc `camera-store`:
```powershell
docker compose up -d postgres redis
docker compose ps
```

## 5. Khởi động Backend
```powershell
cd backend
mvn spring-boot:run
```
- API chạy tại: `http://localhost:8080`
- Swagger UI tài liệu API: `http://localhost:8080/swagger-ui.html`

## 6. Khởi động Frontend
Mở cửa sổ Terminal mới:
```powershell
cd frontend
npm install
npm run dev
```
- Giao diện web chạy tại: `http://localhost:5173`

## 7. Chạy AI Recommendation Pipeline (Offline)
Khi cần huấn luyện hoặc cập nhật mô hình gợi ý:
```powershell
cd ai/recommendation
pip install -r requirements.txt
python scripts/train_content_based.py
```
Mô hình sau khi tính toán sẽ tự động xuất artifact vào `ai/recommendation/models/` để Backend nạp.
