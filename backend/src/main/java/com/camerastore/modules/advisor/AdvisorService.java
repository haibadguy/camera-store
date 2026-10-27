package com.camerastore.modules.advisor;

import com.camerastore.modules.advisor.dto.CompatResponse;
import com.camerastore.modules.advisor.dto.HealthResponse;
import com.camerastore.modules.advisor.dto.ItemDetail;
import com.camerastore.modules.advisor.dto.RecommendResponse;
import com.camerastore.modules.advisor.dto.UserBodiesResponse;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Service;

/**
 * Nghiệp vụ tư vấn: chọn điểm cuối FastAPI và tham số cho mỗi yêu cầu của React.
 *
 * <p>Hiện chỉ chuyển tiếp (chưa có database / đăng nhập, chờ cô chốt chương 3). Đây là chỗ sẽ thêm nghiệp vụ sau
 * này: ánh xạ tài khoản demo sang user_id có sẵn (hợp đồng hạn chế 1), nối giá / ảnh / tồn kho theo asin (hạn chế 7),
 * danh sách dự phòng khi FastAPI lỗi (mục 8). Không kiểm lại tham số (k trong 1..50, exclude, user_id trong dữ liệu):
 * FastAPI là nơi kiểm duy nhất, lỗi của nó được chuyển tiếp nguyên dạng.
 */
@Service
public class AdvisorService {
    private final ModelServiceClient modelService;

    public AdvisorService(ModelServiceClient modelService) {
        this.modelService = modelService;
    }

    public RecommendResponse recommend(BigInteger userId, BigInteger k, String exclude) {
        return modelService.get("/recommend", params("user_id", userId, "k", k, "exclude", exclude),
                RecommendResponse.class);
    }

    public ItemDetail item(BigInteger itemId) {
        return modelService.get("/items/" + itemId, Map.of(), ItemDetail.class);
    }

    public UserBodiesResponse userBodies(BigInteger userId, String exclude) {
        return modelService.get("/users/" + userId + "/bodies", params("exclude", exclude), UserBodiesResponse.class);
    }

    public CompatResponse compat(BigInteger bodyId, BigInteger lensId) {
        return modelService.get("/compat", params("body_id", bodyId, "lens_id", lensId), CompatResponse.class);
    }

    public HealthResponse health() {
        return modelService.get("/health", Map.of(), HealthResponse.class);
    }

    /** Map giữ thứ tự, cho phép giá trị null (tham số null thì ModelServiceClient không gửi). */
    private static Map<String, Object> params(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i < kv.length; i += 2) {
            m.put((String) kv[i], kv[i + 1]);
        }
        return m;
    }
}
