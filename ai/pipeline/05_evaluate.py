"""
05_evaluate.py -- Tong hop ket qua benchmark cua cac mo hinh trong Muc 5.

Doc tat ca file ket qua trong results/:
  - popularity_global.json
  - popularity_mountaware.json
  - lightgcn_results.json (neu co)
  - rgcn_results.json (neu co)

Xuat bang so sanh Markdown va luu results/benchmark_summary.json.

Chay tu thu muc goc camera-store:
  python ai/pipeline/05_evaluate.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = ROOT / "results"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

MODELS = [
    ("Popularity-Global",    RESULTS_DIR / "popularity_global.json"),
    ("Popularity-MountAware",RESULTS_DIR / "popularity_mountaware.json"),
    ("LightGCN",             RESULTS_DIR / "lightgcn_results.json"),
    ("R-GCN variant",        RESULTS_DIR / "rgcn_results.json"),
]

METRICS = [
    ("Hit@5",   "hit@5"),
    ("Hit@10",  "hit@10"),
    ("Hit@20",  "hit@20"),
    ("NDCG@5",  "ndcg@5"),
    ("NDCG@10", "ndcg@10"),
    ("NDCG@20", "ndcg@20"),
    ("CVR@5",   "cvr@5"),
    ("CVR@10",  "cvr@10"),
    ("CVR@20",  "cvr@20"),
]


def load_model_results():
    data = {}
    for name, path in MODELS:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
                # results co the o root hoac trong key 'results'
                metrics = content.get("results", content)
                data[name] = metrics
        else:
            data[name] = None
    return data


def format_table(data):
    headers = ["Model"] + [m[0] for m in METRICS]
    rows = []

    for name, _ in MODELS:
        res = data.get(name)
        if res is None:
            row = [f"**{name}**"] + ["*chưa chạy*"] * len(METRICS)
        else:
            row = [f"**{name}**"]
            for label, key in METRICS:
                val = res.get(key)
                if val is not None and isinstance(val, (int, float)):
                    if "cvr" in key:
                        row.append(f"{val:.4f}")
                    else:
                        row.append(f"{val:.4f}")
                else:
                    row.append("N/A")
        rows.append(row)

    col_widths = [max(len(r[i]) for r in [headers] + rows) for i in range(len(headers))]

    def fmt_row(r):
        return "| " + " | ".join(f"{val:<{col_widths[i]}}" for i, val in enumerate(r)) + " |"

    sep = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"

    lines = [fmt_row(headers), sep]
    for r in rows:
        lines.append(fmt_row(r))

    return "\n".join(lines)


def main():
    print("=" * 70, flush=True)
    print("MUC 5: TONG HOP BENCHMARK RECOMMENDATION", flush=True)
    print("=" * 70, flush=True)

    data = load_model_results()
    table_md = format_table(data)

    print("\n## BẢNG KẾT QUẢ SO SÁNH BENCHMARK\n", flush=True)
    print(table_md, flush=True)

    # Save summary json
    summary = {name: data.get(name) for name, _ in MODELS}
    out_json = RESULTS_DIR / "benchmark_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved summary to: {out_json}", flush=True)


if __name__ == "__main__":
    main()
