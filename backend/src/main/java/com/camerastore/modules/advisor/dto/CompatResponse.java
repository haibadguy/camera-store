package com.camerastore.modules.advisor.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * Phản hồi /compat (hợp đồng mục 6.2). level, rule_id, m, ... có thể null (vẫn ghi ra JSON); reason chỉ có khi
 * thân / ống không có đúng một ngàm hoặc ống không có trong M nên bỏ hẳn trường khi null, đúng như FastAPI.
 */
public record CompatResponse(ItemBrief body, ItemBrief lens, String bodyMount, String lensMount, String bodyKhung,
                             String lensKhung, boolean bodyFilm, boolean lensUncertain, String level,
                             String levelLabel, String ruleId, String ruleNote, Boolean cropUnknown, boolean inMatrix,
                             Integer m, @JsonInclude(JsonInclude.Include.NON_NULL) String reason,
                             String qd49IfOnlyThisBody) {}
