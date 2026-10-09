"""Tự kiểm báo cáo gộp theo quy ước văn phong (E:/DATN/baocao/quy_uoc_van_phong.md).

CHỈ ĐỌC. Ba phần kiểm:
1. Số liệu: mọi số trong thân bài (từ "# Mở đầu" tới "# Tài liệu tham khảo") phải tìm thấy trong
   4 chương gốc hoặc trong log / file kết quả. Số viết kiểu Việt (67.661; 0,0448); log có thể viết
   kiểu Anh (67,661; 0.0448) nên đọc cả hai kiểu. Số có chữ "khoảng / gần / hơn / dưới / chỉ" đứng
   trước được so gần đúng (sai lệch ≤ 2% hoặc trong khoảng làm tròn); số khác phải bằng một số trong
   nguồn sau khi làm tròn tới số chữ số thập phân đang viết. Số nguyên nhỏ (≤ 30) và ngày tháng bỏ qua.
   Một số trong nguồn cũng được xét dưới dạng ×100 (tỉ lệ sang %), /1.000, /1.000.000 (nghìn, triệu).
2. Từ và ký tự bị cấm (thân bài; một số mục áp cả phụ lục).
3. Đường dẫn trong phụ lục A có tồn tại không.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/check_report.py --md E:/DATN/baocao/bao_cao_noidung1-5.md
      --chapters E:/DATN/baocao --label 20261010_lan1
"""
import argparse
import bisect
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_common import REPORT_LOG_DIR, Log, header, sha256_file  # noqa: E402

CHAPTERS = ["chuong_n2_du_lieu.md", "chuong_n3_ma_tran_m.md", "chuong_n4_do_thi.md", "chuong_n5_baselines.md"]
LOG_GLOBS = [
    "ai/data/processed/*.log", "ai/data/processed/*.json",
    "ai/data/kg/*.json", "ai/data/kg/*.txt", "ai/data/kg_v62abf54/*.json",
    "ai/data/survey/*.log", "ai/data/survey/**/*.log",
    "results/n5/test_final_20261009/*.json", "results/n5/test_final_20261009/*.md",
    "results/n5/test_final_20261009/*.log", "results/n5/val_sweep_20261010/*.json",
    "ai/config/n5_final.toml",
]
MAX_BYTES = 20 * 1024 * 1024

VN_NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d])")
EN_NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?![\d])")
APPROX = re.compile(r"(khoảng|gần|hơn|dưới|chỉ|xấp xỉ)\s*$", re.I)
FORBID_WORDS = ["triệt để", "vượt trội", "mạnh mẽ", "toàn diện", "tuyệt đối", "đáng kể", "Lưu ý:",
                "Điểm quan trọng:", "Tóm lại:", "suy từ code", "tính tay", "[CẦN", "Claude", "SOTA",
                "chuẩn xác", "hoàn hảo"]
FORBID_CHARS = ["—", "→", "←", "✔", "✘", "⇒"]


def parse_vn(tok):
    return float(tok.replace(".", "").replace(",", "."))


def parse_en(tok):
    return float(tok.replace(",", ""))


def decimals(tok_vn):
    return len(tok_vn.split(",")[1]) if "," in tok_vn else 0


def strip_noise(text):
    text = text.replace("{,}", ",")
    text = re.sub(r"`[^`]*`", " ", text)                       # mã
    text = re.sub(r"https?://\S+", " ", text)                    # URL
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)(\{[^}]*\})?", r"\1", text)  # ảnh: giữ chú thích
    text = re.sub(r"```\{=openxml\}.*?```", " ", text, flags=re.S)
    text = re.sub(r"\b\d{1,2}/\d{1,2}(?:/\d{4})?\b", " ", text)  # ngày
    text = re.sub(r"\b\d{1,2}/\d{1,2}[–-]\d{1,2}/\d{1,2}\b", " ", text)
    text = re.sub(r"\b(Bảng|Hình|mục|Phụ lục|chương|Chương|nội dung|Nội dung|S)\s*[0-9A-Z]+(?:\.\d+)*\.?", " ", text)
    text = re.sub(r"^#+ .*$", " ", text, flags=re.M)           # tiêu đề
    text = re.sub(r"\[\d{1,2}\]", " ", text)                     # trích dẫn
    text = re.sub(r"@\d+", " ", text)                            # @K
    text = re.sub(r"\b(19|20)\d{2}\b", " ", text)                # năm
    return text


