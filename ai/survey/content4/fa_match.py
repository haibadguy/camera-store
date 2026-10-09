"""
Nội dung 4, việc 2 — bước 1 và 2: lập đáp án ngoài cho tiêu cự / khẩu độ của ống, rồi chia fix / holdout.
Kế hoạch: docs/reviews/n4_focal_aperture_plan.md.

VÒNG LẶP PHẢI TRÁNH: bước khớp ống của eval_external.py dùng chính tiêu cự + khẩu độ để khớp, nên nếu dùng lại thì
tiêu cự luôn "đúng". Ở đây khớp KHÔNG dùng thuộc tính cần đo:
  - chấm TIÊU CỰ : khớp bằng hãng + token chữ + KHẨU ĐỘ    (nguồn: Lensfun, Wikidata P2151)
  - chấm KHẨU ĐỘ : khớp bằng hãng + token chữ + TIÊU CỰ    (nguồn: Lensfun)

Ví dụ: tiêu đề "Canon EF 75-300mm f/4-5.6 III Telephoto Zoom Lens".
  Chấm tiêu cự: khóa = (canon, f/4-5.6). Ứng viên Lensfun cùng hãng + cùng khẩu độ có tên "Canon EF 75-300mm f/4-5.6 III"
  (token chữ {ef, iii}) và "Canon EF 75-300mm f/4-5.6 III USM" ({ef, iii, usm}). Chiều 1: token của tên nguồn phải có
  trong tiêu đề -> bản USM bị loại (tiêu đề không có "usm"). Chiều 2: token của tiêu đề thuộc bộ từ của nguồn phải có
  trong tên nguồn -> {ef, iii} ⊆ {ef, iii}: giữ. Một ứng viên, một tiêu cự (75-300) -> đáp án = 75-300.

Định nghĩa (chốt trước khi chia, không đổi sau đó):
  - Phần tiêu đề dùng để khớp: eval_external.head_main (bản của nội dung 3, cố định).
  - Khóa không phải thuộc tính cần đo được đọc bằng regex CỐ ĐỊNH của eval_external (FOCAL, APER, _num), không bằng
    bộ đọc đang được đo (ai/pipeline/lens_specs.py), để sửa bộ đọc không làm đổi tập khớp hay đáp án.
      khóa khẩu độ (chấm tiêu cự): APER sau tiêu cự đầu tiên, không có thì APER ở bất kỳ đâu (như lens_sig);
      khóa tiêu cự (chấm khẩu độ): FOCAL đầu tiên.
  - Hãng: eval_external.maker_of (tiêu đề: từ hãng đầu tiên trong phần chủ thể).
  - Token chữ của một chuỗi: token chỉ gồm chữ a-z của eval_external.ctoks, bỏ tên hãng (MAKERS), "mm", "f",
    và bỏ các từ mô tả chung trong GENERIC (lens, zoom, wide, black...).
  - Trùng hai chiều với một tên nguồn n:
      (1) chu(n) ⊆ token của tiêu đề;
      (2) chu(tiêu đề) ∩ V ⊆ chu(n), với V = hợp token chữ của mọi tên ống CÙNG NGUỒN, CÙNG HÃNG.
  - Đáp án chỉ lấy khi các ứng viên còn lại cho đúng MỘT giá trị (tiêu cự (f1, f2) / khẩu độ (a1, a2)).
  - Đáp án Lensfun = tiêu cự / khẩu độ đọc từ tên ống chuẩn của Lensfun (eval_external.lens_sig; Lensfun không có
    trường số cho phần lớn ống). Đáp án Wikidata = các giá trị P2151 (mm): 1 giá trị = ống một tiêu cự, 2 = zoom
    (nhỏ, lớn); item có từ 3 giá trị trở lên bị bỏ. Item Wikidata chỉ thuộc lớp máy ảnh (camera model, digital camera
    model) bị bỏ.
  - Phạm vi: ống (item_type = "ong") của ai/data/kg/item_attributes.csv.
  - cum_nguon (cho bootstrap): mã mục nguồn nhỏ nhất trong các ứng viên còn lại.

CHIA FIX / HOLDOUT (một lần chia cho cả hai phép đo, để không thể xem tiêu đề của một ống holdout qua phép đo kia):
  - Nhóm: các ống có chung ít nhất một mục nguồn ứng viên (union-find), để mọi listing của cùng một ống nguồn nằm cùng
    một nửa (vd 7 listing của Canon EF 75-300 III).
  - Tầng: (có đáp án tiêu cự?, có đáp án khẩu độ?, zoom / một tiêu cự theo đáp án tiêu cự).
  - Mỗi tầng: sắp nhóm theo khóa, random.Random(SEED).shuffle, nửa đầu (làm tròn xuống) -> fix, còn lại -> holdout.

Đầu ra (không ghi đè: dừng nếu file đã có):
  ai/survey/content4/fa_answer_key.csv   (mỗi dòng = một ô (phép đo, nguồn, ống))
  ai/survey/content4/fa_split.csv        (parent_asin, nhom, tang, nua)
Script CHỈ in số đếm, không in tiêu đề / đáp án của từng ống, không chạy bộ đọc đang được đo.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/fa_match.py
"""
import collections, csv, json, os, random, re, sys

sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402

SEED = 20261010
ATTRS = "ai/data/kg/item_attributes.csv"
WD_FOCAL = "ai/data/external/wikidata/focal_length_20261008.json"
OUT_KEY = "ai/survey/content4/fa_answer_key.csv"
OUT_SPLIT = "ai/survey/content4/fa_split.csv"
WD_CAMERA_ONLY = {"camera model", "digital camera model"}

# Từ mô tả chung: không phân biệt ống này với ống khác cùng hãng, hay có trong tiêu đề Amazon mà tên chuẩn không ghi.
# Chốt bằng cách đọc bộ từ của tên ống trong Lensfun / Wikidata (không đọc tiêu đề, không đọc kết quả khớp).
GENERIC = {"lens", "lenses", "zoom", "digital", "camera", "cameras", "wide", "angle", "ultra", "telephoto", "tele",
           "standard", "prime", "fixed", "black", "white", "silver", "new", "super", "multi", "coated", "compact",
           "auto", "autofocus", "manual", "focus", "full", "frame", "model", "mark", "edition", "one", "inch", "series",
           "version", "mount", "the", "and", "with", "of", "for", "interchangeable", "mirrorless", "dslr", "slr", "photo",
           "photography", "portrait", "medium", "world", "life", "main", "rear", "key", "toy", "bubble", "bokeh", "go",
           "dual", "insta", "galaxy", "shield"}


def chu(s):
    return frozenset(t for t in ev.ctoks(s) if re.fullmatch(r"[a-z]+", t) and t not in ev.MAKERS
                     and t not in ("mm", "f") and t not in GENERIC)


def aper_key(text):
    """Khẩu độ (a1, a2) đọc bằng regex cố định của eval_external, đúng cách của lens_sig."""
    t = text.lower().replace("–", "-")
    fm = ev.FOCAL.search(t)
    am = (ev.APER.search(t[fm.end():]) if fm else None) or ev.APER.search(t)
    return (ev._num(am.group(1)), ev._num(am.group(2))) if am else None


def focal_key(text):
    fm = ev.FOCAL.search(text.lower().replace("–", "-"))
    return (ev._num(fm.group(1)), ev._num(fm.group(2))) if fm else None


