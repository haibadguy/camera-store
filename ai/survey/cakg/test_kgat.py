"""Kiểm thử dựng tay phần B (KGAT, ai/pipeline/kgat_model.py) theo docs/reviews/cakg_eval_plan.md mục 11. Viết 14/10/2026.

KHÔNG huấn luyện đến hội tụ, không chấm val / test (chỉ 1 epoch pha KG trên đồ thị thật ở K6 để kiểm π được cập nhật).

 K1. Attention (28), ví dụ thiết kế khối 9: π = 0,51872 / 0,48128; và so với cách tính độc lập bằng numpy trên đồ thị nhỏ
     ngẫu nhiên nhiều quan hệ (softmax theo đầu h trên MỌI quan hệ).
 K2. Lan truyền (29)–(30) so với tính tay bằng numpy (W, b, π cho trước, chế độ eval): Bi-Interaction, LeakyReLU 0,2,
     lớp sau nhận e chưa chuẩn hóa, e* = e⁰ ‖ norm(e¹) ‖ ...
 K3. Attention MỚI được dùng ở lan truyền sau: sau after_epoch, π đổi và propagate() = tính tay với π mới (khác π cũ).
 K4. L_KG (27) và L_CF so với tính tay (l2 = Σx²/2, chia batch cố định như code).
 K5. Lấy mẫu KG trên đồ thị thật: đầu khác nhau trong một batch, (h, r, t) dương là bộ ba thật, (h, r, t') âm không bao
     giờ là bộ ba thật; 546 batch / epoch.
 K6. Đồ thị thật: 95.646 nút, 1.116.682 cạnh; tổng π theo đầu = 1; π nằm trong state_dict, nạp lại -> cùng điểm.
 K7. Chế độ eval không dropout: hai lần score_fn chỉ lệch sai số GPU (phép nhân thưa không tất định); train có
     dropout (lệch lớn hơn hẳn).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/test_kgat.py --label 20261014_lan1
"""
import argparse
import importlib
import math
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import kgat_model as KM  # noqa: E402

T07 = importlib.import_module("07_kgat_train")
DEV = E.DEVICE
fails = 0
log = None


def check(name, got, want, tol=5e-6):
    global fails
    if isinstance(want, (float, int)) and not isinstance(want, bool) and isinstance(got, (float, int)):
        ok = math.isclose(float(got), float(want), abs_tol=tol)
    else:
        ok = got == want
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


def check_le(name, got, bound):
    global fails
    ok = got <= bound
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got:.3e} (≤ {bound:g})")


def np_attention(E_, Er, Wr, h, r, t, n):
    s = np.array([(E_[t[k]] @ Wr[r[k]]) @ np.tanh(E_[h[k]] @ Wr[r[k]] + Er[r[k]]) for k in range(len(h))])
    out = np.zeros_like(s)
    for hh in np.unique(h):
        m = h == hh
        e = np.exp(s[m] - s[m].max())
        out[m] = e / e.sum()
    return out


def np_propagate(E_, pi, h, t, W1, b1, W2, b2, n):
    A = np.zeros((n, n))
    for k in range(len(h)):
        A[h[k], t[k]] += pi[k]
    lr = lambda x: np.where(x > 0, x, 0.2 * x)  # noqa: E731
    ego, out = E_, [E_]
    for k in range(len(W1)):
        side = A @ ego
        ego = lr((ego + side) @ W1[k].T + b1[k]) + lr((ego * side) @ W2[k].T + b2[k])
        out.append(ego / np.maximum(np.linalg.norm(ego, axis=1, keepdims=True), 1e-12))
    return np.concatenate(out, 1)


def toy(n=6, R=3, nE=14, dims=(4, 4, 3, 2), seed=0):
    g = torch.Generator().manual_seed(seed)
    pairs = set()
    while len(pairs) < nE:
        pairs.add((int(torch.randint(0, n, (1,), generator=g)), int(torch.randint(0, R, (1,), generator=g)),
                   int(torch.randint(0, n, (1,), generator=g))))
    pairs = sorted(pairs)
    ei = torch.tensor([[p[0] for p in pairs], [p[2] for p in pairs]])
    et = torch.tensor([p[1] for p in pairs])
    torch.manual_seed(seed)
    m = KM.KGAT(n, R, ei.to(DEV), et.to(DEV), 0, 3, 3, 3, dims=dims, cf_batch=4, kg_batch=4)
    return m, ei.numpy(), et.numpy()


