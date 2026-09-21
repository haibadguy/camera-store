# Skill: Implement Feature

## When to use
- ThĂªm má»™t endpoint má»›i.
- Táº¡o má»™t module má»›i.
- Má»Ÿ rá»™ng má»™t tĂ­nh nÄƒng hiá»‡n cĂ³.

## Inputs
- Feature requirement (mĂ´ táº£ ngáº¯n).
- Module thuá»™c vá» (xem `docs/architecture.md`).

## Steps (cĂ³ Ä‘iá»u kiá»‡n)

### 1. XĂ¡c Ä‘á»‹nh module
- Náº¿u module chÆ°a cĂ³, táº¡o thÆ° má»¥c theo cáº¥u trĂºc:
  ```text
  backend/src/main/java/com/camerastore/modules/<module-name>/
  â”œâ”€â”€ <Name>.java
  â”œâ”€â”€ <Name>Controller.java
  â”œâ”€â”€ <Name>Service.java
  â””â”€â”€ <Name>Repository.java
  ```

### 2. Náº¿u cáº§n thay Ä‘á»•i schema
- Cáº­p nháº­t `backend/src/main/resources/db/migration/V<version>__<description>.sql`.
- Cháº¡y `mvn -q clean test` Ä‘á»ƒ kiá»ƒm tra Flyway migration.

### 3. Táº¡o DTO (dĂ¹ng Jakarta Bean Validation)
```java
public record CreateProductRequest(
    @NotBlank String name,
    @NotNull @PositiveOrZero BigDecimal price
) {}
```

### 4. Viáº¿t Service
```java
@Service
public class ProductService {
    private final ProductRepository products;

    public List<Product> findAll() { return products.findAll(); }
}
```

### 5. Viáº¿t Controller
```java
@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductService service;

    @GetMapping
    public List<Product> findAll() { return service.findAll(); }
}
```

### 6. ÄÄƒng kĂ½ Module
- Đăng ký component bằng package scanning hoặc `@Bean` trong Spring Boot.

### 7. Kiá»ƒm tra
- Cháº¡y `mvn spring-boot:run` vĂ  kiá»ƒm tra API.

### 8. Cáº­p nháº­t tĂ i liá»‡u
- Tick checklist trong `docs/checklist.md`.
- Náº¿u cĂ³ lá»—i báº¥t thÆ°á»ng, ghi vĂ o `docs/lessons.md`.

## Output
- Code (service, controller, dto, module).
- Migration (náº¿u cĂ³).
- Checklist Ä‘Æ°á»£c tick.

