package com.camerastore.modules.advisor;

import com.camerastore.common.ApiErrorResponse;
import com.camerastore.common.ApiException;
import com.camerastore.config.ModelServiceProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.net.SocketTimeoutException;
import java.net.URI;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.util.UriComponentsBuilder;

/**
 * Gọi dịch vụ mô hình FastAPI qua HTTP (hợp đồng docs/api_contract.md 1.3). Lớp duy nhất biết địa chỉ FastAPI.
 *
 * <p>Đổi kết quả gọi thành một trong ba trường hợp:
 * <ul>
 *   <li>FastAPI trả 2xx: đọc JSON thành DTO;</li>
 *   <li>FastAPI trả 4xx đúng định dạng lỗi chung (USER_NOT_FOUND, INVALID_PARAM, ...): chuyển tiếp nguyên mã HTTP và
 *       thân lỗi cho React;</li>
 *   <li>không gọi được (FastAPI không chạy, hết giờ) hoặc FastAPI lỗi 5xx / trả dữ liệu hỏng: lỗi riêng của backend
 *       (MODEL_SERVICE_UNAVAILABLE 503, MODEL_SERVICE_TIMEOUT 504, MODEL_SERVICE_ERROR 502,
 *       MODEL_SERVICE_BAD_RESPONSE 502), cùng định dạng lỗi chung.</li>
 * </ul>
 */
@Component
public class ModelServiceClient {
    private final RestClient http;
    private final ObjectMapper json;
    private final ModelServiceProperties props;

    public ModelServiceClient(ModelServiceProperties props, ObjectMapper json) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(props.connectTimeout());
        factory.setReadTimeout(props.readTimeout());
        this.http = RestClient.builder().requestFactory(factory).build();
        this.json = json;
        this.props = props;
    }

    /**
     * GET {base-url}{path}?params, đọc thân 2xx thành kiểu type. Tham số có giá trị null thì không gửi (FastAPI dùng
     * mặc định của nó, vd k = 10, exclude = all_history).
     */
    public <T> T get(String path, Map<String, ?> params, Class<T> type) {
        UriComponentsBuilder b = UriComponentsBuilder.fromUriString(props.baseUrl()).path(path);
        params.forEach((name, value) -> {
            if (value != null) {
                b.queryParam(name, value);
            }
        });
        URI uri = b.encode().build().toUri();
        try {
            return http.get().uri(uri).exchange((req, res) -> {
                HttpStatusCode status = res.getStatusCode();
                try (InputStream body = res.getBody()) {
                    if (status.is2xxSuccessful()) {
                        return read(body, type, path, status);
                    }
                    if (status.is4xxClientError()) {
                        ApiErrorResponse err = read(body, ApiErrorResponse.class, path, status);
                        if (err.error() == null || err.error().code() == null) {
                            throw badResponse(path, status, "lỗi 4xx không đúng định dạng lỗi chung");
                        }
                        throw new ApiException(status, err);
                    }
                    throw upstreamError(path, status, body);
                }
            });
        } catch (ResourceAccessException e) {
            throw unreachable(path, e);
        }
    }

    private <T> T read(InputStream body, Class<T> type, String path, HttpStatusCode status) {
        try {
            return json.readValue(body, type);
        } catch (IOException e) {
            if (causedBy(e, SocketTimeoutException.class)) {
                // hết giờ giữa lúc đọc thân: báo như hết giờ (MODEL_SERVICE_TIMEOUT), không phải dữ liệu hỏng
                throw new ResourceAccessException("Hết giờ khi đọc phản hồi " + path, e);
            }
            throw badResponse(path, status, "không đọc được JSON: " + e.getMessage());
        }
    }

    private ApiException unreachable(String path, ResourceAccessException e) {
        Map<String, Object> details = details(path);
        if (causedBy(e, SocketTimeoutException.class)) {
            // Đã kết nối (hoặc đang kết nối) nhưng quá connect-timeout / read-timeout
            details.put("connect_timeout_ms", props.connectTimeout().toMillis());
            details.put("read_timeout_ms", props.readTimeout().toMillis());
            return new ApiException(HttpStatus.GATEWAY_TIMEOUT, ApiErrorResponse.of("MODEL_SERVICE_TIMEOUT",
                    "Dịch vụ gợi ý (FastAPI) không trả lời kịp.", details));
        }
        details.put("cause", e.getMostSpecificCause().toString());
        return new ApiException(HttpStatus.SERVICE_UNAVAILABLE, ApiErrorResponse.of("MODEL_SERVICE_UNAVAILABLE",
                "Không kết nối được dịch vụ gợi ý (FastAPI) ở " + props.baseUrl()
                        + ": dịch vụ chưa chạy hoặc sai địa chỉ (model-service.base-url).", details));
    }

    /** FastAPI lỗi 5xx: không chuyển chi tiết cho người dùng (hợp đồng mục 7), chỉ giữ mã lỗi gốc để dò. */
    private ApiException upstreamError(String path, HttpStatusCode status, InputStream body) {
        Map<String, Object> details = details(path);
        details.put("upstream_status", status.value());
        try {
            ApiErrorResponse err = json.readValue(body, ApiErrorResponse.class);
            if (err.error() != null) {
                details.put("upstream_code", err.error().code());
            }
        } catch (IOException ignored) {
            // thân không phải JSON lỗi chung: chỉ báo mã HTTP
        }
        return new ApiException(HttpStatus.BAD_GATEWAY,
                ApiErrorResponse.of("MODEL_SERVICE_ERROR", "Dịch vụ gợi ý tạm lỗi.", details));
    }

    private ApiException badResponse(String path, HttpStatusCode status, String why) {
        Map<String, Object> details = details(path);
        details.put("upstream_status", status.value());
        details.put("reason", why);
        return new ApiException(HttpStatus.BAD_GATEWAY, ApiErrorResponse.of("MODEL_SERVICE_BAD_RESPONSE",
                "Dịch vụ gợi ý trả dữ liệu không đúng hợp đồng.", details));
    }

    private Map<String, Object> details(String path) {
        Map<String, Object> d = new LinkedHashMap<>();
        d.put("model_service", props.baseUrl());
        d.put("path", path);
        return d;
    }

    private static boolean causedBy(Throwable e, Class<? extends Throwable> type) {
        for (Throwable t = e; t != null; t = t.getCause()) {
            if (type.isInstance(t)) {
                return true;
            }
        }
        return false;
    }
}
