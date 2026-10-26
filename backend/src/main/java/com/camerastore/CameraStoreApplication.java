package com.camerastore;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import com.camerastore.config.RecommendationServiceProperties;

@SpringBootApplication
@EnableConfigurationProperties(RecommendationServiceProperties.class)
public class CameraStoreApplication {
    public static void main(String[] args) {
        SpringApplication.run(CameraStoreApplication.class, args);
    }
}