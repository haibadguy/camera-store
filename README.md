# Camera Store 📷

Hệ thống thương mại điện tử bán máy ảnh và thiết bị nhiếp ảnh tích hợp hệ thống gợi ý sản phẩm (Recommendation System).

---

## 📁 Cấu trúc Thư mục

- `backend/`: Spring Boot API, JPA entities, và Flyway migrations
- `frontend/`: React + Vite UI (TypeScript, TailwindCSS)
- `ai/`: Python ML pipeline cho Recommendation System (Training, Inference, Models)
- `docs/`: Tài liệu kiến trúc, kế hoạch, yêu cầu hệ thống (SRS) và hướng dẫn

---

## 🛠️ Công nghệ Sử dụng

- **Backend:** Java 21 / Spring Boot 3.x, Spring Data JPA, Flyway, JWT
- **Frontend:** React, TypeScript, Vite, TailwindCSS, TanStack Query
- **Database & Cache:** PostgreSQL 17, Redis 7 (chạy qua Docker)
- **AI/ML:** Python 3.11+ (TF-IDF, Cosine Similarity)

---

## 📋 Hướng dẫn Setup & Khởi chạy Dự án (Dành cho thành viên nhóm)

### 📌 Bước 1: Cài đặt công cụ cần thiết (Chỉ làm 1 lần đầu)
Mỗi thành viên cần cài đặt 5 công cụ sau trên máy Windows:
1. **Git:** [Tải tại đây](https://git-scm.com/download/win)
2. **Node.js (LTS):** [Tải tại đây](https://nodejs.org/)
3. **Java JDK (JDK 17 hoặc 21):** [Tải tại đây](https://www.oracle.com/java/technologies/downloads/#java21)
4. **Maven:** [Tải tại đây](https://maven.apache.org/download.cgi) *(hoặc tích hợp trong IDE)*
5. **Docker Desktop:** [Tải tại đây](https://www.docker.com/products/docker-desktop/)

---

### 📌 Bước 2: Clone Source Code từ GitHub
```powershell
git clone https://github.com/haibadguy/camera-store.git
cd camera-store
```

---

### 📌 Bước 3: Cài đặt thư viện Frontend (Chỉ làm 1 lần đầu)
Tại thư mục `camera-store`:
```powershell
cd frontend
npm install
cd ..
```

---

### 📌 Bước 4: Khởi động Database (Bật mỗi khi bắt đầu làm việc)
1. Mở ứng dụng **Docker Desktop** trên máy tính (đợi trạng thái xanh *Engine Running*).
2. Mở Terminal tại thư mục `camera-store` và chạy:
   ```powershell
   docker compose up -d postgres redis
   ```

---

### 📌 Bước 5: Khởi động Ứng dụng

- **Terminal 1 - Chạy Backend (Spring Boot):**
  ```powershell
  cd backend
  mvn spring-boot:run
  ```
  *(Backend API chạy tại: `http://localhost:8080`)*

- **Terminal 2 - Chạy Frontend (React + Vite):**
  ```powershell
  cd frontend
  npm run dev
  ```
  *(Giao diện Web chạy tại: `http://localhost:5173`)*

---

## 📖 Tài liệu Tham khảo Khác
Chi tiết kiến trúc và quy trình phát triển xem tại thư mục `docs/`:
- [docs/setup.md](docs/setup.md): Hướng dẫn cài đặt chi tiết
- [docs/plan.md](docs/plan.md): Kế hoạch phát triển các Phase
- [docs/architecture.md](docs/architecture.md): Tổng quan kiến trúc hệ thống



