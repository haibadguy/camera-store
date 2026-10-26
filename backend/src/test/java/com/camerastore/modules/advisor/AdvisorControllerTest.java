package com.camerastore.modules.advisor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.RequestBuilder;

/**
 * Spring Boot + FastAPI giả lập (FakeModelService). Kiểm: (1) phản hồi thành công đi qua Spring vẫn trùng nội dung
 * phản hồi thật của FastAPI (sau khi đọc vào DTO rồi ghi lại JSON: không mất / thêm trường, không đổi giá trị);
 * (2) Spring gửi đúng tham số; (3) lỗi của FastAPI được chuyển tiếp nguyên dạng; (4) FastAPI lỗi 5xx / hết giờ / dữ
 * liệu hỏng thành lỗi rõ ràng cùng định dạng lỗi chung; (5) lỗi tham số phía Spring; (6) CORS cho Vite.
 */
@SpringBootTest(properties = "model-service.read-timeout=500ms")
@AutoConfigureMockMvc
class AdvisorControllerTest {
    static final FakeModelService FAKE = new FakeModelService();

    static {
        FAKE.file("/health", 200, "health.json");
        for (String u : List.of("409", "47")) {
            FAKE.file("/recommend?user_id=" + u + "&k=10", 200, "recommend_" + u + ".json");
            FAKE.file("/users/" + u + "/bodies", 200, "users_" + u + "_bodies.json");
        }
        FAKE.file("/recommend?user_id=409&k=10&exclude=all_history", 200, "recommend_409.json");
        FAKE.file("/users/47/bodies?exclude=all_history", 200, "users_47_bodies.json");
        for (String i : List.of("9022", "15485", "1154")) {
            FAKE.file("/items/" + i, 200, "item_" + i + ".json");
        }
        for (String c : List.of("9022_13448", "19071_9696", "9022_118", "9022_105")) {
            String[] bl = c.split("_");
            FAKE.file("/compat?body_id=" + bl[0] + "&lens_id=" + bl[1], 200, "compat_" + c + ".json");
        }
        FAKE.file("/recommend?user_id=99999", 404, "error_user_not_found.json");
        FAKE.file("/recommend?user_id=409&k=0", 422, "error_invalid_k.json");
        FAKE.file("/compat?body_id=9696&lens_id=19071", 400, "error_not_a_body.json");
        FAKE.raw("/recommend?user_id=1", 500, "application/json",
                "{\"error\": {\"code\": \"INTERNAL_ERROR\", \"message\": \"KeyError: 1\", \"details\": {}}}", 0);
        FAKE.raw("/recommend?user_id=2", 200, "application/json", "{}", 2000);     // chậm hơn read-timeout 500 ms
        FAKE.raw("/recommend?user_id=3", 200, "text/html", "<html>không phải JSON</html>", 0);
    }

    @DynamicPropertySource
    static void modelService(DynamicPropertyRegistry r) {
        r.add("model-service.base-url", FAKE::baseUrl);
    }

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;

    // -- (1), (2) phản hồi thành công trùng phản hồi thật của FastAPI ------------------------------------------
    @ParameterizedTest
    @CsvSource({
        "/api/recommend?user_id=409&k=10,          recommend_409.json,      /recommend?user_id=409&k=10",
        "/api/recommend?user_id=47&k=10,           recommend_47.json,       /recommend?user_id=47&k=10",
        "/api/recommend?user_id=409&k=10&exclude=all_history, recommend_409.json, /recommend?user_id=409&k=10&exclude=all_history",
        "/api/users/409/bodies,                    users_409_bodies.json,   /users/409/bodies",
        "/api/users/47/bodies,                     users_47_bodies.json,    /users/47/bodies",
        "/api/users/47/bodies?exclude=all_history, users_47_bodies.json,    /users/47/bodies?exclude=all_history",
        "/api/items/9022,                          item_9022.json,          /items/9022",
        "/api/items/15485,                         item_15485.json,         /items/15485",
        "/api/items/1154,                          item_1154.json,          /items/1154",
        "/api/compat?body_id=9022&lens_id=13448,   compat_9022_13448.json,  /compat?body_id=9022&lens_id=13448",
        "/api/compat?body_id=19071&lens_id=9696,   compat_19071_9696.json,  /compat?body_id=19071&lens_id=9696",
        "/api/compat?body_id=9022&lens_id=118,     compat_9022_118.json,    /compat?body_id=9022&lens_id=118",
        "/api/compat?body_id=9022&lens_id=105,     compat_9022_105.json,    /compat?body_id=9022&lens_id=105",
        "/api/health,                              health.json,             /health",
    })
    void successIsSameContentAsFastApi(String url, String fixture, String forwarded) throws Exception {
        MvcResult r = mvc.perform(get(url)).andReturn();
        assertThat(r.getResponse().getStatus()).isEqualTo(200);
        assertThat(r.getResponse().getContentType()).startsWith("application/json");
        assertThat(body(r)).isEqualTo(json.readTree(FakeModelService.fixture(fixture)));
        assertThat(FAKE.received).contains(forwarded);
    }

