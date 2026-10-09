"""Gộp các phần báo cáo thành một file Markdown và đánh số lại trích dẫn kiểu IEEE.

- Lấy bìa, mở đầu, chương 1–2, phụ lục A (phần đầu) và phụ lục B từ bản thử đã duyệt.
- Chèn chương 3–5, kết luận, tài liệu tham khảo (sinh từ tltk.txt), phần tiếp của phụ lục A,
  phụ lục C–F.
- Trích dẫn [n] được đánh số lại theo thứ tự xuất hiện lần đầu trong văn bản (IEEE); danh mục
  tài liệu sắp theo số mới. Câu mở đầu mục tài liệu tham khảo liệt kê các tài liệu nhóm mới đọc
  phần tóm tắt (cờ "tomtat" trong tltk.txt).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/merge_report.py --dir E:/DATN/baocao --out E:/DATN/baocao/bao_cao_noidung1-5.md
"""
import argparse
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

CITE = re.compile(r"\[(\d{1,2})\]")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").strip("\n") + "\n"


def split_trial(text):
    i_ref = text.index("\n# Tài liệu tham khảo")
    i_a = text.index("\n# Phụ lục A.")
    i_b = text.index("\n# Phụ lục B.")
    front = text[:i_ref].strip("\n") + "\n"
    pl_a = text[i_a:i_b].strip("\n") + "\n"
    pl_b = text[i_b:].strip("\n") + "\n"
    return front, pl_a, pl_b


def compress(nums):
    """[8, 9, 10, 12] -> '[8]–[10], [12]'"""
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"[{nums[i]}]" if i == j else (f"[{nums[i]}], [{nums[j]}]" if j == i + 1
                                                   else f"[{nums[i]}]–[{nums[j]}]"))
        i = j + 1
    return ", ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = args.dir
    front, pl_a, pl_b = split_trial(read(os.path.join(d, "ban_thu.md")))
    old = "Bản thử này mới có phần của mở đầu, chương 1 và chương 2."
    assert old in pl_a
    pl_a = pl_a.replace(" " + old, "")
    parts_body = [front] + [read(os.path.join(d, "phan", f)) for f in ("c3.md", "c4.md", "c5.md", "kl.md")]
    parts_app = [pl_a, read(os.path.join(d, "phan", "plA2.md")), pl_b] + \
        [read(os.path.join(d, "phan", f)) for f in ("plC.md", "plD.md", "plE.md", "plF.md")]

    refs = {}
    for line in read(os.path.join(d, "phan", "tltk.txt")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        num, flag, text = line.split("|", 2)
        refs[int(num)] = (flag, text)

    body = "\n".join(parts_body)
    app = "\n".join(parts_app)
    order = []
    for m in CITE.finditer(body + "\n" + app):
        n = int(m.group(1))
        if n in refs and n not in order:
            order.append(n)
    missing = [n for n in refs if n not in order]
    unknown = sorted({int(m.group(1)) for m in CITE.finditer(body + app)} - set(refs))
    assert not unknown, f"trích dẫn không có trong danh mục: {unknown}"
    if missing:
        print("CẢNH BÁO: tài liệu không được trích:", missing)
    order += missing
    newnum = {old_n: i + 1 for i, old_n in enumerate(order)}

    def renum(text):
        return CITE.sub(lambda m: f"[{newnum[int(m.group(1))]}]" if int(m.group(1)) in newnum else m.group(0), text)

    body, app = renum(body), renum(app)
    tomtat = sorted(newnum[n] for n, (flag, _) in refs.items() if flag == "tomtat")
    doc = sorted(newnum[n] for n, (flag, _) in refs.items() if flag == "doc")
    intro = (f"Với các tài liệu {compress(tomtat)}, nhóm mới đọc phần tóm tắt hoặc tra thông tin xuất bản, "
             f"chưa đọc toàn văn; báo cáo chỉ dùng các tài liệu này ở mức nội dung của phần tóm tắt. "
             f"Với {compress(doc)}, nhóm đã đọc các mục về công thức và cấu hình huấn luyện được dẫn ở chương 5. "
             f"Các tài liệu còn lại là nguồn dữ liệu và trang web, ghi kèm ngày truy cập.")
    ref_lines = "\n\n".join(f"[{newnum[n]}] {refs[n][1]}" for n in order)
    tltk = f"# Tài liệu tham khảo\n\n{intro}\n\n::: {{custom-style=\"TLTK\"}}\n{ref_lines}\n:::\n"
    out = body.rstrip("\n") + "\n\n" + tltk + "\n" + app
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("thứ tự trích dẫn (số tạm -> số mới):", ", ".join(f"{o}->{newnum[o]}" for o in order))
    print(f"ghi {args.out}: {len(out)} ký tự")


if __name__ == "__main__":
    main()
