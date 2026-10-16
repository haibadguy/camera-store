# CaKG-Rec v2 — chọn biến thể trên VAL (06v2_select.py)

Thư mục dò: `results\cakg\val_sweep_v2_20261016`; git 61921d5. Một seed (1) mỗi biến thể; LightGCN chấm lại 3 seed. Bootstrap ghép cặp B = 2000, seed 20261009.

| Mô hình | NDCG@20 trước mặt nạ | NDCG@20 mặt nạ | R@10 chỉ ống, lắp được (mặt nạ) | hiệu vs LightGCN + mặt nạ s1 [95%] | (a) | (b) |
|---|---|---|---|---|---|---|
| lens_gate | 0.04063 | 0.04062 | 0.3850 | +0.0077 [-0.0100; +0.0265] | đạt | đạt |
| loo_hu | 0.04049 | 0.04051 | 0.3827 | +0.0055 [-0.0122; +0.0222] | đạt | KHÔNG |
| body_hardneg | 0.03909 | 0.03912 | 0.2887 | -0.0885 [-0.1139; -0.0619] | KHÔNG | KHÔNG |
| LightGCN s1 | 0.04045 | 0.04044 | 0.3772 | | | |
| LightGCN s2 | 0.04040 | 0.04040 |  | | | |
| LightGCN s3 | 0.04054 | 0.04053 |  | | | |
| CaKG-Rec v1 s1 | 0.03973 | 0.03973 | 0.3949 | | | |

**Mô tả (không dùng để chọn)** — người có thân, top-10 trước mặt nạ, val:

| Mô hình | thân | ống | phụ kiện | thân cùng ngàm | R@10 người có thân | item có h | item không có h | NDCG@20 mặt nạ − LightGCN + mặt nạ s1 [95%] |
|---|---|---|---|---|---|---|---|---|
| lens_gate | 0.82 | 2.69 | 6.13 | 76.6% | 0.0557 | 0.1278 | 0.0402 | +0.00018 [-0.00027; +0.00063] |
| loo_hu | 0.92 | 2.63 | 6.11 | 78.5% | 0.0561 | 0.1300 | 0.0402 | +0.00007 [-0.00039; +0.00055] |
| body_hardneg | 0.34 | 2.19 | 6.92 | 4.4% | 0.0453 | 0.0748 | 0.0389 | -0.00133 [-0.00191; -0.00071] |
| LightGCN s1 | 0.87 | 2.47 | 6.30 | 77.2% | 0.0566 | 0.1268 | 0.0415 |  |
| LightGCN s2 | 0.92 | 2.43 | 6.31 | 78.0% | 0.0559 | 0.1192 | 0.0423 |  |
| LightGCN s3 | 0.87 | 2.45 | 6.34 | 77.7% | 0.0549 | 0.1203 | 0.0408 |  |
| CaKG-Rec v1 s1 | 3.40 | 1.82 | 4.58 | 93.5% | 0.0474 | 0.1241 | 0.0308 |  |

**Kết luận theo quy tắc đăng ký trước:** chọn biến thể lens_gate; bước tiếp: chạy seed 2, 3 (kế hoạch mục 4.3), kiểm điều kiện DỪNG 2
