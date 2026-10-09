"""Chương 4: các chỗ [CẦN KIỂM] đọc được từ dữ liệu đã có (chỉ đọc).

(1) Ví dụ uid 47: phán CVR (common_05.judge_lens) với thân trong train của người này cho ống Nikon 85mm f/1.4D
    (iid 99) và vài ống Canon EF trong M.
(2) Trường details["Focal Length Description"] của ống Sony DT 11-18mm và Sigma 24-70mm (ví dụ ở content4_design mục 3.2).
(3) ISO: "31/247 dòng máy có hơn một giá trị Expanded ISO Maximum" (content4_design, STATUS hạn chế 1): thử lại
    với vài cách nhóm "dòng máy"; in ví dụ Rebel T7i, 5D Mark IV.

Đầu vào: ai/data/kg/*, ai/data/processed/train.txt, ai/data/survey/meta_full_k5.jsonl (extract_full_meta.py).
Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c4_checks.py --label 20261009_lan1
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

from report_common import REPORT_LOG_DIR, Log, header

sys.path.insert(0, "ai/pipeline")
import common_05 as C  # noqa: E402

KG = "ai/data/kg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c4_checks_{a.label}.log"))
    header(log, __file__)
    attrs = {int(r["iid"]): r for r in csv.DictReader(open(f"{KG}/item_attributes.csv", encoding="utf-8"))}
    meta = {}
    for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
        d = json.loads(line)
        meta[d["parent_asin"]] = d

    # ── (1) ──
    train = C.load_train()
    itype = C.load_item_type()
    ctx = C.load_cvr_context()
    bodies = {i for i in train[47] if itype[i] == 0}
    log(f"\n(1) uid 47: thân trong train {sorted(bodies)} "
        + "; ".join(f"{b}: {attrs[b]['title'][:50]}" for b in sorted(bodies)))
    cands = [99] + sorted(i for i in ctx.lenses_in_m if attrs[i]["mount"] == "canon_ef")[:3]
    for l in cands:
        r = attrs[l]
        st = ["M=1" if (b, l) in ctx.m1 else ("không biết" if (b, l) in ctx.unknown else "M=0") for b in sorted(bodies)]
        log(f"  ống {l} ({r['mount']}/{r['khung']}) {r['title'][:60]}: cặp {st} -> judge_lens = "
            f"{C.judge_lens(l, bodies, ctx)}  (True = vi phạm, False = không vi phạm, None = không chấm được)")
    log(f"  ống 99 có trong train của uid 47: {99 in train[47]}")

    # ── (2) ──
    log("\n(2) details['Focal Length Description'] của ống")
    for pat in [r"\bsony\b.*\bdt\b.*11-18", r"\bsigma\b.*24-70"]:
        for i, r in attrs.items():
            if r["item_type"] == "ong" and re.search(pat, r["title"].lower()):
                det = meta[r["parent_asin"]].get("details") or {}
                log(f"  iid {i} {r['parent_asin']} | {r['title'][:80]}")
                log(f"     Focal Length Description = {det.get('Focal Length Description')!r}; "
                    f"Maximum Focal Length = {det.get('Maximum Focal Length')!r}; "
                    f"Minimum Focal Length = {det.get('Minimum Focal Length')!r}")
    fld = [(i, (meta[r["parent_asin"]].get("details") or {}).get("Focal Length Description"))
           for i, r in attrs.items() if r["item_type"] == "ong"]
    log(f"  ống (phân loại hiện tại, {sum(1 for r in attrs.values() if r['item_type'] == 'ong')}) có trường này: "
        f"{sum(1 for _, v in fld if v)}")

    # ── (3) ──
    log("\n(3) Expanded ISO Maximum của thân")
    bodies_all = [r for r in attrs.values() if r["item_type"] == "than"]
    rows = []
    for r in bodies_all:
        det = meta[r["parent_asin"]].get("details") or {}
        v = det.get("Expanded ISO Maximum")
        if v:
            rows.append((r, str(v).strip(), (det.get("Model Name") or "").strip().lower()))
    log(f"  thân (phân loại hiện tại): {len(bodies_all)}; có Expanded ISO Maximum: {len(rows)}")

    def series(r):  # dòng máy theo tiêu đề: hãng + mã máy đầu tiên (vd "rebel t7i", "5d mark iv", "d750")
        t = re.sub(r"[^a-z0-9 ]", " ", r["title"].lower())
        m = re.search(r"(rebel \w+|eos \w+(?: mark \w+)?|\b[a-z]{0,3}\d{1,4}[a-z]{0,2}(?: mark \w+| ii+)?\b)", t)
        return m.group(1) if m else t[:20]

    for name, key in [("Model Name (details)", lambda x: x[2]), ("evidence (luật dòng máy)", lambda x: x[0]["evidence"]),
                      ("mã máy trong tiêu đề", lambda x: series(x[0]))]:
        g = collections.defaultdict(set)
        for x in rows:
            k = key(x)
            if k:
                g[k].add(x[1])
        multi = {k: v for k, v in g.items() if len(v) > 1}
        log(f"  nhóm theo {name}: {len(g)} nhóm, {len(multi)} nhóm có > 1 giá trị")
    g = collections.defaultdict(set)
    for x in rows:
        g[series(x[0])].add(x[1])
    for k in ["rebel t7i", "5d mark iv"]:
        log(f"    ví dụ '{k}': {sorted(g.get(k, set()))}")
    for x in rows:
        if re.search(r"t7i|5d mark iv", x[0]["title"].lower()):
            log(f"      {x[0]['parent_asin']} ISO max {x[1]!r} | Model Name {x[2]!r} | {x[0]['title'][:70]}")
    log.save()


if __name__ == "__main__":
    main()
