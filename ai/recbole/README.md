# RecBole — đối chiếu cài đặt (nhận xét cô 06/11, mục A3)

Viết 06/11/2026. Kế hoạch và kết quả: `docs/reviews/v3_eval_plan.md` mục 7.

## Môi trường riêng (không đụng `ai/.venv`)

```
py -3.12 -m venv E:\DATN\venvs\recbole
E:\DATN\venvs\recbole\Scripts\python.exe -m pip install --no-deps -r ai/recbole/requirements-recbole-lock.txt
```

- `--no-deps`: RecBole 1.2.1 đòi `ray<=2.6.3`, không có bản cho Python 3.12 (`ray` chỉ dùng cho dò tham số tự động).
- `scipy==1.11.4`: scipy ≥ 1.12 làm `LightGCN.get_norm_adj_mat` của RecBole lỗi (`dok_matrix._update`).
- `numpy 1.26.4`, `pandas 2.2.3`: mã RecBole 1.2.1 viết cho numpy 1 / pandas 2.
- RecBole-GNN (SimGCL, ...) không phải gói pip: `git clone https://github.com/RUCAIBox/RecBole-GNN` vào
  `E:\DATN\venvs\src\recbole_gnn_src` (commit `632ef88`), rồi chạy `run_recbole.py --gnn E:\DATN\venvs\src\recbole_gnn_src`.
- Không có bản dựng sẵn `torch_scatter` / `torch_sparse` cho torch 2.14.1 (06/11): `run_recbole.py` thay
  `torch_scatter.scatter_mean` (KGIN) bằng `torch_geometric.utils.scatter(reduce="mean")` và cho RecBole-GNN một
  `torch_sparse` giả (RecBole-GNN tự dùng `edge_index` thường khi thiếu nó); ghi ở `config_used.json` → `patches`.
- torch ≥ 2.6 mặc định `torch.load(weights_only=True)`; checkpoint RecBole có đối tượng Config nên `run_recbole.py`
  đặt `weights_only=False` cho file do chính nó ghi.

## Các bước

1. `ai\.venv\Scripts\python.exe ai/recbole/to_recbole.py` — chép nguyên train / val / test của nhóm sang
   `ai/data/recbole/camera_loo/camera_loo.{train,valid,test}.inter` (benchmark: RecBole không tự chia, không lọc),
   kiểm số dòng, ghi `manifest.json`.
2. (KGIN / KGAT) `ai\.venv\Scripts\python.exe ai/recbole/to_recbole_kg.py` — xuất đồ thị nội dung 4 (chiều xuôi, không
   cạnh người dùng, bỏ 134 cạnh `ngam_khong_chac`) sang `camera_loo.kg` / `.link`. `.link` chỉ chứa 2.972 sản phẩm có
   trong `.kg` (chế độ benchmark không lọc `.link`, ghi thừa thì KGIN lỗi `KeyError`); sản phẩm khác vẫn giữ tương tác.
3. `E:\DATN\venvs\recbole\Scripts\python.exe ai/recbole/run_recbole.py --model LightGCN --seed 1 --epochs 300 --run-dir results/recbole/<đợt>/<tên>`
   (`--probe-epochs N`: chỉ đo thời gian).
4. `ai\.venv\Scripts\python.exe ai/recbole/cross_eval.py --run-dir results/recbole/<đợt>/<tên> --split val` (và `test`)
   — chấm lại embedding RecBole bằng bộ chấm của nhóm (quy tắc hòa π), so với số RecBole tự chấm và số nhóm.

## Baseline v3: `--group-eval` (thêm 06/11 khuya)

`run_recbole.py --model KGIN --seed 1 --epochs 1000 --group-eval --run-dir <...>` (SimGCL thêm `--gnn <RecBole-GNN>`):
RecBole huấn luyện như thường nhưng **chấm val bằng bộ chấm nhóm** (`eval_05`, full ranking, quy tắc hòa π) mỗi 10
epoch, dừng sau 5 lần không tăng (quy tắc RecBole `>=`, `stopping_step` 4); không chấm test. Mỗi lần chấm lưu
`last_state.pth` (mô hình, Adam, bộ đếm dừng sớm, lịch sử, bộ sinh số random / numpy / torch / CUDA **và
`torch.Generator` riêng của dataloader**); gọi lại đúng lệnh → chạy tiếp. Kiểm 06/11 (BPR, CPU): chạy liền 20 epoch và
dừng ở 10 rồi chạy tiếp cho loss / NDCG@20 trùng ở mọi epoch (trước khi lưu generator dataloader thì lệch từ epoch 11 —
CHANGELOG 06/11 khuya). `--stop-after-evals N`: chỉ để kiểm chạy tiếp.
