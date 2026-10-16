"""Chẩn đoán cho thiết kế CaKG-Rec v2 (docs/reviews/cakg_v2_plan.md), CHỈ ĐỌC: chỉ dùng TRAIN và checkpoint v1 seed 1
(results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1/best.pt). Không đọc val, không đọc test, không huấn luyện.
Viết 16/10/2026. Log ghi ra file TÊN MỚI trong ai/data/survey/cakg_v2/.

Giả thuyết cần kiểm (biến thể C "h_u bỏ chính thân đang là item dương"):
  lúc huấn luyện, với cặp dương (u, b) mà b là thân của u có nút trong H, h_u = trung bình các thân của u ĐÃ GỒM b
  (công thức 7). Nên phần phần cứng β_uh β_bh h_uᵀh_b có số hạng ‖h_b‖² / |B_u^H| ("rò rỉ chính mình"). BPR thưởng mô
  hình khi phần này lớn. Lúc chấm, thân của u bị bỏ (item train), nhưng thân CÙNG NGÀM có h gần h_b vẫn được cộng điểm.

Ví dụ: u có 1 thân b (|B| = 1) -> h_u = h_b, phần phần cứng của cặp dương (u, b) = β_uh β_bh ‖h_b‖²; nếu bỏ b khỏi h_u
thì u không còn thân nào -> cổng đóng, phần phần cứng = 0.

In ra:
  1. trong train của người có h_u: số cặp dương là thân có h / ống có h / sản phẩm không có h; |B_u^H| = 1 hay ≥ 2;
  2. phần phần cứng (đã nhân β) của cặp dương là thân: h_u gồm chính b, và h_u bỏ b (với |B| ≥ 2); so với cặp dương là ống;
     so với thân CÙNG NGÀM mà u không có (lấy ngẫu nhiên, seed cố định);
  3. cos(h_b, h_b') giữa hai thân cùng ngàm / khác ngàm.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg_v2/chan_doan_v2.py --label 20261016_lan1
"""
import argparse
import csv
import importlib
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header, sha256_file  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

T06 = importlib.import_module("06_cakg_train")
RUN = "results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1"
SEED = 20261016


