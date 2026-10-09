"""Khảo sát nội dung 4: đếm số ống được gán mục đích sử dụng theo BẢN NHÁP ngưỡng (chưa duyệt, chưa đọc kỹ nguồn).
Tiêu cự quy đổi 35mm = tiêu cự x hệ số crop theo khung của ống. Khung không rõ -> chỉ gán khi kết quả giống nhau
với cả hệ số 1,0 và 1,6. Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/survey_usecase_draft.py
"""
import collections, csv, sys
sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402

CROP_MOUNT = {"mft": 2.0, "four_thirds": 2.0, "nikon_1": 2.7, "pentax_q": 5.5, "fuji_g": 0.79}
attrs = [a for a in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")) if a["item_type"] == "ong"]


def crops(a):
    if a["mount"] in CROP_MOUNT:
        return [CROP_MOUNT[a["mount"]]]
    if a["khung"] == "ff":
        return [1.0]
    if a["khung"] == "apsc":
        return [1.6 if a["mount"].startswith("canon") else 1.5]
    if a["khung"] == "khac" and a["mount"] == "canon_ef":
        return [1.3]
    return [1.0, 1.6]


def labels(f1, f2, a1, a2, c):
    lo, hi = f1 * c, (f2 or f1) * c
    ap_tele = a2 or a1
    out = set()
    if lo <= 135 and hi >= 70 and ap_tele <= 2.8:
        out.add("chan_dung")
    if lo <= 35:
        out.add("phong_canh")
    if hi >= 300:
        out.add("the_thao_chim")
    if lo <= 24:
        out.add("vlog")
    return frozenset(out)


cnt, n_sig, n_amb = collections.Counter(), 0, 0
for a in attrs:
    s = ev.lens_sig(ev.head_main(a["title"]))
    if not s:
        continue
    n_sig += 1
    f1, f2, a1, a2 = [float(x) if x else None for x in s]
    res = {labels(f1, f2, a1, a2, c) for c in crops(a)}
    if len(res) > 1:
        common = frozenset.intersection(*res)
        n_amb += 1
    else:
        common = next(iter(res))
    for l in common:
        cnt[l] += 1
    if not common:
        cnt["(không nhãn nào)"] += 1
print(f"ống đọc được tiêu cự+khẩu độ: {n_sig}; khung không rõ làm nhãn khác nhau giữa crop 1,0/1,6: {n_amb}")
print(dict(cnt.most_common()))
