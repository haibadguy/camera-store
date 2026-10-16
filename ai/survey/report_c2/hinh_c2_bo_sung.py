"""Hai hình bổ sung cho chương 2 quyển đồ án.

CHỈ ĐỌC. Mọi số và tên trên hình đọc từ file, không gõ tay:
- Hình 2.1 bản SVG: vẽ lại đúng hàm `fig_pipeline` của hinh_c2.py từ cùng các file đầu vào (bản PNG đã có, không ghi đè);
- Hình 2.6 (đường giải thích của người dùng thật mã 86, ống Nikon 85mm f/1.4G, hệ thống cuối seed 1):
  results/final_system/explain_test_20261016/lightgcn_s1/explanations.jsonl (b*, e_bᵀe_l, c*),
  ai/data/kg/kg_edges_interacted_with.csv (người dùng có hai thân trong train),
  kg_edges_compatible_with.csv (hai cạnh lắp được), kg_edges_has_spec_mount.csv (ngàm),
  kg_edges_suitable_for.csv (nhãn mục đích), item_attributes.csv (tên sản phẩm).

Chạy:
  E:\\DATN\\camera-store\\ai\\.venv\\Scripts\\python.exe ai/survey/report_c2/hinh_c2_bo_sung.py --root E:/DATN/camera-store \\
      --out E:/DATN/baocao/do_an/hinh --label 20261017_lan1
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from c2_common import Inputs, Log, header, sha256_file, vn_dec, vn_int  # noqa: E402
import bang_c2 as B  # noqa: E402
import hinh_c2 as H  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

UID, LENS = 86, 19119
EXPL = "results/final_system/explain_test_20261016/lightgcn_s1/explanations.jsonl"
USECASE_VN = {"phong_canh": "phong cảnh", "the_thao_chim": "thể thao, chim", "chan_dung": "chân dung", "macro": "macro"}
MOUNT_VN = {"nikon_f": "Nikon F"}


def rows(inp, rel, cond):
    with open(inp.path(rel), encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if cond(r)]


def short(title, n=4):
    """Tên ngắn: các từ đầu của tiêu đề (đọc từ file), bỏ phần mô tả."""
    t = re.split(r"\s+(?:with|for|Lens)\b", title)[0]
    return " ".join(t.split()[:n])


def node(ax, x, y, w, h, text, fc, ec, fs=7.6, ls="-", color=H.INK):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=fc, ec=ec, lw=1.0, ls=ls))
    ax.text(x, y, text, fontsize=fs, ha="center", va="center", color=color, linespacing=1.3)


def edge(ax, p0, p1, label=None, color=H.INK2, lw=1.0, ls="-", off=(0, 0.1), fs=6.8, ha="center"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, color=color, lw=lw, ls=ls,
                                 shrinkA=0, shrinkB=0))
    if label:
        ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], label, fontsize=fs, color=color,
                ha=ha, va="center", linespacing=1.2)


def fig_path(d, out, svg_out):
    W, Ht = 6.6, 3.9
    fig = plt.figure(figsize=(W, Ht), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, Ht)
    ax.axis("off")
    ON, ON_E = "#e8f1fc", "#2a78d6"
    OFF, OFF_E = "#f4f4f2", H.MUTED
    DASH = (0, (4, 2.5))
    ux, bx, lx, rx = 0.5, 2.1, 4.0, 5.8
    yb, yo, yl, ym, yc = 3.0, 1.5, 2.25, 3.35, 1.15
    bw, lw_, rw = 1.25, 1.55, 1.2
    node(ax, ux, yl, 0.78, 0.5, f"người dùng\nmã {d['uid']}", ON, ON_E)
    node(ax, bx, yb, bw, 0.5, f"{d['bstar_name']}\n(thân, $b^*$)", ON, ON_E)
    node(ax, bx, yo, bw, 0.5, f"{d['bother_name']}\n(thân còn lại)", OFF, OFF_E, color=H.INK2)
    node(ax, lx, yl, lw_, 0.5, f"{d['lens_name']}\n(ống được gợi ý)", ON, ON_E)
    node(ax, rx, ym, rw, 0.42, f"ngàm {d['mount']}", OFF, OFF_E, color=H.INK2)
    node(ax, rx, yc, rw, 0.42, f"mục đích: {d['usecase']}", ON, ON_E, ls=DASH)
    # người dùng -> thân (owns: đã đánh giá trong train); nhãn là e_bᵀe_l của thân đó với ống
    edge(ax, (ux + 0.39, yl + 0.1), (bx - bw / 2, yb), None, color=ON_E, lw=1.6)
    ax.text(0.55, 2.95, f"owns\n$\\mathbf{{e}}_b^\\top\\mathbf{{e}}_l$ = {vn_dec(d['e_bstar'], 2)}", fontsize=6.8,
            color=ON_E, ha="center", va="center", linespacing=1.2)
    edge(ax, (ux + 0.39, yl - 0.1), (bx - bw / 2, yo))
    ax.text(0.55, 1.55, f"owns\n$\\mathbf{{e}}_b^\\top\\mathbf{{e}}_l$ = {vn_dec(d['e_bother'], 2)}", fontsize=6.8,
            color=H.INK2, ha="center", va="center", linespacing=1.2)
    # thân -> ống (lắp được)
    edge(ax, (bx + bw / 2, yb), (lx - lw_ / 2, yl + 0.1), None, color=ON_E, lw=1.6)
    ax.text(3.05, 2.85, "compatible_with", fontsize=6.8, color=ON_E, ha="left", va="center")
    edge(ax, (bx + bw / 2, yo), (lx - lw_ / 2, yl - 0.1))
    ax.text(3.05, 1.65, "compatible_with", fontsize=6.8, color=H.INK2, ha="left", va="center")
    # ngàm: thân b* và ống cùng nối tới nút ngàm
    ax.plot([bx, bx], [yb + 0.25, ym], color=H.INK2, lw=1.0)
    edge(ax, (bx, ym), (rx - rw / 2, ym), "has_spec", off=(0, 0.1))
    edge(ax, (lx + 0.3, yl + 0.25), (rx - 0.3, ym - 0.21), "has_spec", off=(0.12, -0.08), ha="left")
    # ống -> mục đích
    edge(ax, (lx + 0.3, yl - 0.25), (rx - 0.3, yc + 0.21), "suitable_for", color=ON_E, lw=1.6, ls=DASH,
         off=(0.12, 0.08), ha="left")
    ax.text(rx, yc - 0.42, "sự kiện của đồ thị,\nkhông phải lý do gợi ý", fontsize=6.6, color=H.INK2, ha="center",
            va="center", style="italic")
    leg = [Line2D([0], [0], color=ON_E, lw=1.6, label="đường giải thích $u \\rightarrow b^* \\rightarrow l \\rightarrow c^*$ trong câu"),
           Line2D([0], [0], color=ON_E, lw=1.6, ls=DASH, label="vế mục đích của câu"),
           Patch(fc=OFF, ec=OFF_E, label="nút có trong đồ thị, không nằm trên đường")]
    ax.legend(handles=leg, loc="lower left", bbox_to_anchor=(0.0, 0.0), fontsize=6.8, frameon=False)
    fig.savefig(out, dpi=300, facecolor="white")
    fig.savefig(svg_out, facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.abspath(os.path.join(HERE, "..", "..", "..")))
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    log = Log(root, f"run_hinh_c2_bo_sung_{args.label}.log")
    header(log, __file__, root)
    inp = Inputs(root, log)
    outs = {k: os.path.join(args.out, v) for k, v in (("svg21", "hinh_2_1_luong_xu_ly.svg"),
                                                      ("png26", "hinh_2_6_duong_giai_thich.png"),
                                                      ("svg26", "hinh_2_6_duong_giai_thich.svg"))}
    os.makedirs(args.out, exist_ok=True)
    for o in outs.values():
        if os.path.exists(o):
            sys.exit(f"DỪNG: {o} đã có (không ghi đè).")
    plt.rcParams.update({"font.family": "Times New Roman", "mathtext.fontset": "stix", "svg.fonttype": "none"})

    # Hình 2.1, bản SVG, cùng số với bản PNG
    fs = B.jload(inp, "ai/data/processed/filtering_stats.json")
    st = B.jload(inp, "ai/data/kg/mount_compat_stats.json")
    kg = B.jload(inp, "ai/data/kg/kg_stats.json")
    tr = B.count_lines(inp.path("ai/data/processed/train.txt"))
    te = B.count_lines(inp.path("ai/data/processed/test.txt"))
    with open(inp.path("ai/config/mount_rules.toml"), encoding="utf-8") as f:
        n_rule = sum(1 for line in f if line.strip() == "[[rule]]")
    d1 = dict(n_rev=fs["raw_electronics_reviews"], n_meta=fs["raw_electronics_metadata"], n_u=fs["filtered_users"],
              n_i=fs["filtered_items"], n_x=fs["filtered_interactions"], n_tr=tr[1], n_te=te[1], n_rule=n_rule,
              nb=st["n_bodies_in_M"], nl=st["n_lenses_in_M"], m1=st["M_nnz"], u1=st["unknown_nnz"],
              kg_n=kg["nut"]["tong"], kg_tn=len(kg["nut"]) - 1, kg_te=len(kg["canh_ke_ca_rev"]),
              kg_e=sum(kg["canh_ke_ca_rev"].values()))
    log(f"Hình 2.1 (SVG): {d1}")
    H.fig_pipeline(d1, outs["svg21"])

    # Hình 2.6
    ex = None
    with open(inp.path(EXPL), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["u"] == UID and r["l"] == LENS:
                ex = r
                break
    assert ex is not None and not ex["errors"], ex
    bodies = [int(b) for b in ex["cand_bodies"]]
    assert len(bodies) == 2 and ex["b_star"] in bodies
    bother = [b for b in bodies if b != ex["b_star"]][0]
    owns = {int(r["iid"]) for r in rows(inp, "ai/data/kg/kg_edges_interacted_with.csv", lambda r: r["uid"] == str(UID))}
    assert set(bodies) <= owns, "người dùng phải có cả hai thân trong train"
    cw = rows(inp, "ai/data/kg/kg_edges_compatible_with.csv",
              lambda r: r["lens_iid"] == str(LENS) and int(r["body_iid"]) in bodies)
    assert len(cw) == 2, cw
    mounts = rows(inp, "ai/data/kg/kg_edges_has_spec_mount.csv",
                  lambda r: int(r["iid"]) in bodies + [LENS] and r["ngam_khong_chac"] == "0")
    mset = {r["mount"] for r in mounts}
    assert len(mset) == 1, mset
    uc = [r["usecase"] for r in rows(inp, "ai/data/kg/kg_edges_suitable_for.csv", lambda r: r["iid"] == str(LENS))]
    assert ex["c_star"] in uc
    titles = {int(r["iid"]): r["title"] for r in rows(inp, "ai/data/kg/item_attributes.csv",
                                                     lambda r: int(r["iid"]) in bodies + [LENS])}
    d = dict(uid=UID, bstar_name=short(titles[ex["b_star"]], 2), bother_name=short(titles[bother], 2),
             lens_name=short(titles[LENS].replace("AF-S FX NIKKOR", "AF-S"), 4), mount=MOUNT_VN.get(mset.pop()),
             usecase=USECASE_VN[ex["c_star"]], e_bstar=ex["e_score"][str(ex["b_star"])], e_bother=ex["e_score"][str(bother)])
    log(f"Hình 2.6: người dùng {UID}; ống {LENS} '{titles[LENS]}'; b* {ex['b_star']} '{titles[ex['b_star']]}' "
        f"e_bᵀe_l {ex['e_score'][str(ex['b_star'])]:.4f}; thân còn lại {bother} '{titles[bother]}' "
        f"e_bᵀe_l {ex['e_score'][str(bother)]:.4f}; ngàm {d['mount']}; nhãn mục đích của ống {uc}; c* {ex['c_star']}; "
        f"cạnh compatible_with {[(r['body_iid'], r['rule_id']) for r in cw]}; câu: {ex['sentence']}")
    log(f"  tên trên hình: {d}")
    fig_path(d, outs["png26"], outs["svg26"])
    for o in outs.values():
        log(f"ghi hình: {o} (sha256 {sha256_file(o)})")
    log.save()


if __name__ == "__main__":
    main()
