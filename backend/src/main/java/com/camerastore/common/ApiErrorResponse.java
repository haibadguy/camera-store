package com.camerastore.common;

import java.util.Map;

/**
 * Định dạng lỗi chung của hợp đồng (docs/api_contract.md mục 7), dùng cho mọi lỗi của /api/**:
 * {"error": {"code": "USER_NOT_FOUND", "message": "...", "details": {...}}}.
 */
public record ApiErrorResponse(ErrorBody error) {

    public record ErrorBody(String code, String message, Map<String, Object> details) {}

    public static ApiErrorResponse of(String code, String message, Map<String, Object> details) {
        return new ApiErrorResponse(new ErrorBody(code, message, details == null ? Map.of() : details));
    }
}