def q(x):
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0:
        return "n = 0"
    p = np.percentile(x, [10, 50, 90])
    return f"n = {len(x):,}, TB {x.mean():.4f}, p10 {p[0]:.4f}, trung vị {p[1]:.4f}, p90 {p[2]:.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg_v2", f"run_chan_doan_v2_{a.label}.log"))
    header(log, __file__)
    pt = os.path.join(RUN, "best.pt")
    log(f"checkpoint: {pt} (sha256 {sha256_file(pt)}); chỉ dùng train, KHÔNG đọc val / test")
    cfg = json.loads(open(os.path.join(RUN, "config.json"), encoding="utf-8").read())["cfg"]
    train = C.load_train()
    m = T06.build_cakg(cfg, train, log=lambda s: None)
    m.load_state_dict(torch.load(pt, map_location=E.DEVICE, weights_only=False)["model"], strict=True)
    m.eval()
    item_type = C.load_item_type()
    with torch.no_grad():
        eU, eI = m.behaviour()
        h, hU, _ = m.hardware()
    loc = m.item_loc.cpu().numpy()
    has_hu = m.has_hu.cpu().numpy()

    # ngàm của thân (has_spec_mount, item_type = than, không phụ kiện)
    mount = {}
    with open(C.DATA_DIR / "kg" / "kg_edges_has_spec_mount.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["item_type"] == "than" and r["src_phu_kien"] == "0" and r["ngam_khong_chac"] == "0":
                mount[int(r["iid"])] = r["mount"]

    # 1. đếm cặp dương
    n_body, n_lens, n_noh, n_b1, n_b2 = 0, 0, 0, 0, 0
    nb_of = {}
    for u, its in train.items():
        if not has_hu[u]:
            continue
        bs = [i for i in its if item_type[i] == 0 and loc[i] >= 0]
        nb_of[u] = len(bs)
        n_b1 += len(bs) == 1
        n_b2 += len(bs) >= 2
        for i in its:
            if loc[i] < 0:
                n_noh += 1
            elif item_type[i] == 0:
                n_body += 1
            else:
                n_lens += 1
    tot = n_body + n_lens + n_noh
    log(f"\n1. Người có h_u: {int(has_hu.sum()):,} (|B_u^H| = 1: {n_b1:,}; ≥ 2: {n_b2:,})")
    log(f"   cặp dương train của họ: {tot:,}; thân có h {n_body:,} ({n_body / tot:.1%}), ống có h {n_lens:,} "
        f"({n_lens / tot:.1%}), sản phẩm không có h {n_noh:,} ({n_noh / tot:.1%})")
    log(f"   -> mọi cặp dương là thân có h đều có thân đó nằm trong h_u (B_u^H = thân train có nút trong H)")

    # 2. phần phần cứng đã nhân β (công thức 9): β_uh β_ih h_uᵀh_i
    def hw_part(us, its, hu_rows):
        us_t = torch.as_tensor(us, device=E.DEVICE)
        it_t = torch.as_tensor(its, device=E.DEVICE)
        with torch.no_grad():
            ones = torch.ones(len(us), dtype=torch.bool, device=E.DEVICE)
            _, bu = m.fu(eU[us_t], hu_rows, ones)
            hi = h[m.item_loc[it_t]]
            _, bi = m.fi(eI[it_t], hi, ones)
            return (bu[:, 1] * bi[:, 1] * (hu_rows * hi).sum(1)).cpu().numpy(), (eU[us_t] * eI[it_t]).sum(1).cpu().numpy()

    rng = np.random.default_rng(SEED)
    bodies_by_mount = {}
    for b, mt in mount.items():
        if loc[b] >= 0:
            bodies_by_mount.setdefault(mt, []).append(b)
    us_b, it_b, us_l, it_l, us_s, it_s, loo_rows_u, loo_rows_b = [], [], [], [], [], [], [], []
    for u, nb in nb_of.items():
        its = train[u]
        bs = [i for i in its if item_type[i] == 0 and loc[i] >= 0]
        for b in bs:
            us_b.append(u)
            it_b.append(b)
            if nb >= 2:
                loo_rows_u.append(u)
                loo_rows_b.append(b)
        for i in its:
            if loc[i] >= 0 and item_type[i] == 1:
                us_l.append(u)
                it_l.append(i)
        # một thân CÙNG NGÀM với một thân của u mà u không có trong train (nếu có)
        cand = sorted({c for b in bs if b in mount for c in bodies_by_mount.get(mount[b], [])} - set(its))
        if cand:
            us_s.append(u)
            it_s.append(int(rng.choice(cand)))
    hw_b, beh_b = hw_part(us_b, it_b, hU[torch.as_tensor(us_b, device=E.DEVICE)])
    hw_l, beh_l = hw_part(us_l, it_l, hU[torch.as_tensor(us_l, device=E.DEVICE)])
    hw_s, beh_s = hw_part(us_s, it_s, hU[torch.as_tensor(us_s, device=E.DEVICE)])
    # h_u bỏ chính b: (|B| h_u − h_b) / (|B| − 1)
    uu = torch.as_tensor(loo_rows_u, device=E.DEVICE)
    bb = torch.as_tensor(loo_rows_b, device=E.DEVICE)
    nb_t = torch.as_tensor([nb_of[u] for u in loo_rows_u], device=E.DEVICE, dtype=torch.float32)[:, None]
    hu_loo = (nb_t * hU[uu] - h[m.item_loc[bb]]) / (nb_t - 1)
    hw_b2_in, _ = hw_part(loo_rows_u, loo_rows_b, hU[uu])
    hw_b2_out, _ = hw_part(loo_rows_u, loo_rows_b, hu_loo)
    sel1 = np.array([nb_of[u] == 1 for u in us_b])
    log("\n2. Phần phần cứng β_uh β_ih h_uᵀh_i (đã nhân β), cặp train của người có h_u:")
    log(f"   cặp dương là thân, |B| = 1 (h_u = h_b; bỏ b thì cổng đóng, phần này = 0): {q(hw_b[sel1])}")
    log(f"   cặp dương là thân, |B| ≥ 2, h_u GỒM b:  {q(hw_b2_in)}")
    log(f"   cặp dương là thân, |B| ≥ 2, h_u BỎ b:   {q(hw_b2_out)}")
    log(f"   cặp dương là ống có h:                 {q(hw_l)}")
    log(f"   thân cùng ngàm u KHÔNG có (ngẫu nhiên): {q(hw_s)}")
    log(f"   (so sánh) điểm hành vi e_uᵀe_i: thân dương {q(beh_b)}; ống dương {q(beh_l)}; thân cùng ngàm không có "
        f"{q(beh_s)}")

    # 3. cos giữa thân cùng ngàm / khác ngàm
    bl = sorted(b for b in mount if loc[b] >= 0)
    hb = F.normalize(h[m.item_loc[torch.as_tensor(bl, device=E.DEVICE)]], dim=1)
    S = (hb @ hb.T).cpu().numpy()
    mt = np.array([mount[b] for b in bl])
    same = (mt[:, None] == mt[None, :]) & ~np.eye(len(bl), dtype=bool)
    diff = mt[:, None] != mt[None, :]
    log(f"\n3. cos(h_b, h_b') giữa {len(bl)} thân có ngàm chắc chắn trong H: cùng ngàm {q(S[same])}; khác ngàm {q(S[diff])}")
    nrm = h[m.item_loc[torch.as_tensor(bl, device=E.DEVICE)]].norm(dim=1).cpu().numpy()
    log(f"   ‖h_b‖ của thân: {q(nrm)}")
    log.save()


if __name__ == "__main__":
    main()
