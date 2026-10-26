package com.camerastore.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class RecommendationServiceConfig {
    @Bean
    RestClient recommendationRestClient(
            RestClient.Builder builder,
            RecommendationServiceProperties properties) {
        return builder.baseUrl(properties.url()).build();
    }
}
