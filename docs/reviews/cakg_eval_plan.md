# Kế hoạch đánh giá CaKG-Rec (khung 2.5–2.6) — đăng ký trước

- Viết 14/10/2026, nhánh `nam/cakg-rec`, **trước khi cài CaKG-Rec / KGAT và trước khi huấn luyện bất kỳ mô hình mới nào**. Thiết kế mô hình: `docs/cakg_design.md` (gọi tắt "thiết kế", công thức (1)–(30)).
- Theo khuôn `docs/reviews/n5_eval_plan.md`. Mốc: commit chứa file này. Thay đổi trước khi chạy test ghi vào mục 13, commit riêng; sau khi chạy test không sửa kế hoạch.
- Các câu [HỎI] của thiết kế (HỎI 1–9) và của file này (HỎI 10–13) **chưa được Nam chốt**; chốt xong mới cài code.
- Số liệu trong file chỉ lấy từ log của `ai/survey/cakg/` (chỉ đọc; không huấn luyện) và từ kết quả nội dung 5 đã có:

| Script | Log |
|---|---|
| `ai/survey/cakg/dem_cakg.py` (chỉ đọc mảng **val**) | `ai/data/survey/cakg/run_dem_cakg_20261014_lan1.log` |
| `ai/survey/cakg/probe_cakg.py` (trọng số ngẫu nhiên, không `optimizer.step`) | `ai/data/survey/cakg/run_probe_cakg_20261014_lan1.log` |
| nội dung 5 (đã chạy test 09/10) | `results/n5/test_final_20261009/summary_test_20261009_125536.json` |

## 1. Ví dụ trước

Hai người dùng có thân, một người không:
- **u1** (EOS 80D). Item test: ống EF-S 10-18. LightGCN xếp ống này hạng 14; CaKG-Rec xếp hạng 6.
- **u2** (Sony a7 + Nikon D750). Item test: Nikon 200-500. Hạng 3 ở cả hai mô hình.
- **u3** (không có thân). Item test: thẻ nhớ. Hạng 40 ở cả hai.

**Recall@10** (mỗi người 1 item test, nên = Hit@10): LightGCN (0 + 1 + 0)/3 = 0,333; CaKG-Rec (1 + 1 + 0)/3 = 0,667. Hiệu = +0,333.

**Bootstrap ghép cặp:** lấy lại 3 người có hoàn lại, ví dụ {u1, u1, u3}. Trên mẫu này LightGCN = 0, CaKG-Rec = 2/3, hiệu = +0,667. Lặp 2.000 lần, lấy phân vị 2,5% và 97,5% của các hiệu → khoảng tin cậy 95%. "Ghép cặp" nghĩa là hai mô hình luôn được tính trên **cùng** mẫu người dùng.

**CVR trước / sau mặt nạ** (thiết kế khối 7). Top-10 trước mặt nạ của u2 có 1 ống Canon EF (cả hai thân M = 0) trong 4 ống chấm được → CVR_strict trước mặt nạ = 1/4. Mặt nạ (15) chặn ống đó → CVR sau mặt nạ = 0, **do cách dựng**. Chỉ số **trước** mặt nạ mới cho biết mô hình có học được ràng buộc hay không.

## 2. Đối tượng được đo

| Thành phần | Phiên bản |
|---|---|
| train / val / test, âm mẫu 1+99 | như `n5_eval_plan.md` mục 3.1 (sha256 không đổi) |
| đồ thị, M, U, loại sản phẩm | `ai/data/kg/` như nội dung 5 (`kg_hetero.pt` `abf149b5…`) |
| đồ thị con phần cứng H | dựng khi nạp từ `kg_edges_*.csv` (thiết kế khối 2), không ghi file mới vào `ai/data/kg/`; script in số nút / cạnh từng quan hệ, phải khớp `run_probe_cakg_20261014_lan1.log` (H_lõi: 1.822 nút, 186.338 cạnh, 14 quan hệ) |
| CVR, kịch bản, full ranking, hòa điểm π | `eval_05.py` (thêm chấm trước / sau mặt nạ, CVR_relaxed; thiết kế mục 12) |

Mọi lần chạy mới ghi sha256 của đầu vào như `train_05.run`.

## 3. Mô hình được so sánh

