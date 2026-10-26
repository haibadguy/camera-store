package com.camerastore.modules.advisor;

import com.camerastore.common.ApiException;
import com.camerastore.modules.advisor.dto.HealthResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * Gọi /health của FastAPI một lần lúc Spring khởi động xong (hợp đồng mục 3, 8) và ghi log. Không dừng Spring nếu
 * FastAPI chưa chạy: FastAPI cần ~12 s để lên, các yêu cầu sau đó sẽ gọi được; trong lúc chờ /api/* trả 503.
 */
@Component
public class ModelServiceStartupCheck {
    private static final Logger log = LoggerFactory.getLogger(ModelServiceStartupCheck.class);
    private final AdvisorService advisor;

    public ModelServiceStartupCheck(AdvisorService advisor) {
        this.advisor = advisor;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void checkModelService() {
        try {
            HealthResponse h = advisor.health();
            log.info("Dịch vụ mô hình sẵn sàng: status={}, seed={}, hợp đồng {}, best.pt sha256 {}",
                    h.status(), h.seed(), h.contractVersion(), h.bestPtSha256());
            if (!"1.3".equals(h.contractVersion())) {
                log.warn("Backend viết theo hợp đồng 1.3, dịch vụ mô hình báo {}", h.contractVersion());
            }
        } catch (ApiException e) {
            log.warn("Chưa gọi được dịch vụ mô hình lúc khởi động ({}). /api/* sẽ trả lỗi tới khi FastAPI chạy.",
                    e.getMessage());
        }
    }
}