    @Test
    void recommendKeepsExplanationNullAndUtf8() throws Exception {
        JsonNode j = body(mvc.perform(get("/api/recommend?user_id=409&k=10")).andReturn());
        assertThat(j.at("/items/0").has("explanation")).isTrue();            // có trường, giá trị null
        assertThat(j.at("/items/0/explanation").isNull()).isTrue();
        assertThat(j.at("/items/1/explanation/text").asText()).contains("bạn đã đánh giá");
        assertThat(j.at("/items/1/explanation/path/0")).isEqualTo(json.readTree("{\"kind\":\"user\",\"id\":409}"));
        assertThat(j.at("/mask/blocked_in_topk_before_mask/0/item_id").asInt()).isEqualTo(13448);
    }

    // -- (3) lỗi của FastAPI chuyển tiếp nguyên dạng --------------------------------------------------------
    @ParameterizedTest
    @CsvSource({
        "/api/recommend?user_id=99999,           404, error_user_not_found.json",
        "/api/recommend?user_id=409&k=0,         422, error_invalid_k.json",
        "/api/compat?body_id=9696&lens_id=19071, 400, error_not_a_body.json",
    })
    void fastApiErrorsArePassedThrough(String url, int status, String fixture) throws Exception {
        MvcResult r = mvc.perform(get(url)).andReturn();
        assertThat(r.getResponse().getStatus()).isEqualTo(status);
        assertThat(body(r)).isEqualTo(json.readTree(FakeModelService.fixture(fixture)));
    }

    // -- (4) FastAPI lỗi 5xx / hết giờ / dữ liệu hỏng ------------------------------------------------------
    @ParameterizedTest
    @CsvSource({
        "/api/recommend?user_id=1, 502, MODEL_SERVICE_ERROR",
        "/api/recommend?user_id=2, 504, MODEL_SERVICE_TIMEOUT",
        "/api/recommend?user_id=3, 502, MODEL_SERVICE_BAD_RESPONSE",
    })
    void upstreamProblemsBecomeClearErrors(String url, int status, String code) throws Exception {
        long t = System.nanoTime();
        JsonNode e = error(get(url), status, code);
        if (code.equals("MODEL_SERVICE_TIMEOUT")) {
            assertThat((System.nanoTime() - t) / 1e6).isLessThan(1500);      // dừng theo read-timeout, không chờ 2 s
            assertThat(e.at("/error/details/read_timeout_ms").asInt()).isEqualTo(500);
        }
        if (code.equals("MODEL_SERVICE_ERROR")) {
            assertThat(e.at("/error/message").asText()).isEqualTo("Dịch vụ gợi ý tạm lỗi.");
            assertThat(e.at("/error/details/upstream_code").asText()).isEqualTo("INTERNAL_ERROR");
            assertThat(e.toString()).doesNotContain("KeyError");             // không lộ chi tiết lỗi bên trong
        }
    }

    // -- (5) lỗi tham số / đường dẫn phía Spring ------------------------------------------------------------
    @ParameterizedTest
    @CsvSource({
        "/api/recommend,                  query, user_id",
        "/api/recommend?user_id=abc,      query, user_id",
        "/api/recommend?user_id=409&k=x,  query, k",
        "/api/items/abc,                  path,  id",
        "/api/compat?body_id=9022,        query, lens_id",
    })
    void springParamErrorsUseContractFormat(String url, String where, String name) throws Exception {
        int before = FAKE.received.size();
        JsonNode e = error(get(url), 422, "INVALID_PARAM");
        assertThat(e.at("/error/details/errors/0/loc")).isEqualTo(json.createArrayNode().add(where).add(name));
        assertThat(FAKE.received).hasSize(before);                            // không gọi FastAPI
    }

    @Test
    void unknownPathAndMethod() throws Exception {
        error(get("/api/khong-co"), 404, "NOT_FOUND");
        error(post("/api/recommend?user_id=409"), 405, "HTTP_ERROR");
    }

    // -- (6) CORS cho cổng dev của Vite ---------------------------------------------------------------------
    @Test
    void corsAllowsViteDevServerOnly() throws Exception {
        MvcResult ok = mvc.perform(options("/api/recommend").header("Origin", "http://localhost:5173")
                .header("Access-Control-Request-Method", "GET")).andReturn();
        assertThat(ok.getResponse().getStatus()).isEqualTo(200);
        assertThat(ok.getResponse().getHeader("Access-Control-Allow-Origin")).isEqualTo("http://localhost:5173");

        MvcResult no = mvc.perform(options("/api/recommend").header("Origin", "http://evil.example")
                .header("Access-Control-Request-Method", "GET")).andReturn();
        assertThat(no.getResponse().getStatus()).isEqualTo(403);
    }

    private JsonNode body(MvcResult r) throws Exception {
        return json.readTree(r.getResponse().getContentAsByteArray());
    }

    /** Kiểm mã HTTP, mã lỗi và đúng định dạng lỗi chung {"error": {"code", "message", "details"}}. */
    private JsonNode error(RequestBuilder req, int status, String code) throws Exception {
        MvcResult r = mvc.perform(req).andReturn();
        assertThat(r.getResponse().getStatus()).isEqualTo(status);
        JsonNode e = body(r);
        assertThat(fieldNames(e)).isEqualTo(Set.of("error"));
        assertThat(fieldNames(e.get("error"))).isEqualTo(Set.of("code", "message", "details"));
        assertThat(e.at("/error/code").asText()).isEqualTo(code);
        assertThat(e.at("/error/details").isObject()).isTrue();
        return e;
    }

    private static Set<String> fieldNames(JsonNode n) {
        Set<String> s = new HashSet<>();
        n.fieldNames().forEachRemaining(s::add);
        return s;
    }
}
