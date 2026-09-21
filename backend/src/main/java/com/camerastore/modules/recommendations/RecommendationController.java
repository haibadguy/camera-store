package com.camerastore.modules.recommendations;

import com.camerastore.modules.catalog.Product;
import com.camerastore.modules.catalog.ProductRepository;
import java.math.BigDecimal;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/recommendations")
public class RecommendationController {
    private final ProductRepository products;

    public RecommendationController(ProductRepository products) {
        this.products = products;
    }

    @GetMapping
    public RecommendationResponse recommend(
            @RequestParam(defaultValue = "5000") BigDecimal budget,
            @RequestParam(required = false) String category) {
        List<Product> items = products
                .findByStockGreaterThanAndPriceLessThanEqualOrderByFeaturedDescPriceAsc(0, budget)
                .stream()
                .filter(product -> category == null || category.isBlank()
                        || product.getCategory().equalsIgnoreCase(category))
                .limit(6)
                .toList();
        return new RecommendationResponse("content-based", budget, category, items);
    }

    public record RecommendationResponse(String strategy, BigDecimal budget,
                                          String category, List<Product> items) {}
}