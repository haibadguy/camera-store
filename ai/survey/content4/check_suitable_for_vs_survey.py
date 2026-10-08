"""Đối chiếu (không phải đầu vào của pipeline): cạnh suitable_for do script 04 sinh (usecase_labels.py) với bảng nhãn
của script khảo sát count_usecase.py (ai/data/survey/usecase_labels_draft.csv). Hai bên phải trùng từng ống.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/check_suitable_for_vs_survey.py
"""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
SURVEY = "ai/data/survey/usecase_labels_draft.csv"
PIPE = "ai/data/kg/kg_edges_suitable_for.csv"

s, p = {}, {}
for r in csv.DictReader(open(SURVEY, encoding="utf-8")):
    for lab in filter(None, r["labels"].split(";")):
        s.setdefault(int(r["iid"]), set()).add(lab)
for r in csv.DictReader(open(PIPE, encoding="utf-8")):
    p.setdefault(int(r["iid"]), set()).add(r["usecase"])
diff = sorted(i for i in set(s) | set(p) if s.get(i, set()) != p.get(i, set()))
print(f"khảo sát ({SURVEY}): {sum(map(len, s.values()))} cạnh, {len(s)} ống có nhãn")
print(f"pipeline ({PIPE}): {sum(map(len, p.values()))} cạnh, {len(p)} ống có nhãn")
print(f"ống có tập nhãn khác nhau: {len(diff)} {diff[:20]}")
sys.exit(1 if diff else 0)