| Mô hình | Huấn luyện mới? | Ghi chú |
|---|---|---|
| Popularity, Popularity-MountAware | không | dùng lại mảng test 09/10 |
| LightGCN | không | dùng lại 3 checkpoint / mảng test 09/10 (λ = 1e-3, chưa chắc hội tụ) |
| **LightGCN + mặt nạ (15)** | không | **mới**: chấm lại 3 checkpoint LightGCN trên test với mặt nạ QĐ 4-9 (thiết kế Đ10) |
| R-GCN | không | dùng lại 3 checkpoint / mảng test 09/10 |
| **KGAT** | **có** | thiết kế khối 9 |
| **CaKG-Rec** (đầy đủ, mặt nạ (15)) | **có** | thiết kế khối 1–7; số chính báo **sau** mặt nạ, kèm số trước mặt nạ của cùng mô hình |
| Ablation (mục 6) | có (2 biến thể) | |

Dùng lại kết quả nội dung 5 là hợp lệ vì cùng train / val / test, cùng `eval_05`, cùng quy tắc hòa π. Test của các mô hình đó **đã chấm một lần** (09/10); chấm lại LightGCN có mặt nạ là phép chấm test **mới**, đăng ký ở đây trước khi chạy.

## 4. Siêu tham số và quy trình

### 4.1. Siêu tham số

| Mô hình | Cố định (nguồn: thiết kế) | Dò trên val (seed 1) |
|---|---|---|
| CaKG-Rec | kênh hành vi như LightGCN chốt (d 64, L 3, lr 1e-3, batch 2048, λ2 = 1e-3); RGAT 2 lớp WIRGAT, 1 đầu, d 64, W_0, không dropout; gộp kênh h' = 64; τ = 0,2; H_lõi | **λ1 ∈ {0,01; 0,1; 1,0}** (3 lần chạy) |
| KGAT | d 64, [64, 32, 16], Bi-Interaction, batch 1024 / 2048, L2 1e-5, message dropout 0,1, attention cập nhật 1 lần / epoch, Xavier | **lr ∈ {1e-3; 1e-4}** (2 lần chạy) |

- Ngân sách như QĐ 5-5: tối đa **300 epoch**, chấm NDCG@20 val **mỗi 10 epoch**, dừng sau **5 lần chấm** không tăng; chạm 300 epoch thì ghi **"chưa chắc hội tụ"**. Cùng ngân sách với LightGCN để so công bằng (LightGCN cũng chạm 300 epoch).
- Chỉ số chọn: **NDCG@20 full ranking trên val, trước mặt nạ** (như QĐ 5-6; vòng huấn luyện `train_05.run` không đổi). Script in thêm NDCG@20 val sau mặt nạ để theo dõi, không dùng để chọn.
- Giá trị tốt nhất nằm ở biên lưới thì ghi lại, **không mở rộng lưới** (như nội dung 5).
- Khởi tạo từ đầu (Xavier) cho mọi mô hình mới, không lấy embedding của LightGCN đã huấn luyện **[HỎI 10]**.

### 4.2. Quy trình (như `n5_eval_plan` mục 7.2)

1. Cài code, viết kiểm thử dựng tay (mục 11), commit.
2. Chạy thử 1–3 epoch (đo thời gian / VRAM thật), không chấm test.
3. **Dò trên val, seed 1**: CaKG-Rec 3 lần, KGAT 2 lần.
4. Ghi cấu hình chốt vào `ai/config/cakg_final.toml`, **commit trước khi chạy test**.
5. Chạy cấu hình chốt với seed 2, 3; chạy ablation (mục 6) seed 1–3 (hoặc theo phương án cắt, mục 9).
6. **Chạy test một lần** bằng một script (`06_test_final.py`, chưa viết) cho mọi mô hình ở mục 3 × mọi seed; script ghi commit và sha256 của `cakg_final.toml`, dừng nếu cây git không sạch.
7. Ghi số vào CHANGELOG / STATUS và commit **trước** khi phân tích ca sai hay chạy thêm.
8. Phát hiện lỗi script sau khi chạy test: sửa, chạy lại, **báo cả hai lần** và lý do.

### 4.3. Seed

3 seed {1, 2, 3} cho mọi mô hình học. Báo trung bình ± độ lệch chuẩn mẫu (ddof = 1). GPU không tất định (đã thấy ở R-GCN): không cam kết trùng sha256 khi chạy lại.

