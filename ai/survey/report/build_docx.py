"""Xuất báo cáo Markdown sang Word (.docx) bằng pandoc (gói pypandoc_binary trong ai/.venv).

Các bước:
1. Tạo file mẫu kiểu chữ (reference.docx) từ mẫu mặc định của pandoc rồi chỉnh bằng python-docx:
   Times New Roman 13, giãn dòng 1,5, căn đều, lề A4 trái 3 cm / phải 2 cm / trên 2 cm / dưới 2 cm,
   số trang ở chân trang, tiêu đề màu đen, Chương mới sang trang, các kiểu riêng cho bìa và tài liệu tham khảo.
2. pandoc: Markdown -> docx (công thức $$...$$ thành công thức Word, bảng thành bảng Word).
3. Chỉnh bảng bằng python-docx: kẻ khung, chữ 12, giãn dòng đơn, hàng đầu in đậm.
Mục lục là trường TOC đặt sẵn trong Markdown; cập nhật bằng Word (word_finalize.ps1).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/build_docx.py --md E:/DATN/baocao/ban_thu.md --out E:/DATN/baocao/ban_thu.docx
"""
import argparse
import os
import sys
import tempfile

import pypandoc
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: F401
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

FONT = "Times New Roman"


def set_font(style, size=None, bold=None, italic=None, color_black=True):
    f = style.font
    f.name = FONT
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(a)) is not None:
            del rfonts.attrib[qn(a)]
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color_black:
        f.color.rgb = RGBColor(0, 0, 0)


def get_style(doc, name, kind=WD_STYLE_TYPE.PARAGRAPH):
    try:
        return doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, kind)
        st.base_style = doc.styles["Normal"]
        return st


def para(style, align=None, spacing=1.5, before=0, after=6, indent=None, keep_next=None):
    pf = style.paragraph_format
    if align is not None:
        pf.alignment = align
    pf.line_spacing = spacing
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if indent is not None:
        pf.first_line_indent = indent
    if keep_next is not None:
        pf.keep_with_next = keep_next


def add_page_number(section):
    p = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in (("begin", None), (None, " PAGE "), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), tag)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)
    run.font.name = FONT
    run.font.size = Pt(12)


def make_reference(path):
    # lấy mẫu mặc định của pandoc (đủ các kiểu pandoc dùng), rồi chỉnh
    tmp_default = path + ".default.docx"
    pypandoc.convert_text("x", "docx", format="markdown", outputfile=tmp_default)
    doc = Document(tmp_default)
    os.remove(tmp_default)
    # xóa nội dung mẫu, giữ sectPr
    body = doc.element.body
    for el in list(body):
        if el.tag != qn("w:sectPr"):
            body.remove(el)

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    sec.footer_distance = Cm(1)
    sec.different_first_page_header_footer = True  # bìa không đánh số trang
    add_page_number(sec)

    st = doc.styles
    set_font(st["Normal"], 13)
    para(st["Normal"], spacing=1.5, after=6)
    for name in ("Body Text", "First Paragraph"):
        s = get_style(doc, name)
        set_font(s, 13)
        para(s, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.5, before=0, after=6, indent=Cm(1))
    s = get_style(doc, "Compact")
    set_font(s, 12)
    para(s, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, before=1, after=1, indent=Cm(0))
    for lvl, size in ((1, 14), (2, 13), (3, 13)):
        s = st[f"Heading {lvl}"]
        set_font(s, size, bold=True, italic=(lvl == 3))
        para(s, spacing=1.5, before=(0 if lvl == 1 else 10), after=6, keep_next=True)
        if lvl == 1:
            s.paragraph_format.page_break_before = True
            s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for name in ("Table Caption", "Image Caption", "Caption"):
        s = get_style(doc, name)
        set_font(s, 12, bold=False, italic=True)
        para(s, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.15, before=6, after=6, indent=Cm(0))
    st["Table Caption"].paragraph_format.keep_with_next = True
    s = get_style(doc, "Captioned Figure")
    para(s, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0, indent=Cm(0), keep_next=True)
    s = get_style(doc, "Figure")
    para(s, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0, indent=Cm(0), keep_next=True)
    s = get_style(doc, "TOC Heading")
    set_font(s, 14, bold=True)
    para(s, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.5, before=0, after=12)
    for name, size, bold, align in (("Bia", 14, True, WD_ALIGN_PARAGRAPH.CENTER),
                                    ("Bia Tieu de", 16, True, WD_ALIGN_PARAGRAPH.CENTER),
                                    ("Bia Trai", 13, False, WD_ALIGN_PARAGRAPH.LEFT)):
        s = get_style(doc, name)
        set_font(s, size, bold=bold)
        para(s, align=align, spacing=1.3, before=0, after=4, indent=Cm(0))
    st["Bia Trai"].paragraph_format.left_indent = Cm(3)
    s = get_style(doc, "TLTK")
    set_font(s, 12)
    para(s, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.2, after=4, indent=Cm(-0.8))
    s.paragraph_format.left_indent = Cm(0.8)
    # kiểu ký tự cho mã (dùng ở phụ lục)
    s = get_style(doc, "Verbatim Char", WD_STYLE_TYPE.CHARACTER)
    s.font.name = "Consolas"
    s.font.size = Pt(9)
    doc.save(path)


