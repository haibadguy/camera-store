# Giải thích cho hệ thống cuối (LightGCN + mặt nạ QĐ 4-9) — kế hoạch đăng ký trước

- Viết 16/10/2026 tối, nhánh `nam/cakg-v2`, **chưa chạy, chờ Nam duyệt**. Bối cảnh: CaKG-Rec v2 không qua DỪNG 2 (`docs/reviews/cakg_v2_plan.md` mục 11), nên hệ thống cuối là **LightGCN + mặt nạ QĐ 4-9** (checkpoint nội dung 5, `ai/config/n5_final.toml`, 3 seed).
- Phạm vi: **chỉ đo phần giải thích và độ trễ**. Không chấm lại độ chính xác, không chọn mô hình, không đổi số test nào đã có.

## 1. Số đã có (không đo lại)

| Đại lượng | LightGCN + mặt nạ, test lần 1 (TB ± ĐLC 3 seed) | Nguồn |
|---|---|---|
| PC@10 / PC_ngắn@10 / PC_mọi_sp@10 | 0,3933 ± 0,0109 / 0,8908 ± 0,0030 / 0,0864 ± 0,0030 | `results/cakg/test_final_20261015/summary_test_20261015_183745.md` mục 4 |
| PC@5 / PC_ngắn@5 | 0,3000 ± 0,0146 / 0,9245 ± 0,0022 | như trên |
| Faithfulness / C9 | **chưa có** (`08_explain.py` chỉ chạy cho CaKG-Rec) | — |
| Độ trễ | **chưa có** (`08b_latency.py` chỉ chạy cho CaKG-Rec seed 1) | — |
| Kiểm "0 lỗi sự kiện" của câu giải thích | **chưa có** cho LightGCN | — |

PC chỉ phụ thuộc đồ thị và top-10 (có đường hay không), không phụ thuộc cách chọn b*, nên dùng lại; script tính lại từ top-10 đã lưu và phải **trùng** mảng `test_mat_na_qd49_pc_counts_at*.npy` (kiểm, không phải số mới).

## 2. Ví dụ trước

Người u có Nikon D750 và D500 (cả hai lắp được ống l = Nikon 70-200). LightGCN không có kênh phần cứng nên không có "đóng góp từng thân" như CaKG-Rec (công thức 24). Quy tắc dưới đây chọn thân có biểu diễn hành vi gần l nhất: e_D750ᵀe_l = 1,2, e_D500ᵀe_l = 0,4 → **b\* = D750**. Câu: "Gợi ý Nikon 70-200 vì ống này lắp trực tiếp được trên D750 bạn đã mua (ngàm Nikon F), và phù hợp chụp thể thao / chim …".
Phản thực tế: bỏ cạnh (u, D750) khỏi đồ thị train, lan truyền lại LightGCN (cùng tham số, không huấn luyện lại), chấm lại u: l rơi khỏi top-10 → tính là "cần thiết". Đối chứng: làm y hệt với D500.

## 3. Quy tắc (cố định, không dò)

- **Đường** như thiết kế (23): u –owns→ b\* –ρ→ l –suitable_for→ c\*, ρ ∈ {compatible_with, crops_sensor}; chỉ cho ống trong top-10 **sau mặt nạ** của người có thân; mẫu câu và kiểm sự kiện như `eval_cakg` (thiết kế khối 8).
- **b\*** = argmax_{b ∈ B_u, M_bl = 1} e_bᵀe_l (embedding cuối của LightGCN cùng seed); hòa: iid nhỏ hơn. **Lý do:** (i) chỉ dùng đại lượng có sẵn trong mô hình, không huấn luyện thêm; (ii) cùng vai trò với cách chọn của CaKG-Rec (h_bᵀh_l) nhưng trên kênh duy nhất LightGCN có; nghĩa đọc được: "người mua b thường mua l"; (iii) **không** dùng chính phép bỏ cạnh để chọn b\*, tránh bẫy "đo bằng đúng cái đã dùng để chọn" mà Red Team lần 1 mục 3.5 đã chỉ ra với ΔS. Không chọn "thân đánh giá gần nhất" vì không liên quan gì tới điểm của mô hình.
- **c\*** = nhãn mục đích của l; ống có ≥ 2 nhãn: nhãn đầu theo thứ tự nút `usecase` trong `kg_node_index.json` (cố định). LightGCN không có cạnh `suitable_for` → c\* **không** ảnh hưởng điểm; câu giải thích phải coi vế này là **sự kiện của đồ thị, không phải lý do của gợi ý** (ghi rõ trong báo cáo).

