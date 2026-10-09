"""Tạo bản sao văn bản (.txt) từ bản sao HTML của trang nguồn, rồi in sha256 của cả hai file.

Bỏ nội dung trong <script>, <style>, <noscript>, <svg>; xuống dòng ở các thẻ khối; gộp khoảng trắng.
Bảng mã: đọc từ thẻ meta charset trong 2.000 byte đầu (vd trang sony.jp dùng Shift_JIS); không có thì dùng UTF-8
(thêm 08/10/2026 cho nguồn nội dung 3; với trang UTF-8 kết quả không đổi).
Chạy: ai\\.venv\\Scripts\\python.exe -I ai/survey/content4/html_to_text.py ai/data/external/usecase_sources/<file>.html ...
"""
import hashlib, re, sys
from html.parser import HTMLParser

SKIP = ("script", "style", "noscript", "svg")
BLOCK = ("p", "br", "li", "h1", "h2", "h3", "h4", "div", "tr", "td", "th", "section", "article")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def charset(raw):
    m = re.search(rb"""<meta[^>]*charset=["']?([\w-]+)""", raw[:2000], re.I)
    return m.group(1).decode("ascii").lower() if m else "utf-8"


for f in sys.argv[1:]:
    p = _Text()
    raw = open(f, "rb").read()
    p.feed(raw.decode(charset(raw), errors="replace").replace("\r\n", "\n").replace("\r", "\n"))   # như open() chế độ văn bản
    t = re.sub(r"[ \t\r\xa0]+", " ", "".join(p.out))
    t = re.sub(r"\n\s*\n+", "\n", t)
    out = f[:-5] + ".txt"
    open(out, "w", encoding="utf-8", newline="\n").write(t)
    print(f"{f}\t{sha256(f)}\n{out}\t{sha256(out)}")
