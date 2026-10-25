package com.camerastore.modules.advisor.dto;

/** Thông tin ngắn của một sản phẩm (dùng trong mask.blocked_in_topk_before_mask, compat.body / compat.lens). */
public record ItemBrief(int itemId, String asin, String title, String type, String typeLabel) {}