# ---------------------------------------------------------------- nguồn
def load_sources():
    """Trả về danh sách mục: dict(nguon, maker, names=[(tên, chu, khóa_khẩu_độ, khóa_tiêu_cự)], focal, aper, id)."""
    out = []
    _, lf = ev.load_lensfun()
    for sig, e in lf:
        mk, f1, f2, a1, a2 = sig
        out.append(dict(nguon="lensfun", maker=mk, names=[(e["name"], chu(e["name"]), (a1, a2), (f1, f2))],
                        focal=(f1, f2), aper=(a1, a2), id=e["id"]))
    rows = json.load(open(WD_FOCAL, encoding="utf-8"))["results"]["bindings"]
    items = collections.defaultdict(lambda: dict(vals=set(), names=set(), cls=set(), maker=None))
    for r in rows:
        it = items[r["item"]["value"]]
        assert r["unit"]["value"].endswith("/Q174789"), r          # milimét
        it["vals"].add(float(r["amount"]["value"]))
        it["cls"].add(r["classLabel"]["value"])
        it["names"].add(r["itemLabel"]["value"])
        it["names"].update(a for a in (r.get("aliases", {}).get("value") or "").split(" | ") if a)
        it["maker"] = it["maker"] or ev.maker_of(r.get("makerLabel", {}).get("value"))
    skip = collections.Counter()
    for uri, it in sorted(items.items()):
        if it["cls"] <= WD_CAMERA_ONLY:
            skip["chỉ lớp máy ảnh"] += 1
            continue
        if len(it["vals"]) > 2:
            skip["từ 3 giá trị P2151"] += 1
            continue
        v = sorted(it["vals"])
        focal = (ev._num(v[0]), ev._num(v[1]) if len(v) == 2 else None)
        names = []
        for n in sorted(it["names"]):
            mk = it["maker"] or ev.maker_of(n)
            ak = aper_key(n)
            if mk and ak:
                names.append((n, chu(n), ak, None))
        if not names:
            skip["không tên nào có hãng + khẩu độ"] += 1
            continue
        mk = it["maker"] or ev.maker_of(names[0][0])
        out.append(dict(nguon="wikidata", maker=mk, names=names, focal=focal, aper=None, id=f"wikidata:{uri}"))
    return out, skip


