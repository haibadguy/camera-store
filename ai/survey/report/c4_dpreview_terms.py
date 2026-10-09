"""Kiểm bản sao trang điều khoản DPReview do Nam lưu bằng trình duyệt (chương 4, "Vì sao không có ISO").

CHỈ ĐỌC file HTML đã lưu (không tải gì từ mạng). In sha256 và kiểm:
- không phải trang chặn bot ("Just a moment...");
- có tiêu đề "DPReview Terms of Use", dòng "Last Updated: May 29, 2026", tên Gear Patrol, LLC;
- mục đánh số 6 (`<ol start="6">`) là "ACCESS TO AND USE OF CONTENT";
- câu cấm công cụ tự động (scrapers, crawlers, bots, scripts ... prior written consent);
- định nghĩa "DPR Content" có chữ "data".

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/c4_dpreview_terms.py --label 20261009_lan1
"""
import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_common import REPORT_LOG_DIR, Log, header, sha256_file  # noqa: E402

TERMS = "ai/data/external/dpreview_terms/dpreview_terms_20261009.html"


def plain_text(raw):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c4_dpreview_terms_{args.label}.log"))
    header(log, __file__)

    raw = open(TERMS, encoding="utf-8", errors="replace").read()
    text = plain_text(raw)
    log(f"file: {TERMS}")
    log(f"  kích thước: {os.path.getsize(TERMS)} byte, sha256 {sha256_file(TERMS)}")
    m = re.search(r"saved from url=\(\d+\)(\S+)", raw)
    log(f"  dấu lưu của trình duyệt (saved from url): {m.group(1) if m else 'không có'}")
    m = re.search(r"<title>([^<]*)</title>", raw)
    log(f"  <title>: {html.unescape(m.group(1)) if m else 'không có'}")

    checks = []
    checks.append(("không phải trang chặn bot", "Just a moment" not in raw))
    checks.append(("có 'DPReview Terms of Use'", "DPReview Terms of Use" in text))
    checks.append(("có 'Last Updated: May 29, 2026'", "Last Updated: May 29, 2026" in text))
    checks.append(("có 'Gear Patrol, LLC'", "Gear Patrol, LLC" in text))
    sec6 = re.search(r'<ol start="6"[^>]*>\s*<li>\s*<strong>([^<]+)</strong>', raw)
    checks.append((f"mục 6 = {sec6.group(1).strip() if sec6 else None!r}",
                   bool(sec6) and sec6.group(1).strip() == "ACCESS TO AND USE OF CONTENT"))
    scrape = re.search(r"Use automated means, including scrapers, crawlers, bots, scripts.*?prior written consent",
                       text)
    checks.append(("có câu cấm công cụ tự động", bool(scrape)))
    defn = re.search(r"DPR Content.{0,5}which means all of the information.*?Usage Data", text)
    checks.append(("định nghĩa 'DPR Content' có chữ 'data'", bool(defn) and " data," in defn.group(0)))

    for name, ok in checks:
        log(f"  [{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {name}")
    if scrape:
        log(f"  câu trích (nguyên văn): {scrape.group(0)}")
    log(f"KẾT LUẬN: {'ĐẠT CẢ' if all(ok for _, ok in checks) else 'CÓ MỤC KHÔNG ĐẠT'}")
    log.save()


if __name__ == "__main__":
    main()
