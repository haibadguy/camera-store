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