def k1():
    log("\n=== K1. Attention (28) ===")
    ei = torch.tensor([[0, 0], [1, 2]])
    et = torch.tensor([0, 0])
    m = KM.KGAT(3, 1, ei.to(DEV), et.to(DEV), 0, 1, 1, 2, dims=(2, 2))
    with torch.no_grad():
        m.E.copy_(torch.tensor([[0.5, 0.5], [1.0, 0.0], [0.0, 1.0]]))
        m.Er.copy_(torch.tensor([[0.1, 0.0]]))
        m.Wr.copy_(torch.eye(2).view(1, 2, 2))
        pi = m.attention()
    check("π(h, r, t1), π(h, r, t2)", [round(x, 5) for x in pi.tolist()], [0.51872, 0.48128])
    m, ei_np, et_np = toy()
    with torch.no_grad():
        got = m.attention().cpu().numpy()
    want = np_attention(m.E.detach().cpu().numpy(), m.Er.detach().cpu().numpy(), m.Wr.detach().cpu().numpy(),
                        ei_np[0], et_np, ei_np[1], 6)
    check_le("đồ thị nhỏ 6 nút, 3 quan hệ, 14 bộ ba: lệch π so với numpy", float(np.abs(got - want).max()), 1e-6)
    check("π khởi tạo = attention của embedding khởi tạo", bool(np.allclose(m.pi.cpu().numpy(), want, atol=1e-6)), True)


def k2_k3():
    log("\n=== K2. Lan truyền (29)–(30) ===")
    m, ei_np, et_np = toy()
    m.eval()
    P = lambda t: t.detach().cpu().numpy()  # noqa: E731
    W1 = [P(w.weight) for w in m.W1]
    b1 = [P(w.bias) for w in m.W1]
    W2 = [P(w.weight) for w in m.W2]
    b2 = [P(w.bias) for w in m.W2]
    with torch.no_grad():
        got = P(m.propagate())
    want = np_propagate(P(m.E), P(m.pi), ei_np[0], ei_np[1], W1, b1, W2, b2, 6)
    check("kích thước e* = 4 + 4 + 3 + 2", got.shape[1], 13)
    check_le("propagate() so với numpy", float(np.abs(got - want).max()), 1e-5)
    check("lớp 0 của e* không chuẩn hóa (= E)", bool(np.allclose(got[:, :4], P(m.E))), True)

    log("\n=== K3. π mới được dùng ở lan truyền sau ===")
    m.train()
    old_pi = P(m.pi).copy()
    rng = np.random.default_rng(0)
    m.after_epoch(rng)
    m.eval()
    new_pi = P(m.pi)
    check("π đổi sau after_epoch (pha KG đổi embedding)", bool(np.abs(new_pi - old_pi).max() > 1e-7), True)
    with torch.no_grad():
        got = P(m.propagate())
        W1 = [P(w.weight) for w in m.W1]
        b1 = [P(w.bias) for w in m.W1]
        W2 = [P(w.weight) for w in m.W2]
        b2 = [P(w.bias) for w in m.W2]
    want_new = np_propagate(P(m.E), new_pi, ei_np[0], ei_np[1], W1, b1, W2, b2, 6)
    want_old = np_propagate(P(m.E), old_pi, ei_np[0], ei_np[1], W1, b1, W2, b2, 6)
    check_le("propagate() sau after_epoch = tính tay với π MỚI", float(np.abs(got - want_new).max()), 1e-5)
    check("... và khác tính tay với π cũ", bool(np.abs(got - want_old).max() > 1e-6), True)
    want_pi = np_attention(P(m.E), P(m.Er), P(m.Wr), ei_np[0], et_np, ei_np[1], 6)
    check_le("π mới = attention của embedding SAU pha KG", float(np.abs(new_pi - want_pi).max()), 1e-6)


def k4():
    log("\n=== K4. L_KG (27), L_CF ===")
    m, ei_np, et_np = toy()
    m.eval()
    h, r, t, tn = (torch.tensor(x, device=DEV) for x in ([0, 1, 2, 3], [0, 1, 2, 0], [1, 2, 3, 4], [5, 4, 0, 1]))
    with torch.no_grad():
        got, base = m.kg_loss(h, r, t, tn)
    P = lambda x: x.detach().cpu().numpy()  # noqa: E731
    E_, Er, Wr = P(m.E), P(m.Er), P(m.Wr)
    H, Rr, Tt, Tn = (P(x) for x in (h, r, t, tn))
    eh = np.stack([E_[a] @ Wr[b] for a, b in zip(H, Rr)])
    ep = np.stack([E_[a] @ Wr[b] for a, b in zip(Tt, Rr)])
    en = np.stack([E_[a] @ Wr[b] for a, b in zip(Tn, Rr)])
    er = Er[Rr]
    gp = ((eh + er - ep) ** 2).sum(1)
    gn = ((eh + er - en) ** 2).sum(1)
    b_ = np.log1p(np.exp(-(gn - gp))).mean()
    reg = 1e-5 * sum((x ** 2).sum() / 2 for x in (eh, er, ep, en)) / 4
    check("L_KG phần chính", round(float(base), 6), round(float(b_), 6))
    check("L_KG = chính + 1e-5 (l2(Wh) + l2(e_r) + l2(Wt) + l2(Wt')) / batch", round(float(got), 6), round(float(b_ + reg), 6))
    u, i, j = (torch.tensor(x, device=DEV) for x in ([0, 1, 2, 0], [0, 1, 2, 1], [2, 0, 1, 2]))
    with torch.no_grad():
        lcf = float(m.loss(u, i, j))
        Z = P(m.propagate())
    zu, zi, zj = Z[[0, 1, 2, 0]], Z[[3, 4, 5, 4]], Z[[5, 3, 4, 5]]
    w = np.log1p(np.exp(-((zu * zi).sum(1) - (zu * zj).sum(1)))).mean() + \
        1e-5 * sum((x ** 2).sum() / 2 for x in (zu, zi, zj)) / 4
    check("L_CF = BPR + 1e-5 (l2(e*_u) + l2(e*_i) + l2(e*_j)) / batch (đuôi item có offset)", round(lcf, 6),
          round(float(w), 6))


