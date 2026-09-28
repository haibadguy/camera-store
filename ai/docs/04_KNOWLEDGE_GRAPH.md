# KIẾN TRÚC ĐỒ THỊ TRI THỨC DỊ THỂ (HETEROGENEOUS KNOWLEDGE GRAPH) — MỤC 4

> **Đề tài:** Hệ thống tư vấn cá nhân hóa thiết bị nhiếp ảnh (Camera Store Recommendation System)  
> **Mục tiêu:** Xây dựng đồ thị tri thức dị thể $G = (V, E, \mathcal{R})$ kết hợp hành vi người dùng (Collaborative Filtering) và tri thức miền kỹ thuật máy ảnh (Domain Constraints).

---

## 1. THIẾT KẾ ĐỒ THỊ HETERODATA (PYTORCH GEOMETRIC)

### 1.1. Thực thể (Node Types - $|V|$)
* **`user` (70,424 nodes):** Biểu diễn người dùng, ID liên tục $[0, 70423]$. Feature là learnable embedding trong mô hình.
* **`item` (28,867 nodes):** Gộp chung thân máy (Body), ống kính (Lens) và phụ kiện (Accessory), ID liên tục $[0, 28866]$.
  * Feature: `item.x` kích thước $[28867, 3]$ (one-hot vector cho loại thiết bị: `0=Body`, `1=Lens`, `2=Accessory`).
  * Chi tiết số lượng: 106 Body, 151 Lens, 28,610 Accessory.
* **`mount` (8 nodes):** 8 ngàm ống kính vật lý chính (`Canon EF`, `Canon RF`, `Nikon F`, `Nikon Z`, `Sony E`, `Fujifilm X`, `Micro Four Thirds`, `Leica L`).
  * Feature: `mount.x` kích thước $[8, 8]$ (ma trận đơn vị Identity).
* **`usecase` (7 nodes):** 7 nhu cầu chụp ảnh cốt lõi (`Portrait`, `Landscape`, `Street`, `Wildlife`, `Sports`, `Astro`, `Macro`).
  * Feature: `usecase.x` kích thước $[7, 7]$ (ma trận đơn vị Identity).

---

## 2. QUAN HỆ & CẠNH ĐỒ THỊ (EDGE TYPES & RELATIONS - $\mathcal{R}$)

Đồ thị được định nghĩa bằng 4 quan hệ xuôi (Forward Relations) và tự động sinh 3 quan hệ ngược qua biến đổi `ToUndirected()` của PyG:

| STT | Quan hệ (Edge Type) | Hướng | Số lượng cạnh | Nguồn dữ liệu |
|:---:|---|:---:|:---:|---|
| 1 | `('user', 'interacted_with', 'item')` | Hai chiều | 482,149 | `train.txt` (Mục 2) |
| 2 | `('item', 'rev_interacted_with', 'user')` | Hai chiều | 482,149 | Tự động sinh bởi `ToUndirected()` |
| 3 | `('item', 'compatible_with', 'item')` | Vô hướng | 6,516 | `compatible_item_edges.csv` (Mục 3: 3,258 cặp xuôi $\times 2$) |
| 4 | `('item', 'has_mount', 'mount')` | Thuận | 257 | `linked_products.csv` (Mục 3) |
| 5 | `('mount', 'rev_has_mount', 'item')` | Ngược | 257 | Tự động sinh bởi `ToUndirected()` |
| 6 | `('item', 'suitable_for', 'usecase')` | Thuận | 441 | Entity Linking Specs (Mục 3) |
| 7 | `('usecase', 'rev_suitable_for', 'item')` | Ngược | 441 | Tự động sinh bởi `ToUndirected()` |

---

## 3. KẾT QUẢ KIỂM THỬ TÍNH ĐÚNG ĐẮN (9 CHECKS VALIDATION)

Toàn bộ 9/9 bước kiểm tra logic toàn vẹn dữ liệu đều đạt chuẩn tuyệt đối:
* ✅ `uid max (70423) < N_USERS (70424)`
* ✅ `iid max (user-item) (28866) < N_ITEMS (28867)`
* ✅ `compat iid in range`
* ✅ `mount idx in [0, 7]`
* ✅ `item_type body == 106`
* ✅ `item_type lens == 151`
* ✅ `has_mount edges (257) == linked items (257)`
* ✅ `compatible edges (3258) == nnz(M) (3258)`
* ✅ `usecase idx in [0, 6]`

---

## 4. CÁC TẬP TIN ARTIFACTS
* File nhị phân đồ thị: [`ai/data/kg/kg_hetero.pt`](file:///d:/camera-store/ai/data/kg/kg_hetero.pt) (Kích thước ~15.9 MB)
* Thống kê đồ thị JSON: [`ai/data/kg/kg_stats.json`](file:///d:/camera-store/ai/data/kg/kg_stats.json)
* Nhật ký kiểm thử: [`ai/data/kg/validation_log.txt`](file:///d:/camera-store/ai/data/kg/validation_log.txt)
