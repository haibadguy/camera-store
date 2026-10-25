package com.camerastore.modules.advisor.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;

/**
 * Phản hồi /recommend (hợp đồng mục 4.2). Tên trường Java camelCase, JSON snake_case (spring.jackson
 * .property-naming-strategy), vd hasBodies -> has_bodies.
 */
public record RecommendResponse(int userId, int k, String exclude, boolean hasBodies, int nBodies,
                                List<RecommendedItem> items, Mask mask) {

    /** Một sản phẩm trong top-k. explanation = null khi không có giải thích (hạn chế 5). */
    public record RecommendedItem(int rank, int itemId, String asin, String title, String type, String typeLabel,
                                  double score, Explanation explanation) {}

    /** Giải thích theo đường u -> b* -> l (-> c*), mục 4.3. cStar có thể null. */
    public record Explanation(String text, List<PathNode> path, List<String> edges, int bStar, String rho,
                              String cStar, double bStarScore, String bStarSource, List<Integer> candidateBodies,
                              boolean verified, List<String> errors) {}

    /**
     * Một nút của đường: user {kind, id}, item {kind, role, item_id, asin, title, type, type_label},
     * usecase {kind, id, label}. Mỗi loại chỉ có một số trường nên bỏ trường null khi ghi JSON; id là số (user)
     * hoặc chuỗi (usecase) nên giữ dạng JsonNode.
     */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record PathNode(String kind, JsonNode id, String role, Integer itemId, String asin, String title,
                           String type, String typeLabel, String label) {}

    /** Mặt nạ QĐ 4-9: số ống bị chặn và các ống bị gỡ khỏi top-k. */
    public record Mask(String rule, int nLensesBlocked, int nBlockedInTopkBeforeMask,
                       List<ItemBrief> blockedInTopkBeforeMask) {}
}
