package com.camerastore.config;

import com.camerastore.modules.catalog.Product;
import com.camerastore.modules.catalog.ProductRepository;
import java.math.BigDecimal;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SeedData {
    @Bean
    CommandLineRunner seedProducts(ProductRepository products) {
        return args -> {
            if (products.count() == 0) {
                products.save(new Product("Lumina X-T5", "Mirrorless", "Cảm biến APS-C 40MP, nhỏ gọn cho hành trình sáng tạo.", "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80", new BigDecimal("3299"), 8, true));
                products.save(new Product("Astra Full Frame 6", "Mirrorless", "Full-frame 24MP với chống rung 5 trục và màu da tự nhiên.", "https://images.unsplash.com/photo-1606986628253-6bc9bb5e82c1?auto=format&fit=crop&w=900&q=80", new BigDecimal("2899"), 5, true));
                products.save(new Product("Vista Street 35", "Compact", "Máy ảnh compact ống kính cố định cho những khoảnh khắc hằng ngày.", "https://images.unsplash.com/photo-1510127034890-ba27508e9f1c?auto=format&fit=crop&w=900&q=80", new BigDecimal("899"), 14, false));
                products.save(new Product("Northstar Pro 8K", "Video", "Quay 8K, profile điện ảnh và hệ sinh thái ống kính chuyên nghiệp.", "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=900&q=80", new BigDecimal("4199"), 3, true));
            }
        };
    }
}