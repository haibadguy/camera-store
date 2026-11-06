"""
kiem_ultragcn_tacgia.py — kiểm ai/pipeline/05e_ultragcn_train.py so với CODE CỦA TÁC GIẢ UltraGCN (RecZoo,
matching/gnn/UltraGCN/main.py @88fae23), trên DỮ LIỆU NHÓM. Viết 06/11/2026 (khuya) theo yêu cầu của Nam: chạy lại phép
kiểm có ghi log (lần kiểm trước chỉ là script tạm trên ma trận đồ chơi 60×40, công thức chép tay, không lưu log).

Code tác giả được lấy NGUYÊN VĂN: đọc main.py, tách bằng ast các hàm load_data, get_ii_constraint_mat và lớp UltraGCN,
exec trong một không gian tên có torch / nn / F / np / sp (như phần import của main.py). Không sửa dòng nào.

Ví dụ điều được kiểm: item A có 3 láng giềng đồng xuất hiện; trọng số ω_AB = G_AB·√(g_A+1)/g_A·1/√(g_B+1) của 05e phải
bằng của tác giả (sai khác chỉ do float64 / float32), 10 láng giềng chọn ra phải là cùng tập (trừ khi hòa ở vị trí 10).

Các phần:
  1. load_data của tác giả trên train.txt / val.txt nhóm: số người / item, β_u, β_i so với 05e.
  2a. get_ii_constraint_mat của tác giả, NGUYÊN VĂN, trên (i) ma trận đồ chơi 60×40 và (ii) đồ thị con thật gồm
      N item nhiều tương tác nhất (hàm của tác giả dựng ma trận dày n_items² nên không chạy được cho 27.940 item với
      RAM trống ~5 GB: 27.940² × 4 byte ≈ 3,1 GB cho riêng một ma trận).
  2b. Toàn bộ 27.940 item: chép đúng các phép tính của get_ii_constraint_mat theo TỪNG HÀNG (hàng i của
      beta_uD.dot(beta_iD) = beta_uD[i] · beta_iD, cùng float32, cùng một phép nhân mỗi phần tử -> cùng giá trị bit) —
      đây là bản chép, ghi rõ trong log.
  3. Hàm loss: lớp UltraGCN của tác giả (forward = L_C + gamma·norm + lambda·L_I) và 05e trên cùng embedding, cùng
      batch thật, cùng âm mẫu: so giá trị loss và gradient.
  4. Âm mẫu của 05e: không trúng item đã có trong train; phân phối đều trên item chưa có (kiểm chi-bình phương).
Chạy (CPU, không đụng GPU đang huấn luyện):
  set CUDA_VISIBLE_DEVICES= & ai\\.venv\\Scripts\\python.exe ai/survey/v3/kiem_ultragcn_tacgia.py --label lan1
Đầu ra (không ghi đè): results/v3/kiem_ultragcn/kiem_ultragcn_<label>.log, .json
"""
import argparse
import ast
import hashlib
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.stats as st
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ai" / "pipeline"))
import common_05 as C  # noqa: E402
import train_05 as T   # noqa: E402

U = importlib.import_module("05e_ultragcn_train")
SRC = Path(r"E:\DATN\venvs\src\ultragcn_src")
MAIN = SRC / "matching" / "gnn" / "UltraGCN" / "main.py"
EXPECT_COMMIT = "88fae23ff0b8321c60655d9c21e0a1bb1173f6af"
K = 10
ELEC = dict(embedding_dim=64, w1=1e-7, w2=1.0, w3=1e-7, w4=1.0, negative_weight=75.0, gamma=5e-5, initial_weight=1e-3)
ELEC["lambda"] = 1e-7

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_author():
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    want = {"load_data", "get_ii_constraint_mat", "UltraGCN"}
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in want]
    assert {n.name for n in nodes} == want, [n.name for n in nodes]
    ns = {"torch": torch, "nn": nn, "F": F, "np": np, "sp": sp, "__name__": "ultragcn_author"}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(MAIN), "exec"), ns)
    return ns