## 5. Chỉ số

- **Full ranking** (kết quả chính): Recall@K, NDCG@K, Hit@K, K ∈ {5, 10, 20}, trên 67.661 người dùng; cách tính như `n5_eval_plan` mục 3 (Recall@K = Hit@K vì mỗi người 1 item test; script kiểm).
- **CVR_strict@K** (thiết kế (18)) **trước** và **sau** mặt nạ; **CVR_relaxed@K** theo R1 và R2 (thiết kế (19)–(22)), trước và sau mặt nạ. Báo kèm số người được tính, số ống chấm được, số vi phạm, số ống được nới.
- **Kịch bản** "ống cho người đã có thân" (1.060 người test: 762 lắp được, 282 không lắp được, 16 không phán được): số chính chỉ ống (1.339), số phụ toàn catalog (QĐ 5-2); Recall / NDCG @K và CVR theo nhóm.
- **Biến thể mặt nạ ∃b (thiết kế (16))**: chỉ báo số mô tả cho CaKG-Rec và LightGCN (Recall@10 mọi người, kịch bản theo nhóm; số người mất item test). Không thuộc so sánh đăng ký.
- **Path Coverage**: PC@K, PC_ngắn@K, PC_mọi_sp@K (thiết kế (25)), K ∈ {5, 10}, sau mặt nạ, người có thân.
- **Faithfulness**: FS_PN@10, ΔS và đối chứng ngẫu nhiên (thiết kế (26)), trên tối đa 2.000 cặp (u, l) có đường giải thích trong top-10 test, chọn bằng seed 20261014.
- **Sampled 1+99** (số phụ, khung 2.6): Hit@K, NDCG@K như nội dung 5; báo thứ tự các mô hình theo full ranking và theo sampled ở K = 5, 10, 20; chỉ mô tả (không kiểm định).
- **Loại sản phẩm trong top-10** (ống / thân / phụ kiện / khác), để thấy kênh phần cứng có kéo lệch top-K về ống không (rủi ro ở thiết kế khối 4).
- **Tài nguyên**: thời gian / epoch, VRAM đỉnh, độ trễ một yêu cầu (mục 10).

## 6. Ablation (khung 2.6)

| Ablation (khung) | Biến thể | Huấn luyện mới? | Đọc ở |
|---|---|---|---|
| Hai kênh / một kênh | CaKG-Rec so với **R-GCN** (một kênh: hành vi + tri thức trong một đồ thị) và **LightGCN** (một kênh hành vi) | không (baseline có sẵn) | C1, C5 |
| Có / không L_comp | **CaKG-Rec, λ1 = 0** (giữ kênh phần cứng, bỏ L_comp) | có | C4 |
| Có / không mặt nạ | cùng mô hình, chấm trước và sau mặt nạ | không | C3, C6, cột "trước mặt nạ" |
| Có / không `suitable_for` | **CaKG-Rec bỏ quan hệ `suitable_for` khỏi H** (12 quan hệ, 4 nút mục đích không còn cạnh) | có | C8 |

- Biến thể dùng **đúng cấu hình chốt** của CaKG-Rec (λ1 chốt, trừ biến thể λ1 = 0), không dò lại.
- Bỏ `suitable_for` làm đường giải thích đủ 3 bước không còn: PC của biến thể này chỉ báo PC_ngắn.
- **Thăm dò, không đăng ký** (chỉ làm nếu còn giờ GPU, ghi rõ là thăm dò): H_pk (HỎI 2); h_u gồm cả ống (HỎI 4); kênh phần cứng dùng R-GCN thay RGAT (bài RGAT không chắc hơn R-GCN, thiết kế khối 2); gộp thẳng không cổng.

## 7. Khoảng tin cậy

Như `n5_eval_plan` mục 8: bootstrap theo người dùng, **ghép cặp**, B = 2.000, seed 20261009, khoảng 95% theo phân vị; chỉ số từng người của mô hình học = trung bình 3 seed của người đó; CVR là tỷ số micro, khoảng tin cậy tính trên tổng vi phạm và tổng ống chấm được cộng qua 3 seed; kịch bản bootstrap riêng trong từng nhóm. FS: bootstrap trên các cặp (u, l) của 𝒮.

