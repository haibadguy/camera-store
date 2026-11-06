"""
build_kaggle_package.py — đóng gói code + dữ liệu đã xử lý thành 2 Kaggle dataset RIÊNG TƯ và 1 notebook mẫu, để
chạy huấn luyện v3 trên Kaggle (cố định seed, ghi log, lưu phiên bản).
Viết 06/11/2026. Script này CHỈ tạo thư mục trên máy; KHÔNG tải gì lên Kaggle (lệnh tải lên in ra ở PACKAGE.md, chạy
tay khi nhóm quyết định tải lên).

Đầu ra: <out>/<tag>/
  camera-store-v3-code/   camera-store.bundle (git bundle đến commit HEAD: notebook clone + checkout đúng commit),
                          COMMIT.txt, recbole_gnn.bundle + RECBOLE_GNN_COMMIT.txt (mã RecBole-GNN cho SimGCL, không
                          phải gói pip), dataset-metadata.json
  camera-store-v3-data/   ai/data/processed/..., ai/data/kg/..., ai/data/recbole/camera_loo/... (file RecBole do
                          to_recbole.py / to_recbole_kg.py sinh ở máy nhóm; đúng đường dẫn trong repo), manifest_sha256.json,
                          dataset-metadata.json
  kernel/                 v3_runner.ipynb (sinh từ kaggle/v3_runner.py, đã điền commit), kernel-metadata.json
  PACKAGE.md              kích thước, sha256, lệnh kaggle CLI để tải lên (chưa chạy)

Riêng tư: `kaggle datasets create` mặc định tạo dataset riêng tư (chỉ công khai khi thêm --public);
kernel-metadata.json đặt "is_private": true.
user_map.json: mặc định thay mã người dùng Amazon bằng "u0", "u1", ... (giữ nguyên số thứ tự). Code huấn luyện chỉ
dùng len(user_map) (common_05.N_USERS), nên kết quả không đổi; không đưa mã người đánh giá của Amazon lên dịch vụ
ngoài. Tắt bằng --keep-user-ids (chỉ khi nhóm quyết định).

Chạy (từ thư mục camera-store, cây git phải sạch):
  ai\\.venv\\Scripts\\python.exe kaggle/build_kaggle_package.py --out E:\\DATN\\kaggle_pkg --tag thu_20261107
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = [
    "ai/data/processed/train.txt", "ai/data/processed/val.txt", "ai/data/processed/test.txt",
    "ai/data/processed/item_map.json", "ai/data/processed/user_map.json",
    "ai/data/processed/val_negatives.json", "ai/data/processed/test_negatives.json",
    "ai/data/kg/kg_hetero.pt", "ai/data/kg/kg_stats.json", "ai/data/kg/kg_node_index.json",
    "ai/data/kg/item_attributes.csv", "ai/data/kg/body_index.json", "ai/data/kg/lens_index.json",
    "ai/data/kg/unknown_mask.npz", "ai/data/kg/compatibility_matrix.npz",
    "ai/data/kg/kg_edges_compatible_with.csv", "ai/data/kg/kg_edges_crops_sensor.csv",
    "ai/data/kg/kg_edges_requires_adapter.csv", "ai/data/kg/kg_edges_has_spec_mount.csv",
    "ai/data/kg/kg_edges_has_spec_sensor_format.csv", "ai/data/kg/kg_edges_has_spec_focal_range.csv",
    "ai/data/kg/kg_edges_has_spec_aperture_class.csv", "ai/data/kg/kg_edges_suitable_for.csv",
    # RecBole (v3, 06/11): chép nguyên file đã sinh ở máy nhóm, không sinh lại trên Kaggle -> đầu vào RecBole trùng
    # sha256 với lần đối chiếu ở máy nhóm (docs/reviews/v3_eval_plan.md mục 7). Mã người dùng ở đây là số thứ tự.
    "ai/data/recbole/camera_loo/camera_loo.train.inter", "ai/data/recbole/camera_loo/camera_loo.valid.inter",
    "ai/data/recbole/camera_loo/camera_loo.test.inter", "ai/data/recbole/camera_loo/camera_loo.kg",
    "ai/data/recbole/camera_loo/camera_loo.link",
    "ai/data/recbole/camera_loo/manifest.json", "ai/data/recbole/camera_loo/manifest_kg.json",
]
GNN_SRC = r"E:\DATN\venvs\src\recbole_gnn_src"
GNN_COMMIT = "632ef888589944c190ad8f449b49ca559618d4df"   # bản đã dùng ở máy nhóm (ai/recbole/README.md)
OWNER = "KAGGLE_USERNAME"     # điền tên tài khoản Kaggle khi tải lên (không ghi vào repo)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def py_to_ipynb(src, commit):
    """Đổi file định dạng '# %%' sang .ipynb (nbformat 4), điền commit."""
    text = Path(src).read_text(encoding="utf-8").replace("__COMMIT__", commit)
    cells, cur, kind = [], [], None
    for line in text.splitlines():
        if line.startswith("# %%"):
            if kind is not None:
                cells.append((kind, cur))
            kind, cur = ("markdown" if "[markdown]" in line else "code"), []
            continue
        cur.append(line[2:] if kind == "markdown" and line.startswith("# ") else
                   ("" if kind == "markdown" and line == "#" else line))
    if kind is not None:
        cells.append((kind, cur))
    nb_cells = []
    for kind, lines in cells:
        while lines and not lines[-1].strip():
            lines.pop()
        src_lines = [ln + "\n" for ln in lines[:-1]] + lines[-1:]
        c = {"cell_type": kind, "metadata": {}, "source": src_lines}
        if kind == "code":
            c.update(execution_count=None, outputs=[])
        nb_cells.append(c)
    return {"cells": nb_cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                           "name": "python3"},
                                            "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--keep-user-ids", action="store_true")
    ap.add_argument("--gnn-src", default=GNN_SRC, help="bản clone RecBole-GNN (phải ở commit GNN_COMMIT, không sửa)")
    ap.add_argument("--allow-dirty", action="store_true", help="chỉ để thử script; gói như vậy không dùng để chạy thật")
    a = ap.parse_args()
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    assert a.allow_dirty or not dirty, "cây git có file đã theo dõi bị sửa mà chưa commit -> commit trước"
    commit = git("rev-parse", "HEAD")
    out = Path(a.out) / a.tag
    assert not out.exists(), f"đã có {out}, không ghi đè (đổi --tag)"
    code_d, data_d, kern_d = out / "camera-store-v3-code", out / "camera-store-v3-data", out / "kernel"
    for d in (code_d, data_d, kern_d):
        d.mkdir(parents=True)

    # 1. code: git bundle đến HEAD (cả lịch sử của nhánh, để `git checkout <commit>` được)
    git("bundle", "create", str(code_d / "camera-store.bundle"), "HEAD")
    (code_d / "COMMIT.txt").write_text(commit + "\n", encoding="utf-8")
    gnn_head = subprocess.run(["git", "-C", a.gnn_src, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    assert gnn_head == GNN_COMMIT, f"RecBole-GNN ở {gnn_head}, cần {GNN_COMMIT}"
    assert not subprocess.run(["git", "-C", a.gnn_src, "status", "--porcelain"], capture_output=True, text=True,
                              check=True).stdout.strip(), "bản clone RecBole-GNN có file bị sửa"
    subprocess.run(["git", "-C", a.gnn_src, "bundle", "create", str(code_d / "recbole_gnn.bundle"), "HEAD"],
                   capture_output=True, check=True)
    (code_d / "RECBOLE_GNN_COMMIT.txt").write_text(GNN_COMMIT + "\n", encoding="utf-8")
    (code_d / "dataset-metadata.json").write_text(json.dumps(
        {"title": "camera-store-v3-code", "id": f"{OWNER}/camera-store-v3-code",
         "licenses": [{"name": "other"}]}, indent=2), encoding="utf-8")

    # 2. dữ liệu
    files = {}
    for rel in DATA_FILES:
        src, dst = ROOT / rel, data_d / rel
        assert src.exists(), f"thiếu {src}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("user_map.json") and not a.keep_user_ids:
            um = json.loads(src.read_text(encoding="utf-8"))
            vals = sorted(um.values())
            assert vals == list(range(len(um))), "user_map không phải 0..N-1"
            dst.write_text(json.dumps({f"u{v}": v for v in vals}), encoding="utf-8")
        else:
            shutil.copyfile(src, dst)
        files[rel] = sha256(dst)
    man = {"commit": commit, "dirty": dirty, "user_ids_anonymized": not a.keep_user_ids, "files": files,
           "source_sha256": {rel: sha256(ROOT / rel) for rel in DATA_FILES}}
    (data_d / "manifest_sha256.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    (data_d / "dataset-metadata.json").write_text(json.dumps(
        {"title": "camera-store-v3-data", "id": f"{OWNER}/camera-store-v3-data",
         "licenses": [{"name": "other"}]}, indent=2), encoding="utf-8")

    # 3. notebook
    nb = py_to_ipynb(ROOT / "kaggle" / "v3_runner.py", commit)
    assert "__COMMIT__" not in json.dumps(nb, ensure_ascii=False)
    (kern_d / "v3_runner.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    (kern_d / "kernel-metadata.json").write_text(json.dumps(
        {"id": f"{OWNER}/camera-store-v3-runner", "title": "camera-store-v3-runner", "code_file": "v3_runner.ipynb",
         "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True,
         "enable_tpu": False, "enable_internet": True,
         "dataset_sources": [f"{OWNER}/camera-store-v3-code", f"{OWNER}/camera-store-v3-data"],
         "competition_sources": [], "kernel_sources": []}, indent=2), encoding="utf-8")

    # 3b. bản .zip của 2 dataset (để tải lên bằng trình duyệt: 1 file / dataset; trong zip giữ nguyên cây thư mục)
    zips = {}
    for d in (code_d, data_d):
        zp = shutil.make_archive(str(out / d.name), "zip", root_dir=d)
        zips[Path(zp).name] = sha256(zp)

    # 4. PACKAGE.md
    def size(d):
        return sum(p.stat().st_size for p in d.rglob("*") if p.is_file()) / 2 ** 20
    md = [f"# Gói Kaggle {a.tag}", "", f"- commit `{commit}` (dirty: {dirty})",
          f"- code: {size(code_d):.1f} MiB; dữ liệu: {size(data_d):.1f} MiB ({len(files)} file); "
          f"user_map ẩn mã: {not a.keep_user_ids}",
          f"- sha256 bundle `{sha256(code_d / 'camera-store.bundle')}`; RecBole-GNN `{GNN_COMMIT}` "
          f"(bundle `{sha256(code_d / 'recbole_gnn.bundle')}`)",
          f"- sha256 manifest dữ liệu `{sha256(data_d / 'manifest_sha256.json')}`",
          *[f"- `{k}` ({(out / k).stat().st_size / 2 ** 20:.1f} MiB) sha256 `{v}`" for k, v in zips.items()], "",
          "Tải lên bằng trình duyệt: làm theo `kaggle/HUONG_DAN_KAGGLE.md` (dùng 2 file .zip và `kernel/v3_runner.ipynb`).",
          "",
          "## Lệnh tải lên bằng kaggle CLI (chưa chạy)", "",
          f"Trước khi chạy: thay `{OWNER}` trong 3 file `*-metadata.json` bằng tên tài khoản Kaggle.", "",
          "```", f"kaggle datasets create -p \"{code_d}\" --dir-mode zip",
          f"kaggle datasets create -p \"{data_d}\" --dir-mode zip",
          f"kaggle kernels push -p \"{kern_d}\"", "```", "",
          "Không thêm `--public`: dataset tạo ra là riêng tư. Phiên bản mới của dữ liệu / code: "
          "`kaggle datasets version -p <thư mục> -m \"<commit>\" --dir-mode zip`."]
    (out / "PACKAGE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
