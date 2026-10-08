"""
eval_05.py — Đánh giá nội dung 5 theo kế hoạch đăng ký trước docs/reviews/n5_eval_plan.md (mục 3, 4, 5, 8, 11).
Viết 09/10/2026 (sửa lỗi L4, L7, L8, L14, L15 một phần, L17 của kế hoạch mục 2).

Ví dụ (kế hoạch mục 1): u1 train = {D}, val = E, test = A; điểm B 0,9 | C 0,8 | A 0,7 | E 0,1.
  Chấm test: bỏ D (train) và E (val) khỏi ứng viên -> thứ tự B, C, A -> hạng của A = 3
  -> Hit@2 = Recall@2 = 0, Hit@5 = Recall@5 = 1, NDCG@5 = 1/log2(3 + 1) = 0,5.

Quy tắc chung:
  - ứng viên của u = mọi sản phẩm (hoặc chỉ ống, ở kịch bản) trừ sản phẩm u có trong train; khi chấm test bỏ thêm
    item val (QĐ 5-1);
  - hạng(p) = 1 + #{j ứng viên: s_j > s_p} + #{j ứng viên: s_j = s_p và π(j) < π(p)}; π là hoán vị cố định
    (seed 20261009), dùng chung cho mọi mô hình (mục 3.3);
  - top-K xếp theo (điểm giảm dần, π tăng dần) trên đúng tập ứng viên đó, nên khớp với hạng: script kiểm
    "hạng ≤ K ⇔ item cần đoán nằm trong top-K" cho mọi người dùng;
  - Recall@K tính từ top-K (số item cần đoán trong top-K / số item cần đoán = 1), Hit@K và NDCG@K tính từ hạng;
    script kiểm Recall@K = Hit@K từng người;
  - CVR@K lấy top-K này, phán bằng common_05.judge_lens (QĐ 4-9), gộp micro.
"""

import csv
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402

TIE_SEED  = 20261009          # hoán vị hòa π (mục 3.3)
BOOT_SEED = 20261009          # bootstrap (mục 8)
K_LIST    = [5, 10, 20]
K_MAX     = 20
TYPE_NAME = {0: "than", 1: "ong", 2: "phu_kien", 3: "khac"}
N5_DIR    = C.RESULTS_DIR / "n5"
ADAPTER_CSV = C.DATA_DIR / "kg" / "kg_edges_requires_adapter.csv"
DEVICE    = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Đầu vào ghi sha256 vào mỗi lần chạy (mục 3.1, 11)
INPUT_FILES = [C.TRAIN_TXT, C.VAL_TXT, C.TEST_TXT, C.VAL_NEG_JSON, C.TEST_NEG_JSON, C.ITEM_ATTR_CSV, C.KG_PT,
               *C.M1_EDGE_CSVS, ADAPTER_CSV, C.UNKNOWN_NPZ, C.BODY_INDEX, C.LENS_INDEX,
               Path(C.__file__), Path(__file__)]


# -- Ghi chép lần chạy ------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def inputs_sha256():
    return {str(Path(p).resolve().relative_to(C.ROOT)).replace("\\", "/"): sha256(p) for p in INPUT_FILES}


