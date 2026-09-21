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
