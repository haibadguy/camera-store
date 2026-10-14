"""Kiểm các ví dụ tính tay trong docs/cakg_design.md (mỗi khối một ví dụ nhỏ, số do người viết đặt ra).

CHỈ TÍNH SỐ trên ví dụ dựng tay, không đọc dữ liệu thật, không huấn luyện. Mục đích: mọi con số của ví dụ trong tài
liệu thiết kế có nguồn là output script (CLAUDE.md, nguyên tắc 4), và công thức trong tài liệu khớp code mẫu.
Log ghi ra file TÊN MỚI trong ai/data/survey/cakg/.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/vidu_tinh_tay.py --label 20261014_lan1
"""
import argparse
import math
import os
import sys

sys.path.insert(0, "ai/survey/report")
from report_common import Log, header  # noqa: E402


def sig(x):
    return 1 / (1 + math.exp(-x))


def softmax(xs):
    m = max(xs)
    e = [math.exp(x - m) for x in xs]
    s = sum(e)
    return [v / s for v in e]


def lrelu(x, a=0.2):
    return x if x > 0 else a * x


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg", f"run_vidu_tinh_tay_{a.label}.log"))
    header(log, __file__)

    # ── Khối 1: LightGCN, 1 lớp, embedding 1 chiều ──
    log("\nKhối 1 — LightGCN (L = 1 lớp, d = 1)")
    log("  cạnh train: u1–A, u1–B, u2–B, u2–C; bậc: u1 2, u2 2, A 1, B 2, C 1")
    e0 = {"u1": 1.0, "u2": 0.0, "A": 0.5, "B": -0.5, "C": 1.0}
    N = {"u1": ["A", "B"], "u2": ["B", "C"], "A": ["u1"], "B": ["u1", "u2"], "C": ["u2"]}
    e1 = {v: sum(e0[w] / math.sqrt(len(N[v]) * len(N[w])) for w in N[v]) for v in e0}
    ef = {v: (e0[v] + e1[v]) / 2 for v in e0}
    for v in e0:
        log(f"  {v}: e(0) = {e0[v]:+.4f}, e(1) = {e1[v]:+.5f}, e = (e(0) + e(1)) / 2 = {ef[v]:+.5f}")
    yB, yC = ef["u1"] * ef["B"], ef["u1"] * ef["C"]
    log(f"  ŷ(u1, B) = {yB:+.5f}; ŷ(u1, C) = {yC:+.5f}; BPR(u1, B, C) = −ln σ(ŷB − ŷC) = "
        f"{-math.log(sig(yB - yC)):.5f}")

    # ── Khối 2: một lớp RGAT tại thân b ──
    log("\nKhối 2 — một lớp RGAT (WIRGAT, logit cộng) tại thân b, d = 2, W^(r) = I, W_0 = I, bias 0")
    hb, hl1, hl2, hm = (0.5, 0.5), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)
    q, k = (1.0, 0.0), (0.0, 1.0)
    qi = dot(hb, q)
    logits = [lrelu(qi + dot(hl1, k)), lrelu(qi + dot(hl2, k))]
    al = softmax(logits)
    log(f"  quan hệ rev_compatible_with: q_b = {qi:.2f}; k_l1 = {dot(hl1, k):.2f}, k_l2 = {dot(hl2, k):.2f}; "
        f"logit {logits[0]:.2f}, {logits[1]:.2f}; α = {al[0]:.4f}, {al[1]:.4f}")
    msg_c = tuple(al[0] * x + al[1] * y for x, y in zip(hl1, hl2))
    out = tuple(m + n_ + s for m, n_, s in zip(msg_c, hm, hb))
    log(f"  tin từ ống: {msg_c[0]:.4f}, {msg_c[1]:.4f}; tin từ ngàm (α = 1): {hm}; tự giữ W_0 h_b: {hb}")
    log(f"  h_b' = ReLU(tổng) = ({max(out[0], 0):.4f}, {max(out[1], 0):.4f})")

    # ── Khối 3 + 4: gộp kênh ──
    log("\nKhối 3–4 — gộp kênh: ω_c = qᵀ tanh(W x_c + b), W = I, b = 0, q = (1, 1); z = [β_e e ; β_h h]")
    q2 = (1.0, 1.0)

    def fuse(e, h):
        we = dot(q2, [math.tanh(x) for x in e])
        if h is None:
            return [1.0, 0.0], list(e) + [0.0, 0.0], we, None
        wh = dot(q2, [math.tanh(x) for x in h])
        be, bh = softmax([we, wh])
        return [be, bh], [be * x for x in e] + [bh * x for x in h], we, wh
    cases = {"ống l2": ((0.2, 0.4), (0.6, 0.0)), "người u1 (có thân b)": ((0.5, 0.1), (0.4, 0.2)),
             "thẻ nhớ C (không có h)": ((0.3, 0.2), None), "người u2 (không có thân)": ((0.1, 0.3), None)}
    Z = {}
    for name, (e, h) in cases.items():
        beta, z, we, wh = fuse(e, h)
        Z[name] = z
        log(f"  {name}: e = {e}, h = {h}; ω_e = {we:.5f}" + (f", ω_h = {wh:.5f}" if wh is not None else
            ", ω_h = −∞ (không có kênh)") + f"; β = ({beta[0]:.5f}, {beta[1]:.5f}); z = "
            + "(" + ", ".join(f"{x:.5f}" for x in z) + ")")
    s1 = dot(Z["người u1 (có thân b)"], Z["ống l2"])
    beh = dot(Z["người u1 (có thân b)"][:2], Z["ống l2"][:2])
    hw = dot(Z["người u1 (có thân b)"][2:], Z["ống l2"][2:])
    log(f"  ŷ(u1, l2) = z_u1 · z_l2 = {s1:.5f} = phần hành vi {beh:.5f} + phần phần cứng {hw:.5f}")
    s2 = dot(Z["người u2 (không có thân)"], Z["thẻ nhớ C (không có h)"])
    log(f"  ŷ(u2, C) = {s2:.5f} = e_u2 · e_C = {dot((0.1, 0.3), (0.3, 0.2)):.5f} (đúng bằng LightGCN)")
    s3 = dot(Z["người u1 (có thân b)"], Z["thẻ nhớ C (không có h)"])
    log(f"  ŷ(u1, C) = {s3:.5f} = β_e(u1) · e_u1 · e_C (phần phần cứng = 0)")

    # ── Khối 5: L_comp ──
    log("\nKhối 5 — L_comp cho một cặp dương, τ = 0,2")
    sims = {"l1 EF 50mm (M = 1, dương)": 0.8, "l2 EF-S 18-55 (M = 0, âm)": 0.3, "l3 Nikon DX 35mm (M = 0, âm)": -0.2,
            "l4 Sigma 17-50 DC cho Canon (U = 1, bỏ)": 0.6}
    tau = 0.2
    sp = sims["l1 EF 50mm (M = 1, dương)"] / tau
    sn = [sims["l2 EF-S 18-55 (M = 0, âm)"] / tau, sims["l3 Nikon DX 35mm (M = 0, âm)"] / tau]
    lc = -math.log(math.exp(sp) / (math.exp(sp) + sum(math.exp(x) for x in sn)))
    log(f"  sim/τ: dương {sp:.2f}; âm {sn[0]:.2f}, {sn[1]:.2f}; l4 không vào mẫu số")
    log(f"  ℓ = −log(e^{sp:.0f} / (e^{sp:.0f} + e^{sn[0]:.1f} + e^{sn[1]:.0f})) = log(1 + e^{sn[0] - sp:.1f} + "
        f"e^{sn[1] - sp:.0f}) = {lc:.5f}")
    lc_wrong = -math.log(math.exp(sp) / (math.exp(sp) + sum(math.exp(x) for x in sn) + math.exp(0.6 / tau)))
    log(f"  (nếu lỡ đưa l4 vào mẫu số: {lc_wrong:.5f}, phạt một cặp không biết đúng sai)")

    # ── Khối 6: L_total ──
    log("\nKhối 6 — L_total = L_BPR + λ1 L_comp + λ2 ‖Θ‖²")
    lb, reg, l1, l2 = 0.60, 2.5, 0.1, 1e-3
    log(f"  L_BPR = {lb}, L_comp = {lc:.5f}, ‖Θ_batch‖² = {reg}, λ1 = {l1}, λ2 = {l2}: "
        f"L_total = {lb + l1 * lc + l2 * reg:.5f}")

    # ── Khối 7: mặt nạ và CVR ──
    log("\nKhối 7 — mặt nạ, CVR trước / sau")
    log("  người có Sony a7 (sony_e) + Nikon D750 (nikon_f); top-4 trước mặt nạ: Nikon 200-500 (D750 M = 1), "
        "Canon EF 70-200 (cả hai M = 0), thẻ nhớ, Sony FE 50 (a7 M = 1)")
    log("  CVR trước mặt nạ @4 = 1 vi phạm / 3 ống chấm được = " f"{1 / 3:.4f}")
    log("  QĐ 4-9 chặn Canon EF (mọi thân M = 0); KHÔNG chặn Nikon 200-500 (D750 M = 1)")
    log("  biến thể ∃b chặn cả Canon EF lẫn Nikon 200-500 (a7 M = 0) và Sony FE 50 (D750 M = 0)")

    # ── Khối 8: giải thích ──
    log("\nKhối 8 — đóng góp từng thân vào phần phần cứng (h_u = trung bình h_b)")
    hb1, hb2, hl = (0.9, 0.1), (0.3, 0.5), (0.8, 0.2)
    bu, bi = 0.4, 0.5
    c1 = bu * bi * dot(hb1, hl) / 2
    c2 = bu * bi * dot(hb2, hl) / 2
    hu = tuple((x + y) / 2 for x, y in zip(hb1, hb2))
    tot = bu * bi * dot(hu, hl)
    log(f"  β_h(u) = {bu}, β_h(l) = {bi}; c(D750) = {c1:.4f}, c(D500) = {c2:.4f}; tổng = {c1 + c2:.4f} = "
        f"β_h(u) β_h(l) ⟨h_u, h_l⟩ = {tot:.4f}; chọn b* = D750")

    # ── Khối 9: KGAT ──
    log("\nKhối 9 — attention KGAT π(h, r, t) = (W_r e_t)ᵀ tanh(W_r e_h + e_r), W_r = I")
    eh, er = (0.5, 0.5), (0.1, 0.0)
    t1, t2 = (1.0, 0.0), (0.0, 1.0)
    th = [math.tanh(x + y) for x, y in zip(eh, er)]
    p = [dot(t1, th), dot(t2, th)]
    sp_ = softmax(p)
    log(f"  tanh(e_h + e_r) = ({th[0]:.5f}, {th[1]:.5f}); π thô = {p[0]:.5f}, {p[1]:.5f}; "
        f"sau softmax = {sp_[0]:.5f}, {sp_[1]:.5f}")
    log.save()


if __name__ == "__main__":
    main()
