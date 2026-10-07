"""Từ điển nhận diện ngàm (bản khảo sát, CHƯA phải pipeline).
Mỗi ngàm: danh sách regex chạy trên chuỗi đã lowercase.
Chỉ bắt khi văn bản NÓI RÕ ngàm (tên ngàm, hoặc tiền tố dòng ống kính gắn chặt với 1 ngàm).
Tên hãng trơn ("Canon", "Sony Alpha", "Nikkor") KHÔNG đủ -> không gán."""
import re

MM = r"\s?\d{1,3}(?:\.\d)?(?:\s?-\s?\d{1,3})?\s?mm"   # "50mm", "24-70 mm", "18-55mm"

MOUNT_PATTERNS = {
    # Canon
    "Canon RF":   [r"\bcanon\s+rf\b(?!-?\d{3}\b)", r"\brf[\s-]?mount", r"\brf-s(?=\d|\b)", r"\brf" + MM],
    "Canon EF-M": [r"\bef-?m\b", r"\bcanon\s+(?:eos\s+)?m[\s-]?mount"],
    "Canon EF":   [r"\bcanon\s+ef\b(?!-[sm]\b)", r"\bef[\s-]?mount", r"\bef-?s\b", r"\bef" + MM,
                   r"\bef/ef-?s\b", r"\bcanon\b.*\bef\s?\d{2,3}(?:-\d{2,3})?\b"],          # EF và EF-S gộp 1 họ (ống EF lắp được mọi thân EF/EF-S)
    "Canon FD":   [r"\bcanon\s+fd\b", r"\bfd[\s-]?mount"],
    # Nikon
    "Nikon Z":    [r"\bnikon\s+z(?:[\s-]?mount)?\b", r"\bz[\s-]mount\b", r"\bnikkor\s+z\b"],
    "Nikon F":    [r"\bnikon\s+f(?:[\s-]?mount)?\b(?!/)", r"\bf[\s-]mount\b", r"\baf-[sp]\b",
                   r"\bnikon\s+f\s?\((?:fx|dx)\)", r"\bai-s\b"],
    "Nikon 1":    [r"\bnikon\s+1\b(?!\d)", r"\b1\s+nikkor\b"],
    # Sony
    "Sony E":     [r"\bsony\s+f?e\b(?!-\d)", r"\bf?e[\s-]mount\b", r"\bemount\b", r"\bfe" + MM,
                   r"\bselp?\d{2,4}", r"\bnex\b", r"\bsony\b.*\bfe\b(?!-)"],
    "Sony A":     [r"\bsal\d{2,5}", r"\bsony\s+a[\s-]?mount\b", r"\ba[\s-]mount\b", r"\bsony/minolta\b", r"\bminolta\s+(?:af|maxxum|a\b|alpha)"],
    # Fujifilm
    "Fujifilm X": [r"\bfuji(?:film)?\s+x(?:[\s-]?mount)?\b(?![-\s]?[a-z]{0,3}\d|\s+series)", r"\bx[\s-]mount\b", r"\bxf" + MM, r"\bxc" + MM,
                   r"\bfujinon\s+xf"],
    "Fujifilm G": [r"\bgfx\b", r"\bg[\s-]mount\b"],
    # Olympus / Panasonic
    "Micro Four Thirds": [r"\bmicro\s*(?:four|4)\s*(?:thirds|/\s?3)", r"\bm4/3\b", r"\bmft\b", r"\bm43\b",
                          r"\bm\.?\s?zuiko\b", r"\blumix\s+g\s?(?:x\s)?(?:vario|\d)"],
    "Four Thirds": [r"(?<!micro )(?<!micro)\bfour\s*thirds\b", r"(?<!\bm\.)(?<!\bm\. )(?<!\bm )\bzuiko\s+digital\b"],
    # Khác
    "L-Mount":    [r"\bl[\s-]mount\b", r"\bleica\s+l\b"],
    "Leica M":    [r"\bleica\s+m(?:[\s-]?mount)?\b(?!-?\d)"],
    "Pentax K":   [r"\bpentax\s+k(?:a?f\d?)?(?:[\s-]?mount)?\b(?!-?\d)", r"\bk[\s-]mount\b", r"\bkaf\d?\b", r"\bpk\s+mount"],
    "Pentax Q":   [r"\bpentax\s+q\b"],
    "Samsung NX": [r"\bsamsung\s+nx(?:[\s-]?mount)?\b(?!\d)", r"\bnx[\s-]mount\b"],
    "Sigma SA":   [r"\bsigma\s+sa\b", r"\bsa[\s-]mount\b"],
    "M42":        [r"\bm42\b"],
    "T-Mount":    [r"\bt2?[\s-]mount\b", r"\bt-?2\s+(?:adapter|ring)"],
    "C-Mount":    [r"\bc[\s-]mount\b"],
}
COMPILED = {m: [re.compile(p) for p in ps] for m, ps in MOUNT_PATTERNS.items()}