def git_state():
    """Commit hiện tại và cây git có file đã theo dõi bị sửa mà chưa commit không (bỏ qua file chưa theo dõi)."""
    def run(*a):
        return subprocess.run(["git", *a], cwd=C.ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain", "--untracked-files=no"))}


class Log:
    """In ra màn hình và ghi vào một file log mới (không ghi đè: file đã có thì DỪNG)."""
    def __init__(self, path):
        self.path = Path(path)
        assert not self.path.exists(), f"log đã có, không ghi đè: {self.path}"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "w", encoding="utf-8")

    def __call__(self, msg=""):
        print(msg, flush=True)
        self.f.write(msg + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


def now_tag():
    return time.strftime("%Y%m%d_%H%M%S")


# -- Dữ liệu đánh giá ------------------------------------------------------

def tie_keys(n_items=None, seed=TIE_SEED):
    """π[j] = khóa hòa của sản phẩm j: một hoán vị ngẫu nhiên cố định của 0..n_items-1."""
    return np.random.default_rng(seed).permutation(C.N_ITEMS if n_items is None else n_items).astype(np.int64)


@dataclass
class Split:
    """Một tập cần chấm. users[i] có item cần đoán pos[i]; sản phẩm bị bỏ khỏi ứng viên của users[i] là
    excl_col[excl_ptr[i]:excl_ptr[i+1]] (train, và item val khi chấm test)."""
    name: str
    users: np.ndarray
    pos: np.ndarray
    excl_ptr: np.ndarray
    excl_col: np.ndarray


def make_split(name, train, target, val=None, users=None):
    """train: {uid: set}; target: {uid: item cần đoán}; val: {uid: item val} — chỉ truyền khi chấm test (QĐ 5-1)."""
    if users is None:
        users = sorted(target)
    users = np.asarray(users, dtype=np.int64)
    pos = np.array([target[u] for u in users], dtype=np.int64)
    ptr, col = [0], []
    for u, p in zip(users.tolist(), pos.tolist()):
        ex = set(train.get(u, set()))
        if val is not None:
            ex.add(val[u])
        assert p not in ex, f"item cần đoán của user {u} nằm trong tập bị loại"
        col.extend(sorted(ex))
        ptr.append(len(col))
    return Split(name, users, pos, np.array(ptr, dtype=np.int64), np.array(col, dtype=np.int64))


def load_eval_split(split, train=None):
    """Tập chấm thật: 'val' (bỏ train) hoặc 'test' (bỏ train + item val)."""
    if train is None:
        train = C.load_train()
    val = C.load_pos("val")
    if split == "val":
        return make_split("val", train, val)
    if split == "test":
        return make_split("test", train, C.load_pos("test"), val=val)
    raise ValueError(split)


# -- Xếp hạng toàn bộ -------------------------------------------------------

@torch.no_grad()
def full_rank(score_batch, sp, pi, cand_items=None, k_max=K_MAX, batch=1024, device=DEVICE, k_list=K_LIST):
    """score_batch(uids LongTensor trên device) -> FloatTensor [b, n_items].
    cand_items: None = toàn catalog; mảng bool [n_items] = chỉ các sản phẩm này (vd chỉ ống, kịch bản mục 5.3).
    Trả về dict numpy theo thứ tự sp.users:
      rank [n]   hạng của item cần đoán trong tập ứng viên (quy tắc hòa π);
      top  [n, k_max] sản phẩm top-k_max theo (điểm giảm, π tăng), chỉ gồm ứng viên;
      n_tie [n]  số ứng viên khác item cần đoán có cùng điểm với nó."""
    pi_t = torch.as_tensor(pi, device=device)
    order = torch.argsort(pi_t)                                   # cột theo π tăng dần
    cand_row = None if cand_items is None else torch.as_tensor(np.asarray(cand_items, bool), device=device)
    ex_ptr, ex_col = sp.excl_ptr, sp.excl_col
    ranks, tops, ties = [], [], []
    n = len(sp.users)
    for s in range(0, n, batch):
        e = min(s + batch, n)
        b = e - s
        u = torch.as_tensor(sp.users[s:e], device=device)
        p = torch.as_tensor(sp.pos[s:e], device=device)
        S = score_batch(u).float()
        n_items = S.shape[1]
        assert not torch.isnan(S).any(), "điểm có NaN"
        ar = torch.arange(b, device=device)
        cand = (torch.ones(b, n_items, dtype=torch.bool, device=device) if cand_row is None
                else cand_row.unsqueeze(0).expand(b, n_items).clone())
        rows = torch.as_tensor(np.repeat(np.arange(b), np.diff(ex_ptr[s:e + 1])), device=device)
        cols = torch.as_tensor(ex_col[ex_ptr[s]:ex_ptr[e]], device=device)
        cand[rows, cols] = False
        assert bool(cand[ar, p].all()), "item cần đoán không nằm trong tập ứng viên"
        # hạng
        s_p = S[ar, p].unsqueeze(1)
        better = (S > s_p) & cand
        eq = (S == s_p) & cand
        eq[ar, p] = False
        before = eq & (pi_t.unsqueeze(0) < pi_t[p].unsqueeze(1))
        rank = 1 + better.sum(1) + before.sum(1)
        # top-k: sắp theo π tăng, rồi sort ổn định theo điểm giảm, rồi sort ổn định theo "là ứng viên" giảm
        Sx = S[:, order]
        cx = cand[:, order]
        i1 = torch.sort(Sx, dim=1, descending=True, stable=True).indices
        i2 = torch.sort(cx.gather(1, i1).to(torch.int8), dim=1, descending=True, stable=True).indices[:, :k_max]
        idx = i1.gather(1, i2)
        top = order[idx]
        assert bool(cand.gather(1, top).all()), "top-k chứa sản phẩm không phải ứng viên (ít ứng viên hơn k?)"
        for k in k_list:
            if k <= k_max:
                in_top = (top[:, :k] == p.unsqueeze(1)).any(1)
                assert torch.equal(in_top, rank <= k), f"hạng và top-{k} không khớp"
        ranks.append(rank.cpu())
        tops.append(top.cpu())
        ties.append(eq.sum(1).cpu())
    return {"rank": torch.cat(ranks).numpy().astype(np.int64),
            "top": torch.cat(tops).numpy().astype(np.int64),
            "n_tie": torch.cat(ties).numpy().astype(np.int64)}


def per_user_metrics(rank, top, pos, k_list=K_LIST):
    """Chỉ số từng người: hit, recall (tính từ top-K), ndcg. Kiểm recall = hit từng người."""
    out = {}
    for k in k_list:
        hit = (rank <= k).astype(np.float64)
        recall = (top[:, :k] == pos[:, None]).sum(1) / 1.0          # mỗi người dùng có đúng 1 item cần đoán
        assert np.array_equal(recall, hit), f"Recall@{k} khác Hit@{k}"
        out[f"hit@{k}"] = hit
        out[f"recall@{k}"] = recall
        out[f"ndcg@{k}"] = np.where(rank <= k, 1.0 / np.log2(rank + 1.0), 0.0)
    return out


def mean_metrics(per_user):
    return {k: float(v.mean()) for k, v in per_user.items()}


def type_mix(top, item_type, k=10):
    """Số thân / ống / phụ kiện / khác trung bình trong top-k (mục 3.4)."""
    t = item_type[top[:, :k]]
    return {TYPE_NAME[c]: float((t == c).sum(1).mean()) for c in sorted(TYPE_NAME)}


# -- CVR và kịch bản --------------------------------------------------------

def cvr_from_top(users, top, bodies, item_type, ctx, k_list=K_LIST):
    """CVR@K (QĐ 4-9) từ top-K đã xếp. bodies: {uid: set thân trong train}.
    Trả về (tổng hợp, từng người): từng người là mảng số ống chấm được / số vi phạm theo K (0 nếu không có thân)."""
    n = len(users)
    per = {k: (np.zeros(n, np.int64), np.zeros(n, np.int64)) for k in k_list}
    for r, u in enumerate(users.tolist()):
        bs = bodies.get(u)
        if not bs:
            continue
        verdict = [C.judge_lens(int(i), bs, ctx) if item_type[i] == 1 else None for i in top[r, :max(k_list)]]
        for k in k_list:
            v = [x for x in verdict[:k] if x is not None]
            per[k][0][r] = len(v)
            per[k][1][r] = sum(v)
    out = {}
    for k in k_list:
        nl, nv = per[k]
        out[f"cvr@{k}"] = float(nv.sum() / nl.sum()) if nl.sum() else float("nan")
        out[f"cvr_n_users@{k}"] = int((nl > 0).sum())
        out[f"cvr_n_lenses@{k}"] = int(nl.sum())
        out[f"cvr_n_violations@{k}"] = int(nv.sum())
    out["cvr_n_users_with_body"] = int(sum(1 for u in users.tolist() if bodies.get(u)))
    return out, per


def load_adapter_pairs():
    with open(ADAPTER_CSV, encoding="utf-8") as f:
        return {(int(r["body_iid"]), int(r["lens_iid"])) for r in csv.DictReader(f)}


def scenario_groups(users, pos, bodies, item_type, ctx, adapter=frozenset()):
    """Kịch bản 'ống cho người đã có thân' (mục 5.1): người có thân trong train, item cần đoán là ống trong M.
    Trả về mảng nhãn theo users: 'lap_duoc' (judge_lens False), 'khong_lap_duoc' (True), 'khong_phan_duoc' (None),
    '' = ngoài kịch bản; và mảng bool 'có cặp requires_adapter' (chỉ có nghĩa ở nhóm không lắp được)."""
    lab = np.full(len(users), "", dtype=object)
    adp = np.zeros(len(users), bool)
    for r, (u, it) in enumerate(zip(users.tolist(), pos.tolist())):
        bs = bodies.get(u)
        if not bs or item_type[it] != 1 or it not in ctx.lenses_in_m:
            continue
        v = C.judge_lens(it, bs, ctx)
        lab[r] = {False: "lap_duoc", True: "khong_lap_duoc", None: "khong_phan_duoc"}[v]
        adp[r] = v is True and any((b, it) in adapter for b in bs)
    return lab, adp


# -- MountAware: ống "chắc chắn vi phạm" -----------------------------------

def certain_violation_mask(bodies, ctx, n_users=None):
    """Mặt nạ bool [n_users, số ống trong M]: True = judge_lens(ống, thân của u) is True (mục 6.2).
    Người không có thân, hoặc có thân ngoài M, không có ống nào bị đánh dấu (judge_lens không bao giờ trả True)."""
    lens = np.array(sorted(ctx.lenses_in_m), dtype=np.int64)
    col = {int(l): j for j, l in enumerate(lens)}
    m1 = {}
    unk = {}
    for (b, l) in ctx.m1:
        m1.setdefault(b, np.zeros(len(lens), bool))[col[l]] = True
    for (b, l) in ctx.unknown:
        if l in col:
            unk.setdefault(b, np.zeros(len(lens), bool))[col[l]] = True
    zero = np.zeros(len(lens), bool)
    mask = np.zeros((C.N_USERS if n_users is None else n_users, len(lens)), bool)
    for u, bs in bodies.items():
        if not bs or any(b not in ctx.bodies_in_m for b in bs):
            continue
        ok = np.zeros(len(lens), bool)
        for b in bs:
            ok |= m1.get(b, zero) | unk.get(b, zero)
        mask[u] = ~ok
    return lens, mask


# -- Sampled 1+99 (số phụ, mục 3.5) ----------------------------------------

@torch.no_grad()
def sampled_rank(score_batch, sp, negs, batch=4096, device=DEVICE):
    """Hạng trong 1 + 99 âm mẫu của script 02. Quy tắc hòa của Hải (common_05._rank_of_pos cộng nhiễu dương vào
    âm mẫu): âm mẫu bằng điểm xếp trên item cần đoán, tức hạng = 1 + #{âm mẫu có điểm ≥ điểm item}. Không bỏ train."""
    neg = np.array([negs[u] for u in sp.users.tolist()], dtype=np.int64)
    out = []
    for s in range(0, len(sp.users), batch):
        e = min(s + batch, len(sp.users))
        S = score_batch(torch.as_tensor(sp.users[s:e], device=device)).float()
        p = torch.as_tensor(sp.pos[s:e], device=device)
        sp_ = S.gather(1, p.unsqueeze(1))
        sn = S.gather(1, torch.as_tensor(neg[s:e], device=device))
        out.append((1 + (sn >= sp_).sum(1)).cpu())
    return torch.cat(out).numpy().astype(np.int64)


# -- Chấm đầy đủ một mô hình trên một tập -----------------------------------

class EvalContext:
    """Nạp một lần mọi thứ cần để chấm: train, tập chấm, loại sản phẩm, CVR, kịch bản, π, âm mẫu."""
    def __init__(self, split, train=None):
        self.train = C.load_train() if train is None else train
        self.split = load_eval_split(split, self.train)
        self.item_type = C.load_item_type()
        self.ctx = C.load_cvr_context()
        self.bodies = C.build_train_bodies(self.train, None, self.item_type)
        self.pi = tie_keys()
        self.adapter = load_adapter_pairs()
        self.negs = C.load_negatives(split)
        self.scn_lab, self.scn_adp = scenario_groups(self.split.users, self.split.pos, self.bodies,
                                                     self.item_type, self.ctx, self.adapter)
        self.is_lens = self.item_type == 1


def evaluate(score_batch, ev, log=print, save_dir=None, prefix=""):
    """Chấm đủ theo kế hoạch: full ranking (chính), CVR@K, loại sản phẩm trong top-10, kịch bản (chỉ ống: chính;
    toàn catalog: phụ), sampled 1+99 (phụ). Lưu mảng từng người dùng (.npy) vào save_dir nếu có."""
    sp = ev.split
    t = time.time()
    fr = full_rank(score_batch, sp, ev.pi)
    pu = per_user_metrics(fr["rank"], fr["top"], sp.pos)
    res = {"split": sp.name, "n_users": int(len(sp.users)), "full": mean_metrics(pu),
           "n_users_tie_at_target": int((fr["n_tie"] > 0).sum()), "top10_type_mix": type_mix(fr["top"], ev.item_type)}
    cvr, cvr_pu = cvr_from_top(sp.users, fr["top"], ev.bodies, ev.item_type, ev.ctx)
    res["cvr"] = cvr
    log(f"  [{sp.name}] full ranking ({time.time() - t:.1f}s): " + " ".join(
        f"{m}@{k}={res['full'][f'{m}@{k}']:.4f}" for k in K_LIST for m in ("recall", "ndcg")))
    log(f"  [{sp.name}] người dùng có item cần đoán bị hòa điểm: {res['n_users_tie_at_target']:,} | "
        f"top-10 trung bình: {res['top10_type_mix']}")
    log(f"  [{sp.name}] CVR: " + " ".join(f"@{k}={cvr[f'cvr@{k}']:.4f} ({cvr[f'cvr_n_violations@{k}']:,}/"
                                       f"{cvr[f'cvr_n_lenses@{k}']:,} ống, {cvr[f'cvr_n_users@{k}']:,} người)"
                                       for k in K_LIST) + f" | người có thân {cvr['cvr_n_users_with_body']:,}")

    # Kịch bản: số chính chỉ ống, số phụ toàn catalog
    sel = np.flatnonzero(ev.scn_lab != "")
    sub = Split(sp.name, sp.users[sel], sp.pos[sel],
                np.concatenate([[0], np.cumsum(np.diff(sp.excl_ptr)[sel])]),
                np.concatenate([sp.excl_col[sp.excl_ptr[i]:sp.excl_ptr[i + 1]] for i in sel]))
    fl = full_rank(score_batch, sub, ev.pi, cand_items=ev.is_lens)
    pl = per_user_metrics(fl["rank"], fl["top"], sub.pos)
    cl_pu = cvr_from_top(sub.users, fl["top"], ev.bodies, ev.item_type, ev.ctx)[1]
    scn = {}
    for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"):
        m = ev.scn_lab[sel] == g
        d = {"n_users": int(m.sum()), "n_with_adapter_pair": int(ev.scn_adp[sel][m].sum())}
        if m.any():
            d["lens_only"] = {k: float(v[m].mean()) for k, v in pl.items()}
            d["lens_only_cvr"] = {f"cvr@{k}": (float(cl_pu[k][1][m].sum() / cl_pu[k][0][m].sum())
                                               if cl_pu[k][0][m].sum() else float("nan")) for k in K_LIST}
            d["lens_only_cvr_n_lenses"] = {f"@{k}": int(cl_pu[k][0][m].sum()) for k in K_LIST}
            d["full_catalog"] = {k: float(v[sel][m].mean()) for k, v in pu.items()}
        scn[g] = d
        if m.any():
            log(f"  [{sp.name}] kịch bản {g:<16} {d['n_users']:>5} người: chỉ ống " + " ".join(
                f"R@{k}={d['lens_only'][f'recall@{k}']:.4f}" for k in K_LIST) + " | CVR " + " ".join(
                f"@{k}={d['lens_only_cvr'][f'cvr@{k}']:.4f}" for k in K_LIST) + " | toàn catalog " + " ".join(
                f"R@{k}={d['full_catalog'][f'recall@{k}']:.4f}" for k in K_LIST))
    res["scenario"] = scn

    # Sampled 1+99 (số phụ)
    sr = sampled_rank(score_batch, sp, ev.negs)
    res["sampled_1_99"] = {f"{m}@{k}": float(v.mean()) for k in K_LIST for m, v in
                           (("hit", (sr <= k)), ("ndcg", np.where(sr <= k, 1 / np.log2(sr + 1.0), 0.0)))}
    log(f"  [{sp.name}] sampled 1+99 (số phụ): " + " ".join(f"{k}={v:.4f}" for k, v in res["sampled_1_99"].items()))

    if save_dir is not None:
        save_dir = Path(save_dir)
        arrays = {"users": sp.users, "rank_full": fr["rank"], "top20_full": fr["top"], "n_tie_full": fr["n_tie"],
                  "rank_sampled": sr, "scn_users": sub.users, "rank_lens_only": fl["rank"], "top20_lens_only": fl["top"]}
        for k in K_LIST:
            arrays[f"cvr_n_lenses@{k}"], arrays[f"cvr_n_viol@{k}"] = cvr_pu[k]
        res["arrays_sha256"] = {}
        for name, a in arrays.items():
            fn = save_dir / f"{prefix}{name.replace('@', '_at')}.npy"
            assert not fn.exists(), f"không ghi đè: {fn}"
            np.save(fn, np.ascontiguousarray(a))
            res["arrays_sha256"][fn.name] = sha256(fn)
    return res


# -- Bootstrap ghép cặp (mục 8) --------------------------------------------

def bootstrap_paired(series, pairs=(), B=2000, seed=BOOT_SEED, chunk=100):
    """series: {tên: (tử số [n], mẫu số [n] hoặc None)} — chỉ số = tổng tử / tổng mẫu (None: mẫu = số người).
    Mọi chuỗi dùng CHUNG các mẫu người dùng (ghép cặp). pairs: [(a, b)] -> khoảng của a − b.
    Trả về {tên: (điểm, thấp 2,5%, cao 97,5%)}."""
    names = list(series)
    n = len(next(iter(series.values()))[0])
    rng = np.random.default_rng(seed)
    draws = {nm: [] for nm in names}

    def stat(nm, idx):
        num, den = series[nm]
        s = num[idx].sum(axis=-1)
        return s / (den[idx].sum(axis=-1) if den is not None else idx.shape[-1])

    for s in range(0, B, chunk):
        idx = rng.integers(0, n, size=(min(chunk, B - s), n))
        for nm in names:
            draws[nm].append(stat(nm, idx))
    draws = {nm: np.concatenate(v) for nm, v in draws.items()}
    full = np.arange(n)
    out = {nm: (float(stat(nm, full)), *map(float, np.percentile(draws[nm], [2.5, 97.5]))) for nm in names}
    for a, b in pairs:
        d = draws[a] - draws[b]
        out[f"{a} - {b}"] = (out[a][0] - out[b][0], *map(float, np.percentile(d, [2.5, 97.5])))
    return out