class Corpus:
    """Chuỗi số nguyên văn của 4 chương và của log; giá trị số của 4 chương để so số làm tròn."""

    def __init__(self, chap_dir, log):
        self.chap_tokens, self.log_tokens, vals = set(), set(), set()
        files = [os.path.join(chap_dir, c) for c in CHAPTERS]
        for c in files:
            t = open(c, encoding="utf-8").read().replace("{,}", ",")
            for m in VN_NUM.finditer(t):
                self.chap_tokens.add(m.group(1))
                vals.add(parse_vn(m.group(1)))
        n_logs = 0
        for g in LOG_GLOBS:
            for p in glob.glob(g, recursive=True):
                if os.path.getsize(p) > MAX_BYTES:
                    continue
                n_logs += 1
                t = open(p, encoding="utf-8", errors="replace").read()
                for m in EN_NUM.finditer(t):
                    self.log_tokens.add(m.group(1))
                for m in VN_NUM.finditer(t):
                    self.log_tokens.add(m.group(1))
        derived = set()
        for v in vals:
            derived.update((v, v * 100, v / 1000, v / 1e6))
        self.chap_vals = sorted(derived)
        log(f"nguồn: {len(files)} chương ({len(self.chap_tokens)} chuỗi số), "
            f"{n_logs} log / file kết quả ({len(self.log_tokens)} chuỗi số)")

    def in_log(self, tok_vn):
        """Chuỗi số có nguyên văn trong log, kiểu Việt hoặc đổi sang kiểu Anh."""
        en = tok_vn.replace(".", "\0").replace(",", ".").replace("\0", ",")
        return tok_vn in self.log_tokens or en in self.log_tokens

    def near_chapter(self, lo, hi):
        i = bisect.bisect_left(self.chap_vals, lo)
        return i < len(self.chap_vals) and self.chap_vals[i] <= hi

    def nearest_chapter(self, target):
        i = bisect.bisect_left(self.chap_vals, target)
        cands = [self.chap_vals[j] for j in (i - 1, i) if 0 <= j < len(self.chap_vals)]
        return min(cands, key=lambda c: abs(c - target)) if cands else None

    def classify(self, tok, approx, scale):
        """Trả (loại, giá trị khớp): loại là 'chuong' / 'log' / 'lam_tron', hoặc (None, None)."""
        if scale == 1 and not approx:
            if tok in self.chap_tokens:
                return "chuong", None
            if self.in_log(tok):
                return "log", None
            return None, None
        v, d = parse_vn(tok), decimals(tok)
        target = v * scale
        tol = max(0.5 * 10 ** (-d) * scale, 0.02 * abs(target))
        if self.near_chapter(target - tol, target + tol):
            return "lam_tron", self.nearest_chapter(target)
        return None, None


def check_numbers(region, corpus, log, name):
    text = strip_noise(region)
    bad, review, n, kinds = [], [], 0, {"chuong": 0, "log": 0, "lam_tron": 0}
    for line in text.split("\n"):
        for m in VN_NUM.finditer(line):
            tok = m.group(1)
            v = parse_vn(tok)
            if decimals(tok) == 0 and "." not in tok and v <= 30:
                continue
            n += 1
            before = line[:m.start()]
            after = line[m.end():m.end() + 8].strip()
            approx = bool(APPROX.search(before[-12:]))
            scale = 1e3 if after.startswith("nghìn") else (1e6 if after.startswith("triệu") else 1)
            k, near = corpus.classify(tok, approx, scale)
            if k is None:
                bad.append((tok, line.strip()[:110]))
            else:
                kinds[k] += 1
                if k == "log":
                    review.append(("chỉ có trong log", tok, line.strip()[:100]))
                elif k == "lam_tron":
                    review.append((f"làm tròn từ {near:g}", tok, line.strip()[:90]))
    log(f"[{name}] số đã xét: {n} (nguyên văn trong 4 chương {kinds['chuong']}, nguyên văn trong log "
        f"{kinds['log']}, làm tròn từ số của 4 chương {kinds['lam_tron']}); không tìm thấy: {len(bad)}")
    for tok, ctx in bad:
        log(f"    KHÔNG THẤY {tok:>12}  | {ctx}")
    log(f"  cần đọc tay ({len(review)} số chỉ có trong log hoặc là số làm tròn):")
    for what, tok, ctx in review:
        log(f"    {tok:>10} ({what}) | {ctx}")
    return bad


