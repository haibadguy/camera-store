"""Nội dung 3: kiểm nguồn và câu trích của bảng luật ngàm (ai/config/mount_rules.toml) và bảng mã ống Sony
(ai/config/sony_lens_codes.toml), theo chuẩn QĐ nội dung 4 – 15 (Red Team nội dung 3 lần 1, T5 và T2).

Làm 4 việc:
  1. Kiểm bản sao của từng nguồn (thư mục meta.thu_muc_ban_sao): sha256 của HTML và văn bản khớp TOML; văn bản có câu
     dau_hieu_bai và không phải trang lỗi / trang chặn ("access denied", "just a moment", "enable javascript and cookies").
  2. Kiểm từng câu trích ([[rule.can_cu]]) có NGUYÊN VĂN, LIỀN MỘT ĐOẠN trong bản sao văn bản (so sau khi gộp khoảng trắng,
     viết thường, đổi dấu nháy / gạch cong sang dạng thường). Câu trích có "..." bị coi là THIẾU (quy ước v0.5: không ghép đoạn).
     Luật kiem_chung = "da_doc_trang" phải có >= 1 căn cứ OK. In số chỗ suy rộng và nhận định nhóm của từng luật.
  3. Kiểm bảng mã Sony: sha256, dấu hiệu bài, câu trích về khổ của từng mã.
  4. Phạm vi bảng mã: trong item_attributes.csv, ống Sony (tiêu đề mở đầu "Sony", ngàm sony_e / sony_a) mà phần đầu tiêu đề
     không có chữ FE / DT / E / APS-C nhưng có mã SEL/SAL -> mã đó có trong bảng không.
Có lỗi ở 1–3, hoặc ở 4 có mã chưa có trong bảng -> in DỪNG, mã thoát 2.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/check_rule_sources.py > ai/data/survey/run_check_rule_sources_<nhãn>.log
"""
import argparse
import collections
import csv
import hashlib
import html
import os
import re
import sys
import tomllib

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import mount_detect as md  # noqa: E402

MIN_TXT = 1000                                   # văn bản ngắn hơn -> coi là trang rỗng / lỗi
BAD = ("access denied", "just a moment", "enable javascript and cookies")


