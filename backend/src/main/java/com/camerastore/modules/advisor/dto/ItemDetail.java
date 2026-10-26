package com.camerastore.modules.advisor.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/**
 * Phản hồi /items/{id} (hợp đồng mục 5). focalMm, maxApertureF, khung, mountSource có thể null (vẫn ghi ra JSON);
 * nLensesM1 chỉ có với thân máy nên bỏ hẳn trường khi null, đúng như FastAPI.
 */
public record ItemDetail(int itemId, String asin, String title, String type, String typeLabel, String mount,
                         String khung, boolean mayPhim, boolean mountUncertain, String mountSource, String categories,
                         boolean inMatrix, FocalRange focalMm, ApertureRange maxApertureF, List<String> usecases,
                         List<String> usecasesLabel,
                         @JsonInclude(JsonInclude.Include.NON_NULL) Integer nLensesM1) {

    public record FocalRange(Double min, Double max) {}

    public record ApertureRange(Double atMinFocal, Double atMaxFocal) {}
}