## 8. So sánh đăng ký trước (K = 10)

| # | So sánh | Chỉ số | Tập | Vai trò |
|---|---|---|---|---|
| **C1** | CaKG-Rec (mặt nạ) − LightGCN | Recall@10, NDCG@10 | mọi người dùng | chính |
| **C2** | CaKG-Rec (mặt nạ) − LightGCN + mặt nạ | Recall@10, NDCG@10 | người có thân; mọi người dùng | **chính** (tách tác dụng kênh phần cứng khỏi mặt nạ) |
| **C3** | CaKG-Rec (trước mặt nạ) − LightGCN (trước mặt nạ) | CVR_strict@10 | người có thân | **chính** (mô hình có học ràng buộc không) |
| C4 | CaKG-Rec − CaKG-Rec λ1 = 0 (cả hai trước mặt nạ) | CVR_strict@10; Recall@10 | người có thân; mọi người dùng | phụ (đóng góp L_comp) |
| C5 | CaKG-Rec (mặt nạ) − R-GCN | Recall@10, NDCG@10 | mọi người dùng | phụ (hai kênh / một kênh) |
| **C6** | kịch bản chỉ ống: CaKG-Rec (mặt nạ) − LightGCN + mặt nạ; CaKG-Rec (mặt nạ) − LightGCN | Recall@10 | nhóm lắp được (762); nhóm không lắp được (282) | **chính** (khung 2.6, "kịch bản người có thân") |
| C7 | KGAT − LightGCN | Recall@10, NDCG@10 | mọi người dùng | phụ |
| C8 | CaKG-Rec − CaKG-Rec bỏ `suitable_for` | Recall@10; PC_ngắn@10 | mọi người dùng; người có thân | phụ |
| C9 | FS_PN@10: đường giải thích − đường ngẫu nhiên | FS_PN@10 | 𝒮 (có đối chứng) | phụ |

- Hiệu được coi là khác 0 khi khoảng 95% không chứa 0. **Không giả định chiều** (CaKG-Rec có thể kém hơn); kết quả nào cũng báo.
- Không hiệu chỉnh đa so sánh (như nội dung 5); C1, C2, C3, C6 là **chính**, các so sánh khác là phụ; mọi so sánh ngoài bảng là "thăm dò". Số khoảng tin cậy: 20 (đếm theo chỉ số × tập × cặp so sánh).
- Dự kiến (chưa kiểm chứng): vì CaKG-Rec chỉ khác LightGCN trên 15,3% người × 9,30% sản phẩm (thiết kế khối 3), **C1 có thể không khác 0**. Đây không phải lý do đổi so sánh sau khi xem số.
- Nhóm "không lắp được" (282): với mặt nạ (15), Recall@10 chỉ ống **chắc chắn = 0** (item test bị chặn), giống MountAware ở S5. Báo số này để thấy cái giá của mặt nạ, không coi là kết quả học.

## 9. Tài nguyên và ước tính giờ GPU

### 9.1. Đo thử (trọng số ngẫu nhiên, `run_probe_cakg_20261014_lan1.log`)

| Phần | ms / bước | / epoch | Đỉnh GPU |
|---|---:|---:|---:|
| CaKG-Rec (H_lõi), batch 2048, 225 bước | 95 | 21,4 s | 600 MiB |
| CaKG-Rec (H_pk) | 97 | 21,8 s | 657 MiB |
| riêng RGAT + L_comp | 19,9 | — | 466 MiB |
| `RGATConv` của PyG, **một lớp** trên H_lõi (không dùng) | 1.302 | — | **8.985 MiB** |
| KGAT, attention cố định trong epoch, CF batch 1024 (450 bước) | 68 | 0,5 phút | 1.347 MiB |
| KGAT, attention có gradient mỗi bước | 159 | 1,2 phút | 3.284 MiB |
| KGAT, bước TransR batch 2048 (546 bước) | 6,0 | 3,3 s | 251 MiB |
| tính biểu diễn mọi người / sản phẩm (CaKG-Rec, eval) | 28 | — | 312 MiB |

Lúc đo RAM trống 7.557 MiB, tiến trình dùng khoảng 1,66 GB RAM. Vừa GPU 6 GB với dư lớn.