def compare_neighbors(idx_a, w_a, idx_b, w_b, rows):
    """a = tác giả, b = 05e. Chỉ xét láng giềng có trọng số > 0. Trả về dict thống kê."""
    max_abs = max_rel = 0.0
    diff_rows, tie_rows, real_rows, examples = 0, 0, 0, []
    for r in rows:
        wa = w_a[r].astype(np.float64)
        wb = w_b[r].astype(np.float64)
        ma, mb = wa > 0, wb > 0
        sa, sb = np.sort(wa[ma])[::-1], np.sort(wb[mb])[::-1]
        if len(sa) != len(sb):
            real_rows += 1
            examples.append({"row": int(r), "loai": "số láng giềng > 0 khác", "tac_gia": len(sa), "05e": len(sb)})
            continue
        if len(sa):
            d = np.abs(sa - sb)
            max_abs = max(max_abs, float(d.max()))
            max_rel = max(max_rel, float((d / np.maximum(np.abs(sb), 1e-300)).max()))
        A, B = set(idx_a[r][ma].tolist()), set(idx_b[r][mb].tolist())
        if A != B:
            diff_rows += 1
            kth = sb[-1]                       # trọng số nhỏ nhất được chọn (vị trí K hoặc cuối)
            wa_of = dict(zip(idx_a[r][ma].tolist(), wa[ma].tolist()))
            wb_of = dict(zip(idx_b[r][mb].tolist(), wb[mb].tolist()))
            only = [wa_of[j] for j in A - B] + [wb_of[j] for j in B - A]
            if all(abs(x - kth) <= 1e-6 * kth for x in only):
                tie_rows += 1
            else:
                real_rows += 1
                if len(examples) < 5:
                    examples.append({"row": int(r), "loai": "tập khác, không do hòa", "chi_tac_gia": sorted(A - B),
                                     "chi_05e": sorted(B - A)})
    return {"rows": len(rows), "max_abs_w": max_abs, "max_rel_w": max_rel, "rows_set_differ": diff_rows,
            "rows_differ_only_by_tie_at_k": tie_rows, "rows_real_difference": real_rows, "examples": examples}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--sub-items", type=int, default=4000, help="phần 2a(ii): số item nhiều tương tác nhất")
    a = ap.parse_args()
    out = ROOT / "results" / "v3" / "kiem_ultragcn"
    out.mkdir(parents=True, exist_ok=True)
    lp, jp = out / f"kiem_ultragcn_{a.label}.log", out / f"kiem_ultragcn_{a.label}.json"
    assert not lp.exists() and not jp.exists(), f"đã có {lp}, đổi --label"
    fh = open(lp, "w", encoding="utf-8")

    def log(*m):
        s = " ".join(str(x) for x in m)
        print(s, flush=True)
        fh.write(s + "\n")
        fh.flush()

    torch.set_num_threads(4)
    res = {"label": a.label, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    commit = subprocess.run(["git", "-C", str(SRC), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True).stdout.strip())
    res["src"] = {"author_commit": commit, "main_py_sha256": sha256(MAIN), "repo_commit": git, "repo_dirty": dirty,
                  "05e_sha256": sha256(ROOT / "ai" / "pipeline" / "05e_ultragcn_train.py"),
                  "train_txt_sha256": sha256(C.TRAIN_TXT)}
    log(f"kiem_ultragcn_tacgia {a.label} | {res['time']} | tác giả {commit} (main.py sha256 "
        f"{res['src']['main_py_sha256'][:12]}…) | repo {git} dirty={dirty} | torch {torch.__version__} CPU")
    assert commit == EXPECT_COMMIT, f"bản clone tác giả ở {commit}, cần {EXPECT_COMMIT}"
    AU = load_author()
    log("Đã tách nguyên văn từ main.py: load_data, get_ii_constraint_mat, class UltraGCN")

    # ---------- 1. load_data ----------
    t = time.time()
    val_txt = C.TRAIN_TXT.parent / "val.txt"
    train_data, _test, train_mat, n_user, m_item, cons = AU["load_data"](str(C.TRAIN_TXT), str(val_txt))
    train = C.load_train()
    u, i = T.train_pairs(train)
    du = np.bincount(u, minlength=C.N_USERS).astype(np.float64)
    di = np.bincount(i, minlength=C.N_ITEMS).astype(np.float64)
    bu = np.zeros(C.N_USERS)
    bu[du > 0] = np.sqrt(du[du > 0] + 1) / du[du > 0]
    bi = 1 / np.sqrt(di + 1)
    bu_a = cons["beta_uD"].double().numpy()
    bi_a = cons["beta_iD"].double().numpy()
    p1 = {"n_user_tac_gia": int(n_user), "n_item_tac_gia": int(m_item), "n_user_nhom": C.N_USERS,
          "n_item_nhom": C.N_ITEMS, "cap_train_tac_gia": len(train_data), "cap_train_nhom": int(len(u)),
          "train_mat_nnz": int(train_mat.nnz),
          "max_rel_beta_u": float(np.max(np.abs(bu_a - bu[:n_user]) / bu[:n_user])),
          "max_rel_beta_i": float(np.max(np.abs(bi_a - bi[:m_item]) / bi[:m_item])),
          "sec": round(time.time() - t, 1)}
    res["1_load_data"] = p1
    log(f"[1] load_data (train.txt + val.txt nhóm): {p1}")
    log("    (n_item của tác giả = mã item lớn nhất trong train/val + 1; item chỉ có ở test nằm ngoài -> so trên phần chung)")
    assert p1["n_user_tac_gia"] == C.N_USERS and p1["cap_train_tac_gia"] == len(u) == p1["train_mat_nnz"]
    assert p1["max_rel_beta_u"] < 1e-6 and p1["max_rel_beta_i"] < 1e-6

    # ---------- 2a(i). đồ chơi ----------
    rng = np.random.default_rng(0)
    nu, ni, k5 = 60, 40, 5
    M = rng.random((nu, ni)) < 0.12
    M[:, -2:] = False
    M[np.arange(nu), rng.integers(0, ni - 2, nu)] = True
    tu, ti = np.nonzero(M)
    with np.errstate(divide="ignore", invalid="ignore"):
        ia, wa = AU["get_ii_constraint_mat"](sp.csr_matrix(M.astype(np.float32)), k5)
    ib, wb, _ = U.ii_neighbors(tu, ti, nu, ni, k5)
    r2a = compare_neighbors(ia.numpy(), np.nan_to_num(wa.numpy()), ib.numpy(), wb.numpy(), range(ni - 2))
    r2a["item_khong_co_trong_train"] = {"tac_gia_w": wa[-2:].tolist(), "05e_w": wb[-2:].tolist()}
    res["2a_do_choi"] = r2a
    log(f"[2a-i] get_ii_constraint_mat NGUYÊN VĂN, đồ chơi 60×40 (K = 5): {r2a}")

    # ---------- 2a(ii). đồ thị con thật ----------
    t = time.time()
    top = np.argsort(-di, kind="stable")[:a.sub_items]
    remap = -np.ones(C.N_ITEMS, np.int64)
    remap[top] = np.arange(len(top))
    keep = remap[i] >= 0
    su, si = u[keep], remap[i[keep]]
    sub = sp.csr_matrix((np.ones(len(su), np.float32), (su, si)), shape=(C.N_USERS, len(top)))
    ia, wa = AU["get_ii_constraint_mat"](sub, K)
    ib, wb, _ = U.ii_neighbors(su, si, C.N_USERS, len(top), K)
    r2b = compare_neighbors(ia.numpy(), wa.numpy(), ib.numpy(), wb.numpy(), range(len(top)))
    r2b.update(n_items=len(top), n_pairs=int(len(su)), sec=round(time.time() - t, 1))
    res["2a_do_thi_con_that"] = r2b
    log(f"[2a-ii] get_ii_constraint_mat NGUYÊN VĂN, đồ thị con thật {len(top)} item nhiều tương tác nhất "
        f"({len(su):,} cặp, K = 10): {r2b}")

    # ---------- 2b. toàn bộ, chép theo hàng ----------
    t = time.time()
    tm = sp.csr_matrix((np.ones(len(u), np.float32), (u, i)), shape=(C.N_USERS, C.N_ITEMS))
    A = tm.T.dot(tm)                                         # như tác giả: train_mat.T.dot(train_mat), float32
    items_D = np.sum(A, axis=0).reshape(-1)
    users_D = np.sum(A, axis=1).reshape(-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        beta_uD = np.asarray((np.sqrt(users_D + 1) / users_D).reshape(-1, 1))
    beta_iD = np.asarray((1 / np.sqrt(items_D + 1)).reshape(1, -1))
    A = A.tocsr()
    res_mat = torch.zeros((C.N_ITEMS, K))
    res_sim = torch.zeros((C.N_ITEMS, K))
    for r in range(C.N_ITEMS):
        row = torch.from_numpy(beta_uD[r] * beta_iD[0]) * torch.from_numpy(A.getrow(r).toarray()[0])
        s, ix = torch.topk(row, K)
        res_mat[r], res_sim[r] = ix, s
    ia_full, wa_full = res_mat.long().numpy(), res_sim.float().numpy()
    t_a = time.time() - t
    t = time.time()
    ib_full, wb_full, nnz = U.ii_neighbors(u, i, C.N_USERS, C.N_ITEMS, K)
    ib_full, wb_full = ib_full.numpy(), wb_full.numpy()
    g0 = np.asarray(A.sum(axis=1)).reshape(-1) == 0
    rows = [r for r in range(C.N_ITEMS) if not g0[r]]
    r2c = compare_neighbors(ia_full, wa_full, ib_full, wb_full, rows)
    r2c.update(n_items=C.N_ITEMS, G_nnz=int(nnz), items_g0=int(g0.sum()),
               g0_tac_gia_nan=bool(np.isnan(wa_full[g0]).all()) if g0.any() else None,
               g0_05e_w0=bool((wb_full[g0] == 0).all()) if g0.any() else None,
               sec_tac_gia=round(t_a, 1), sec_05e=round(time.time() - t, 1))
    res["2b_toan_bo_chep_theo_hang"] = r2c
    log(f"[2b] toàn bộ {C.N_ITEMS:,} item, chép get_ii_constraint_mat theo từng hàng (float32 như tác giả): {r2c}")

    # ---------- 3. loss ----------
    torch.manual_seed(0)
    cfg = {"dim": 64, "initial_weight": 1e-3, "w1": 1e-7, "w2": 1.0, "w3": 1e-7, "w4": 1.0, "negative_num": 75,
           "negative_weight": 75.0, "gamma": 5e-5, "lambda": 1e-7}
    keys = torch.as_tensor(np.unique(u.astype(np.int64) * C.N_ITEMS + i))
    mine = U.UltraGCN(C.N_USERS, C.N_ITEMS, cfg, torch.as_tensor(du), torch.as_tensor(di),
                      torch.as_tensor(ib_full), torch.as_tensor(wb_full), keys)
    with torch.no_grad():                                   # nhúng nhỏ quá thì loss ~ hằng số; cho lớn hơn để thấy lệch
        mine.user_embeds.weight.normal_(0, 0.1)
        mine.item_embeds.weight.normal_(0, 0.1)
    params = dict(ELEC, user_num=C.N_USERS, item_num=C.N_ITEMS)
    cons_full = {"beta_uD": torch.from_numpy(np.nan_to_num(bu_a, posinf=0.0)).float(),
                 "beta_iD": torch.from_numpy(np.concatenate([bi_a, np.ones(C.N_ITEMS - m_item)])).float()}

    def author_model(ii_idx, ii_w):
        m = AU["UltraGCN"](params, cons_full, torch.as_tensor(ii_w), torch.as_tensor(ii_idx))
        m.load_state_dict({"user_embeds.weight": mine.user_embeds.weight.detach().clone(),
                           "item_embeds.weight": mine.item_embeds.weight.detach().clone()})
        return m

    g = torch.Generator().manual_seed(1)
    p3 = []
    for b in range(3):
        sel = torch.randint(0, len(u), (2048,), generator=g)
        bu_t, bi_t = torch.as_tensor(u)[sel], torch.as_tensor(i)[sel]
        neg = mine.sample_neg(bu_t)
        mine.sample_neg = lambda _u, _n=neg: _n             # cùng âm mẫu cho cả hai bên
        mine.zero_grad()
        lm = mine.loss(bu_t, bi_t, None)
        lm.backward()
        gm = [mine.user_embeds.weight.grad.clone(), mine.item_embeds.weight.grad.clone()]
        del mine.sample_neg
        row = {"batch": b, "loss_05e": float(lm)}
        for tag, (ii_i, ii_w) in (("ii_cua_05e", (ib_full, wb_full)), ("ii_cua_tac_gia", (ia_full, wa_full))):
            am = author_model(ii_i, ii_w)
            la = am(bu_t, bi_t, neg)
            la.backward()
            ga = [am.user_embeds.weight.grad, am.item_embeds.weight.grad]
            gd = max(float((x - y).abs().max()) for x, y in zip(ga, gm))
            gs = max(float(y.abs().max()) for y in gm)
            row[tag] = {"loss_tac_gia": float(la), "rel_loss": abs(float(la) - float(lm)) / abs(float(lm)),
                        "max_abs_grad_diff": gd, "max_abs_grad": gs}
        p3.append(row)
        log(f"[3] batch {b}: {row}")
    res["3_loss"] = p3

    # ---------- 4. âm mẫu ----------
    g = torch.manual_seed(2)
    sel = torch.randint(0, len(u), (2048,))
    neg = mine.sample_neg(torch.as_tensor(u)[sel])
    hit = int(np.isin(torch.as_tensor(u)[sel].unsqueeze(1).expand_as(neg).numpy() * C.N_ITEMS + neg.numpy(),
                      keys.numpy()).sum())
    u0 = int(np.argmax(du))
    draws = mine.sample_neg(torch.full((20000,), u0, dtype=torch.long)).reshape(-1).numpy()
    allowed = np.setdiff1d(np.arange(C.N_ITEMS), np.asarray(sorted(train[u0])))
    cnt = np.bincount(draws, minlength=C.N_ITEMS)
    chi = st.chisquare(cnt[allowed])
    p4 = {"batch_2048x75_trung_item_train": hit, "user": u0, "so_item_train_cua_user": int(du[u0]),
          "so_luot_lay": int(len(draws)), "trung_item_train": int(np.isin(draws, list(train[u0])).sum()),
          "chi2": float(chi.statistic), "df": int(len(allowed) - 1), "p_value": float(chi.pvalue)}
    res["4_am_mau"] = p4
    log(f"[4] âm mẫu 05e: {p4}")

    ok = (r2a["rows_real_difference"] == 0 and r2b["rows_real_difference"] == 0 and r2c["rows_real_difference"] == 0
          and r2c["max_rel_w"] < 1e-5 and all(r["ii_cua_05e"]["rel_loss"] < 1e-5 for r in p3) and hit == 0
          and p4["trung_item_train"] == 0 and p4["p_value"] > 0.001)
    res["ket_luan_dat"] = bool(ok)
    log(f"KẾT LUẬN: {'ĐẠT' if ok else 'KHÔNG ĐẠT'} (ngưỡng: 0 hàng khác thật; lệch tương đối trọng số < 1e-5; lệch loss "
        f"tương đối < 1e-5 khi cùng ma trận láng giềng; 0 âm mẫu trúng train; p chi-bình phương > 0,001)")
    jp.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {jp}")
    fh.close()


if __name__ == "__main__":
    main()
