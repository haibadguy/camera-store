package com.camerastore.modules.recommendations;

import com.camerastore.common.ApiResponse;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_GATEWAY;

@RestController
@RequestMapping("/api/recommendations")
public class RecommendationController {
    private final RestClient recommendationClient;

    public RecommendationController(RestClient recommendationClient) {
        this.recommendationClient = recommendationClient;
    }

    @GetMapping
    public ApiResponse<JsonNode> recommend(
            @RequestParam("user_id") int userId,
            @RequestParam(defaultValue = "10") int k,
            @RequestParam(defaultValue = "all_history") String exclude) {
        if (k < 1 || k > 50) {
            throw new ResponseStatusException(
                    org.springframework.http.HttpStatus.BAD_REQUEST,
                    "k phải nằm trong khoảng 1..50");
        }
        try {
            ResponseEntity<JsonNode> response = recommendationClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/recommend")
                            .queryParam("user_id", userId)
                            .queryParam("k", k)
                            .queryParam("exclude", exclude)
                            .build())
                    .retrieve()
                    .toEntity(JsonNode.class);
            return new ApiResponse<>(response.getBody());
        } catch (RestClientResponseException exception) {
            throw new ResponseStatusException(
                    exception.getStatusCode(),
                    "Dịch vụ recommendation từ chối yêu cầu: " + exception.getResponseBodyAsString(),
                    exception);
        } catch (RuntimeException exception) {
            throw new ResponseStatusException(
                    BAD_GATEWAY,
                    "Không thể kết nối dịch vụ recommendation.",
                    exception);
        }
    }
}
