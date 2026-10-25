package com.camerastore.modules.advisor;

import com.camerastore.modules.advisor.dto.CompatResponse;
import com.camerastore.modules.advisor.dto.HealthResponse;
import com.camerastore.modules.advisor.dto.ItemDetail;
import com.camerastore.modules.advisor.dto.RecommendResponse;
import com.camerastore.modules.advisor.dto.UserBodiesResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Điểm cuối cho React (/api/...). Cùng tên tham số và cùng dạng dữ liệu với dịch vụ mô hình
 * (docs/api_contract.md 1.3), chỉ thêm tiền tố /api. Lỗi trả theo định dạng lỗi chung (GlobalExceptionHandler).
 */
@RestController
@RequestMapping("/api")
public class AdvisorController {
    private final AdvisorService advisor;

    public AdvisorController(AdvisorService advisor) {
        this.advisor = advisor;
    }

    /** Vd /api/recommend?user_id=409&k=10. k, exclude không gửi thì FastAPI dùng mặc định (10, all_history). */
    @GetMapping("/recommend")
    public RecommendResponse recommend(@RequestParam("user_id") long userId,
                                       @RequestParam(value = "k", required = false) Integer k,
                                       @RequestParam(value = "exclude", required = false) String exclude) {
        return advisor.recommend(userId, k, exclude);
    }

    @GetMapping("/items/{id}")
    public ItemDetail item(@PathVariable("id") long itemId) {
        return advisor.item(itemId);
    }

    @GetMapping("/users/{id}/bodies")
    public UserBodiesResponse userBodies(@PathVariable("id") long userId,
                                         @RequestParam(value = "exclude", required = false) String exclude) {
        return advisor.userBodies(userId, exclude);
    }

    @GetMapping("/compat")
    public CompatResponse compat(@RequestParam("body_id") long bodyId, @RequestParam("lens_id") long lensId) {
        return advisor.compat(bodyId, lensId);
    }

    /** /health của FastAPI nguyên dạng nếu dịch vụ chạy; không chạy thì 503 MODEL_SERVICE_UNAVAILABLE. */
    @GetMapping("/health")
    public HealthResponse health() {
        return advisor.health();
    }
}
