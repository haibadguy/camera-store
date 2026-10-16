"""Vẽ các hình của chương 2 quyển đồ án.

CHỈ ĐỌC. Mọi số trên hình đọc từ file kết quả / log đã có, không gõ tay:
- Hình 2.1 (sơ đồ luồng xử lý): filtering_stats.json, train/val/test.txt, mount_compat_stats.json, kg_stats.json;
- Hình 2.2 (lược đồ đồ thị tri thức): kg_stats.json (dùng lại hàm vẽ của ai/survey/report/hinh_ch45.py);
- Hình 2.3 (kết quả test chính), Hình 2.5 (lấy mẫu 1 + 99 so với xếp hạng toàn bộ): summary_test_*.json của
  nội dung 5 (09/10) và nội dung 6–8 (15/10), test lần 1, 3 seed;
- Hình 2.4 (thành phần top-10 của người có thân): log phân tích sau test
  ai/data/survey/redteam/run_redteam_cakg_b_20261015_lan1.log (test và val) và dung2.json / select.json (val, v2).

Chạy:
  E:\\DATN\\camera-store\\ai\\.venv\\Scripts\\python.exe ai/survey/report_c2/hinh_c2.py --root E:/DATN/camera-store \\
      --out E:/DATN/baocao/do_an/hinh --label 20261017_lan1
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "report"))
from c2_common import Inputs, Log, header, sha256_file, vn_dec, vn_int  # noqa: E402
import bang_c2 as B  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch  # noqa: E402

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e4e3df"
SERIES = "#2a78d6"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # thân, ống, phụ kiện, khác (đã chạy validate_palette)
BOX_FILL, BOX_EDGE = "#e8f1fc", "#2a78d6"
OFF_FILL, OFF_EDGE = "#f4f4f2", "#898781"
SURFACE = "white"


# --------------------------------------------------------------------------- Hình 2.1
def box(ax, x, y, w, h, text, fs=7.6, on=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=BOX_FILL if on else OFF_FILL, ec=BOX_EDGE if on else OFF_EDGE,
                                lw=0.9, ls="-" if on else (0, (4, 2.5))))
    ax.text(x + w / 2, y + h / 2, text, fontsize=fs, color=INK if on else INK2, ha="center", va="center",
            linespacing=1.35)


def arrow(ax, p0, p1, ls="-", color=INK2):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, color=color, lw=0.9, ls=ls,
                                 shrinkA=0, shrinkB=0))


def line(ax, pts, ls="-", color=INK2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=0.9, ls=ls, solid_capstyle="butt")


def fig_pipeline(d, out):
    W, H = 6.6, 9.0
    fig = plt.figure(figsize=(W, H), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    x0, w, h = 0.6, 5.4, 0.64
    y = {"b1": 8.2, "b2": 7.28, "b3": 6.36, "b4": 5.44, "b5": 4.22, "b6": 3.3, "b7": 2.38, "b8": 1.46, "b9": 0.62}
    box(ax, x0, y["b1"], w, h, "Dữ liệu thô: Amazon Reviews 2023, nhóm Electronics\n"
        f"{vn_int(d['n_rev'])} đánh giá, {vn_int(d['n_meta'])} sản phẩm có thông tin")
    box(ax, x0, y["b2"], w, h, "Tiền xử lý (mục 2.2): lọc lĩnh vực máy ảnh, gộp tương tác lặp, k-core k = 5, chia theo thời gian\n"
        f"{vn_int(d['n_u'])} người dùng, {vn_int(d['n_i'])} sản phẩm, {vn_int(d['n_x'])} tương tác; "
        f"train {vn_int(d['n_tr'])}, val và test mỗi tập {vn_int(d['n_te'])}", fs=7.2)
    box(ax, x0, y["b3"], w, h, f"Phân loại sản phẩm, đọc ngàm và khung, {d['n_rule']} luật tương thích (mục 2.3)\n"
        f"ma trận M {vn_int(d['nb'])} × {vn_int(d['nl'])}: {vn_int(d['m1'])} cặp M = 1; "
        f"mặt nạ U: {vn_int(d['u1'])} cặp \"không biết\"")
    box(ax, x0, y["b4"], w, h, "Đồ thị tri thức dị thể $\\mathcal{G}$ (mục 2.3)\n"
        f"{vn_int(d['kg_n'])} nút thuộc {d['kg_tn']} loại, {d['kg_te']} loại cạnh (kể cả chiều ngược), {vn_int(d['kg_e'])} cạnh")
    hw = 2.55
    box(ax, x0, y["b5"], hw, 0.8, "Kênh hành vi (mục 2.2)\nLightGCN 3 lớp trên đồ thị\nngười dùng – sản phẩm (chỉ train)\n"
        "$\\rightarrow\\ \\mathbf{e}_u,\\ \\mathbf{e}_i$", fs=7.2)
    box(ax, x0 + w - hw, y["b5"], hw, 0.8, "Kênh phần cứng (mục 2.3)\nRGAT 2 lớp trên đồ thị con $H$\n(thân, ống, ngàm, khổ, mục đích)\n"
        "$\\rightarrow\\ \\mathbf{h}_b,\\ \\mathbf{h}_l,\\ \\mathbf{h}_u$", fs=7.2, on=False)
    bx6 = 2.3
    box(ax, bx6, y["b6"], x0 + w - bx6, h, "Gộp kênh có cổng và $\\mathcal{L}_{\\mathrm{comp}}$ (mục 2.4)\n"
        "$\\hat{y}_{ui}$ = phần hành vi + phần phần cứng;  $\\mathcal{L}=\\mathcal{L}_{\\mathrm{BPR}}+\\lambda_1\\mathcal{L}_{\\mathrm{comp}}"
        "+\\lambda_2\\|\\Theta\\|^2$", fs=7.0, on=False)
    box(ax, x0, y["b7"], w, h, "Lớp mặt nạ cứng (1.7) khi xếp hạng (mục 2.4)\n"
        "chặn ống mà mọi thân của người dùng chắc chắn không lắp được, rồi lấy top-K")
    box(ax, x0, y["b8"], w, h, "Giải thích theo đường $u \\rightarrow b^* \\rightarrow l \\rightarrow c^*$ (mục 2.4)\n"
        "câu tiếng Việt theo mẫu, mọi chỗ trống lấy từ $\\mathcal{G}$, kiểm sự kiện bằng chương trình")
    box(ax, x0, y["b9"], w, 0.5, "Giao diện tư vấn: React, Spring Boot, FastAPI (chương 3)")
    cx = x0 + w / 2
    for a, b in (("b1", "b2"), ("b2", "b3"), ("b3", "b4")):
        arrow(ax, (cx, y[a]), (cx, y[b] + h))
    # G -> hai kênh
    arrow(ax, (x0 + hw / 2, y["b4"]), (x0 + hw / 2, y["b5"] + 0.8))
    arrow(ax, (x0 + w - hw / 2, y["b4"]), (x0 + w - hw / 2, y["b5"] + 0.8), ls=(0, (4, 2.5)), color=MUTED)
    # hai kênh -> gộp
    arrow(ax, (x0 + hw, y["b5"] + 0.2), (bx6 + 0.25, y["b6"] + h), ls=(0, (4, 2.5)), color=MUTED)
    arrow(ax, (x0 + w - hw / 2, y["b5"]), (x0 + w - hw / 2, y["b6"] + h), ls=(0, (4, 2.5)), color=MUTED)
    # hệ thống cuối: kênh hành vi -> mặt nạ
    arrow(ax, (x0 + 0.55, y["b5"]), (x0 + 0.55, y["b7"] + h))
    ax.text(x0 + 0.65, (y["b5"] + y["b7"] + h) / 2, "hệ thống cuối:\n$\\hat{y}_{ui}=\\mathbf{e}_u^{\\top}\\mathbf{e}_i$",
            fontsize=6.8, color=INK2, ha="left", va="center")
    arrow(ax, (x0 + w - hw / 2, y["b6"]), (x0 + w - hw / 2, y["b7"] + h), ls=(0, (4, 2.5)), color=MUTED)
    for a, b in (("b7", "b8"), ("b8", "b9")):
        hb = 0.5 if b == "b9" else h
        arrow(ax, (cx, y[a]), (cx, y[b] + hb))
    # M, U -> L_comp và mặt nạ (bên phải)
    xr = x0 + w + 0.3
    line(ax, [(x0 + w, y["b3"] + h / 2), (xr, y["b3"] + h / 2), (xr, y["b7"] + h / 2)])
    arrow(ax, (xr, y["b7"] + h / 2), (x0 + w, y["b7"] + h / 2))
    arrow(ax, (xr, y["b6"] + h / 2), (x0 + w, y["b6"] + h / 2), ls=(0, (4, 2.5)), color=MUTED)
    ax.text(xr + 0.06, (y["b3"] + y["b7"]) / 2 + 0.6, "M, U", fontsize=7, color=INK2, rotation=90, ha="left", va="center")
    # G -> giải thích (bên trái)
    xl = x0 - 0.3
    line(ax, [(x0, y["b4"] + h / 2), (xl, y["b4"] + h / 2), (xl, y["b8"] + h / 2)])
    arrow(ax, (xl, y["b8"] + h / 2), (x0, y["b8"] + h / 2))
    ax.text(xl - 0.06, (y["b4"] + y["b8"]) / 2 + 0.6, "đường đi trong $\\mathcal{G}$", fontsize=7, color=INK2, rotation=90,
            ha="right", va="center")
    # chú thích
    leg = [Patch(fc=BOX_FILL, ec=BOX_EDGE, lw=0.9, label="khối của hệ thống cuối (LightGCN + mặt nạ + giải thích)"),
           Patch(fc=OFF_FILL, ec=OFF_EDGE, lw=0.9, ls=(0, (4, 2.5)), label="khối chỉ có trong CaKG-Rec (mục 2.6)")]
    ax.legend(handles=leg, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=7, frameon=False,
              handlelength=2.2)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------- Hình 2.3
def hbars(ax, labels, vals, sds, title, texts, xmax=None):
    ys = list(range(len(vals)))[::-1]
    ax.barh(ys, vals, color=SERIES, height=0.58, zorder=3)
    for yv, v, s in zip(ys, vals, sds):
        if s:
            ax.errorbar(v, yv, xerr=s, color=INK, capsize=2.5, lw=0.8, zorder=4)
    top = xmax or max(v + (s or 0) for v, s in zip(vals, sds))
    for yv, v, s, t in zip(ys, vals, sds, texts):
        ax.text(v + (s or 0) + top * 0.03, yv, t, va="center", ha="left", fontsize=7, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7.4)
    ax.set_xlim(0, top * 1.42)
    ax.set_title(title, fontsize=8.6, color=INK, pad=5)
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn_dec(v, 2)))
    ax.tick_params(axis="x", labelsize=7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_main(n5, ck, out, log):
    rows = [("Popularity", n5["Popularity"], False), ("Popularity-MountAware", n5["Popularity-MountAware"], True),
            ("R-GCN", n5["R-GCN"], False), ("KGAT", ck["kgat|truoc_mat_na"], False),
            ("LightGCN", ck["lightgcn|truoc_mat_na"], False), ("LightGCN + mặt nạ\n(hệ thống cuối)", ck["lightgcn|mat_na_qd49"], True),
            ("CaKG-Rec, trước mặt nạ", ck["cakg|truoc_mat_na"], False), ("CaKG-Rec, mặt nạ", ck["cakg|mat_na_qd49"], True)]
    labels = [r[0] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 3.5), dpi=300, sharey=True)
    for ax, (title, get) in zip(axes, (
            ("Recall@10, mọi người dùng", lambda t: t["full"]["recall@10"]),
            ("CVR@10, người có thân", lambda t: t["cvr"]["cvr@10"]),
            ("Recall@10 chỉ ống, nhóm lắp được", lambda t: t["scenario"]["lap_duoc"]["lens_only"]["recall@10"]))):
        vals = [get(r[1])["mean"] for r in rows]
        sds = [get(r[1]).get("sd") for r in rows]
        if title.startswith("CVR"):
            texts = ["0 (do cách dựng)" if r[2] else vn_dec(v, 3) for r, v in zip(rows, vals)]
        else:
            texts = [vn_dec(v, 4 if v < 0.1 else 3) for v in vals]
        hbars(ax, labels, vals, sds, title, texts)
        log(f"Hình 2.3, {title}: " + "; ".join(f"{l.replace(chr(10), ' ')} {vn_dec(v, 4)}" for l, v in zip(labels, vals)))
    fig.tight_layout(w_pad=0.6)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------- Hình 2.4
def stacked(ax, labels, mixes, title):
    ys = list(range(len(mixes)))[::-1]
    keys = ("than", "ong", "pk", "khac")
    left = [0.0] * len(mixes)
    for k, c in zip(keys, CAT):
        vals = [m[k] for m in mixes]
        ax.barh(ys, vals, left=left, color=c, height=0.6, edgecolor=SURFACE, linewidth=1.0, zorder=3)
        for yv, l0, v in zip(ys, left, vals):
            if v >= 0.55 or (k == "than" and v >= 0.3):
                ax.text(l0 + v / 2, yv, vn_dec(v, 2), ha="center", va="center", fontsize=6.6,
                        color="white" if k in ("than", "ong") else INK)
        left = [a + b for a, b in zip(left, vals)]
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7.4)
    ax.set_xlim(0, 10)
    ax.set_title(title, fontsize=8.6, color=INK, pad=5, loc="left")
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    ax.tick_params(axis="x", labelsize=7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def mean_mix(xs):
    return {k: sum(x[k] for x in xs) / len(xs) for k in ("than", "ong", "pk", "khac")}


def fig_top10(inp, out, log):
    rt = B.parse_rt_b(inp)
    sel = B.jload(inp, B.one(inp, "results/cakg/val_sweep_v2_20261016/select_*/select.json"))
    d2 = B.jload(inp, B.one(inp, "results/cakg/val_sweep_v2seeds_20261016/dung2_*/dung2.json"))

    def g(split, keys):
        return mean_mix([rt[(split, k, "truoc_mat_na")] for k in keys])

    def conv(m):
        return {"than": m["than"], "ong": m["ong"], "pk": m["phu_kien"], "khac": m["khac"]}

    lg = [f"lightgcn_s{s}" for s in (1, 2, 3)]
    v1 = [f"cakg_s{s}" for s in (1, 2, 3)]
    test = [("LightGCN (TB 3 seed)", g("test", lg)), ("CaKG-Rec (TB 3 seed)", g("test", v1)),
            ("CaKG-Rec, λ1 = 0 (seed 1)", g("test", ["abl_lam1_0_s1"])),
            ("CaKG-Rec, bỏ suitable_for (seed 1)", g("test", ["abl_bo_suitable_for_s1"]))]
    a3 = mean_mix([conv(v["co_che"]["top10_mix_body_users"]) for v in d2["per_seed"].values()])
    val = [("LightGCN (TB 3 seed)", g("val", lg)), ("CaKG-Rec (TB 3 seed)", g("val", v1)),
           ("Biến thể A (TB 3 seed)", a3),
           ("Biến thể B (seed 1)", conv(sel["variants"]["loo_hu"]["co_che"]["top10_mix_body_users"])),
           ("Biến thể C (seed 1)", conv(sel["variants"]["body_hardneg"]["co_che"]["top10_mix_body_users"]))]
    fig, axes = plt.subplots(2, 1, figsize=(6.6, 4.1), dpi=300, gridspec_kw={"height_ratios": [4, 5]})
    stacked(axes[0], [t[0] for t in test], [t[1] for t in test], "(a) Test lần 1")
    stacked(axes[1], [t[0] for t in val], [t[1] for t in val], "(b) Val: CaKG-Rec và ba biến thể sửa (mục 2.6.2)")
    axes[1].set_xlabel("số sản phẩm trung bình trong 10 gợi ý đầu (trước mặt nạ) của 10.406 người có thân", fontsize=7.4)
    leg = [Patch(fc=c, label=l) for c, l in zip(CAT, ("thân máy", "ống kính", "phụ kiện", "khác"))]
    fig.legend(handles=leg, loc="upper right", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.99, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=1.0)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    plt.close(fig)
    for name, m in test + val:
        log(f"Hình 2.4, {name}: thân {vn_dec(m['than'], 2)}, ống {vn_dec(m['ong'], 2)}, phụ kiện {vn_dec(m['pk'], 2)}, "
            f"khác {vn_dec(m['khac'], 2)}")


# --------------------------------------------------------------------------- Hình 2.5
def fig_sampled(n5, ck, out, log):
    models = [("Popularity", n5["Popularity"]), ("Popularity-\nMountAware", n5["Popularity-MountAware"]),
              ("R-GCN", n5["R-GCN"]), ("KGAT", ck["kgat|truoc_mat_na"]), ("LightGCN", ck["lightgcn|truoc_mat_na"]),
              ("CaKG-Rec\n(mặt nạ)", ck["cakg|mat_na_qd49"])]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), dpi=300)
    for ax, (title, src, key) in zip(axes, (("Hit@20, lấy mẫu 1 + 99", "sampled_1_99", "hit@20"),
                                            ("Recall@20, xếp hạng toàn bộ", "full", "recall@20"))):
        vals = [m[1][src][key]["mean"] for m in models]
        sds = [m[1][src][key].get("sd") for m in models]
        xs = range(len(vals))
        ax.bar(xs, vals, color=SERIES, width=0.6, zorder=3)
        for x, v, s in zip(xs, vals, sds):
            if s:
                ax.errorbar(x, v, yerr=s, color=INK, capsize=2.5, lw=0.8, zorder=4)
            ax.text(x, v + (s or 0) + max(vals) * 0.03, vn_dec(v, 4), ha="center", va="bottom", fontsize=6.6, color=INK)
        ax.set_xticks(list(xs))
        ax.set_xticklabels([m[0] for m in models], fontsize=6.8)
        ax.set_ylim(0, max(vals) * 1.2)
        ax.set_title(title, fontsize=8.6, color=INK, pad=5)
        ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn_dec(v, 2)))
        ax.tick_params(axis="y", labelsize=7)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        log(f"Hình 2.5, {title}: " + "; ".join(f"{m[0].replace(chr(10), ' ')} {vn_dec(v, 4)}" for m, v in zip(models, vals)))
    fig.tight_layout(w_pad=1.2)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.abspath(os.path.join(HERE, "..", "..", "..")))
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    log = Log(root, f"run_hinh_c2_{args.label}.log")
    header(log, __file__, root)
    inp = Inputs(root, log)
    names = {"pipe": "hinh_2_1_luong_xu_ly.png", "kg": "hinh_2_2_do_thi.png", "main": "hinh_2_3_ket_qua_test.png",
             "top10": "hinh_2_4_top10_nguoi_co_than.png", "samp": "hinh_2_5_lay_mau_va_toan_bo.png"}
    os.makedirs(args.out, exist_ok=True)
    outs = {k: os.path.join(args.out, v) for k, v in names.items()}
    for o in outs.values():
        if os.path.exists(o):
            sys.exit(f"DỪNG: {o} đã có (không ghi đè).")
    plt.rcParams.update({"font.family": "Times New Roman", "mathtext.fontset": "stix", "axes.edgecolor": MUTED,
                         "xtick.color": INK2, "ytick.color": INK2})

    fs = B.jload(inp, "ai/data/processed/filtering_stats.json")
    st = B.jload(inp, "ai/data/kg/mount_compat_stats.json")
    kg = B.jload(inp, "ai/data/kg/kg_stats.json")
    tr = B.count_lines(inp.path("ai/data/processed/train.txt"))
    te = B.count_lines(inp.path("ai/data/processed/test.txt"))
    with open(inp.path("ai/config/mount_rules.toml"), encoding="utf-8") as f:
        n_rule = sum(1 for line in f if line.strip() == "[[rule]]")
    d = dict(n_rev=fs["raw_electronics_reviews"], n_meta=fs["raw_electronics_metadata"], n_u=fs["filtered_users"],
             n_i=fs["filtered_items"], n_x=fs["filtered_interactions"], n_tr=tr[1], n_te=te[1], n_rule=n_rule,
             nb=st["n_bodies_in_M"], nl=st["n_lenses_in_M"], m1=st["M_nnz"], u1=st["unknown_nnz"],
             kg_n=kg["nut"]["tong"], kg_tn=len(kg["nut"]) - 1, kg_te=len(kg["canh_ke_ca_rev"]),
             kg_e=sum(kg["canh_ke_ca_rev"].values()))
    log(f"Hình 2.1: {d}")
    fig_pipeline(d, outs["pipe"])

    from hinh_ch45 import fig_kg  # hàm vẽ lược đồ đã dùng cho báo cáo nội dung 1–5
    fig_kg(kg, outs["kg"])
    log(f"Hình 2.2: nút {kg['nut']}; cạnh xuôi {kg['canh_xuoi']}")

    n5, ck, _ = B.load_tests(inp)
    fig_main(n5, ck, outs["main"], log)
    fig_top10(inp, outs["top10"], log)
    fig_sampled(n5, ck, outs["samp"], log)
    for o in outs.values():
        log(f"ghi hình: {o} (sha256 {sha256_file(o)})")
    log.save()


if __name__ == "__main__":
    main()