## 4. Phép đo

1. **Kiểm sự kiện:** mọi câu cho mọi ống trong top-10 sau mặt nạ của người có thân, 3 seed: số lỗi phải = 0.
2. **Faithfulness** (như thiết kế (26), làm rõ 15/10): 𝒮 = cặp (u, l) có đường đủ 3 bước trong top-10 test **đã lưu** (`results/cakg/test_final_20261015/lightgcn_s{1,2,3}/test_mat_na_qd49_top20_full.npy`, kiểm sha256 với `result.json`), tối đa 2.000 cặp / seed, chọn bằng seed 20261014; 3 seed, báo riêng từng seed.
   - Phản thực tế: bỏ cạnh (u, b\*) khỏi ma trận kề train (chuẩn hóa lại bậc), lan truyền lại 3 lớp, chấm lại **chỉ người u**, ứng viên và mặt nạ như lúc chấm test (mặt nạ giữ nguyên vì quyền sở hữu thân không đổi). Cạnh (b\*, l) và (l, c\*) không có trong đồ thị của LightGCN nên không bỏ được: ghi rõ.
   - FS_PN@10 = tỉ lệ cặp l rơi khỏi top-10; ΔS = điểm giảm (mô tả). Tách theo số thân lắp được của u (1 / ≥ 2), như Red Team mục 3.5.
   - **C9-LG** (so sánh duy nhất): FS_PN@10(bỏ b\*) − FS_PN@10(bỏ b' lấy đều trong các thân khác của u có M_b'l = 1), trên các cặp có b'; bootstrap theo cặp, B = 2.000, seed 20261009; < 30 cặp có b' thì chỉ mô tả. Không giả định chiều.
   - Kiểm GPU không tất định: chấm lại **không bỏ gì** cho mọi cặp; cặp mà l không còn trong top-10 khi chấm lại được đếm, báo và loại.
3. **Độ trễ** (như `08b_latency.py`, seed 1): một yêu cầu = điểm 27.940 sản phẩm từ embedding đã tính sẵn + bỏ item train + mặt nạ + top-10 + dựng đường và câu cho các ống trong top-10; 1.000 người (seed 20261014), 50 lần khởi động không tính; GPU (có `synchronize`) và CPU; p50 / p95 / p99 / max; báo riêng thời gian tính sẵn embedding, đỉnh VRAM, thông tin máy. Không gồm HTTP / FastAPI / Spring Boot.

## 5. Cài và chạy (sau khi Nam duyệt)

- Script mới `ai/pipeline/09_explain_lightgcn.py` (dùng lại `eval_cakg`: `PathContext`, mẫu câu, `verify_explanation`, `pc_from_top`; `eval_05.full_rank`), kiểm thử dựng tay (ví dụ mục 2; bỏ cạnh của người không có thân trong top-10 → không có cặp; bỏ "không gì" → FS = 0), commit, thử trên **val**, rồi chạy trên test đã lưu **một lần** (cây sạch, cờ `--allow-test`). Kết quả `results/final_system/explain_<ngày>/`, log tên mới; commit trước khi phân tích.
- Ước tính: Faithfulness ~6.000 lần lan truyền lại (vài ms mỗi lần trên GPU) + chấm một người → ước tính dưới 15 phút (chưa đo); độ trễ vài phút.

## 6. Hạn chế biết trước

- b\* theo e_bᵀe_l là một quy tắc giải thích **sau** (post-hoc), không phải phân rã chính xác điểm của LightGCN.
- Vế mục đích (c\*) không thể trung thực với LightGCN (không có trong đồ thị của mô hình).
- Test top-10 đã dùng ở lần 1 để báo PC; phép đo này dùng lại cùng top-10, không phải tập mới.
