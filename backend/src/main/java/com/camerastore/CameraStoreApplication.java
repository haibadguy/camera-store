package com.camerastore;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class CameraStoreApplication {
    public static void main(String[] args) {
        SpringApplication.run(CameraStoreApplication.class, args);
    }
}