### 9.2. Ước tính (tính tay từ 9.1)

Hệ số thực tế / probe lấy từ LightGCN nội dung 5: 13,7 s thật (`median_sec_per_epoch`) / 12,5 s probe ≈ 1,1 (gồm lấy âm mẫu, xáo, chấm val).
- CaKG-Rec: 21,4 s × 1,1 ≈ 23,5 s / epoch → 300 epoch ≈ **2,0 giờ / lần**.
- KGAT (attention 1 lần / epoch): (30,6 + 3,3) s × 1,1 ≈ 37 s / epoch → 300 epoch ≈ **3,1 giờ / lần** (nếu chọn attention có gradient: ≈ 6,9 giờ / lần).

| Việc | Lần chạy | Giờ / lần (xấu nhất) | Tổng |
|---|---:|---:|---:|
| CaKG-Rec dò λ1 (seed 1) | 3 | 2,0 | 6,0 |
| CaKG-Rec chốt, seed 2, 3 | 2 | 2,0 | 4,0 |
| Ablation λ1 = 0, seed 1–3 | 3 | 2,0 | 6,0 |
| Ablation bỏ `suitable_for`, seed 1–3 | 3 | 2,0 | 6,0 |
| KGAT dò lr (seed 1) | 2 | 3,1 | 6,2 |
| KGAT chốt, seed 2, 3 | 2 | 3,1 | 6,2 |
| Chạy thử, chấm test, LightGCN + mặt nạ, Faithfulness (2.000 cặp × ~30 ms), độ trễ | — | — | < 1 |
| **Tổng xấu nhất** | 15 | | **≈ 35 giờ** |

Dừng sớm có thể làm giảm, nhưng LightGCN đã chạm 300 epoch nên lấy mức xấu nhất. **Chưa kiểm chứng** 300 epoch đủ hội tụ.

### 9.3. Có vừa 1–2 tuần không

- GPU: ~35 giờ ≈ 4 đêm chạy (~9 giờ / đêm). Thời gian người (ước lượng, chưa kiểm chứng): cài code 3–4 ngày, kiểm thử dựng tay 1 ngày, phân tích + viết 2 ngày → **khoảng 9–10 ngày làm việc: vừa 2 tuần, không vừa 1 tuần**. Cô dặn xong chương 1–2 mới đi tiếp chương 3, nên chương 1 phải viết song song lúc GPU chạy.
- **Đề xuất cắt nếu thiếu thời gian** (theo thứ tự) **[HỎI 11]**:
  1. Hai ablation (λ1 = 0, bỏ `suitable_for`) chỉ **seed 1** → bớt 8 giờ (còn ~27 giờ). C4, C8 khi đó không có độ lệch giữa seed, ghi hạn chế.
  2. KGAT **không dò lr** (dùng 1e-3, thuộc lưới của bài) → bớt 3,1 giờ.
  3. λ1 chỉ dò {0,1; 1,0} → bớt 2 giờ.
  Cắt cả 3: ≈ 22 giờ GPU (~2,5 đêm). Không cắt: số seed của CaKG-Rec chốt và KGAT chốt (cần 3 seed cho C1–C3, C7).

## 10. Đo độ trễ và VRAM

- **VRAM huấn luyện:** `torch.cuda.reset_peak_memory_stats()` đầu lần chạy; sau mỗi epoch ghi `max_memory_allocated` và `max_memory_reserved` vào lịch sử; `result.json` thêm `peak_vram_allocated_mib`, `peak_vram_reserved_mib` (hiện `train_05` chưa ghi). Báo đỉnh của lần chạy chốt, cả 3 seed.
- **Thời gian huấn luyện:** trung vị giây / epoch (đã có trong `result.json`), tổng giờ đến epoch tốt nhất.
- **Độ trễ suy luận một yêu cầu** (khung 2.6): script riêng chạy **sau** khi chấm test, trên checkpoint chốt seed 1:
  - tính sẵn biểu diễn mọi người / sản phẩm một lần (báo thời gian riêng);
  - với 1.000 người dùng test chọn ngẫu nhiên (seed 20261014), đo một yêu cầu = điểm 27.940 sản phẩm + bỏ item train + mặt nạ (15) + top-10 + dựng đường và câu giải thích cho các ống trong top-10;
  - khởi động 50 yêu cầu không tính; `torch.cuda.synchronize()` trước khi bấm giờ trên GPU; đo trên **GPU và CPU**; báo p50, p95, p99, max;
  - không tính HTTP / FastAPI / Spring Boot (đo ở nội dung 10).
  - Probe (biểu diễn ngẫu nhiên): GPU p50 1,36 ms / p95 1,67 ms; CPU p50 0,47 ms / p95 0,63 ms (`run_probe_cakg_20261014_lan1.log`). Lần nháp trước cho GPU 0,64 / 0,94 ms, CPU 0,75 / 1,11 ms: dao động giữa các lần đo lớn so với giá trị, nên báo cả máy, tải nền và số lần lặp.