def set_cell_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        borders.append(e)
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(borders)
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        tblPr.append(w)
    w.set(qn("w:type"), "pct")
    w.set(qn("w:w"), "5000")


def set_row_props(trPr, header):
    """Thêm cantSplit (không tách hàng qua trang) và tblHeader (lặp hàng đầu) đúng thứ tự lược đồ."""
    pre_tags = {qn(f"w:{t}") for t in ("cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter")}
    children = [c for c in trPr if c.tag not in (qn("w:cantSplit"), qn("w:tblHeader"))]
    pre = [c for c in children if c.tag in pre_tags]
    height = [c for c in children if c.tag == qn("w:trHeight")]
    rest = [c for c in children if c not in pre and c not in height]
    for c in list(trPr):
        trPr.remove(c)
    new = pre + [OxmlElement("w:cantSplit")] + height
    if header:
        new.append(OxmlElement("w:tblHeader"))
    for c in new + rest:
        trPr.append(c)


def fix_tables(path):
    doc = Document(path)
    for table in doc.tables:
        set_cell_borders(table)
        n_rows = len(table.rows)
        keep_together = n_rows <= 16  # bảng ngắn: không tách sang trang sau
        for ri, row in enumerate(table.rows):
            set_row_props(row._tr.get_or_add_trPr(), header=(ri == 0))
            for cell in row.cells:
                for p in cell.paragraphs:
                    pf = p.paragraph_format
                    pf.line_spacing = 1.0
                    pf.first_line_indent = Cm(0)
                    pf.space_after = Pt(1)
                    pf.space_before = Pt(1)
                    if keep_together and ri < n_rows - 1:
                        pf.keep_with_next = True
                    for r in p.runs:
                        if r.style is not None and r.style.name == "Verbatim Char":
                            r.font.size = Pt(8.5)
                        else:
                            r.font.size = Pt(11 if len(table.columns) >= 4 else 12)
                        if ri == 0:
                            r.font.bold = True
        # giãn đoạn văn ngay sau bảng
        nxt = table._tbl.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            Paragraph(nxt, table._parent).paragraph_format.space_before = Pt(8)
    doc.save(path)
    return len(doc.tables)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    md_dir = os.path.dirname(os.path.abspath(args.md))
    with tempfile.TemporaryDirectory() as td:
        ref = os.path.join(td, "reference.docx")
        make_reference(ref)
        pypandoc.convert_file(
            args.md, "docx", format="markdown", outputfile=args.out,
            extra_args=[f"--reference-doc={ref}", f"--resource-path={md_dir}"],
        )
    n = fix_tables(args.out)
    print(f"pandoc {pypandoc.get_pandoc_version()}: {args.md} -> {args.out}; {n} bảng")


if __name__ == "__main__":
    main()
