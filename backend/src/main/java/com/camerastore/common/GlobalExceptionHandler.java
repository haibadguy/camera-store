package com.camerastore.common;

import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/**
 * Đổi mọi lỗi sang định dạng lỗi chung của hợp đồng (mục 7). Mã lỗi phía Spring dùng lại đúng mã của FastAPI
 * (INVALID_PARAM 422, NOT_FOUND 404, INTERNAL_ERROR 500) để React chỉ phải xử lý một bảng mã.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** Lỗi đã có sẵn mã + thân: lỗi FastAPI chuyển tiếp, hoặc lỗi gọi FastAPI (ModelServiceClient). */
    @ExceptionHandler(ApiException.class)
    ResponseEntity<ApiErrorResponse> api(ApiException e) {
        return ResponseEntity.status(e.getStatus()).body(e.getBody());
    }

    /** Thiếu tham số bắt buộc, vd /api/recommend không có user_id. */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    ResponseEntity<ApiErrorResponse> missing(MissingServletRequestParameterException e) {
        return invalid("query", e.getParameterName(), "Thiếu tham số bắt buộc.");
    }

    /** Sai kiểu, vd user_id=abc. */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    ResponseEntity<ApiErrorResponse> typeMismatch(MethodArgumentTypeMismatchException e) {
        boolean inPath = e.getParameter().hasParameterAnnotation(PathVariable.class);
        return invalid(inPath ? "path" : "query", e.getName(), "Phải là số nguyên.");
    }

    @ExceptionHandler(NoResourceFoundException.class)
    ResponseEntity<ApiErrorResponse> notFound(NoResourceFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiErrorResponse.of("NOT_FOUND", "Không có đường dẫn /" + e.getResourcePath(), null));
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    ResponseEntity<ApiErrorResponse> method(HttpRequestMethodNotSupportedException e) {
        return ResponseEntity.status(HttpStatus.METHOD_NOT_ALLOWED)
                .body(ApiErrorResponse.of("HTTP_ERROR", "Phương thức " + e.getMethod() + " không được hỗ trợ.", null));
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ApiErrorResponse> other(Exception e) {
        log.error("Lỗi không lường trước", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiErrorResponse.of("INTERNAL_ERROR", "Lỗi trong backend.", null));
    }

    /** Cùng dạng details của INVALID_PARAM bên FastAPI: {"errors": [{"loc": [...], "msg": "..."}]}. */
    private static ResponseEntity<ApiErrorResponse> invalid(String where, String name, String msg) {
        Map<String, Object> details = Map.of("errors", List.of(Map.of("loc", List.of(where, name), "msg", msg)));
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(ApiErrorResponse.of("INVALID_PARAM", "Tham số không hợp lệ.", details));
    }
}