def self_test(corpus, log):
    """Số thật phải được nhận đúng loại; số giả không được nhận là 'có trong 4 chương'."""
    cases = [("0,0448", False, 1, {"chuong"}), ("0,0449", False, 1, {None, "log"}),
             ("67.661", False, 1, {"chuong"}), ("67.662", False, 1, {None, "log"}),
             ("0,04487", False, 1, {None}), ("68", True, 1, {"lam_tron"}),
             ("2,5", True, 1e6, {"lam_tron"}), ("123.456.789", True, 1, {None})]
    ok = True
    for tok, approx, scale, expect in cases:
        got, _ = corpus.classify(tok, approx, scale)
        ok &= got in expect
        log(f"    tự thử {tok:>8} (khoảng={approx}, x{scale:g}): {got} {'đúng' if got in expect else 'SAI'}")
    log(f"[tự thử] {'ĐẠT' if ok else 'KHÔNG ĐẠT'}")
    return ok


def check_forbidden(region, log, name, prose_only_chars=True):
    issues = []
    for i, line in enumerate(region.split("\n"), 1):
        s = line.strip()
        for w in FORBID_WORDS:
            if w.lower() in s.lower():
                issues.append((i, f"từ cấm '{w}'", s[:100]))
        if prose_only_chars and (s.startswith("|") or s.startswith("$$") or s.startswith("!")):
            continue
        prose = re.sub(r"\$[^$]*\$", " ", s)
        for c in FORBID_CHARS:
            if c in prose:
                issues.append((i, f"ký tự '{c}'", s[:100]))
    log(f"[{name}] từ / ký tự cấm: {len(issues)}")
    for i, what, ctx in issues:
        log(f"    dòng {i}: {what} | {ctx}")
    return issues


def check_body_style(body, log):
    issues = []
    for i, line in enumerate(body.split("\n"), 1):
        s = line.strip()
        if not s or s.startswith("|") or s.startswith("#"):
            continue
        if "`" in s:
            issues.append((i, "có mã (backtick)", s[:90]))
        if re.search(r"\b[0-9a-f]{7,40}\b", s) and re.search(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b", s):
            issues.append((i, "giống mã băm / commit", s[:90]))
        if re.search(r"\.(py|log|json|csv|toml)\b|ai/|results/", s):
            issues.append((i, "đường dẫn / tên file", s[:90]))
        if re.search(r"\bQĐ\b", s):
            issues.append((i, "mã quyết định", s[:90]))
        bold = [m.start() for m in re.finditer(r"\*\*", s)]
        if bold and bold[0] != 0:
            issues.append((i, "in đậm giữa câu", s[:90]))
    log(f"[thân bài] quy ước trình bày: {len(issues)} chỗ")
    for i, what, ctx in issues:
        log(f"    dòng {i}: {what} | {ctx}")
    return issues


def check_paths(appendix_a, log):
    missing, n = [], 0
    for m in re.finditer(r"`([^`]+)`", appendix_a):
        tok = m.group(1).split()[0]
        if "/" in tok and re.search(r"\.(py|log|json|csv|toml|md|txt|ps1)$", tok):
            n += 1
            if not glob.glob(tok):
                missing.append(tok)
    log(f"[phụ lục A] đường dẫn đã xét: {n}; không tồn tại: {len(missing)}")
    for p in missing:
        log(f"    {p}")
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--chapters", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_check_report_{args.label}.log"))
    header(log, __file__)
    text = open(args.md, encoding="utf-8").read()
    log(f"báo cáo: {args.md} (sha256 {sha256_file(args.md)})")
    i0, i1 = text.index("\n# Mở đầu"), text.index("\n# Tài liệu tham khảo")
    i_a, i_b = text.index("\n# Phụ lục A."), text.index("\n# Phụ lục B.")
    body, appendix, app_a = text[i0:i1], text[i_a:], text[i_a:i_b]
    corpus = Corpus(args.chapters, log)
    st_ok = self_test(corpus, log)
    bad_body = check_numbers(body, corpus, log, "thân bài")
    bad_app = check_numbers(appendix, corpus, log, "phụ lục (tham khảo)")
    f_body = check_forbidden(body, log, "thân bài")
    f_all = check_forbidden(text[:i0] + text[i1:], log, "bìa, tài liệu, phụ lục")
    s_body = check_body_style(body, log)
    miss = check_paths(app_a, log)
    holes = sorted(set(re.findall(r"\[(?:TÊN TRƯỜNG|KHOA|LỚP|MSSV|LINK GITHUB)\]", text)))
    log(f"chỗ để trống cần điền: " + ", ".join(f"{h} ×{text.count(h)}" for h in holes))
    ok = st_ok and not (bad_body or f_body or f_all or s_body or miss)
    log("KẾT LUẬN: " + ("ĐẠT CẢ" if ok else "CÒN CHỖ CẦN XEM (liệt kê ở trên)"))
    log.save()


if __name__ == "__main__":
    main()
