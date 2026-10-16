# CaKG-Rec v2 — kiểm DỪNG 2 trên VAL, 3 seed (lens_gate) (06v2_dung2.py)

git b789393; chỉ đọc mảng val đã lưu. Bootstrap ghép cặp B = 2000, seed 20261009; chỉ số từng người = trung bình 3 seed.

| Mô hình | seed | NDCG@20 trước mặt nạ | NDCG@20 mặt nạ | R@10 chỉ ống, lắp được (mặt nạ) | best epoch |
|---|---|---|---|---|---|
| lens_gate | 1 | 0.04063 | 0.04062 | 0.3850 | 280 |
| lens_gate | 2 | 0.04025 | 0.04026 | 0.3894 | 280 |
| lens_gate | 3 | 0.04050 | 0.04045 | 0.3927 | 300 |
| LightGCN + mặt nạ | 1 | | 0.04044 | 0.3772 | |
| LightGCN + mặt nạ | 2 | | 0.04040 | 0.3927 | |
| LightGCN + mặt nạ | 3 | | 0.04053 | 0.3827 | |

- (b') TB 3 seed NDCG@20 val sau mặt nạ: lens_gate 0.04044 vs LightGCN + mặt nạ 0.04046 -> **KHÔNG đạt** (mô tả: hiệu theo người -0.00002 [-0.00029; +0.00026])
- (a') nhóm lắp được (904 người), Recall@10 chỉ ống sau mặt nạ, TB 3 seed: 0.3890 vs 0.3842, hiệu +0.0048 [-0.0037; +0.0136] -> cận trên > 0: **đạt**

**Mô tả (không dùng để quyết)** — người có thân, top-10 trước mặt nạ, val:

| seed | thân | ống | phụ kiện | thân cùng ngàm | R@10 người có thân | item có h | item không có h |
|---|---|---|---|---|---|---|---|
| 1 | 0.82 | 2.69 | 6.13 | 76.6% | 0.0557 | 0.1278 | 0.0402 |
| 2 | 0.85 | 2.61 | 6.20 | 75.4% | 0.0572 | 0.1316 | 0.0411 |
| 3 | 0.86 | 2.60 | 6.22 | 76.4% | 0.0541 | 0.1230 | 0.0393 |

**Kết luận theo quy tắc đăng ký trước:** DỪNG 2: không đạt. Không chấm test lần 2. Hệ thống cuối = LightGCN + mặt nạ QĐ 4-9.
