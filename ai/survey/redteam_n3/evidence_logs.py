"""
Red Team nội dung 3, lần 1 — mục 4, bảng "Chưa có bằng chứng trong Project" (CHẨN ĐOÁN).

Với mỗi số liệu trong bảng: tìm trong các log / file tóm tắt đang có trên máy xem có file nào chứa số đó không.
KHÔNG chạy lại script nào; chỉ đọc file văn bản. Số trong log viết kiểu Anh (54,638; 87.9%) nên regex theo kiểu đó.

Mỗi số có một hoặc nhiều "cách khớp" (alternatives); mỗi cách là danh sách regex phải cùng có trong MỘT file.
Kết quả in: số -> các file khớp (kèm dòng khớp đầu tiên) hoặc "KHÔNG CÓ".
Log do phiên Red Team này tạo (run_redteam_n3_*.log) được đánh dấu [mới] để tách khỏi bằng chứng có từ trước.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/evidence_logs.py > ai/data/survey/run_redteam_n3_evidence.log
"""
import glob
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.chdir(ROOT)

PATTERNS = ["ai/data/survey/*.log", "ai/data/survey/*.json", "ai/data/survey/before_typefix/*.json",
            "ai/data/survey/before_typefix/*.txt", "ai/data/kg/*.txt", "ai/data/kg/*.log",
            "ai/data/kg/mount_compat_stats.json", "ai/data/kg_new/*.txt", "ai/data/kg_new/mount_compat_stats.json",
            "ai/data/*.log", "ai/survey/content3/*.log", "ai/survey/content3/*.txt"]
SKIP = {"child_asins.json",          # chỉ chứa ASIN, không phải log
        "run_redteam_n3_evidence.log"}  # đầu ra của chính script này
files = sorted({f.replace("\\", "/") for p in PATTERNS for f in glob.glob(p) if os.path.basename(f) not in SKIP})
text = {f: open(f, encoding="utf-8-sig", errors="replace").read() for f in files}
NEW = "run_redteam_n3_"


def B(s):          # số đứng riêng (không dính chữ số / dấu phân cách khác)
    return r"(?<![\d.,])" + s + r"(?![\d]|[.,]\d)"


