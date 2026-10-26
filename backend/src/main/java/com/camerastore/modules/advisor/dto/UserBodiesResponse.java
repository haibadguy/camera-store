package com.camerastore.modules.advisor.dto;

import java.util.List;

/** Phản hồi /users/{id}/bodies (hợp đồng mục 6.1): các thân máy dùng cho mặt nạ và giải thích. */
public record UserBodiesResponse(int userId, String exclude, int nHistoryItems, int nBodies, List<OwnedBody> bodies,
                                 int nLensesBlocked) {

    /** source: thân nằm ở train / val / test của lịch sử. */
    public record OwnedBody(int itemId, String asin, String title, String mount, String khung, boolean mayPhim,
                            boolean inMatrix, int nLensesM1, String source) {}
}