def find_mounts(text):
    """Trả về {ngàm: chuỗi khớp đầu tiên} cho mọi ngàm được nhắc rõ trong text."""
    t = (text or "").lower()
    hits = {}
    for m, regs in COMPILED.items():
        for r in regs:
            mo = r.search(t)
            if mo:
                hits[m] = mo.group(0)
                break
    # "micro four thirds" chứa "four thirds": nếu chỉ có cụm micro thì bỏ Four Thirds
    # Có MFT thì bỏ Four Thirds, trừ khi văn bản nói "four thirds" riêng (vd ngàm chuyển 4/3 -> MFT)
    if "Four Thirds" in hits and "Micro Four Thirds" in hits:
        t2 = re.sub(r"micro\s*(?:four|4)\s*(?:thirds|/\s?3)", "", t)
        if not re.search(r"\bfour\s*thirds\b", t2):
            del hits["Four Thirds"]
    return hits


# Luật "hãng + máy DSLR/SLR" -> ngàm (chỉ dùng cho ỐNG KÍNH): hãng chỉ có 1 ngàm cho dòng DSLR.
# vd "Tokina 12-24mm for Canon EOS Digital SLR" -> Canon EF; "Nikon AF Nikkor 35-70mm" -> Nikon F.
SLR = r"(?:dslr|d-slr|digital\s+slr|slr|reflex)"
BRAND_SLR = {
    "Canon EF": [rf"\bcanon\b.*\b{SLR}\b", rf"\b{SLR}\b.*\bcanon\b", r"\bcanon\s+eos\s+(?:digital\s+)?rebel\b",
                 r"\bfor\s+canon\s+eos\s+(?:\d{1,4}d|[1-9]d|rebel)", r"\bcanon\s+eos\s+(?:digital|film)\b"],
    "Nikon F":  [rf"\bnikon\b.*\b{SLR}\b", rf"\b{SLR}\b.*\bnikon\b", r"\baf(?:-d)?\s+(?:zoom-)?nikkor\b",
                 r"\bfor\s+nikon\s+d\d{2,4}\b", r"\bnikon\s+af\b"],
    "Sony A":   [rf"\b(?:minolta|sony)\b.*\b{SLR}\b(?!.*\b(?:nex|e-?mount)\b)", r"\bminolta\b.*\baf\b", r"\bmaxxum\b"],
    "Pentax K": [rf"\bpentax\b.*\b{SLR}\b", r"\bpentax\s+(?:smc\s+)?(?:d\s?fa|da|fa)\b", r"\bpentax-(?:d\s?fa|da|fa)\b"],
    "Four Thirds": [rf"\bolympus\b.*\b{SLR}\b", r"(?<!micro\s)\b4/3\s+(?:digital\s+)?(?:cameras|dslr|system)"],
}
BRAND_SLR_C = {m: [re.compile(p) for p in ps] for m, ps in BRAND_SLR.items()}
MIRRORLESS_HINT = re.compile(r"\bmirrorless\b|\beos\s?[mr]\d*\b|\bnex\b|\bnikon\s+z\b|\bnikon\s+1\b")


def find_slr_mounts(text):
    t = (text or "").lower()
    if MIRRORLESS_HINT.search(t):
        return {}
    hits = {}
    for m, regs in BRAND_SLR_C.items():
        for r in regs:
            mo = r.search(t)
            if mo:
                hits[m] = mo.group(0)[:40]
                break
    return hits


# Giá trị details["Compatible Mountings"]: tách theo dấu phẩy, mỗi mảnh map riêng.
CM_EXTRA = [
    (re.compile(r"^nikon\s*\(?(?:fx|dx)\)?$|^nikon\s+f\s?\(?(?:fx|dx)\)?$|^nikon f\(dx\)$"), "Nikon F"),
    (re.compile(r"^pentax\s+kaf\d?$|^pentax\s+k$"), "Pentax K"),
    (re.compile(r"^(?:sony/)?minolta\s+alpha(?:\s+dt)?$|^sony\s+a$"), "Sony A"),
    (re.compile(r"^sony\s+(?:fe|e)(?:\s+\(nex\))?$"), "Sony E"),
    (re.compile(r"^olympus/panasonic\s+micro\s+4/3$"), "Micro Four Thirds"),
    (re.compile(r"^leica\s+l$"), "L-Mount"),
    (re.compile(r"^leica\s+m$"), "Leica M"),
    (re.compile(r"^canon\s+ef-?s$"), "Canon EF"),
    (re.compile(r"^fujifilm\s+g$"), "Fujifilm G"),
]


def cm_mounts(value):
    """Map giá trị Compatible Mountings -> (tập ngàm rõ, tập mảnh mơ hồ)."""
    clear, vague = set(), set()
    for tok in re.split(r"[,;]|\band\b", value or ""):
        tok = tok.strip().lower()
        if not tok:
            continue
        got = None
        for r, m in CM_EXTRA:
            if r.search(tok):
                got = m; break
        if got is None:
            h = find_mounts(tok)
            if len(h) == 1:
                got = next(iter(h))
        if got:
            clear.add(got)
        else:
            vague.add(tok)
    return clear, vague
