package com.camerastore.modules.advisor.dto;

/** Phản hồi /health của FastAPI (hợp đồng mục 3). */
public record HealthResponse(String status, String model, int seed, String bestPtSha256, String embeddingsSha256,
                             String device, int nUsers, int nItems, UsersWithBodies nUsersWithBodies,
                             double startupS, String contractVersion) {

    public record UsersWithBodies(int train, int allHistory) {}
}
