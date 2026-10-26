package com.camerastore.common;

import org.springframework.http.HttpStatusCode;

/** Lỗi trả cho React: mã HTTP + thân lỗi theo định dạng chung. GlobalExceptionHandler đổi nó thành phản hồi. */
public class ApiException extends RuntimeException {
    private final HttpStatusCode status;
    private final ApiErrorResponse body;

    public ApiException(HttpStatusCode status, ApiErrorResponse body) {
        super(body.error().code() + ": " + body.error().message());
        this.status = status;
        this.body = body;
    }

    public HttpStatusCode getStatus() { return status; }
    public ApiErrorResponse getBody() { return body; }
}
