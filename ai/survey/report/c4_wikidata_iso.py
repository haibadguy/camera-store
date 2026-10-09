"""Chương 4, "Vì sao không có ISO": Wikidata có thuộc tính nào cho độ nhạy sáng (ISO) của máy ảnh không.

Gửi MỘT truy vấn SPARQL tới query.wikidata.org (chỉ đọc; User-Agent chung của dự án, không gửi thông tin cá nhân):
liệt kê mọi thuộc tính có nhãn tiếng Anh chứa "iso", "sensitivity" hoặc "film speed". Lưu kết quả thô (JSON) và log.
Đây là lần tra lại ngày chạy script, không phải lần tra 08/10 (lần đó không lưu log).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c4_wikidata_iso.py --label 20261009_lan1
"""
import argparse
import datetime
import json
import os
import urllib.parse
import urllib.request

from report_common import REPORT_LOG_DIR, Log, header, sha256_file

UA = "camera-store-thesis/0.1 (research script)"
QUERY = """SELECT ?p ?label ?type WHERE {
  ?p a wikibase:Property ; wikibase:propertyType ?type ; rdfs:label ?label .
  FILTER(LANG(?label) = "en")
  FILTER(CONTAINS(LCASE(?label), "iso") || CONTAINS(LCASE(?label), "sensitivity") || CONTAINS(LCASE(?label), "film speed"))
} ORDER BY ?label"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c4_wikidata_iso_{a.label}.log"))
    out_json = os.path.join(REPORT_LOG_DIR, f"wikidata_iso_props_{a.label}.json")
    if os.path.exists(out_json):
        raise SystemExit(f"DỪNG: {out_json} đã có")
    header(log, __file__)
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    t = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
    open(out_json, "xb").write(raw)
    rows = json.loads(raw)["results"]["bindings"]
    log(f"truy vấn lúc {t}\n{QUERY}\nkết quả thô: {out_json} (sha256 {sha256_file(out_json)})")
    log(f"{len(rows)} thuộc tính:")
    for r in rows:
        log(f"  {r['p']['value'].rsplit('/', 1)[-1]:8s} {r['label']['value']}  [{r['type']['value'].rsplit('#', 1)[-1]}]")

    # Lần 2 (thêm 09/10 sau khi lần 1 thấy P6789 "ISO speed"): thuộc tính này dùng cho bao nhiêu item, có máy ảnh không
    for name, q in USAGE_QUERIES:
        url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
        rows = json.loads(raw)["results"]["bindings"]
        log(f"\n[{name}]\n{q}\n{len(rows)} dòng:")
        for r in rows[:40]:
            log("  " + " | ".join(f"{k}={v['value']}" for k, v in r.items()))
    log.save()


USAGE_QUERIES = [
    ("số item dùng P6789", "SELECT (COUNT(DISTINCT ?item) AS ?n) (COUNT(*) AS ?claims) WHERE { ?item wdt:P6789 ?v }"),
    ("item dùng P6789 (tối đa 40), kèm 'instance of'",
     """SELECT ?item ?itemLabel ?v ?clsLabel WHERE { ?item wdt:P6789 ?v . OPTIONAL { ?item wdt:P31 ?cls }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } LIMIT 40"""),
    ("máy ảnh (P31/P279* Q15328 'camera') có P6789",
     """SELECT (COUNT(DISTINCT ?item) AS ?n) WHERE { ?item wdt:P6789 ?v ; wdt:P31/wdt:P279* wd:Q15328 . }"""),
]


if __name__ == "__main__":
    main()