- Thông tin máy ghi kèm: GPU, driver / CUDA, torch, RAM trống lúc đo.

## 11. Kiểm thử trước khi chạy (dựng tay)

- Mọi ví dụ của thiết kế (số ở `run_vidu_tinh_tay_20261014_lan2.log`) chạy qua code thật ra đúng số: LightGCN 1 lớp; một lớp RGAT; gộp kênh có cổng; L_comp (cặp U không vào mẫu số); L_total; mặt nạ (15) và (16) trên người hai hệ máy; phân rã đóng góp từng thân (24); attention KGAT.
- `RGATLayer` trùng `RGATConv` (cùng trọng số) với sai số < 1e-5 (đã thấy 1,91e-06 trong probe).
- Đồ thị con H: số cạnh từng quan hệ khớp bảng ở thiết kế khối 2; không có nút người dùng; không có cạnh `ngam_khong_chac`.
- Cổng: với người không có h_u, điểm của mọi sản phẩm = e_uᵀe_i.
- Mặt nạ (15) trùng `eval_05.certain_violation_mask` từng ô; CVR_strict sau mặt nạ = 0 trên dữ liệu thật (cả CaKG-Rec lẫn LightGCN + mặt nạ).
- CVR_relaxed: ca uid 2465 trên val (ống iid 19161): strict vi phạm, R1 vi phạm, R2 không vi phạm; tổng trên LightGCN s1 val khớp `run_dem_cakg_20261014_lan1.log` (3.005 / 61 / 109).
- PC: trên top-10 val của LightGCN s1 (trước mặt nạ), số đường ngắn / đủ khớp log (20.436 / 9.095 trên 23.441 ống chấm được).
- Faithfulness: với một "mô hình" chỉ có kênh hành vi (β_h = 0), FS_PN = 0 và ΔS = 0.
- Mọi câu giải thích sinh ra: mọi cạnh được nhắc có trong đồ thị (kiểm tự động trên mọi câu của test).
- Bootstrap: hai mô hình giống hệt → hiệu = 0.

## 12. Đầu ra và log

- Kết quả ghi `results/cakg/<nhãn lần chạy>/`; log tên mới kèm ngày và nhãn; không ghi đè `results/n5/`.
- Mỗi lần chạy lưu: cấu hình, commit, sha256 đầu vào, đường học, checkpoint tốt nhất, VRAM đỉnh, và mảng theo người (hạng item test trước / sau mặt nạ, top-20 trước / sau mặt nạ, số ống chấm được / vi phạm / được nới theo K) để bootstrap không cần chạy lại.

## 13. Câu hỏi của kế hoạch (chưa chốt)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| HỎI 10 | Khởi tạo CaKG-Rec từ đầu hay từ embedding LightGCN đã huấn luyện (nhanh hơn, nhưng CaKG-Rec được hơn 300 epoch)? | Từ đầu, cùng ngân sách 300 epoch |
| HỎI 11 | Cắt phần nào nếu thiếu thời gian (mục 9.3)? | Chạy đủ nếu có 2 tuần; thiếu thì cắt theo thứ tự 1 → 3 |
| HỎI 12 | So sánh chính là C1, C2, C3, C6? | Đồng ý |
| HỎI 13 | Faithfulness chọn 2.000 cặp có đường giải thích (không phải mọi cặp)? | Đồng ý (chi phí ~1 phút GPU; mọi cặp là ~10.000 người × tới 10 ống) |

## 14. Sửa đổi kế hoạch

| Ngày | Sửa | Lý do |
|---|---|---|
| | | |
