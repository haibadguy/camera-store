package com.camerastore.modules.advisor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.ServerSocket;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/** FastAPI không chạy (cổng không ai nghe): Spring vẫn khởi động được và trả 503 MODEL_SERVICE_UNAVAILABLE. */
@SpringBootTest
@AutoConfigureMockMvc
class ModelServiceDownTest {

    @DynamicPropertySource
    static void modelService(DynamicPropertyRegistry r) throws IOException {
        int port;
        try (ServerSocket s = new ServerSocket(0)) {      // lấy một cổng trống rồi đóng lại
            port = s.getLocalPort();
        }
        String url = "http://127.0.0.1:" + port;
        r.add("model-service.base-url", () -> url);
    }

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;

    @ParameterizedTest
    @ValueSource(strings = {"/api/health", "/api/recommend?user_id=409&k=10", "/api/items/9022",
                            "/api/users/47/bodies", "/api/compat?body_id=9022&lens_id=13448"})
    void returns503WhenFastApiIsDown(String url) throws Exception {
        MvcResult r = mvc.perform(get(url)).andReturn();
        assertThat(r.getResponse().getStatus()).isEqualTo(503);
        JsonNode e = json.readTree(r.getResponse().getContentAsByteArray());
        assertThat(e.at("/error/code").asText()).isEqualTo("MODEL_SERVICE_UNAVAILABLE");
        assertThat(e.at("/error/message").asText()).contains("Không kết nối được dịch vụ gợi ý (FastAPI)");
        assertThat(e.at("/error/details/model_service").asText()).startsWith("http://127.0.0.1:");
    }
}