def norm(s):
    s = html.unescape(s).lower()
    for a, b in (("—", "-"), ("–", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("\xa0", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check_copy(base, name, s, marker):
    """Trả (status, văn bản đã chuẩn hóa hoặc None)."""
    h, t = os.path.join(base, s["ban_sao"]), os.path.join(base, s["ban_sao_txt"])
    if not (os.path.exists(h) and os.path.exists(t)):
        print(f"  {name:24s} LỖI  thiếu file bản sao ({s['ban_sao']})")
        return "LỖI", None
    h_ok, t_ok = sha256(h) == s["sha256_html"], sha256(t) == s["sha256_txt"]
    raw = open(t, encoding="utf-8").read()
    txt = norm(raw)
    content_ok = len(raw) >= MIN_TXT and norm(marker) in txt and not any(b in txt for b in BAD)
    st = "OK" if (h_ok and t_ok and content_ok) else "LỖI"
    print(f"  {name:24s} {st:4s} sha256 html={'khớp' if h_ok else 'LỆCH'} txt={'khớp' if t_ok else 'LỆCH'} "
          f"nội dung bài={'có' if content_ok else 'THIẾU'} ({len(raw)} ký tự) | {s.get('cach_luu', '')[:60]}")
    return st, (txt if st == "OK" else None)


def quote_ok(q, txt):
    if txt is None:
        return "THIẾU (bản sao lỗi)"
    if "..." in q or "…" in q:
        return "THIẾU (có '...')"
    return "OK" if norm(q) in txt else "THIẾU"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="ai/config/mount_rules.toml")
    ap.add_argument("--codes", default="ai/config/sony_lens_codes.toml")
    ap.add_argument("--attrs", default="ai/data/kg/item_attributes.csv")
    args = ap.parse_args()
    cfg = tomllib.load(open(args.rules, "rb"))
    codes = tomllib.load(open(args.codes, "rb"))
    errors = []

    # ---------------- 1. bản sao nguồn của bảng luật ----------------
    print(f"=== 1. Bản sao nguồn ({args.rules} v{cfg['meta']['version']}) ===")
    base = cfg["meta"]["thu_muc_ban_sao"]
    texts = {}
    for name, s in cfg["sources"].items():
        st, txt = check_copy(base, name, s, s["dau_hieu_bai"])
        if st != "OK":
            errors.append(f"nguồn {name}")
        texts[name] = txt
        if "ban_sao_phu" in s:
            p = os.path.join(base, s["ban_sao_phu"])
            print(f"      bản phụ {s['ban_sao_phu']}: {'có' if os.path.exists(p) else 'KHÔNG CÓ'}"
                  f"{', sha256 ' + sha256(p)[:16] + '…' if os.path.exists(p) else ''}")

    # ---------------- 2. câu trích của từng luật ----------------
    print("\n=== 2. Căn cứ của từng luật (kiểm theo bản sao văn bản) ===")
    used = collections.Counter()
    summary = []
    for r in cfg["rule"]:
        n_ok, n_all = 0, 0
        print(f"-- {r['id']} [{r['kiem_chung']}] -> {r['level']}")
        for c in r.get("can_cu", []):
            n_all += 1
            used[c["source"]] += 1
            if c["source"] not in cfg["sources"]:
                st = "THIẾU (nguồn không có trong [sources])"
            else:
                st = quote_ok(c["trich"], texts[c["source"]])
            if st != "OK":
                errors.append(f"luật {r['id']}: {c['source']}")
            elif c["kiem_chung"] == "da_doc_trang":
                n_ok += 1
            print(f"    {st:5s} {c['source']}: {c['trich'][:100]}")
        for x in r.get("suy_rong", []):
            print(f"    [suy rộng] {x[:140]}")
        for x in r.get("nhan_dinh_nhom", []):
            print(f"    [nhận định nhóm, chưa có nguồn] {x[:140]}")
        verdict = ("OK" if n_ok else "THIẾU") if r["kiem_chung"] == "da_doc_trang" else \
                  (f"{r['kiem_chung']} ({'căn cứ OK ' + str(n_ok) if n_all else 'không có trang'})")
        if r["kiem_chung"] == "da_doc_trang" and not n_ok:
            errors.append(f"luật {r['id']}: không có căn cứ OK")
        print(f"    => căn cứ OK: {n_ok}/{n_all} | suy rộng: {len(r.get('suy_rong', []))} | "
              f"nhận định nhóm: {len(r.get('nhan_dinh_nhom', []))} | {verdict}")
        summary.append((r["id"], r["kiem_chung"], n_ok, n_all, len(r.get("suy_rong", [])),
                        len(r.get("nhan_dinh_nhom", [])), verdict))
    unused = sorted(set(cfg["sources"]) - set(used))
    print(f"\nnguồn không luật nào dẫn: {unused}")
    print("\nTÓM TẮT LUẬT (id | kiểm chứng | căn cứ OK / tổng | suy rộng | nhận định nhóm | kết luận)")
    for row in summary:
        print("  " + " | ".join(str(x) for x in row))
    print(f"tổng số chỗ suy rộng: {sum(r[4] for r in summary)}; nhận định nhóm: {sum(r[5] for r in summary)}")

    # ---------------- 3. bảng mã Sony ----------------
    print(f"\n=== 3. Bảng mã ống Sony ({args.codes} v{codes['meta']['version']}) ===")
    cbase = codes["meta"]["thu_muc_ban_sao"]
    for code, v in codes["codes"].items():
        st, txt = check_copy(cbase, code, v, codes["meta"]["dau_hieu_bai"])
        q = quote_ok(v["trich"], txt)
        if st != "OK" or q != "OK":
            errors.append(f"mã {code}")
        print(f"      -> khung {v['khung']:4s} | câu trích {q} | {v['trich']}")

    # ---------------- 4. phạm vi bảng mã trên dữ liệu ----------------
    print(f"\n=== 4. Mã SEL/SAL trong dữ liệu ({args.attrs}) ===")
    need = collections.defaultdict(list)
    word_only = collections.Counter()
    for a in csv.DictReader(open(args.attrs, encoding="utf-8")):
        if a["item_type"] != "ong" or a["mount"] not in ("sony_e", "sony_a"):
            continue
        t = md.head(a["title"].lower())
        if not md.SONY_BRAND.search(t):
            continue
        cs = sorted({m.group(0).upper() for m in md.SONY_CODE.finditer(t)})
        if not cs:
            continue
        if any(rx.search(t) for _, rx in md.SONY_WORDS):
            for c in cs:
                word_only[c] += 1
            continue
        for c in cs:
            need[c].append(a["parent_asin"])
    print(f"mã có trong tiêu đề nhưng khung lấy từ CHỮ (không cần bảng): {len(word_only)} mã, {sum(word_only.values())} ống: "
          f"{dict(sorted(word_only.items()))}")
    print(f"mã cần tra bảng (tiêu đề không có chữ FE / DT / E / APS-C): {len(need)} mã, {sum(len(v) for v in need.values())} ống")
    missing = []
    for c, asins in sorted(need.items()):
        ok = c in codes["codes"]
        print(f"  {c:10s} {'có trong bảng -> ' + codes['codes'][c]['khung'] if ok else 'CHƯA CÓ TRONG BẢNG -> khong_ro'} | {asins}")
        if not ok:
            missing.append(c)
    extra = sorted(set(codes["codes"]) - set(need))
    print(f"mã trong bảng nhưng không cần cho dữ liệu: {extra}")
    if missing:
        errors.append(f"mã chưa có nguồn: {missing}")

    print("\n" + ("=> OK: mọi bản sao, câu trích và mã đều kiểm được" if not errors else f"=> DỪNG: {errors}"))
    sys.exit(2 if errors else 0)


if __name__ == "__main__":
    main()
