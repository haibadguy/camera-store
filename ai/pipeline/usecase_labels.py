"""
Gắn nhãn mục đích sử dụng cho ống kính (nội dung 4, quan hệ suitable_for: ống -> usecase).

Luật đọc từ ai/config/usecase_rules.toml (QUY TẮC NHÓM TỰ ĐẶT, xem đầu file TOML); tiêu cự / khẩu độ đọc bằng
ai/pipeline/lens_specs.read_title. Logic chép nguyên từ ai/survey/content4/count_usecase.py (hàm crops, labels_at,
label), bỏ phần đối chiếu (vlog tham khảo, bỏ mốc 135), để script 04 gọi được mà không đọc CSV của script khảo sát.
Việc kiểm nguồn và câu trích vẫn do count_usecase.py làm.

Ví dụ: "Canon EF 70-200mm f/2.8L IS III USM", khung ff, ngàm canon_ef
  -> crop 1,0 -> lo_eq 70, hi_eq 200, khẩu độ đầu tele 2.8
  -> chân dung (phủ [85, 135] và f/2.8 <= 2.8); không phong cảnh (70 > 35); không thể thao/chim (200 < 300)
"""
import re
import tomllib
from pathlib import Path

import lens_specs as ls

RULES_TOML = Path(__file__).resolve().parent.parent / "config" / "usecase_rules.toml"


class UsecaseRules:
    def __init__(self, path=RULES_TOML):
        self.cfg = tomllib.load(open(path, "rb"))
        self.version = self.cfg["meta"]["version"]
        self.rules = self.cfg["rules"]
        # nhãn sinh cạnh: mọi luật không có trang_thai = "da_bo" (vlog đã bỏ, QĐ 4-11), theo thứ tự trong file
        self.labels = [k for k, r in self.rules.items() if r.get("trang_thai") != "da_bo"]
        self.macro_re = re.compile(self.rules["macro"]["tu_khoa"], re.I)

    def crops(self, mount, khung):
        """Hệ số crop theo khổ ống (QĐ 4-4: khổ ống được thiết kế cho). Khổ không rõ -> nhiều hệ số."""
        c = self.cfg["crop"]
        if mount in c["theo_ngam"]:
            return [c["theo_ngam"][mount]]
        if khung == "ff":
            return [c["ff"]]
        if khung == "apsc":
            return [c["apsc_canon"] if mount.startswith("canon") else c["apsc_khac"]]
        if khung == "khac" and mount == "canon_ef":
            return [c["aps_h"]]
        return list(c["khong_ro"])

    def _labels_at(self, f1, f2, ap1, ap2, crop, is_macro_word):
        lo, hi = f1 * crop, (f2 or f1) * crop
        ap_tele = ap2 or ap1
        r = self.rules
        out = set()
        if lo <= r["phong_canh"]["lo_eq_max"]:
            out.add("phong_canh")
        if hi >= r["the_thao_chim"]["hi_eq_min"]:
            out.add("the_thao_chim")
        a, b = r["chan_dung"]["eq_overlap"]
        if lo <= b and hi >= a and ap_tele <= r["chan_dung"]["ap_tele_max"]:
            out.add("chan_dung")
        if is_macro_word and (f2 is None or not r["macro"]["chi_ong_mot_tieu_cu"]):
            out.add("macro")
        return frozenset(out)

    def label_lens(self, title, mount, khung):
        """Nhãn của một ống (tập con của self.labels). Ống không đọc được tiêu cự + khẩu độ -> rỗng.
        Nhiều hệ số crop (khổ không rõ) -> chỉ giữ nhãn mà mọi hệ số cùng cho ra (giao)."""
        s = ls.read_title(title)
        if not s:
            return frozenset()
        f1, f2, ap1, ap2 = s
        mw = bool(self.macro_re.search(ls.head_main(title)))
        res = [self._labels_at(f1, f2, ap1, ap2, c, mw) for c in self.crops(mount, khung)]
        return frozenset.intersection(*res) & frozenset(self.labels)