# (dòng của bảng Red Team, nhãn số liệu, [cách khớp 1, cách khớp 2, ...]); mỗi cách khớp = [regex, ...]
CLAIMS = [
    ("1. Holdout/fix trước sửa", "holdout Lensfun 502/571 = 87,9%", [[B("502/571")]]),
    ("1. Holdout/fix trước sửa", "holdout Wikidata 263/315 = 83,5%", [[B("263/315")]]),
    ("1. Holdout/fix trước sửa", "holdout theo sản phẩm 527/612 = 86,1%", [[B("527/612")]]),
    ("1. Holdout/fix trước sửa", "holdout ngàm Lensfun 358/366", [[B("358/366")]]),
    ("1. Holdout/fix trước sửa", "fix 481/548, 245/295, 514/598", [[B("481/548"), B("245/295"), B("514/598")]]),
    ("2. Kết quả 07/10", "Lensfun loại 983/1.119 = 87,8%", [[B("983/1,?119")], [r'"loai_dung": 983\b', r'"khop": 1119\b']]),
    ("2. Kết quả 07/10", "Lensfun ngàm 672/685 = 98,1%", [[B("672/685")], [r'"ngam_dung": 672\b', r'"ngam_gan": 685\b']]),
    ("2. Kết quả 07/10", "Lensfun khung 351/351", [[B("351/351")], [r'"khung_dung": 351\b', r'"khung_gan": 351\b']]),
    ("2. Kết quả 07/10", "openMVG khung 214/215 = 99,5%", [[B("214/215")], [r'"khung_dung": 214\b', r'"khung_gan": 215\b']]),
    ("2. Kết quả 07/10", "Wikidata loại 508/610 = 83,3%", [[B("508/610")], [r'"loai_dung": 508\b', r'"khop": 610\b']]),
    ("2. Kết quả 07/10", "Wikidata ngàm 450/450", [[B("450/450")], [r'"ngam_dung": 450\b', r'"ngam_gan": 450\b']]),
    ("2. Kết quả 07/10", "bỏ qua tiêu đề phụ kiện 236 / 133 / 190",
     [[r"236 tiêu đề phụ kiện", r"133 tiêu đề phụ kiện", r"190 tiêu đề phụ kiện"],
      [r'"bo_qua_tieu_de_phu_kien": 236\b', r'"bo_qua_tieu_de_phu_kien": 133\b', r'"bo_qua_tieu_de_phu_kien": 190\b']]),
    ("3. M trung gian", "482 × 886", [[r"482\s*[x×]\s*886"]]),
    ("3. M trung gian", "M=1 54.638 / không biết 3.474 (kg_new, trước QĐ 11)", [[B("54,638"), B("3,474")]]),
    ("3. M trung gian", "M=1 56.276 / không biết 1.836 / cờ 1.638 (sau QĐ 11)", [[B("56,276"), B("1,836"), B("1,638")]]),
    ("3. M trung gian", "538 × 1.037; ống 1 ngàm 1.167 (sau sửa loại lần 1)", [[r"538\s*[x×]\s*1,?037"], [r"ống có 1 ngàm: 1,167"]]),
    ("3. M trung gian", "M=1 75.690", [[B("75,690")]]),
    ("3. M trung gian", "cờ crop 2.186", [[B("2,186")]]),
    ("3. M trung gian", "không biết 2.960", [[B("2,960")]]),
    ("4. Thân phim", "17 thân máy phim", [[r"thân máy phim(?: \(QĐ 16\))?: 17\b"]]),
    ("4. Thân phim", "Nikon F 7 + Canon EF 8 + Canon FD 2", [[r"'canon_ef': 8, 'nikon_f': 7, 'canon_fd': 2"]]),
    ("4. Thân phim", "462 cặp crops_sensor (DX trên thân Nikon phim)", [[r"nikon_dx_on_fx_f\s+462\b"]]),
    ("4. Thân phim", "294 cặp cờ QĐ 11 trên thân phim", [[r"autocrop\s+294\b"]]),
    ("4. Thân phim", "trước sửa: 53 và 36 cặp", [[r"nikon_dx_on_fx_f\D{0,20}53\b"], [r"autocrop\D{0,20}36\b"]]),
    ("5. 84 ca sai nửa fix", "514/598 (=> 84 ca sai loại)", [[B("514/598"), r"ca sai của nửa FIX"]]),
    ("5. 84 ca sai nửa fix", "68 lỗi quy tắc / 16 đáp án sai", [[r"\b68\b.{0,40}\b16\b"], [r"quy tắc sai.{0,10}68"]]),
    ("5. 84 ca sai nửa fix", "47 / 15 / 3 / 2 / 1", [[r"\b47\b.{0,30}\b15\b.{0,30}\b3\b"]]),
    ("6. Đổi loại ngoài holdout", "138 / 32 / 7 / 2 / 1", [[r"phu_kien\s*->\s*ong\D{0,10}138\b"], [B("138") + r".{0,60}\b32\b"]]),
    ("7. Dev 50", "loại 49/50, ngàm 46/50, khung 43/50", [[B("49/50")], [B("46/50")], [B("43/50")]]),
    ("7. Dev 50", "36 mẫu ngoài holdout: 35/36, 32/36, 30/36", [[B("35/36")], [B("32/36")], [B("30/36")]]),
    ("7. Dev 50", "14 mẫu dev nằm trong holdout", [[r"\b14\b[^\n]{0,40}holdout"], [r"holdout[^\n]{0,40}\b14\b"]]),
    ("8. Split", "sha256 FECEE371…3C0B", [[r"(?i)fecee371"]]),
    ("8. Split", "lần 1 = lần 2 từng ô (diff)", [[r"(?i)(giống hệt|identical|khác nhau: 0|0 ô khác)"]]),
    ("9. Kịch bản", "951 người dùng (661 / 9 / 10 / 23 / 248)",
     [[B("951"), r"compatible_with\s+661\b", r"crops_sensor\s+9\b", r"requires_adapter\s+10\b", r"unknown\s+23\b",
       r"incompatible\s+248\b"]]),
    ("10. Khảo sát mục 4", "1.364 thân / 1.434 ống (sample03)", [[r"Body \(1,?364\)", r"Lens \(1,?434\)"]]),
    ("10. Khảo sát mục 4", "494 máy thay ống (315 DSLR + 179 Mirrorless)", [[B("494")]]),
    ("10. Khảo sát mục 4", "826 máy không thay ống / 801 Point & Shoot", [[B("826")], [B("801")]]),
    ("10. Khảo sát mục 4", "493 máy compact có ngàm trong CM", [[r"camera_fixed_or_video\s+1580\s+493\b"]]),
    ("10. Khảo sát mục 4", "lệch 4,8% ống (39/812)", [[B(r"4[.,]8") + r"\s?%"], [r"\b39/812\b"]]),
    ("10. Khảo sát mục 4", "  thành phần: lens rec&CM 812, rec==CM 773", [[r"\blens\b[^\n]*\b812\s+773\b"]]),
    ("10. Khảo sát mục 4", "lệch 5,4% thân (22/407)", [[B(r"5[.,]4") + r"\s?%"], [r"\b22/407\b"]]),
    ("10. Khảo sát mục 4", "  thành phần: body rec&CM 407, rec==CM 385", [[r"\bbody\b[^\n]*\b407\s+385\b"]]),
    ("10. Khảo sát mục 4", "445 thân + 967 ống; 5,05%", [[r"thân máy có ngàm: 445 \| ống kính có ngàm: 967", r"5\.05%"]]),
    ("10. Khảo sát mục 4", "85,1% số thân và ống thật", [[B(r"85[.,]1") + r"\s?%"]]),
    ("10. Khảo sát mục 4", "8,83% số tương tác", [[r"8\.83%"]]),
    ("10. Khảo sát mục 4", "1.065 người dùng kịch bản; 729 cùng ngàm", [[r"1,065", r"cùng ngàm với thân đã có: 729"]]),
    ("10. Khảo sát mục 4", "326 (30,6%) khác ngàm hẳn; 10 qua ngàm chuyển", [[B("326")], [B(r"30[.,]6") + r"\s?%"]]),
    ("10. Khảo sát mục 4", "  (log có: khác ngàm 336 = 326 + 10?)", [[r"khác ngàm: 336\b"]]),
    ("10. Khảo sát mục 4", "104/967 ống hãng thứ ba > 1 asin con; 175/445 thân", [[r"\(True, True\): 104\b", r"175 \(39\.3%\)"]]),
    ("11. Wilson", "khoảng tin cậy Wilson [85,0–90,3] ...", [[r"(?i)wilson"], [r"85[.,]0\s*[-–]\s*90[.,]3"]]),
]


