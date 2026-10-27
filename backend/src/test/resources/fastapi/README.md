# Phản hồi thật của dịch vụ mô hình (FastAPI) dùng làm dữ liệu cho test

FastAPI giả lập trong test (`FakeModelService`) trả đúng các file này. Tất cả là phản hồi thật của dịch vụ seed 1
(`results/service/emb_s1_20261021`, hợp đồng 1.3, commit `3df7b48`), không sửa tay:

- `recommend_409.json`, `recommend_47.json`, `users_409_bodies.json`, `users_47_bodies.json`, `item_9022.json`
  (thân), `item_15485.json` (ống), `item_1154.json` (phụ kiện): chép từ `frontend/src/mock/`
  (sinh bởi `ai/service/export_mock.py`, `exclude=all_history`).
- `health.json`, `compat_*.json`, `error_*.json`: lấy ngày 26/10/2026 bằng `curl` tới
  `ai/service/run_service.py --emb-dir results/service/emb_s1_20261021 --port 8041`
  (log dịch vụ `results/service/logs/serve_fixture_backend_20261026_lan1.log`):
  - `/health`;
  - `/compat?body_id=9022&lens_id=13448` (incompatible, m = 0), `body_id=19071&lens_id=9696` (compatible_with, m = 1),
    `body_id=9022&lens_id=118` (ống "không chắc" ngàm: có mức, không có trong M, có `reason`),
    `body_id=9022&lens_id=105` (ống ngàm `khong_ro`: `level = null`, có `reason`);
  - lỗi: `/recommend?user_id=99999` (404), `/recommend?user_id=409&k=0` (422),
    `/compat?body_id=9696&lens_id=19071` (400).
- `error_user_not_found_huge.json` (`/recommend?user_id=99999999999999999999`, 404), `error_invalid_k_huge.json`
  (`/recommend?user_id=409&k=999999999999`, 422), `error_item_not_found_huge.json` (`/items/99999999999999999999`, 404):
  lấy ngày 28/10/2026 bằng `curl` tới `run_service.py` seed 1 cổng 8071 (commit `c16c7b1`; log dịch vụ để ngoài repo),
  cho test số nguyên vượt kiểu long (phản biện `E:\DATN\reviews\redteam_code_lan1.md` mục S2).