def real_checks():
    log("\n=== K5–K7. Đồ thị thật ===")
    train = C.load_train()
    torch.manual_seed(0)
    cfg = T07.make_cfg(1e-3, 0)
    m = T07.build_kgat(cfg, train, log=lambda s: log("  " + s))
    check("số nút / cạnh", [m.n, int(m.head.numel())], [95646, 1116682])
    check("số batch KG / epoch = 1.116.682 // 2048 + 1", m.n_kg_batches, 546)
    s = torch.zeros(m.n, device=DEV).index_add_(0, m.head, m.pi)
    heads = torch.unique(m.head)
    check_le("tổng π theo đầu h = 1: lệch tối đa", float((s[heads] - 1).abs().max()), 1e-5)
    rng = np.random.default_rng(1)
    keys = set(((m._kg_h * m.R + m._kg_r) * m.n + m._kg_t).tolist())
    ok_pos = ok_neg = ok_dist = True
    for _ in range(10):
        h, r, t, tn = m.sample_kg(rng)
        ok_dist &= len(np.unique(h)) == len(h)
        ok_pos &= all(((a * m.R + b) * m.n + c) in keys for a, b, c in zip(h, r, t))
        ok_neg &= not any(((a * m.R + b) * m.n + c) in keys for a, b, c in zip(h, r, tn))
    check("10 batch KG: đầu khác nhau trong batch", bool(ok_dist), True)
    check("10 batch KG: bộ ba dương là bộ ba thật", bool(ok_pos), True)
    check("10 batch KG: không âm mẫu nào là bộ ba thật", bool(ok_neg), True)
    # K7: eval tất định, train có dropout
    m.eval()
    users = torch.arange(0, 512, device=DEV)
    with torch.no_grad():
        a1 = m.score_fn()(users)
        a2 = m.score_fn()(users)
    d_eval = float((a1 - a2).abs().max())
    check_le("eval: hai lần score_fn lệch (chỉ sai số cộng dồn không tất định của phép nhân thưa trên GPU)", d_eval,
             1e-5)
    m.train()
    with torch.no_grad():
        z1, z2 = m.propagate(), m.propagate()
        d_train = float((z1 - z2).abs().max())
    check("train: message dropout làm hai lần lan truyền lệch nhiều hơn hẳn (> 1000 × lệch eval)",
          d_train > 1000 * max(d_eval, 1e-9), True)
    log(f"  lệch eval {d_eval:.3e}, lệch train {d_train:.3e}")
    # K6: π trong state_dict; nạp lại cho cùng điểm
    m.eval()
    with torch.no_grad():
        m.set_attention(torch.rand_like(m.pi))
        ref = m.score_fn()(users)
    sd = {k: v.clone() for k, v in m.state_dict().items()}
    check("π nằm trong state_dict", "pi" in sd, True)
    torch.manual_seed(5)
    m2 = T07.build_kgat(cfg, train, log=lambda s: None)
    m2.load_state_dict(sd)
    m2.eval()
    with torch.no_grad():
        got = m2.score_fn()(users)
    check_le("nạp state_dict -> cùng điểm (π và ma trận lan truyền dựng lại)", float((got - ref).abs().max()), 1e-5)


def main():
    global log
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg", f"run_test_kgat_{a.label}.log"))
    header(log, __file__)
    log(f"thiết bị {DEV}" + (f" ({torch.cuda.get_device_name(0)})" if DEV.type == "cuda" else ""))
    k1()
    k2_k3()
    k4()
    real_checks()
    log(f"\n{'ĐẠT CẢ' if fails == 0 else f'CÓ {fails} KIỂM TRA SAI'}")
    log.save()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
