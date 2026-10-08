"""Nội dung 4, việc 2: tải đáp án tiêu cự từ Wikidata (P2151, focal length) để đo bước đọc tiêu cự từ tiêu đề ống.

Truy vấn: mọi item thuộc cùng các lớp như query_mount_models.rq (camera model, digital camera model, product model,
product line, lens model, camera lens) có P2151. Lấy từng giá trị (số + đơn vị + hạng của phát biểu), nhãn tiếng Anh,
bí danh tiếng Anh, hãng. KHÔNG lấy f-number (P6790 chỉ có ở 2 ống, content4_design mục 6C).

Ghi (không ghi đè; tên file kèm ngày):
  ai/data/external/wikidata/query_focal_length.rq
  ai/data/external/wikidata/focal_length_<YYYYMMDD>.json      (kết quả SPARQL thô)
  ai/data/external/wikidata/focal_length_<YYYYMMDD>.meta.txt  (thời điểm tải, sha256, số dòng)
User-Agent chỉ ghi tên dự án chung (CLAUDE.md mục 5).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/fetch_wikidata_focal.py
"""
import datetime, hashlib, json, os, sys, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
D = "ai/data/external/wikidata/"
QUERY = """# Wikidata: item có P2151 (focal length), cùng các lớp như query_mount_models.rq
SELECT ?item ?itemLabel ?class ?classLabel ?makerLabel ?amount ?unit ?rank
       (GROUP_CONCAT(DISTINCT ?alias; separator=" | ") AS ?aliases)
WHERE {
  ?item p:P2151 ?st .
  ?st psv:P2151 ?v ; wikibase:rank ?rank .
  ?v wikibase:quantityAmount ?amount ; wikibase:quantityUnit ?unit .
  ?item wdt:P31 ?class .
  VALUES ?class { wd:Q20888659 wd:Q20741022 wd:Q10929058 wd:Q20679033 wd:Q109672300 wd:Q192234 }
  OPTIONAL { ?item wdt:P176 ?maker . }
  OPTIONAL { ?item skos:altLabel ?alias . FILTER(LANG(?alias) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?item ?itemLabel ?class ?classLabel ?makerLabel ?amount ?unit ?rank
"""


def main():
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    out = f"{D}focal_length_{day}.json"
    if os.path.exists(out):
        sys.exit(f"DỪNG: {out} đã có, không ghi đè")
    with open(D + "query_focal_length.rq", "w", encoding="utf-8", newline="\n") as f:
        f.write(QUERY)
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "camera-store-thesis/0.1 (research script)",
                                               "Accept": "application/sparql-results+json"})
    t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = urllib.request.urlopen(req, timeout=120).read()
    rows = json.loads(raw)["results"]["bindings"]
    with open(out, "wb") as f:
        f.write(raw)
    h = hashlib.sha256(raw).hexdigest()
    items = {r["item"]["value"] for r in rows}
    with open(f"{D}focal_length_{day}.meta.txt", "w", encoding="utf-8") as f:
        f.write(f"retrieved_at={t}\nfile={os.path.basename(out)}\nsha256={h}\nrows={len(rows)}\nitems={len(items)}\n")
    print(f"tải lúc {t}: {len(rows)} dòng, {len(items)} item, sha256 {h}")


if __name__ == "__main__":
    main()
