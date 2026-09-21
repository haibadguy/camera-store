# 📚 TỔNG HỢP TOÀN BỘ TÀI LIỆU DỰ ÁN CAMERA STORE (CONSOLIDATED PROJECT DOCS)

> **Mục đích:** File này gộp đầy đủ toàn bộ tài liệu hiện có trong dự án thành 1 file duy nhất với chuẩn tiếng Việt UTF-8 sạch sẽ 100%, không còn bất kỳ lỗi font chữ (mojibake) nào.

---

## 📑 MỤC LỤC TÀI LIỆU ĐƯỢC GỘP TRONG FILE NÀY

- [AGENTS.md](#file-agents-md)
- [README.md](#file-readme-md)
- [docs/FOUNDATION_BASELINE.md](#file-docs-foundation_baseline-md)
- [docs/PROJECT_STATUS_AND_ROADMAP.md](#file-docs-project_status_and_roadmap-md)
- [docs/plan.md](#file-docs-plan-md)
- [docs/checklist.md](#file-docs-checklist-md)
- [docs/constitution.md](#file-docs-constitution-md)
- [docs/decisions.md](#file-docs-decisions-md)
- [docs/architecture.md](#file-docs-architecture-md)
- [docs/coding-style.md](#file-docs-coding-style-md)
- [docs/workflow.md](#file-docs-workflow-md)
- [docs/setup.md](#file-docs-setup-md)
- [docs/overview.md](#file-docs-overview-md)
- [docs/done.md](#file-docs-done-md)
- [docs/lessons.md](#file-docs-lessons-md)
- [backend/README.md](#file-backend-readme-md)
- [frontend/README.md](#file-frontend-readme-md)
- [ai/README.md](#file-ai-readme-md)
- [.ai/README.md](#file--ai-readme-md)
- [.ai/skills/implement-feature/SKILL.md](#file--ai-skills-implement-feature-skill-md)
- [.ai/skills/review-code/SKILL.md](#file--ai-skills-review-code-skill-md)

---


================================================================================
<a id="file-agents-md"></a>
## 📄 NỘI DUNG FILE: `AGENTS.md`
================================================================================

# AGENTS.md

## Role
Bạn là AI assistant cho Camera Store - một dự án đồ án thương mại điện tử chuyên về máy ảnh, tích hợp hệ thống tư vấn & gợi ý cá nhân hóa (Recommendation System). Trọng tâm đồ án là Recommendation System. Sử dụng kiến trúc Modular Monolith với Spring Boot 3, JPA/Hibernate + Flyway, PostgreSQL 17 và React 19.

## Commands
- Backend dev: `cd backend && mvn spring-boot:run` (Port: 8080)
- Frontend dev: `cd frontend && npm run dev` (Port: 5173)
- Migration: Flyway tự động chạy khi Spring Boot khởi động; kiểm tra: `cd backend && mvn flyway:info`
- Backend build: `cd backend && mvn clean package`
- Frontend build: `cd frontend && npm run build`

## Source of Truth (Thứ tự ưu tiên khi có mâu thuẫn thông tin)
1. `docs/FOUNDATION_BASELINE.md` – Bản móng kỹ thuật & ranh giới 3 thành viên
2. `docs/PROJECT_STATUS_AND_ROADMAP.md` – Lộ trình trọng tâm AI & phân nhóm A/B
3. `docs/constitution.md` – Nguyên tắc kiến trúc bất biến
4. `docs/decisions.md` – Quyết định kiến trúc đã được chấp nhận (ADRs)
5. `docs/architecture.md` – Kiến trúc tổng thể và ranh giới module
6. `docs/coding-style.md` – Quy tắc code chuẩn
7. `docs/plan.md` – Kế hoạch phase
8. `docs/checklist.md` – Danh sách kiểm tra tiến độ

## Scope & Constraints
- Đồ án tập trung vào hệ thống tư vấn gợi ý thiết bị nhiếp ảnh (Content-based, Constraint filtering, Explainable reasons).
- Giao diện E-commerce chỉ là nền tảng tối thiểu để hiển thị và thu thập hành vi (`user_behaviors`).
- Ưu tiên giải pháp đơn giản, dễ bảo trì, dễ demo.
- Không giới thiệu các mẫu kiến trúc phức tạp (Microservices, CQRS, Event Sourcing, DDD đầy đủ, Hexagonal).
- Tránh tạo abstraction không cần thiết.

## AI Skills
- Implement feature: tham khảo `.ai/skills/implement-feature/SKILL.md`
- Review code / fix bug: tham khảo `.ai/skills/review-code/SKILL.md`

## Workflow
Thực hiện theo chiến lược Vertical Slice: `DB Migration -> Spring Boot API -> React UI -> Smoke Test`.

## API Reference
Swagger/OpenAPI tại `http://localhost:8080/swagger-ui.html` là nguồn sự thật duy nhất cho API contracts. Mọi response đều bọc trong `ApiResponse<T>`.




================================================================================
<a id="file-readme-md"></a>
## 📄 NỘI DUNG FILE: `README.md`
================================================================================

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







================================================================================
<a id="file-docs-foundation_baseline-md"></a>
## 📄 NỘI DUNG FILE: `docs/FOUNDATION_BASELINE.md`
================================================================================

# 🏗️ BẢN MÓNG HOÀN CHỈNH DỰ ÁN (FOUNDATION BASELINE)

> **Dự án:** Camera Store — E-Commerce & AI Recommendation System  
> **Trọng tâm đề tài:** **Hệ thống tư vấn & gợi ý thiết bị nhiếp ảnh cá nhân hóa (AI Recommendation System)**.  
> **Mục đích tài liệu:** Thiết lập "bản móng kỹ thuật" bất biến để **3 thành viên (Backend, Frontend, AI)** có thể phát triển song song độc lập ngay lập tức mà không gây xung đột Git, không lệch pha Database và không mất thời gian chờ đợi nhau.

---

## 1. 🎯 TẠI SAO PHẢI CÓ BẢN MÓNG TRƯỚC KHI CHIA VIỆC?

Khi một nhóm 3 người bắt tay vào code mà chưa khóa bản móng:
1. **Tránh xung đột Git (Git Conflict Hell):** Nếu không phân tách ranh giới module rõ ràng, 3 người sẽ cùng chỉnh sửa `App.tsx`, `application.yml`, hoặc các file migration, dẫn đến xung đột khi merge.
2. **Tránh lệch pha Database (Database Desync):** Nếu không dùng Flyway migration chung từ đầu, máy thành viên này chạy được nhưng máy thành viên khác sập do thiếu bảng, sai tên cột hoặc thiếu khóa ngoại.
3. **Tránh bất đồng API (API Mismatch):** Frontend không cần chờ Backend. Chỉ cần chốt DTO & Contract mẫu (`ApiResponse<T>`), Frontend có thể mock data đúng chuẩn interface để dựng UI trước.
4. **Không làm chệch trọng tâm đồ án:** Định hình rõ các bảng dữ liệu `camera_specifications` và `user_behaviors` ngay từ đầu để phục vụ thuật toán Recommendation, tránh việc tập trung quá nhiều vào các tính năng thương mại điện tử phụ.

---

## 2. 🛠️ TECH STACK THỐNG NHẤT

| Phân hệ | Công nghệ chính | Ghi chú kiến trúc |
| :--- | :--- | :--- |
| **Backend** | Java 21, Spring Boot 3.4.5, Spring Data JPA | **Modular Monolith** sạch sẽ, không chia Microservices |
| **Database Migrations**| Flyway Database Migration | Quản lý schema bằng code, không sửa DB thủ công |
| **Security & Doc** | Spring Security 6, JWT, SpringDoc OpenAPI (Swagger) | Swagger: `http://localhost:8080/swagger-ui.html` |
| **Frontend** | React 19, TypeScript 5.8, Vite 6, Vanilla CSS | Không dùng UI framework nặng (MUI/AntD), tự chủ CSS |
| **Client State & API**| TanStack Query v5, Axios | Quản lý cache server-state và gọi REST API |
| **AI Recommendation** | Python 3.11+, Scikit-Learn, Pandas, NumPy | Huấn luyện offline: TF-IDF, Cosine Similarity, Constraint Rules |
| **Database & Cache** | PostgreSQL 17, Redis 7 | Chạy qua Docker Compose |
| **Hạ tầng Local** | Docker Compose | Chạy dịch vụ DB/Cache nền tảng |

---

## 3. 📁 CẤU TRÚC THƯ MỤC CHUẨN HÓA (FOLDER STRUCTURE)

Mỗi thành viên làm việc tập trung trong thư mục của mình:

```
camera-store/
├── docker-compose.yml              # Quản lý PostgreSQL & Redis local
├── docs/                           # Tài liệu kiến trúc & bản móng
│   ├── FOUNDATION_BASELINE.md      # [File này] Bản móng kỹ thuật chung
│   ├── PROJECT_STATUS_AND_ROADMAP.md # Lộ trình tổng quan
│   └── plan.md                     # Phân chia Phase
│
├── backend/                        # [PHỤ TRÁCH: THÀNH VIÊN 1 - BACKEND LEAD]
│   ├── pom.xml
│   └── src/main/
│       ├── java/com/camerastore/
│       │   ├── CameraStoreApplication.java
│       │   ├── config/             # SecurityConfig, CorsConfig, OpenApiConfig, RedisConfig
│       │   ├── common/             # ApiResponse<T>, PageResponse<T>, GlobalExceptionHandler, ErrorCode
│       │   └── modules/            # Các domain nghiệp vụ độc lập
│       │       ├── catalog/        # Product, Brand, Category, CameraSpec Entity, Repo, Service, Controller
│       │       ├── auth/           # User, Role, AuthService, AuthController, JwtProvider
│       │       ├── userbehavior/   # Tracking VIEW, ADD_TO_CART
│       │       └── recommendations/# RecommendationService (đọc model artifact từ AI)
│       └── resources/
│           ├── application.yml
│           └── db/migration/       # V1__init_schema.sql, V2__seed_cameras.sql
│
├── frontend/                       # [PHỤ TRÁCH: THÀNH VIÊN 2 - FRONTEND LEAD]
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                 # QueryClientProvider & Routing
│       ├── styles.css              # Design System CSS thuần (Solid E-Commerce)
│       ├── types/                  # TypeScript Types khớp 100% Backend DTO
│       │   ├── api.ts              # ApiResponse<T>, ErrorResponse
│       │   ├── product.ts          # Product, CameraSpec, Brand, Category
│       │   └── recommendation.ts   # RecommendationRequest, RecommendationResult
│       ├── services/               # Axios client & API endpoints
│       │   ├── apiClient.ts        # Axios instance, Interceptors
│       │   └── productService.ts
│       ├── components/             # UI Components tái sử dụng (Header, Footer, Button, Card, Modal)
│       └── pages/                  # Storefront & Admin pages
│           ├── HomePage.tsx
│           ├── CatalogPage.tsx
│           ├── ProductDetailPage.tsx
│           └── RecommendationAdvisorModal.tsx
│
└── ai/                             # [PHỤ TRÁCH: THÀNH VIÊN 3 - AI & DATA LEAD]
    └── recommendation/
        ├── requirements.txt        # scikit-learn, pandas, numpy
        ├── data/
        │   ├── cameras_seed.csv    # Dataset camera specs khớp 100% DB PostgreSQL
        │   └── user_interactions.csv
        ├── models/                 # Chứa model artifacts xuất ra cho Backend đọc
        │   └── similarity_matrix.json # hoặc .pkl
        ├── scripts/
        │   ├── prepare_data.py     # Làm sạch dữ liệu thông số máy ảnh
        │   ├── train_content_based.py # TF-IDF + Cosine Similarity
        │   └── evaluate_offline.py # Tính toán Precision@K, Recall@K, Coverage
        └── README.md
```

---

## 4. 🗄️ BẢN MÓNG DATABASE (FLYWAY MIGRATIONS & SEED DATA)

### 4.1. Migration Khởi Tạo Schema (`V1__init_schema.sql`)
File migration đầu tiên sẽ tạo đầy đủ 8 bảng cốt lõi phục vụ E-Commerce và Hệ thống Gợi ý:

```sql
-- 1. DANH MỤC & THƯƠNG HIỆU
CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(120) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE brands (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(120) NOT NULL UNIQUE,
    country VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. SẢN PHẨM MÁY ẢNH & THIẾT BỊ
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    brand_id BIGINT NOT NULL REFERENCES brands(id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(250) NOT NULL UNIQUE,
    price NUMERIC(14, 2) NOT NULL CHECK (price >= 0),
    original_price NUMERIC(14, 2),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    description TEXT,
    image_url VARCHAR(500) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. THÔNG SỐ KỸ THUẬT MÁY ẢNH (CAMERA SPECIFICATIONS - CỐT LÕI CHO AI)
CREATE TABLE camera_specifications (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    sensor_type VARCHAR(80) NOT NULL,       -- Full-frame, APS-C, Medium Format, 1-inch
    resolution_mp NUMERIC(5, 1) NOT NULL,   -- 24.2, 33.0, 40.2, 61.0 (Megapixels)
    lens_mount VARCHAR(80) NOT NULL,        -- Sony E, Canon RF, Fujifilm X, Nikon Z
    iso_range VARCHAR(50),                  -- 100-51200
    video_resolution VARCHAR(80),           -- 4K 60p, 6.2K 30p, 8K 30p
    continuous_shooting_fps INTEGER,        -- 10, 20, 30, 40 (fps)
    weight_grams INTEGER,                   -- 377, 557, 658 (grams)
    has_image_stabilization BOOLEAN DEFAULT TRUE,
    target_need VARCHAR(100)                -- portrait, travel, vlog, sports
);

-- 4. TÀI KHOẢN NGƯỜI DÙNG & PHÂN QUYỀN
CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE        -- ROLE_CUSTOMER, ROLE_ADMIN
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 5. THEO DÕI HÀNH VI NGƯỜI DÙNG (USER BEHAVIORS - PHỤC VỤ AI HYBRID RECOMMENDATION)
CREATE TABLE user_behaviors (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100),                -- Dành cho khách chưa đăng nhập (Guest)
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,       -- VIEW, ADD_TO_CART, WISHLIST, PURCHASE
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_camera_specs_product ON camera_specifications(product_id);
CREATE INDEX idx_behaviors_user ON user_behaviors(user_id);
```

### 4.2. Dữ Liệu Mẫu Nền Tảng (`V2__seed_data.sql`)
Chứa sẵn 15+ mẫu máy ảnh thật từ Sony, Canon, Fujifilm, Nikon có đầy đủ thông số kỹ thuật thật để phục vụ huấn luyện AI và hiển thị catalog ngay.

---

## 5. ☕ BẢN MÓNG BACKEND (SPRING BOOT)

### 5.1. Chuẩn Wrapper Phản Hồi Toàn Cục (`ApiResponse<T>`)
Tất cả API trả về cấu trúc thống nhất:

```java
package com.camerastore.common;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {
    private int code;           // 200, 400, 401, 404, 500
    private String message;     // "Success", "Product not found", etc.
    private T result;           // DTO Payload
}
```

### 5.2. Bộ Bắt Lỗi Toàn Cục (`GlobalExceptionHandler`)
```java
package com.camerastore.common;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGeneralException(Exception ex) {
        ApiResponse<Void> response = ApiResponse.<Void>builder()
                .code(500)
                .message("Internal Server Error: " + ex.getMessage())
                .build();
        return ResponseEntity.internalServerError().body(response);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException ex) {
        String defaultMessage = ex.getBindingResult().getAllErrors().get(0).getDefaultMessage();
        ApiResponse<Void> response = ApiResponse.<Void>builder()
                .code(400)
                .message("Validation failed: " + defaultMessage)
                .build();
        return ResponseEntity.badRequest().body(response);
    }
}
```

### 5.3. Cấu hình Bảo Mật Baseline (`SecurityConfig`)
- Cho phép CORS từ `http://localhost:5173`.
- Mở public: `/api/v1/products/**`, `/api/v1/recommendations/**`, `/swagger-ui/**`, `/v3/api-docs/**`.

---

## 6. ⚛️ BẢN MÓNG FRONTEND (REACT + TYPESCRIPT)

### 6.1. TypeScript Interface Khớp 100% Backend (`src/types/index.ts`)
```typescript
export interface ApiResponse<T> {
  code: number;
  message: string;
  result: T;
}

export interface CameraSpec {
  sensorType: string;
  resolutionMp: number;
  lensMount: string;
  isoRange?: string;
  videoResolution: string;
  continuousShootingFps?: number;
  weightGrams: number;
  hasImageStabilization: boolean;
  targetNeed: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  brandName: string;
  categoryName: string;
  price: number;
  originalPrice?: number;
  stock: number;
  imageUrl: string;
  description: string;
  specs?: CameraSpec;
  aiMatchScore?: number;
  aiReasons?: string[];
}

export interface RecommendationRequest {
  budgetMax?: number;
  preferredBrand?: string;
  lensMount?: string;
  targetNeed?: string;
}
```

### 6.2. Axios Instance Chuẩn (`src/services/apiClient.ts`)
```typescript
import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error("API Call Error:", error?.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

---

## 7. 🐍 BẢN MÓNG AI RECOMMENDATION (PYTHON PIPELINE)

### 7.1. Cấu Trúc Dataset Đồng Nhất (`ai/recommendation/data/cameras_seed.csv`)
File CSV định nghĩa các trường dữ liệu khớp chuẩn cột Database PostgreSQL:

```csv
product_id,name,brand,price,sensor_type,resolution_mp,lens_mount,video_resolution,weight_grams,target_need
1,Sony Alpha A7 IV,Sony,54990000,Full-frame,33.0,Sony E,4K 60p,658,portrait
2,Canon EOS R6 Mark II,Canon,58990000,Full-frame,24.2,Canon RF,4K 60p,670,sports
3,Fujifilm X-T5,Fujifilm,42990000,APS-C,40.2,Fujifilm X,6.2K 30p,557,travel
4,Sony ZV-E10 II,Sony,22990000,APS-C,26.0,Sony E,4K 60p,377,vlog
5,Nikon Z6 III,Nikon,64990000,Full-frame,24.5,Nikon Z,6K 60p RAW,760,sports
```

### 7.2. Pipeline Huấn Luyện Cốt Lõi (Content-Based + Constraint + Explainable)
```python
# ai/recommendation/scripts/train_content_based.py
import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def train_and_export():
    df = pd.read_csv('../data/cameras_seed.csv')
    
    # Kết hợp các thuộc tính thành chuỗi đặc trưng (Feature string)
    df['features'] = df['sensor_type'] + " " + df['lens_mount'] + " " + df['target_need'] + " " + df['video_resolution']
    
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df['features'])
    
    # Tính ma trận tương đồng Cosine
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Xuất ma trận tương đồng thành artifact JSON để Backend đọc trực tiếp
    similarity_dict = {}
    for idx, row in df.iterrows():
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        # Lấy top 5 sản phẩm tương tự
        top_similar = [int(df.iloc[i[0]]['product_id']) for i in sim_scores[1:6]]
        similarity_dict[int(row['product_id'])] = top_similar

    with open('../models/similarity_matrix.json', 'w') as f:
        json.dump(similarity_dict, f, indent=2)
    print("Exported similarity_matrix.json successfully!")

if __name__ == '__main__':
    train_and_export()
```

### 7.3. Thuật Toán Lọc Ràng Buộc & Giải Thích Lý Do (Constraint + Explainable Rules)
```python
# ai/recommendation/scripts/constraint_and_explain.py

def filter_and_explain(df, budget_max=None, preferred_brand=None, lens_mount=None, target_need=None):
    results = []
    
    for _, camera in df.iterrows():
        # 1. RÀNG BUỘC (Constraint Filtering)
        if budget_max and camera['price'] > budget_max:
            continue
        if preferred_brand and preferred_brand != 'All' and camera['brand'] != preferred_brand:
            continue
        if lens_mount and lens_mount != 'All' and lens_mount.lower() not in camera['lens_mount'].lower():
            continue
        if camera['stock'] <= 0:
            continue
            
        # 2. SINH LÝ DO GIẢI THÍCH (Explainable Reasons Generation)
        reasons = []
        if target_need and target_need == camera['target_need']:
            need_labels = {
                'portrait': 'Tối ưu cho chụp chân dung nhờ cảm biến Full-frame và xóa phông mịn',
                'travel': 'Trọng lượng nhẹ dưới 600g thuận tiện cho du lịch & phượt',
                'vlog': 'Hỗ trợ quay video 4K sắc nét và micro định hướng chuyên dụng cho Vlog',
                'sports': 'Tốc độ chụp liên tiếp cao bắt nét chuyển động nhanh'
            }
            reasons.append(need_labels.get(target_need, 'Phù hợp với mục đích sử dụng đã chọn'))
            
        if budget_max and camera['price'] <= budget_max:
            reasons.append(f"Nằm trong khoảng ngân sách dự kiến (Giá: {camera['price']:,} VNĐ)")
            
        if lens_mount and lens_mount != 'All':
            reasons.append(f"Tương thích hoàn toàn với hệ ngàm {camera['lens_mount']}")
            
        results.append({
            'product_id': int(camera['product_id']),
            'name': camera['name'],
            'price': float(camera['price']),
            'ai_reasons': reasons
        })
        
    return results
```

---

## 8. 🤝 NGUYÊN TẮC LÀM VIỆC NHÓM (COLLABORATION RULES)

1. **Quy tắc Git:**
   - **Tuyệt đối không ai commit trực tiếp lên branch `main`**.
   - Mỗi thành viên tạo branch riêng: `feature/be-catalog-api`, `feature/fe-advisor-ui`, `feature/ai-tfidf`.
   - Trước khi merge vào `main`, tạo Pull Request và yêu cầu ít nhất 1 thành viên review.
2. **Quy tắc Database:**
   - **Tuyệt đối không sửa Database thủ công trong pgAdmin/DBeaver**.
   - Mọi thay đổi bảng/cột phải viết file migration tiếp theo (ví dụ: `V3__...sql`).
3. **Quy tắc API:**
   - Mọi API phải trả về bọc trong `ApiResponse<T>`.
   - API mới phải tự cập nhật chú thích OpenAPI để hiển thị trên Swagger.
4. **Quy tắc AI:**
   - Artifact mô hình xuất ra dạng `similarity_matrix.json` hoặc `.pkl` cố định trong `ai/recommendation/models/` để Backend nạp offline.

---

## 9. ⚡ KẾ HOẠCH HÀNH ĐỘNG NGAY (IMMEDIATE ACTION PLAN)

Sau khi đọc file này, nhóm thực hiện 5 bước khởi động theo đúng thứ tự:

1. **Bước 1 (Backend Lead):** Tạo file `V1__init_schema.sql` và `V2__seed_data.sql` trong `backend/src/main/resources/db/migration/`. Chạy ứng dụng để Flyway tự sinh bảng trên PostgreSQL.
2. **Bước 2 (Backend Lead):** Viết class `ApiResponse<T>`, `GlobalExceptionHandler` và dựng REST API đầu tiên: `GET /api/v1/products` hiển thị danh sách từ PostgreSQL lên Swagger.
3. **Bước 3 (Frontend Lead):** Tạo `src/types/index.ts` và `src/services/apiClient.ts` theo đúng định dạng mục 6. Kết nối `apiClient` gọi vào API Backend.
4. **Bước 4 (AI Lead):** Cài đặt môi trường Python, chuẩn bị `cameras_seed.csv` và chạy script sinh `similarity_matrix.json`.
5. **Bước 5 (Cả nhóm):** Họp nhanh 15 phút kiểm tra kết nối chéo giữa DB -> Backend API -> Frontend UI -> AI Artifact, sau đó chính thức tách 3 nhánh Git để bắt đầu tăng tốc!




================================================================================
<a id="file-docs-project_status_and_roadmap-md"></a>
## 📄 NỘI DUNG FILE: `docs/PROJECT_STATUS_AND_ROADMAP.md`
================================================================================

# 🎯 BÁO CÁO TRẠNG THÁI & LỘ TRÌNH THỰC THI DỰ ÁN (PROJECT STATUS & MASTER ROADMAP)

> **Tên đề tài đồ án:** *"Xây dựng hệ thống tư vấn cá nhân hóa lựa chọn thiết bị nhiếp ảnh (Camera Store & AI Recommendation System)"*  
> **TRỌNG TÂM ĐỒ ÁN:** **AI Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)**. Giao diện E-commerce chỉ đóng vai trò **nền tảng tối thiểu** để thu thập dữ liệu và demo luồng tư vấn.  
> **Mục tiêu tài liệu:** Cung cấp bức tranh toàn cảnh về hiện trạng dự án, kiến trúc, quy tắc phát triển và lộ trình tập trung đúng trọng tâm để bất kỳ bên thứ 3 (AI assistant/code reviewer) đọc vào đều bám sát yêu cầu của giảng viên, tránh làm tràn lan các tính năng web thương mại điện tử gây mất thời gian.

---

## 1. 📍 TỔNG QUAN HIỆN TRẠNG DỰ ÁN (CURRENT STATE)

### 1.1. Công nghệ & Hạ tầng (Tech Stack)
- **Backend:** Java 21, Spring Boot 3.4.5 (Modular Monolith), Spring Data JPA, Flyway (Database Migration), Spring Security + JWT, Validation, OpenAPI/Swagger.
- **Frontend:** React 19, TypeScript 5.8, Vite 6, Vanilla CSS (Design System tùy chỉnh, tối giản).
- **Database & Cache:** PostgreSQL 17 (Cơ sở dữ liệu chính), Redis 7 (Cache kết quả gợi ý AI).
- **Recommendation Engine (AI Core):** Python 3.11+, Scikit-Learn, Pandas, NumPy (Huấn luyện Content-based, Constraint Filtering, Hybrid & Explainable Recommendation).
- **DevOps & Environment:** Docker Compose (Chạy PostgreSQL và Redis local).

### 1.2. Những gì ĐÃ HOÀN THÀNH (Done Baseline - Phase 0)
- [x] **Tài liệu dự án đầy đủ (`docs/`):** `AGENTS.md`, `constitution.md`, `architecture.md`, `coding-style.md`, `setup.md`, `plan.md`, `checklist.md`.
- [x] **Khung Backend (Spring Boot Skeleton):** Cấu trúc module (`config/`, `common/`, `modules/`), Flyway migration khởi tạo (`V1__create_products.sql`), `application.yml`.
- [x] **Khung Frontend (React + Vite Skeleton):** `App.tsx`, `styles.css`, TypeScript & Vite config.
- [x] **Hạ tầng Docker Local:** `docker-compose.yml` khởi chạy thành công PostgreSQL 17 & Redis 7.

---

## 2. 🛡️ CÁC NGUYÊN TẮC VÀNG CHỐNG LỆCH TRỌNG TÂM (CONSTRAINTS & RULES)

1. **TRỌNG TÂM LÀ AI RECOMMENDATION SYSTEM:** E-commerce web chỉ là vỏ nền tảng để hiển thị và thu thập hành vi. Mọi quyết định kỹ thuật phải ưu tiên cho chất lượng gợi ý (Constraint filtering + Explainable reasons) hơn là phát triển quá nhiều tính năng thương mại điện tử phức tạp.
2. **Chiến lược Vertical Slice & Nhóm ưu tiên:** Hoàn thành nhanh Nhóm Nền Tảng Tối Thiểu để dành tối đa thời gian cho Nhóm Trọng Tâm AI.
3. **Không Over-Engineering:** Không chia Microservices, không dùng CQRS/Event Sourcing. Giữ vững Modular Monolith trên Spring Boot 3 + React + Python ML offline.
4. **Nguồn sự thật duy nhất:** 
   - Đề xuất đề tài gửi giảng viên hướng dẫn.
   - `docs/PROJECT_STATUS_AND_ROADMAP.md` (File này).
   - Swagger OpenAPI tại Backend (`http://localhost:8080/swagger-ui.html`).

---

## 3. 🚀 LỘ TRÌNH PHÁT TRIỂN TINH GỌN (MASTER ROADMAP)

Lộ trình được chia thành **2 Nhóm chính** và **1 Nhóm mở rộng** để đảm bảo tiến độ đồ án (10-12 tuần):

```
┌────────────────────────────────────────────────────────────────────────┐
│ NHÓM A: NỀN TẢNG TỐI THIỂU (Phải có để thu thập dữ liệu & demo AI)     │
│ Phase 0 (Done) ──> Phase 1 (Shell) ──> Phase 2 (Catalog & Specs)       │
│                ──> Phase 3 (Auth cơ bản) ──> Phase 4 (Tracking)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ NHÓM B: TRỌNG TÂM ĐỒ ÁN (Tập trung dồn sức 60-70% thời lượng)           │
│ Phase 5 (Recommendation Core: Content-Based + Constraint + Explain)   │
│ Phase 6 (Hybrid & Behavior Integration)                                │
│ Phase 7 (Offline Evaluation: Precision@K... & Dashboard Metrics CTR)   │
│ Phase 8 (Polish, Demo & Báo cáo đồ án)                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Nếu còn thừa thời gian)
┌───────────────────────────────────▼────────────────────────────────────┐
│ PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE)                                 │
│ Order / Checkout đầy đủ, Admin CRUD nâng cao, Coupon, Bundles           │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (TỐC ĐỘ CAO)

#### 🔹 Phase 1: Shell, Global Exception Handler & Design System (ĐANG THỰC HIỆN)
- **Backend:** `GlobalExceptionHandler`, wrapper `ApiResponse<T>`, Spring Security baseline (Cors, public endpoints), Swagger OpenAPI docs.
- **Frontend:** React Router (`/`, `/catalog`, `/product/:id`, `/recommendations`), Shell Layout (Header, Navigation, Footer), Bộ Shared Components cơ bản (Button, Card, Input, Modal, Badge, Spinner).
- **Exit Gate Phase 1:** Build Backend/Frontend thành công, router mượt mà.

#### 🔹 Phase 2: Catalog & Camera Specifications (Rút gọn)
- **Backend:** Schema Flyway (`categories`, `brands`, `products`, `camera_specifications`). API Query sản phẩm (Lọc theo brand, category, khoảng giá) & API Chi tiết máy ảnh kèm Camera Specs.
- **Frontend:** Trang Catalog Grid (Bộ lọc, Tìm kiếm, Sắp xếp, Phân trang) & Trang Chi tiết máy ảnh (Hiển thị đầy đủ thông số kỹ thuật cảm biến, ngàm lens, ISO...).
- **Exit Gate Phase 2:** Hiển thị danh sách và chi tiết máy ảnh kèm đầy đủ bộ Camera Specs phục vụ AI.

#### 🔹 Phase 3: Auth & Account Cơ Bản
- **Backend:** Schema `users`, `roles`. API Đăng ký, Đăng nhập (JWT), Spring Security Guard.
- **Frontend:** Modal / Trang Đăng nhập, Đăng ký. Auth Context lưu JWT.
- **Exit Gate Phase 3:** Đăng nhập thành công, lưu thông tin User ID để phục vụ gợi ý cá nhân hóa.

#### 🔹 Phase 4: Behavior Tracking (Thu thập dữ liệu hành vi)
- **Backend:** Schema `user_behaviors`. API ghi nhận sự kiện: `VIEW` (xem chi tiết) và `ADD_TO_CART` (thêm vào giỏ).
- **Frontend:** Tự động phát sự kiện tracking khi người dùng xem sản phẩm hoặc tương tác.
- **Exit Gate Phase 4:** Hành vi của user được lưu chính xác vào Database Postgres.

---

### 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (RECOMMENDATION ENGINE - DỒN SỨC CHÍNH)

#### 🔹 Phase 5: Recommendation Engine CORE (Constraint + Explainable + Content-Based)
*Đây là module quan trọng nhất của đồ án, bao gồm 3 thành phần cốt lõi:*

- **5a. Content-Based Recommendation Engine:**
  - Python Script: Biến đổi thuộc tính máy ảnh (Camera Specs) qua TF-IDF Vectorizer + Scaler.
  - Tính toán ma trận độ tương đồng Cosine (Cosine Similarity Matrix).
  - Cold-start fallback: Gợi ý sản phẩm nổi bật / bán chạy cho khách hàng mới.
- **5b. Constraint Filtering (Lọc Ràng Buộc - BẮT BUỘC):**
  - Lọc theo **Ngân sách** (Budget constraint).
  - Lọc theo **Tương thích thiết bị** (Ngàm Lens vs Thân máy camera mount compatibility).
  - Lọc theo **Tồn kho & Trạng thái kinh doanh**.
  - Lọc theo **Loại thiết bị / Nhu cầu sử dụng** (Chụp chân dung, Phượt/Du lịch, Quay vlogging).
- **5c. Explainable Recommendation (Giải Thích Lý Do Gợi Ý - BẮT BUỘC):**
  - Sinh lý do gợi ý tự động cho từng sản phẩm:
    - *"Phù hợp chụp chân dung nhờ cảm biến Full-frame và khẩu độ lớn."*
    - *"Nằm trong ngân sách 15 - 20 triệu đồng bạn lựa chọn."*
    - *"Tương thích hoàn toàn với ngàm Canon RF hiện có của bạn."*
- **Exit Gate Phase 5:** API `/api/v1/recommendations/consult` trả về danh sách gợi ý kèm lý do giải thích (Explainable Reasons) và tuân thủ đúng các ràng buộc (Constraints).

#### 🔹 Phase 6: Hybrid & Behavior Integration
- Kết hợp mô hình Content-based specs với dữ liệu lịch sử hành vi `user_behaviors` (`VIEW`, `ADD_TO_CART`).
- Cập nhật điểm trọng số (Scoring & Ranking) cho sản phẩm gợi ý dựa trên mức độ quan tâm thực tế của khách hàng.
- **Exit Gate Phase 6:** Người dùng có lịch sử xem máy ảnh DSLR sẽ nhận được danh sách gợi ý nâng cao thiên về DSLR & Lens tương thích.

#### 🔹 Phase 7: Đánh Giá Mô Hình Offline & Recommendation Metrics Dashboard
- **Đánh giá Offline (Python):** Tính toán và báo cáo các chỉ số toán học:
  - **Precision@K, Recall@K, Hit Rate@K, Coverage, Latency**.
- **Admin Metrics Dashboard (Spring Boot + React):**
  - Giao diện đo lường tỷ lệ nhấp vào gợi ý (**CTR - Click Through Rate**).
  - Thống kê hiệu quả tư vấn của hệ thống AI.
- **Exit Gate Phase 7:** Có báo cáo metric offline đầy đủ + Dashboard đo lường CTR sẵn sàng đưa vào báo cáo đồ án.

#### 🔹 Phase 8: Polish, Demo & Báo Cáo Đồ Án
- Kiểm thử toàn diện khép kín từ Database sạch.
- Chuẩn bị Kịch bản Demo chi tiết thể hiện rõ bài toán tư vấn gợi ý.
- Hoàn thiện Báo cáo đồ án (Word/PDF) và Slide thuyết minh bảo vệ trước hội đồng.
- **Exit Gate Phase 8:** Thuyết minh bảo vệ thành công đồ án với điểm số tối đa.

---

### 🎁 PHẦN MỞ RỘNG (OPTIONAL - CHỈ LÀM NẾU DƯ THỜI GIAN)
- Đơn hàng & Payment Checkout đầy đủ.
- Admin CRUD quản lý sản phẩm nâng cao.
- Mã giảm giá (Coupon), Combo sản phẩm (Bundles).

---

## 4. 📝 HƯỚNG DẪN DÀNH CHO AI BÊN THỨ 3 (INSTRUCTIONS FOR 3RD PARTY AI)

Nếu bạn đưa file này cho bất kỳ công cụ AI nào khác (ChatGPT, Claude, Cursor, Copilot...):
> ⚠️ **LƯU Ý NGHÊM NGẶT:** Trọng tâm của đồ án này là **Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)**, KHÔNG PHẢI E-commerce platform thông thường.  
> 1. Mọi đề xuất mã nguồn hay kiến trúc phải tập trung giải quyết bài toán AI Recommendation (Content-based, Constraint filtering, Explainable reasons, Offline evaluation).  
> 2. Không sa đà xây dựng các tính năng thương mại điện tử phức tạp ở Nhóm A làm lãng phí thời gian.  
> 3. Tuân thủ chiến lược Vertical Slice và cây thư mục quy định tại Phần 1.

---
*Tài liệu này được cập nhật theo đúng yêu cầu trọng tâm đồ án tại: `docs/PROJECT_STATUS_AND_ROADMAP.md`*




================================================================================
<a id="file-docs-plan-md"></a>
## 📄 NỘI DUNG FILE: `docs/plan.md`
================================================================================

# Kế hoạch & Định hướng Dự án Camera Store

Dự án được triển khai theo chiến lược **Vertical Slice**. Mỗi phase bắt buộc phải hoàn thiện trọn vẹn từ `Database/Schema -> Spring Boot API -> React UI -> Smoke Test` và đạt Exit Gate trước khi mở rộng sang phase tiếp theo.

> ⚠️ **TÔN CHỈ DỰ ÁN:** **Recommendation System (Hệ thống gợi ý & tư vấn máy ảnh)** là TRỌNG TÂM DUY NHẤT của đồ án. Giao diện E-commerce chỉ đóng vai trò nền tảng tối thiểu để thu thập dữ liệu và demo luồng tư vấn.

---

## 1. Định hướng Cấu trúc Toàn bộ File & Submodule trong Project

```
camera-store/
├── AGENTS.md                   # User rules & nguyên tắc phối hợp AI
├── Camera Store — Specification.md # Tài liệu yêu cầu chi tiết (SRS/BRD)
├── README.md                   # Tổng quan dự án & hướng dẫn khởi chạy nhanh
├── docker-compose.yml          # Container orchestration (PostgreSQL, Redis)
│
├── docs/                       # TÀI LIỆU HƯỚNG DẪN & NGUYÊN TẮC THIẾT KẾ
│   ├── PROJECT_STATUS_AND_ROADMAP.md # [Source of Truth Bổ Sung] Báo cáo lộ trình trọng tâm AI
│   ├── constitution.md         # [Source of Truth 1] Nguyên tắc kiến trúc cố định
│   ├── decisions.md            # [Source of Truth 2] Nhật ký quyết định kiến trúc (ADRs)
│   ├── architecture.md         # [Source of Truth 3] Tổng quan kiến trúc & sơ đồ phụ thuộc
│   ├── coding-style.md         # [Source of Truth 4] Quy chuẩn viết code Backend/Frontend/AI
│   ├── workflow.md             # [Source of Truth 5] Quy trình phát triển (Phase Gates)
│   ├── checklist.md            # [Source of Truth 6] Tiến độ thực thi chi tiết
│   ├── plan.md                 # Kế hoạch tổng thể chia Phase (File này)
│   ├── overview.md             # Mục tiêu sản phẩm & bài toán E-commerce + AI Recommendation
│   ├── setup.md                # Hướng dẫn cài đặt môi trường dev local
│   ├── done.md                 # Nhật ký công việc đã hoàn thành
│   └── lessons.md              # Bài học kinh nghiệm & lưu ý debug
│
├── backend/                    # SPRING BOOT MODULAR MONOLITH (JAVA 21)
│   ├── pom.xml                 # Maven dependencies (Spring Boot 3.4.5, JPA, Flyway, Postgres, JWT, Validation, OpenAPI)
│   ├── Dockerfile              # Container image cho backend
│   └── src/main/java/com/camerastore/
│       ├── config/             # Cấu hình chung (Security, Cors, OpenAPI/Swagger, Redis)
│       ├── common/             # Exceptions, DTO response chuẩn (ApiResponse<T>), Utils
│       └── modules/            # CÁC DOMAIN BUSINESS NẰM TRONG CÁC PACKAGE ĐỘC LẬP
│           ├── auth/           # Login, Register, JWT token management, Security Guards
│           ├── users/          # User profile, Address management, Role management
│           ├── products/       # Catalog, Category, Brand, Product Variant, Camera Specifications
│           ├── cart/           # Shopping Cart, CartItems management (Tối giản)
│           ├── userbehavior/   # Tracking behavior events (VIEW, ADD_TO_CART)
│           └── recommendations/# CORE AI MODULE: Recommendation Service (Content-based, Constraint filtering, Explainable reasons)
│       └── resources/
│           ├── application.yml # Backend configuration
│           └── db/migration/   # Flyway SQL migration scripts (V1__, V2__...)
│
├── frontend/                   # REACT + VITE + TYPESCRIPT SPA
│   ├── package.json            # Node dependencies (React 19, Vite 6, TypeScript, TanStack Query)
│   ├── vite.config.ts          # Vite build & proxy settings
│   └── src/
│       ├── components/         # Shared UI components (Layouts, Navbar, Footer, Buttons, Cards, Modals)
│       ├── pages/
│       │   ├── storefront/     # Customer Pages (Home, Catalog, ProductDetail, Recommendations, Profile)
│       │   └── admin/          # Admin Pages (Recommendation Metrics Dashboard, Catalog Manage)
│       ├── services/           # Axios API Client calls & TanStack Query hooks
│       ├── types/              # TypeScript interfaces/types chuẩn hóa từ Swagger API contract
│       └── utils/              # Helper functions (Currency formatter, Date parser, Storage)
│
└── ai/                         # PYTHON RECOMMENDATION PIPELINE (OFFLINE/BATCH)
    └── recommendation/
        ├── data/               # Raw dataset & Processed feature matrix
        ├── models/             # Exported model artifacts (.pkl, .json)
        ├── scripts/
        │   ├── prepare_data.py # Trích xuất & làm sạch camera specs, user behavior
        │   ├── train.py        # Feature engineering (TF-IDF, MinMax Scaler) & Cosine similarity calculation
        │   └── evaluate.py     # Offline evaluation (Precision@K, Recall@K, Hit Rate@K, Coverage, Latency)
        └── README.md           # Hướng dẫn chạy pipeline Python & định dạng artifact xuất cho Spring Boot
```

---

## 2. Phương thức Thực thi (Vertical Slice)

- **Mỗi slice gồm 5 bước**:
  1. Contract / DB Schema & Flyway Migration.
  2. Backend DTO (`ApiResponse<T>`), Entity, Service, Controller & Swagger annotation.
  3. Frontend Route, State Handlers (Loading, Empty, Error, Success).
  4. Seed / Demo Data & API Integration.
  5. Focused Testing & Check Exit Gate Evidence.
- **Không polish UI E-commerce rườm rà** làm lệch tiến độ phần AI Recommendation.

---

## 3. Phân Chia Phase Chi Tiết (Grouped Phases Roadmap)

### 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (Phải có để thu thập dữ liệu & hiển thị)

| Phase | Mục tiêu chính | Đầu ra chính | Trạng thái |
|---|---|---|:---:|
| **Phase 0** | Baseline Setup | Schema, Docker Compose, Spring Boot & React Skeleton | **DONE** |
| **Phase 1** | Shell, Global Error & Design System | Router, GlobalExceptionHandler, ApiResponse<T>, Swagger, UI Shell | **ACTIVE** |
| **Phase 2** | Catalog & Camera Specs | API Product/Specs, Filter/Search, Detail Page với thông số máy ảnh | BLOCKED |
| **Phase 3** | Auth & User Identity | Login, Register, JWT Auth, User Context | BLOCKED |
| **Phase 4** | Behavior Tracking | Tracking `VIEW` & `ADD_TO_CART`, Giỏ hàng tối giản | BLOCKED |

### 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (AI RECOMMENDATION CORE - DỒN 60-70% SỨC CỰC)

| Phase | Mục tiêu chính | Đầu ra chính | Trạng thái |
|---|---|---|:---:|
| **Phase 5** | AI Recommendation Core (Constraint + Explainable + Content) | Content-based TF-IDF/Cosine, Constraint filtering (Ngân sách, Ngàm lens, Loại máy), Explainable reasons ("Phù hợp chụp chân dung...") | BLOCKED |
| **Phase 6** | Hybrid & Behavior Integration | Kết hợp dữ liệu lịch sử `user_behaviors` vào mô hình gợi ý cá nhân hóa | BLOCKED |
| **Phase 7** | Offline Evaluation & Admin Metrics Dashboard | Đánh giá Offline (Precision@K, Recall@K, Coverage) & Dashboard đo lường CTR | BLOCKED |
| **Phase 8** | Release, Demo & Báo cáo Đồ án | Smoke test toàn hệ thống, Kịch bản Demo bài toán tư vấn, Báo cáo đồ án | BLOCKED |

### 🎁 PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE)
- Checkout & Order Management đầy đủ.
- Admin CRUD Quản lý sản phẩm nâng cao.
- Coupon & Bundles.

---

## 4. Chi tiết Exit Gate Các Phase

- **Phase 0 Exit Gate (DONE)**: Migration chạy sạch, PostgreSQL & Redis container hoạt động, Swagger contract sẵn sàng.
- **Phase 1 Exit Gate**: Backend & Frontend build pass, Router mượt mà, `GlobalExceptionHandler` format lỗi chuẩn.
- **Phase 2 Exit Gate**: Hiển thị danh sách và chi tiết máy ảnh kèm đầy đủ bộ Camera Specs phục vụ AI.
- **Phase 3 Exit Gate**: Đăng nhập/Đăng ký thành công, JWT token bảo vệ đúng endpoint.
- **Phase 4 Exit Gate**: Sự kiện `VIEW` và `ADD_TO_CART` được ghi lại chuẩn xác vào Database Postgres.
- **Phase 5 Exit Gate (RẤT QUAN TRỌNG)**: API tư vấn gợi ý trả về danh sách sản phẩm tuân thủ ràng buộc (Constraint: budget, lens mount) và có lý do giải thích sinh tự động (Explainable reasons).
- **Phase 6 Exit Gate**: User có lịch sử xem máy ảnh DSLR nhận danh sách gợi ý cá nhân hóa tương ứng.
- **Phase 7 Exit Gate**: Có báo cáo metric offline (Precision@K, Recall@K...) + Dashboard đo lường CTR cho Admin.
- **Phase 8 Exit Gate**: Demo bài toán tư vấn gợi ý thành công từ DB sạch, sẵn sàng nộp và bảo vệ đồ án.




================================================================================
<a id="file-docs-checklist-md"></a>
## 📄 NỘI DUNG FILE: `docs/checklist.md`
================================================================================

# Development Checklist

> **Trọng tâm đề tài:** **AI Recommendation System** (Tư vấn cá nhân hóa máy ảnh & thiết bị nhiếp ảnh).  
> **Phân nhóm:** Nhóm A (Nền tảng tối thiểu) -> Nhóm B (Trọng tâm AI Core) -> Nhóm C (Phần mở rộng Optional).

---

## 📦 NHÓM A: NỀN TẢNG TỐI THIỂU (Phục vụ thu thập dữ liệu & demo AI)

### Phase 0: Contract & Baseline Lock (DONE)
- [x] Kiến trúc Spring Boot Modular Monolith, PostgreSQL, Docker Compose thống nhất
- [x] JPA entities, Flyway migrations nền tảng đã thiết lập
- [x] Tài liệu kiến trúc và quy chuẩn code đã khóa
- [x] **Gate:** Docker Compose khởi chạy PostgreSQL/Redis thành công, build baseline pass.

### Phase 1: Foundation, Global Error & Design System (ACTIVE)
- [ ] PostgreSQL & Redis chạy bằng Docker Compose
- [ ] Cấu hình `ApiResponse<T>`, `GlobalExceptionHandler` bắt lỗi toàn cục
- [ ] Cấu hình Spring Security baseline (CORS Vite, permit Swagger & public endpoints)
- [ ] Frontend setup: `apiClient.ts` (Axios), TypeScript types khớp Backend DTO
- [ ] Router frontend (`/`, `/catalog`, `/product/:id`, `/recommendations`), layout shell
- [ ] **Gate:** Backend/Frontend build pass, Swagger UI mở được tại `http://localhost:8080/swagger-ui.html`.

### Phase 2: Catalog & Camera Specifications
- [ ] Bảng `categories`, `brands`, `products`, `camera_specifications` qua Flyway
- [ ] API duyệt sản phẩm (lọc brand, category, khoảng giá, phân trang)
- [ ] API chi tiết sản phẩm kèm đầy đủ thông số kỹ thuật (Camera Specs)
- [ ] Frontend trang Catalog & trang Chi tiết máy ảnh (hiển thị bảng thông số)
- [ ] **Gate:** Khách hàng duyệt sản phẩm -> lọc/tìm kiếm -> xem chi tiết máy ảnh kèm thông số specs hoàn chỉnh.

### Phase 3: Identity & Customer Account Cơ Bản
- [ ] Bảng `users`, `roles` qua Flyway
- [ ] Đăng ký, đăng nhập, JWT authentication, mật khẩu băm BCrypt
- [ ] Frontend Modal / Form Đăng nhập, lưu JWT vào Auth State
- [ ] **Gate:** Đăng nhập thành công, nhận JWT token để định danh người dùng phục vụ cá nhân hóa.

### Phase 4: Behavior Tracking (Thu thập dữ liệu hành vi)
- [ ] Bảng `user_behaviors` ghi nhận sự kiện: `VIEW`, `ADD_TO_CART`
- [ ] API nhận sự kiện tracking từ frontend
- [ ] Frontend tự động gửi tracking event khi xem máy ảnh hoặc thêm vào giỏ
- [ ] Giỏ hàng tối giản (lưu local/session)
- [ ] **Gate:** Sự kiện `VIEW` và `ADD_TO_CART` được lưu đúng vào PostgreSQL với `user_id` hoặc `session_id`.

---

## 🔥 NHÓM B: TRỌNG TÂM ĐỒ ÁN (AI RECOMMENDATION CORE - DỒN 60-70% THỜI LƯỢNG)

### Phase 5: Recommendation Engine Core (Constraint + Explainable + Content-Based)
- [ ] Dataset `cameras_seed.csv` chuẩn hóa thông số specs (cảm biến, ngàm lens, megapixel, giá, nhu cầu)
- [ ] **5a. Content-Based Model:** Python script tiền xử lý, TF-IDF vectorizer trên specs, tính ma trận Cosine Similarity
- [ ] **5b. Constraint Filtering (Bắt buộc):** Lọc theo ngân sách (budget), lọc theo tương thích ngàm lens (lens mount), lọc theo tình trạng tồn kho, lọc theo mục đích chụp (chân dung, du lịch, vlog, thể thao)
- [ ] **5c. Explainable Recommendations (Bắt buộc):** Tự động sinh lý do gợi ý ("Phù hợp chụp chân dung nhờ cảm biến Full-frame 33MP", "Tương thích ngàm Canon RF", "Nằm trong ngân sách 50 triệu")
- [ ] Xuất artifact mô hình (`similarity_matrix.json`) sang `ai/recommendation/models/`
- [ ] Backend `RecommendationService` đọc artifact offline, nạp cache Redis và cung cấp API tư vấn
- [ ] Frontend tích hợp giao diện Trợ Lý Tư Vấn AI (Wizard chọn nhu cầu/ngân sách -> hiển thị kết quả kèm lý do)
- [ ] **Gate:** API tư vấn trả về danh sách gợi ý tuân thủ đúng ràng buộc (ngân sách, ngàm) và có lý do giải thích minh bạch.

### Phase 6: Hybrid & Behavior Integration
- [ ] Kết hợp dữ liệu lịch sử `user_behaviors` (`VIEW`, `ADD_TO_CART`) vào thuật toán gợi ý
- [ ] Nâng điểm trọng số cho các sản phẩm/hãng mà người dùng quan tâm gần đây
- [ ] Xử lý Cold-Start Fallback: Gợi ý máy ảnh nổi bật / bán chạy cho người dùng mới
- [ ] **Gate:** Khách hàng đã xem máy ảnh Sony sẽ nhận được danh sách gợi ý ưu tiên dòng máy Sony & Lens ngàm E tương thích.

### Phase 7: Đánh Giá Offline & Recommendation Dashboard
- [ ] Python script đánh giá mô hình offline: Precision@K, Recall@K, Hit Rate@K, Coverage
- [ ] Lưu log sự kiện nhấp vào gợi ý để tính toán CTR (Click-Through-Rate)
- [ ] Dashboard quản trị đơn giản hiển thị số liệu đo lường hiệu quả mô hình AI
- [ ] **Gate:** Có bảng số liệu đánh giá offline (Precision@K...) và báo cáo CTR sẵn sàng đưa vào báo cáo đồ án.

### Phase 8: Polish, Demo & Báo Cáo Đồ Án
- [ ] Kiểm thử luồng tư vấn gợi ý hoàn chỉnh từ database sạch
- [ ] Chuẩn bị kịch bản demo (3 kịch bản: khách mới, khách chụp chân dung, khách quay vlog)
- [ ] Hoàn thiện Slide thuyết minh và Báo cáo đồ án (Word/PDF)
- [ ] **Gate:** Demo kịch bản gợi ý mượt mà trước hội đồng, bảo vệ đồ án thành công.

---

## 🎁 PHẦN MỞ RỘNG (OPTIONAL / NICE-TO-HAVE - CHỈ LÀM NẾU DƯ THỜI GIAN)
- [ ] Checkout, Order Transactional, trừ kho tự động
- [ ] Lịch sử đơn hàng cá nhân
- [ ] Admin CRUD nâng cao (quản lý sản phẩm, coupon)




================================================================================
<a id="file-docs-constitution-md"></a>
## 📄 NỘI DUNG FILE: `docs/constitution.md`
================================================================================

# Project Constitution

## Vai trò file này
File cố định. Đây là bộ quy tắc làm việc không nên thay đổi trong suốt dự án trừ khi có quyết định kiến trúc lớn.

## 1. Architecture rules
- Ưu tiên modular monolith thay vì microservices.
- Giữ các domain tách biệt theo Spring Boot packages/modules.
- Tránh over-engineering trừ khi yêu cầu nghiệp vụ thực sự đòi hỏi.

## 2. Development rules
- Xây dựng tính năng theo từng lát cắt hoàn chỉnh (Vertical Slice).
- Giữ code rõ ràng, nhất quán và có kiểm thử.
- Sử dụng JPA entities và Flyway migrations làm nguồn sự thật duy nhất cho database modeling.
- Không tự ý thêm dịch vụ hoặc abstraction không cần thiết.

## 3. Recommendation rules
- Logic recommendation nằm độc lập trong module `recommendations`.
- Bắt đầu với Content-based filtering kết hợp Constraint filtering và Explainable reasons.
- Tích hợp đơn giản: Spring Boot đọc model artifact từ Python (file JSON/PKL) và nạp cache Redis.
- Không phức tạp hóa phiên bản đầu tiên.

## 4. Documentation rules
- Cập nhật tài liệu mỗi khi có thay đổi kiến trúc hoặc hợp đồng API.
- Giữ các ghi chú kiến trúc và tài liệu triển khai luôn đồng bộ.

## 5. Quality rules
- Luôn kiểm tra build backend (`mvn clean package`) và frontend (`npm run build`) trước khi hoàn thành task.
- Đảm bảo các luồng cốt lõi hoạt động: duyệt danh mục, thông số máy ảnh, tư vấn gợi ý AI.
- Giữ dự án luôn ở trạng thái sẵn sàng demo và báo cáo trước hội đồng.




================================================================================
<a id="file-docs-decisions-md"></a>
## 📄 NỘI DUNG FILE: `docs/decisions.md`
================================================================================

# Architecture Decisions

## Decision 001: Use a modular monolith
**Status:** Accepted

**Reason:**
- The project scope is suitable for a single backend application.
- It is easier to develop, debug, and deploy than a distributed system.
- The team can keep the architecture simple while still separating business concerns.

**Tradeoffs:**
- The system cannot scale independently by module.
- Cross-module coupling must be managed carefully.

## Decision 002: Use Spring Boot packages as business boundaries
**Status:** Accepted

**Reason:**
- Spring Boot packages make the codebase easier to organize.
- Each module can own its own controller, service, and domain logic.
- This aligns well with the modular monolith approach.

## Decision 003: Keep recommendation logic isolated
**Status:** Accepted

**Reason:**
- Recommendation is a specialized feature with different processing needs.
- It is easier to evolve later if it has a dedicated boundary.
- The initial version can start with content-based filtering.

## Decision 004: Run recommendation training offline first
**Status:** Accepted

**Reason:**
- The project needs a reliable demo and repeatable evaluation more than realtime model training.
- Batch artifacts keep Python out of the request path and avoid introducing a second API service.
- Spring Boot remains the single runtime API for the frontend.

**Rules:**
- Python owns dataset preparation, training, batch inference and offline metrics.
- Spring Boot owns recommendation endpoints, authorization, filtering and presentation metadata.
- Every published artifact must have a model version and training timestamp.
- Realtime or hybrid algorithms are future extensions, not Phase 1 dependencies.

## Decision 005: Redis as cache layer for AI recommendations
**Status:** Accepted

**Reason:**
- The cosine similarity matrix and personalized recommendation responses are compute-heavy and should not query PostgreSQL repeatedly.
- Redis provides ultra-fast lookup (TTL: 1 hour) for `recommendations:similar:{productId}` and `recommendations:personalized:{userId}`.
- If Redis is down, Spring Boot falls back gracefully to in-memory cache or direct DB queries without breaking the user experience.






================================================================================
<a id="file-docs-architecture-md"></a>
## 📄 NỘI DUNG FILE: `docs/architecture.md`
================================================================================

# Architecture Notes

## Overall Architecture
Dự án sử dụng kiến trúc Modular Monolith - một ứng dụng Spring Boot duy nhất, các package tách biệt rõ ràng theo business domain.

Docker Compose là môi trường chạy và chuẩn hóa local/deployment (PostgreSQL 17, Redis 7), không phải ranh giới microservice. `backend` vẫn là một Spring Boot application/deployment duy nhất.

## Module Boundaries
- `auth`: Authentication & Authorization (Spring Security, JWT)
- `users`: User profile & account
- `products`: Catalog, categories, brands, camera specifications
- `cart`: Shopping cart tối giản
- `userbehavior`: Tracking hành vi người dùng (`VIEW`, `ADD_TO_CART`) cho recommendation
- `recommendations`: Recommendation engine (Content-based, Constraint filtering, Explainable reasons)

## Business Context
**Actors:**
- **Guest (Khách vãng lai)**: Xem danh mục, lọc theo ngân sách/thông số, nhận tư vấn AI.
- **User (Đã đăng ký)**: Lưu thông tin, theo dõi hành vi để nhận gợi ý cá nhân hóa.
- **Admin**: Quản lý sản phẩm, xem dashboard đo lường CTR và metrics recommendation.

**Core Workflows:**
1. Duyệt danh mục sản phẩm -> Xem chi tiết thông số máy ảnh (Camera Specs).
2. Sử dụng Trợ lý Tư vấn AI (Wizard 3 bước: nhu cầu, ngân sách, ngàm lens) -> Nhận danh sách gợi ý kèm lý do minh bạch.
3. Ghi nhận hành vi tương tác (`VIEW`, `ADD_TO_CART`) phục vụ thuật toán Hybrid.
4. Đánh giá mô hình offline (Precision@K, Recall@K, Coverage) và đo lường CTR trên Dashboard.

## Data Layer
- **PostgreSQL 17**: Main relational database store.
- **JPA/Hibernate + Flyway**: Persistence và migration source of truth.
- **Redis 7**: Cache layer cho ma trận tương đồng Cosine và kết quả gợi ý cá nhân hóa (TTL: 1 giờ).

## Recommendation Boundary
Logic recommendation nằm trong service/module Spring Boot riêng. Python ở `ai/recommendation/` phụ trách dataset preparation, training, offline evaluation và batch inference; không chạy như một Python microservice riêng biệt. Artifact mô hình (`similarity_matrix.json` hoặc `.pkl`) được Spring Boot đọc để phục vụ REST API.




================================================================================
<a id="file-docs-coding-style-md"></a>
## 📄 NỘI DUNG FILE: `docs/coding-style.md`
================================================================================

# Coding Style

## Nguyên tắc chung
- Dùng `camelCase` cho biến và phương thức.
- Dùng `PascalCase` cho class, component, và model.
- Dùng `kebab-case` cho tên thư mục và file (trừ khi framework yêu cầu khác).

## Xử lý lỗi
- Ưu tiên domain-specific exceptions thay vì generic `Error`.
- Validate input ở tầng DTO bằng Jakarta Bean Validation trước khi vào service.
- Bắt lỗi tập trung tại `GlobalExceptionHandler`, không nuốt ngoại lệ mà không xử lý.

## Tổ chức module (Backend Spring Boot)
- Mỗi module có thư mục riêng dưới `backend/src/main/java/com/camerastore/modules/`.
- Phân định rõ: `controllers`, `services`, `dto`, `entities`, `repositories`.
- Không truy cập database trực tiếp từ controller – luôn qua service.
- Controller luôn trả về response bọc trong `ApiResponse<T>`.

## Logging
- Dùng logger chuẩn của framework (SLF4J/Logback).
- Log ở mức INFO cho các hoạt động bình thường, ERROR cho ngoại lệ.
- Tuyệt đối không log password, token, hoặc thông tin cá nhân nhạy cảm.

## Database & Persistence
- Dùng Spring Data JPA repository để truy vấn.
- Mọi thay đổi schema bảng bắt buộc phải tạo file Flyway migration mới trong `db/migration/`.
- Với các thao tác ghi nhiều bảng, sử dụng `@Transactional`.

## Module và phụ thuộc
- Tránh vòng lặp import (circular dependency).
- Tách logic dùng chung vào module `common`.

## Anti-patterns cần tránh
- ❌ Truy cập repository trực tiếp trong Controller khi có business logic.
- ❌ Import vòng tròn giữa các service.
- ❌ Ném ngoại lệ chung chung (generic `RuntimeException` không rõ lý do).
- ❌ DTO chứa logic nghiệp vụ.
- ❌ Controller quá dày (nên mỏng, chỉ nhận request, validate và gọi service).




================================================================================
<a id="file-docs-workflow-md"></a>
## 📄 NỘI DUNG FILE: `docs/workflow.md`
================================================================================

# Agent Workflow and Phase Gates

## 1. Xác định nguồn sự thật (Source of Truth)
Đọc tài liệu theo đúng thứ tự ưu tiên:

1. `docs/FOUNDATION_BASELINE.md` – Bản móng kỹ thuật & ranh giới 3 thành viên
2. `docs/PROJECT_STATUS_AND_ROADMAP.md` – Lộ trình trọng tâm AI & phân nhóm A/B
3. `docs/constitution.md` – Nguyên tắc kiến trúc bất biến
4. `docs/decisions.md` – Quyết định kiến trúc đã được chấp nhận
5. `docs/architecture.md` – Kiến trúc tổng thể và ranh giới module
6. `docs/coding-style.md` – Quy tắc code chuẩn
7. `docs/plan.md` – Kế hoạch phase
8. `docs/checklist.md` – Danh sách kiểm tra tiến độ

Swagger/OpenAPI tại `http://localhost:8080/swagger-ui.html` là nguồn sự thật duy nhất cho API contracts.

## 2. Chọn đúng phase và vertical slice
- Mỗi task phải ghi rõ phase, module, API/UI surface và acceptance criteria.
- Không bắt đầu phase mới khi gate của phase trước chưa đạt.
- Ưu tiên flow hoàn chỉnh theo lát cắt: Database Migration → Spring Boot API → React UI → Smoke Test.
- Không ôm đồm task quá lớn dàn trải toàn bộ project.

## 3. Trước khi code
- Xác định entity, DTO, validation, error cases và API response (`ApiResponse<T>`).
- Nếu đổi schema, tạo file Flyway migration mới trước khi viết code Java.
- Nếu đổi recommendation, xác định feature source, constraint và explainable reason bị ảnh hưởng.
- Giới hạn file được phép thay đổi trong scope task.

## 4. Trong khi code
- Tuân theo `docs/coding-style.md`.
- Controller mỏng; business logic nằm trong service.
- Dùng DTO validation cho input.
- Không tin giá, role hoặc stock do frontend gửi lên (luôn kiểm tra tại server).
- Không log password, token hoặc dữ liệu nhạy cảm.
- Cập nhật Swagger khi API thay đổi.

## 5. Sau mỗi task
Chạy kiểm tra nhỏ nhất phù hợp:

1. Typecheck/build của phần vừa sửa (`mvn clean package` hoặc `npm run build`).
2. Unit/service test cho logic mới.
3. API smoke test cho endpoint quan trọng qua Swagger.
4. Frontend flow test nếu sửa UI.
5. Flyway migration check nếu sửa schema.

## 6. Gate của phase
Chỉ tick checklist khi có bằng chứng (evidence):
- Command đã chạy và kết quả pass;
- Endpoint/UI flow đã được kiểm tra thực tế;
- Lỗi chính và boundary cases đã được xử lý;
- Swagger, schema hoặc docs đã đồng bộ.

## 7. Kết thúc task
- Kiểm tra `docs/done.md`.
- Cập nhật `docs/checklist.md` đúng mục, không tick thay cho phase khác.
- Cập nhật `docs/lessons.md` khi có lỗi bất thường hoặc quyết định mới.




================================================================================
<a id="file-docs-setup-md"></a>
## 📄 NỘI DUNG FILE: `docs/setup.md`
================================================================================

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




================================================================================
<a id="file-docs-overview-md"></a>
## 📄 NỘI DUNG FILE: `docs/overview.md`
================================================================================

# Camera Store Project Overview

## Mục tiêu sản phẩm
Xây dựng một hệ thống thương mại điện tử chuyên biệt về thiết bị nhiếp ảnh (máy ảnh, ống kính, phụ kiện) tích hợp **Hệ Thống Gợi Ý & Tư Vấn Cá Nhân Hóa (Recommendation System)**.

## Định vị trọng tâm
Khác với các website e-commerce thông thường:
1. **Recommendation System là TRỌNG TÂM HỌC THUẬT CỐT LÕI (chiếm 60-70% nỗ lực)**:
   - Thuật toán Content-based filtering phân tích sâu thông số kỹ thuật máy ảnh (Camera Specs: cảm biến, ngàm lens, megapixel, video, trọng lượng).
   - Lọc ràng buộc khắt khe (Constraint Filtering: ngân sách, tương thích ngàm lens, tình trạng tồn kho, mục đích sử dụng).
   - Sinh lý do gợi ý tự động, minh bạch bằng ngôn ngữ tự nhiên (Explainable Recommendations).
   - Tích hợp dữ liệu hành vi người dùng (`VIEW`, `ADD_TO_CART`) để nâng cấp mô hình Hybrid.
   - Đánh giá chất lượng mô hình offline bằng các chỉ số toán học: Precision@K, Recall@K, Hit Rate@K, Coverage.
2. **E-commerce đóng vai trò NỀN TẢNG TỐI THIỂU**:
   - Cung cấp giao diện duyệt sản phẩm, xem chi tiết và giỏ hàng để thu thập dữ liệu hành vi người dùng thực tế và làm môi trường demo sống động cho hệ thống gợi ý AI.

## Công nghệ sử dụng
- **Frontend**: React 19, Vite 6, TypeScript, TanStack Query, Vanilla CSS (Design System phẳng, thực tế).
- **Backend**: Spring Boot 3.4.5, Java 21, REST API, Swagger OpenAPI 3, Spring Security, JWT.
- **Database & Cache**: PostgreSQL 17 (dữ liệu quan hệ chính), Redis 7 (cache kết quả tính toán recommendation).
- **AI Recommendation**: Python 3.11, Pandas, NumPy, Scikit-learn (TF-IDF, Cosine Similarity, Constraint rules).
- **Hạ tầng**: Docker Compose quản lý PostgreSQL và Redis local.

## Kiến trúc hệ thống
Sử dụng kiến trúc **Modular Monolith**. Toàn bộ logic nghiệp vụ backend nằm trong các package riêng biệt của một ứng dụng Spring Boot duy nhất, kết nối một cơ sở dữ liệu PostgreSQL duy nhất. Không phân chia microservices phức tạp để đảm bảo tính ổn định, dễ bảo trì và dễ demo.




================================================================================
<a id="file-docs-done-md"></a>
## 📄 NỘI DUNG FILE: `docs/done.md`
================================================================================

# Definition of Done (Tiêu Chuẩn Nghiệm Thu)

## Mọi task
- [ ] Mã nguồn nằm đúng thư mục/module và không làm phát sinh file thừa ngoài phạm vi yêu cầu.
- [ ] Dữ liệu đầu vào được kiểm tra hợp lệ (validation) và xử lý ngoại lệ tập trung.
- [ ] Không phá vỡ phân quyền bảo mật, quyền sở hữu dữ liệu hoặc API hiện có.
- [ ] Backend build thành công (`mvn clean package`) nếu có thay đổi backend.
- [ ] Frontend build thành công (`npm run build`) nếu có thay đổi giao diện.
- [ ] Kiểm tra thực tế (smoke test) chạy ổn định, không có lỗi runtime.
- [ ] Tài liệu/checklist được cập nhật tương ứng nếu có thay đổi hợp đồng API hoặc tiến độ.

## API task (Backend)
- [ ] DTO và Jakarta Bean Validation đầy đủ.
- [ ] Response được bọc đúng chuẩn `ApiResponse<T>`.
- [ ] Swagger/OpenAPI phản ánh chính xác request, response và mã lỗi.
- [ ] Controller mỏng, không chứa business logic hay gọi trực tiếp Repository (phải qua Service).

## Database task
- [ ] Quan hệ schema, chỉ mục (index), tính duy nhất (uniqueness) và ràng buộc khóa ngoại đã được kiểm tra kỹ.
- [ ] Script migration Flyway chạy thành công trên cơ sở dữ liệu sạch (`mvn flyway:info`).
- [ ] Dữ liệu seed chạy tốt và không sinh dữ liệu mâu thuẫn.
- [ ] Thao tác ghi nhiều bảng sử dụng `@Transactional`.

## Recommendation task (AI)
- [ ] Thuộc tính máy ảnh (Camera specs) và sự kiện hành vi có nguồn dữ liệu chuẩn hóa, khớp với Database.
- [ ] Có thuật toán lọc ràng buộc (Constraint filtering) loại bỏ sản phẩm hết hàng hoặc vượt ngân sách.
- [ ] Có giải thích lý do gợi ý tự động (Explainable reasons).
- [ ] Có cơ chế Fallback xử lý trường hợp người dùng mới (Cold-start).
- [ ] Có chỉ số đánh giá offline (Precision@K, Recall@K, Coverage) trước khi xuất bản model artifact mới.

## Phase completion (Nghiệm thu phase)
- [ ] Đạt toàn bộ tiêu chí Exit Gate tương ứng trong `docs/checklist.md`.
- [ ] Có bằng chứng rõ ràng (lệnh build pass, API trả về đúng kết quả, luồng UI hoạt động mượt mà).




================================================================================
<a id="file-docs-lessons-md"></a>
## 📄 NỘI DUNG FILE: `docs/lessons.md`
================================================================================

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




================================================================================
<a id="file-backend-readme-md"></a>
## 📄 NỘI DUNG FILE: `backend/README.md`
================================================================================

# Backend

Spring Boot backend for the camera store recommendation system.

The runtime stack is Java, Spring Boot, Spring Data JPA, Flyway and PostgreSQL.

## Scope

- Auth, users, products, cart, orders, reviews, wishlist, behavior tracking, recommendations, admin, analytics
- JPA entities and Flyway migrations
- Python recommendation integration is maintained in `../ai/recommendation/`.





================================================================================
<a id="file-frontend-readme-md"></a>
## 📄 NỘI DUNG FILE: `frontend/README.md`
================================================================================

# Frontend

React + Vite frontend for the camera store recommendation system.





================================================================================
<a id="file-ai-readme-md"></a>
## 📄 NỘI DUNG FILE: `ai/README.md`
================================================================================

﻿# AI Recommendation

This folder contains the Python recommendation component described by the project specification.

## Structure

- `recommendation/train.py`: model training entry point
- `recommendation/predict.py`: inference entry point
- `recommendation/requirements.txt`: Python dependencies
- `recommendation/models/`: generated model artifacts

The first supported algorithm is content-based recommendation. Collaborative and hybrid
experiments can be added without coupling the Spring Boot modules to training code.





================================================================================
<a id="file--ai-readme-md"></a>
## 📄 NỘI DUNG FILE: `.ai/README.md`
================================================================================

﻿# AI Project Guide

This folder contains only reusable instructions for AI agents. Project truth lives in `docs/`.

## Project context
Read the root [AGENTS.md](../AGENTS.md) first, then use the canonical documents in
[`docs/`](../docs/): overview, architecture, constitution, decisions, coding style,
plan, workflow, checklist, done, and lessons.

## Skills
- [skills/implement-feature/SKILL.md](skills/implement-feature/SKILL.md)
- [skills/review-code/SKILL.md](skills/review-code/SKILL.md)





================================================================================
<a id="file--ai-skills-implement-feature-skill-md"></a>
## 📄 NỘI DUNG FILE: `.ai/skills/implement-feature/SKILL.md`
================================================================================

# Skill: Implement Feature

## Khi nào sử dụng
- Thêm một REST endpoint mới.
- Tạo một module nghiệp vụ mới trong Spring Boot.
- Mở rộng một tính năng hiện có.

## Đầu vào cần có
- Yêu cầu tính năng (mô tả ngắn).
- Module trực thuộc (tra cứu `docs/architecture.md`).

## Các bước thực hiện (Theo chuẩn Vertical Slice)

### 1. Xác định module nghiệp vụ
Tạo hoặc định vị thư mục module theo cấu trúc chuẩn:
```text
backend/src/main/java/com/camerastore/modules/<module-name>/
├── <Name>.java                (JPA Entity)
├── <Name>Controller.java      (REST Controller)
├── <Name>Service.java         (Business Service)
├── <Name>Repository.java      (Spring Data JPA Repository)
└── dto/                       (Request/Response DTOs)
```

### 2. Thay đổi cấu trúc Database (nếu có)
- Tạo file migration mới: `backend/src/main/resources/db/migration/V<version>__<description>.sql`.
- Chạy `cd backend && mvn test-compile` để kiểm tra cú pháp migration.

### 3. Tạo DTO (sử dụng Jakarta Bean Validation)
```java
public record CreateProductRequest(
    @NotBlank(message = "Tên sản phẩm không được để trống") 
    String name,
    
    @NotNull(message = "Giá sản phẩm là bắt buộc") 
    @PositiveOrZero(message = "Giá không được âm") 
    BigDecimal price
) {}
```

### 4. Viết Service
```java
@Service
@RequiredArgsConstructor
public class ProductService {
    private final ProductRepository productRepository;

    public List<ProductResponse> getAllProducts() {
        return productRepository.findAll().stream()
                .map(this::toResponse)
                .toList();
    }
}
```

### 5. Viết Controller (Luôn bọc trong ApiResponse<T>)
```java
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Tag(name = "Product Catalog", description = "APIs quản lý danh mục máy ảnh")
public class ProductController {
    private final ProductService productService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<ProductResponse>>> getAllProducts() {
        List<ProductResponse> data = productService.getAllProducts();
        return ResponseEntity.ok(ApiResponse.<List<ProductResponse>>builder()
                .code(200)
                .message("Success")
                .result(data)
                .build());
    }
}
```




================================================================================
<a id="file--ai-skills-review-code-skill-md"></a>
## 📄 NỘI DUNG FILE: `.ai/skills/review-code/SKILL.md`
================================================================================

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

### 3. Xử lý lỗi (Fix Bug)
- Xác định nguyên nhân gốc rễ (Root Cause).
- Sửa mã nguồn và chạy lại test để đảm bảo không phát sinh lỗi hồi quy (regression).
- Nếu là lỗi đặc biệt hoặc phức tạp: ghi chú bài học vào `docs/lessons.md`.

### 4. Sau khi hoàn thành
- Chạy `cd backend && mvn clean compile` hoặc `cd frontend && npm run build` để kiểm tra tính toàn vẹn.
- Cập nhật checklist tương ứng nếu có.


