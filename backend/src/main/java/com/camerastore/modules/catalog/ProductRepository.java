package com.camerastore.modules.catalog;

import java.math.BigDecimal;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByStockGreaterThanAndPriceLessThanEqualOrderByFeaturedDescPriceAsc(
            Integer stock, BigDecimal price);
}