def first_line(t, rx):
    m = re.search(rx, t, re.M)
    if not m:
        return ""
    s = t.rfind("\n", 0, m.start()) + 1
    e = t.find("\n", m.end())
    return t[s:e if e >= 0 else None].strip()[:150]


print(f"Quét {len(files)} file văn bản:")
for f in files:
    print(f"  {f}  ({os.path.getsize(f):,} B){'  [mới, phiên Red Team]' if NEW in f else ''}")

# Wilson: tìm thêm trong mọi file .py của ai/
py_hits = [f.replace("\\", "/") for f in glob.glob("ai/**/*.py", recursive=True)
           if "redteam_n3" not in f.replace("\\", "/") and ".venv" not in f
           and re.search(r"(?i)wilson", open(f, encoding="utf-8", errors="replace").read())]

summary = []
cur_row = None
for row, label, alts in CLAIMS:
    if row != cur_row:
        print(f"\n### {row}")
        cur_row = row
    hits = []
    for f in files:
        for alt in alts:
            if all(re.search(rx, text[f], re.M) for rx in alt):
                hits.append((f, first_line(text[f], alt[0])))
                break
    old = [h for h in hits if NEW not in h[0]]
    new = [h for h in hits if NEW in h[0]]
    state = "CÓ LOG" if old else ("CHỈ CÓ LOG MỚI (phiên này)" if new else "KHÔNG CÓ")
    summary.append((row, label, state, [h[0] for h in old], [h[0] for h in new]))
    print(f"- {label}: {state}")
    for f, line in hits:
        print(f"    {f}{'  [mới]' if NEW in f else ''}\n      > {line}")

print("\n### Wilson trong code: " + (", ".join(py_hits) if py_hits else "không file .py nào trong ai/ có chữ 'wilson'"))

# File dữ liệu được nhắc trong bảng Red Team: có tồn tại không
print("\n### File được nhắc trong bảng Red Team (chỉ kiểm tồn tại)")
for p in ["ai/data/survey/run_typefix_report.log", "ai/data/survey/before_typefix/eval_external_matches.csv",
          "ai/data/survey/before_typefix/eval_external_matches_lan1.csv", "ai/data/survey/run_eval_external.log",
          "ai/data/kg_new/mount_compat_log.txt", "ai/data/survey/before_typefix/mount_compat_log.txt",
          "ai/survey/content3/eval_split.csv", "ai/survey/content3/check_dev.py", "ai/survey/content3/label_dev_50_claude.csv",
          "ai/data/survey/run_check_dev.log", "ai/data/survey/run_scenario_kgnew.log", "ai/data/survey/run_survey2.log",
          "ai/data/survey/run_coverage.log", "ai/data/survey/run_sample03.log", "ai/data/survey/run_child_asins.log",
          "ai/data/survey/run_fix_errors_before.log"]:
    print(f"  {'CÓ   ' if os.path.exists(p) else 'KHÔNG'} {p}"
          + (f"  ({os.path.getsize(p):,} B, sửa lần cuối {__import__('time').strftime('%d/%m %H:%M', __import__('time').localtime(os.path.getmtime(p)))})" if os.path.exists(p) else ""))

# Đếm ASIN sai loại trong log nửa fix (đọc log, không chạy lại)
fx = "ai/data/survey/run_fix_errors_before.log"
if fx in text:
    asins = {m.group(1) for m in re.finditer(r"^\w+ (B\w{9}|\d{9}[\dX]) sai=loai", text[fx], re.M)}
    print(f"\n### {fx}: số ASIN khác nhau có dòng 'sai=loai' = {len(asins)} (so với 84 = 598 - 514)")

print("\n### TÓM TẮT")
for row, label, state, old, new in summary:
    print(f"  [{state:26s}] {row} | {label} | {', '.join(old) or '-'}{' | mới: ' + ', '.join(new) if new else ''}")