def main():
    global OUT_KEY, OUT_SPLIT
    if len(sys.argv) == 3 and sys.argv[1] == "--out-dir":          # chạy lại để kiểm tái lập, ghi vào thư mục khác
        OUT_KEY = os.path.join(sys.argv[2], os.path.basename(OUT_KEY))
        OUT_SPLIT = os.path.join(sys.argv[2], os.path.basename(OUT_SPLIT))
    for p in (OUT_KEY, OUT_SPLIT):
        if os.path.exists(p):
            sys.exit(f"DỪNG: {p} đã có, không ghi đè")
    src, skip = load_sources()
    print("Nguồn:", dict(collections.Counter(e["nguon"] for e in src)), "| Wikidata bỏ:", dict(skip))
    vocab = collections.defaultdict(set)                       # (nguồn, hãng) -> V
    for e in src:
        for n in e["names"]:
            vocab[(e["nguon"], e["maker"])] |= n[1]
    by_aper = collections.defaultdict(list)                    # chấm tiêu cự
    by_foc = collections.defaultdict(list)                     # chấm khẩu độ (chỉ Lensfun)
    for e in src:
        for n in e["names"]:
            by_aper[(e["nguon"], e["maker"], n[2])].append((e, n))
            if e["nguon"] == "lensfun":
                by_foc[(e["maker"], n[3])].append((e, n))

    lenses = [a for a in csv.DictReader(open(ATTRS, encoding="utf-8")) if a["item_type"] == "ong"]
    rows, stat = [], collections.Counter()
    for a in lenses:
        h = ev.head_main(a["title"])
        mk = ev.maker_of(h)
        tt = set(ev.ctoks(h))
        tchu = chu(h)
        if not mk:
            stat["không có hãng"] += 1
            continue
        ak, fk = aper_key(h), focal_key(h)
        jobs = []
        if ak:
            jobs += [("tieu_cu", s, by_aper.get((s, mk, ak), [])) for s in ("lensfun", "wikidata")]
        if fk:
            jobs.append(("khau_do", "lensfun", by_foc.get((mk, fk), [])))
        for phep, nguon, cands in jobs:
            V = vocab[(nguon, mk)]
            keep = [(e, n) for e, n in cands if n[1] <= tt and (tchu & V) <= n[1]]
            if not cands:
                continue
            stat[f"{phep}/{nguon}: có ứng viên cùng khóa"] += 1
            if not keep:
                stat[f"{phep}/{nguon}: bị loại do token chữ"] += 1
                continue
            vals = {e["focal"] if phep == "tieu_cu" else e["aper"] for e, _ in keep}
            if len(vals) != 1:
                stat[f"{phep}/{nguon}: nhiều hơn một giá trị"] += 1
                continue
            v = next(iter(vals))
            ids = sorted({e["id"] for e, _ in keep})
            rows.append(dict(parent_asin=a["parent_asin"], iid=a["iid"], phep_do=phep, nguon=nguon,
                             dap_an_1=v[0], dap_an_2=v[1] or "", cum_nguon=ids[0], muc_nguon=" ".join(ids),
                             n_muc=len(ids), ten_nguon=min(keep, key=lambda x: x[0]["id"])[1][0], tieu_de=a["title"]))
            stat[f"{phep}/{nguon}: khớp"] += 1
    print(f"Ống: {len(lenses)}")
    for k in sorted(stat):
        print(f"  {k}: {stat[k]}")

    # ---------------------------------------------------------------- chia
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in rows:
        for m in r["muc_nguon"].split():
            parent[find("asin:" + r["parent_asin"])] = find(m)
    groups = collections.defaultdict(set)
    for r in rows:
        groups[find("asin:" + r["parent_asin"])].add(r["parent_asin"])
    by_asin = collections.defaultdict(list)
    for r in rows:
        by_asin[r["parent_asin"]].append(r)
    strata = collections.defaultdict(list)
    for g in groups.values():
        rs = [r for x in g for r in by_asin[x]]
        has_f = any(r["phep_do"] == "tieu_cu" for r in rs)
        has_a = any(r["phep_do"] == "khau_do" for r in rs)
        zoom = any(r["phep_do"] == "tieu_cu" and r["dap_an_2"] for r in rs)
        tang = f"{'F' if has_f else '-'}{'A' if has_a else '-'}_{('zoom' if zoom else 'mot_tieu_cu') if has_f else 'khong_ro'}"
        strata[tang].append(sorted(g))
    rng = random.Random(SEED)
    split = []
    for t in sorted(strata):
        gs = sorted(strata[t])
        rng.shuffle(gs)
        half = len(gs) // 2
        for i, g in enumerate(gs):
            for x in g:
                split.append((x, g[0], t, "fix" if i < half else "holdout"))
    half_of = {x: n for x, _, _, n in split}

    with open(OUT_KEY, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["parent_asin"], r["phep_do"], r["nguon"])))
    with open(OUT_SPLIT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parent_asin", "nhom", "tang", "nua"])
        w.writerows(sorted(split))

    print(f"\nSố ống có ít nhất một đáp án: {len(by_asin)}; số nhóm: {len(groups)}; "
          f"nhóm nhiều ống nhất: {max(len(g) for g in groups.values())}")
    c = collections.Counter((t, n) for _, _, t, n in split)
    print("Tầng × nửa (số ống):")
    for t in sorted(strata):
        print(f"  {t:16s} fix {c[(t, 'fix')]:4d}   holdout {c[(t, 'holdout')]:4d}   (số nhóm {len(strata[t])})")
    print("Số ô / số ống theo phép đo, nguồn, nửa:")
    for phep in ("tieu_cu", "khau_do"):
        for nguon in ("lensfun", "wikidata", "*"):
            for nua in ("fix", "holdout"):
                rs = [r for r in rows if r["phep_do"] == phep and nguon in (r["nguon"], "*") and half_of[r["parent_asin"]] == nua]
                if rs:
                    print(f"  {phep:8s} {nguon:9s} {nua:8s} ô {len(rs):4d}  ống {len({r['parent_asin'] for r in rs}):4d}  "
                          f"cụm {len({(r['nguon'], r['cum_nguon']) for r in rs}):4d}")
    print(f"\nĐã ghi {OUT_KEY} ({len(rows)} dòng), {OUT_SPLIT} ({len(split)} dòng)")


if __name__ == "__main__":
    main()
