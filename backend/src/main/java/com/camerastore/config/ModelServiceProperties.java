package com.camerastore.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Địa chỉ và thời gian chờ của dịch vụ mô hình FastAPI (khối model-service trong application.yml).
 *
 * @param baseUrl        vd http://127.0.0.1:8001
 * @param connectTimeout chờ mở kết nối
 * @param readTimeout    chờ phản hồi sau khi đã kết nối
 */
@ConfigurationProperties(prefix = "model-service")
public record ModelServiceProperties(String baseUrl, Duration connectTimeout, Duration readTimeout) {}
