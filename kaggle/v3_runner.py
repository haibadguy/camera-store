# %% [markdown]
# # camera-store v3 — chạy huấn luyện trên Kaggle
#
# Notebook này được sinh từ `kaggle/v3_runner.py` (định dạng `# %%`) bởi `kaggle/build_kaggle_package.py`.
# Kế hoạch: `docs/reviews/v3_eval_plan.md`; cách làm trên web: `kaggle/HUONG_DAN_KAGGLE.md`. Mỗi lần
# "Save Version → Save & Run All" là một **phiên bản** của notebook: code (commit git), dữ liệu (sha256), danh sách việc
# `JOBS`, log và kết quả đều nằm trong phiên bản đó.
#
# Quy tắc:
# 1. Code lấy từ dataset `camera-store-v3-code` (git bundle) và **checkout đúng commit** `EXPECT_COMMIT`; lệch thì dừng.
#    RecBole-GNN (SimGCL) cũng lấy từ bundle trong dataset đó, kiểm đúng commit.
# 2. Dữ liệu lấy từ dataset `camera-store-v3-data`; **kiểm sha256 từng file** với `manifest_sha256.json`; lệch thì dừng.
# 3. Seed: mỗi việc truyền `--seed` cho script (script tự đặt seed torch / numpy như khi chạy ở máy nhóm).
# 4. Log: mỗi việc ghi `logs/<việc>_<RUN_LABEL>_<thời điểm>.log` (tên mới, không ghi đè) + log của chính script.
# 5. Không chấm test trên Kaggle (script huấn luyện chỉ chấm val). Chấm test làm ở máy nhóm, theo kế hoạch.
# 6. Hai môi trường, đều là venv **Python 3.12.10** (cùng bản với máy nhóm) do `uv` tạo; Python sẵn có của Kaggle
#    (3.13 tại 11/2026) chỉ dùng để chạy notebook này và cài `uv`, không chạy việc huấn luyện nào:
#    - "nhom" (`/tmp/env_nhom`): torch / PyG / numpy / scipy theo `kaggle/requirements-kaggle.txt`, các gói phụ thuộc
#      ghim theo `ai/requirements-lock.txt` (venv `ai/.venv` ở máy nhóm);
#    - "recbole" (`/tmp/env_recbole`): đúng file `ai/recbole/requirements-recbole-lock.txt` (venv RecBole ở máy nhóm:
#      numpy 1.26.4, scipy 1.11.4, recbole 1.2.1, torch 2.14.1+cu126 ...).
#    Khác máy nhóm (bắt buộc vì Kaggle chạy Linux): torch bản Linux kéo thêm các gói `nvidia-*` và `triton` (bản Windows
#    không có); phiên bản các gói này do torch 2.14.1 quy định, ghi trong `pip_freeze_*.txt` của mỗi phiên bản.

# %%
# ===== CẤU HÌNH CỦA PHIÊN BẢN NÀY (sửa trước khi Save Version) =====
EXPECT_COMMIT = "__COMMIT__"          # build_kaggle_package.py điền
ACCOUNT = "nam"                       # "nam" | "hai" | "quyen": chọn bộ việc của tài khoản này (PRESETS bên dưới);
                                      # "kiem": notebook kiểm môi trường (mọi việc của 3 tài khoản, mỗi việc 1 epoch)
RUN_LABEL = "kiem_moi_truong" if ACCOUNT == "kiem" else "thu_s1_" + ACCOUNT
                                      # nhãn lần chạy; chạy tiếp ở phiên bản sau thì GIỮ NGUYÊN nhãn
RESUME = False                        # True khi chạy tiếp: phải thêm output của phiên bản trước làm input (xem dưới)
REQUIRE_GPU = "T4"                    # mỗi mô hình chạy mọi seed trên cùng loại GPU (kế hoạch mục 5) -> sai GPU thì dừng
JOB_DEADLINE_H = 8.5                  # sau mốc này (tính từ đầu phiên) ngắt việc đang chạy, lưu kết quả để chạy tiếp.
                                      # Giới hạn giờ / phiên của Kaggle CHƯA KIỂM CHỨNG -> để thận trọng 8,5 giờ.
UV_VERSION = "0.13.5"                 # công cụ tạo venv (cài từ PyPI; cần bật Internet)
PY_VERSION = "3.12.10"                # Python của cả hai venv = Python của ai/.venv và venv RecBole ở máy nhóm

# Đợt "thu" (nhóm chốt 06/11): mỗi baseline seed 1, một cấu hình; chỉ val. Việc: (tên, môi trường, script, tham số).
# "{GNN}" được thay bằng thư mục RecBole-GNN đã clone. Trần 1.000 epoch, chấm val mỗi 10 epoch, dừng sau 5 lần không tăng.
PRESETS = {
    "nam": [   # KGIN: mặc định RecBole (d 64, 4 ý định, node dropout 0,5), context_hops = 2 (giữa lưới {1, 2, 3})
        ("kgin_hops2_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "KGIN", "--seed", "1", "--epochs", "1000", "--group-eval", "--set", "context_hops=2"]),
    ],
    "hai": [   # SimGCL: mặc định RecBole-GNN, λ = 0,01 (giữa lưới đã đăng ký {0,005; 0,01; 0,05})
        ("simgcl_lam0.01_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "SimGCL", "--seed", "1", "--epochs", "1000", "--group-eval", "--gnn", "{GNN}",
          "--set", "lambda=0.01"]),
    ],
    "quyen": [  # BPR-MF code nhóm (số chính), UltraGCN (cấu hình Electronics của tác giả), BPR RecBole (đối chiếu)
        ("bprmf_l2-1e-04_s1", "nhom", "ai/pipeline/05d_bprmf_train.py", ["--l2", "1e-4", "--seed", "1"]),
        ("ultragcn_electronics_s1", "nhom", "ai/pipeline/05e_ultragcn_train.py", ["--seed", "1"]),
        ("recbole_bpr_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "BPR", "--seed", "1", "--epochs", "1000", "--group-eval"]),
    ],
}

def one_epoch(job):
    """Bản kiểm của một việc: cùng script, cùng tham số, chỉ 1 epoch (RecBole: --epochs 1, vẫn chấm val sau epoch 1
    vì RecBole lấy eval_step = min(eval_step, epochs); code nhóm: --max-epoch 1, train_05 chấm khi epoch = max_epoch)."""
    name, which, script, args = job
    args = list(args)
    if "--epochs" in args:
        args[args.index("--epochs") + 1] = "1"
    else:
        args += ["--max-epoch", "1"]
    return ("kiem_" + name, which, script, args)

PRESETS["kiem"] = [one_epoch(j) for acc in ("nam", "hai", "quyen") for j in PRESETS[acc]]
JOBS = PRESETS[ACCOUNT]

# %%
import hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

T_START = time.time()
INP = Path("/kaggle/input")
WORK = Path("/kaggle/working")
REPO = WORK / "camera-store"
GNN_DIR = Path("/tmp/recbole_gnn_src")
LOGS = WORK / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print("$", cmd if isinstance(cmd, str) else " ".join(map(str, cmd)), flush=True)
    r = subprocess.run(cmd, shell=isinstance(cmd, str), text=True, capture_output=True, **kw)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")
        raise RuntimeError(f"lệnh lỗi (mã {r.returncode})")
    return r.stdout

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

UNZ = Path("/tmp/unz")

def find_input(name):
    c = [p for p in INP.rglob(name)] + ([p for p in UNZ.rglob(name)] if UNZ.exists() else [])
    assert len(c) == 1, f"không tìm thấy đúng một {name} trong {INP}: {c}"
    return c[0]

# Tải lên dạng .zip: thường Kaggle tự giải nén (CHƯA KIỂM CHỨNG); nếu input vẫn là file .zip thì giải nén ra /tmp/unz.
import zipfile
for z in sorted(INP.rglob("camera-store-v3-*.zip")):
    key = "camera-store.bundle" if "code" in z.name else "manifest_sha256.json"
    if not list(INP.rglob(key)):
        print("giải nén", z)
        zipfile.ZipFile(z).extractall(UNZ / z.stem)

def hours():
    return (time.time() - T_START) / 3600

# %%
# ===== Môi trường =====
env = {"python_kaggle": platform.python_version(), "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
       "account_preset": ACCOUNT, "run_label": RUN_LABEL}
try:
    env["nvidia_smi"] = sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")
except Exception as e:  # không có GPU
    env["nvidia_smi"] = f"không có GPU: {e}"
print(json.dumps(env, indent=2, ensure_ascii=False))
assert REQUIRE_GPU in env["nvidia_smi"], f"cần GPU {REQUIRE_GPU} (Settings → Accelerator), đang có: {env['nvidia_smi']}"

# %%
# ===== Code: clone git bundle, checkout đúng commit; RecBole-GNN =====
bundle = find_input("camera-store.bundle")
if REPO.exists():
    shutil.rmtree(REPO)
sh(["git", "clone", "--quiet", str(bundle), str(REPO)])
sh(["git", "-C", str(REPO), "checkout", "--quiet", EXPECT_COMMIT])
head = sh(["git", "-C", str(REPO), "rev-parse", "HEAD"]).strip()
assert head == EXPECT_COMMIT, f"commit {head} khác {EXPECT_COMMIT}"
env["commit"] = head
gnn_expect = find_input("RECBOLE_GNN_COMMIT.txt").read_text().strip()
if GNN_DIR.exists():
    shutil.rmtree(GNN_DIR)
sh(["git", "clone", "--quiet", str(find_input("recbole_gnn.bundle")), str(GNN_DIR)])
sh(["git", "-C", str(GNN_DIR), "checkout", "--quiet", gnn_expect])
env["recbole_gnn_commit"] = sh(["git", "-C", str(GNN_DIR), "rev-parse", "HEAD"]).strip()
assert env["recbole_gnn_commit"] == gnn_expect
print("commit", head, "| RecBole-GNN", gnn_expect)

# %%
# ===== Thư viện: tạo venv Python 3.12.10 bằng uv (chỉ tạo môi trường mà JOBS cần) =====
# Không dùng `python -m venv` của Kaggle: ảnh Kaggle (Debian/Ubuntu) không có ensurepip, và Python 3.13 của Kaggle
# không có bản numpy 1.26.4 / scipy 1.11.4 mà môi trường RecBole cần. uv tự tải Python 3.12.10 (bản dựng
# python-build-standalone) nên không phụ thuộc Python của ảnh Kaggle.
t_env = time.time()
os.environ["UV_CACHE_DIR"] = "/tmp/uv_cache"              # tải torch một lần, hai venv dùng chung
os.environ["UV_PYTHON_INSTALL_DIR"] = "/tmp/uv_python"
sh([sys.executable, "-m", "pip", "install", "-q", f"uv=={UV_VERSION}"])
UV = [sys.executable, "-m", "uv"]
env["uv"] = sh(UV + ["--version"]).strip()
sh(UV + ["python", "install", PY_VERSION])

TORCH_INDEX = "https://download.pytorch.org/whl/cu126"   # như dòng --extra-index-url trong các file lock

def pins_text(text):
    """{tên chuẩn hóa: phiên bản} từ các dòng `tên==phiên_bản` (file requirements / lock / pip freeze)."""
    out = {}
    for ln in text.splitlines():
        ln = ln.split("#")[0].strip()
        if "==" in ln and not ln.startswith("-"):
            k, v = ln.split("==", 1)
            out[k.strip().lower().replace("_", "-").replace(".", "-")] = v.strip()
    return out

def pins(path):
    return pins_text(Path(path).read_text(encoding="utf-8"))

def clean_req(path, name):
    """Bản sao chỉ gồm các dòng `tên==phiên_bản` (bỏ chú thích, dòng tùy chọn như --extra-index-url: chỉ số gói
    truyền qua dòng lệnh) -> uv đọc file requirements / ràng buộc như nhau ở mọi phiên bản."""
    out = Path(f"/tmp/req_{name}_{Path(path).name}")
    out.write_text("".join(f"{k}=={v}\n" for k, v in pins(path).items()), encoding="utf-8")
    return str(out)

def make_env(name, steps, must_match, lock):
    """Tạo venv /tmp/env_<name> (Python PY_VERSION), cài theo `steps`, rồi kiểm:
    mọi gói trong `must_match` có đúng phiên bản; mọi gói đã cài mà có trong `lock` cũng đúng phiên bản của `lock`."""
    path = Path(f"/tmp/env_{name}")
    if path.exists():
        shutil.rmtree(path)
    sh(UV + ["venv", "--quiet", "--python", PY_VERSION, "--python-preference", "only-managed", str(path)])
    py = str(path / "bin" / "python")
    for args in steps:
        args = [clean_req(x, name) if str(x).endswith(".txt") else x for x in args]
        sh(UV + ["pip", "install", "--quiet", "--python", py, "--extra-index-url", TORCH_INDEX,
                  "--index-strategy", "unsafe-best-match", *args])
    freeze = sh(UV + ["pip", "freeze", "--python", py])
    (LOGS / f"pip_freeze_{name}_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.txt").write_text(freeze, encoding="utf-8")
    got, want, lk = pins_text(freeze), pins(must_match), pins(lock)
    bad = {k: (v, got.get(k)) for k, v in want.items() if got.get(k) != v}
    bad.update({k: (lk[k], v) for k, v in got.items() if k in lk and lk[k] != v})
    assert not bad, f"venv {name}: phiên bản lệch (cần, có): {bad}"
    chk = json.loads(sh([py, "-c", "import json, platform, torch; print(json.dumps({'python': platform.python_version(), "
                         "'torch': torch.__version__, 'cuda': torch.cuda.is_available(), "
                         "'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"]
                        ).strip().splitlines()[-1])
    assert chk["python"] == PY_VERSION, chk
    assert chk["cuda"], f"venv {name}: torch không thấy GPU: {chk}"
    chk["not_in_lock"] = sorted(f"{k}=={v}" for k, v in got.items() if k not in lk)   # gói chỉ có ở Linux
    env[f"env_{name}"] = chk
    print(name, json.dumps(chk, ensure_ascii=False), flush=True)
    return py

NEED = {e for _, e, _, _ in JOBS}
PY = {}
if "nhom" in NEED:
    lock = REPO / "ai" / "requirements-lock.txt"
    req = REPO / "kaggle" / "requirements-kaggle.txt"
    PY["nhom"] = make_env("nhom", [["-r", str(req), "-c", str(lock)]], req, lock)
if "recbole" in NEED:
    lock = REPO / "ai" / "recbole" / "requirements-recbole-lock.txt"
    # (1) torch kèm gói phụ thuộc (bản Linux cần nvidia-* / triton), các gói chung ghim theo lock;
    # (2) cả file lock, --no-deps như ở máy nhóm (recbole 1.2.1 đòi ray<=2.6.3, không có bản cho Python 3.12).
    PY["recbole"] = make_env("recbole", [[f"torch=={pins(lock)['torch']}", "-c", str(lock)],
                                         ["--no-deps", "-r", str(lock)]], lock, lock)
env["env_setup_minutes"] = round((time.time() - t_env) / 60, 1)
print(json.dumps(env, indent=2, ensure_ascii=False))

# %%
# ===== Dữ liệu: chép vào repo (KHÔNG symlink: eval_05.inputs_sha256 cần đường dẫn nằm trong repo), kiểm sha256 =====
man_p = find_input("manifest_sha256.json")
DATA_ROOT = man_p.parent
man = json.loads(man_p.read_text(encoding="utf-8"))
bad = []
for rel, h in man["files"].items():
    src, dst = DATA_ROOT / rel, REPO / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if sha256(dst) != h:
        bad.append(rel)
assert not bad, f"sha256 lệch: {bad}"
env["data_manifest_sha256"] = sha256(man_p)
env["data_packaged_from_commit"] = man["commit"]
env["data_files_checked"] = len(man["files"])
print(f"Đã kiểm {len(man['files'])} file dữ liệu: sha256 khớp")

# %%
# ===== (Tùy chọn) chạy tiếp từ phiên bản trước =====
# Mỗi việc lưu trạng thái chạy tiếp ở mỗi lần chấm val (train_05: last.pt; RecBole --group-eval: last_state.pth).
# Muốn chạy tiếp: "Add Input" → Your Work / Notebooks → output của phiên bản trước của CHÍNH notebook này, đặt RESUME = True,
# GIỮ NGUYÊN ACCOUNT, RUN_LABEL và JOBS (cấu hình phải trùng: script tự kiểm). Việc đã có result.json được bỏ qua.
RES = REPO / "results" / "kaggle" / RUN_LABEL
if RESUME:
    c = [p for p in INP.rglob(RUN_LABEL) if p.is_dir() and p.parent.name == "out" and (p / "results").is_dir()]
    assert len(c) == 1, f"cần đúng một thư mục .../out/{RUN_LABEL}/results trong input, thấy: {c}"
    prev = c[0]
    shutil.copytree(prev / "results", RES, dirs_exist_ok=True)
    shutil.copytree(prev / "logs", LOGS / "truoc", dirs_exist_ok=True)   # log các phiên bản trước, giữ nguyên
    prev_sum = json.loads((prev / "summary.json").read_text(encoding="utf-8"))
    env["resumed_from"] = {"path": str(prev), "prev_env": prev_sum.get("env"), "prev_jobs": prev_sum.get("jobs")}
    assert prev_sum["env"]["commit"] == EXPECT_COMMIT, "phiên bản trước chạy commit khác -> không chạy tiếp được"
    print("Chạy tiếp từ", prev)
(LOGS / f"env_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.json").write_text(
    json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")

# %%
# ===== Chạy các việc (ngắt khi tới JOB_DEADLINE_H, trạng thái chạy tiếp đã lưu ở lần chấm val gần nhất) =====
OUT = WORK / "out" / RUN_LABEL

def collect(done):
    if RES.exists():
        shutil.copytree(RES, OUT / "results", dirs_exist_ok=True)
    shutil.copytree(LOGS, OUT / "logs", dirs_exist_ok=True)
    summary = {"env": env, "jobs": done,
               "outputs_sha256": {str(p.relative_to(OUT)): sha256(p) for p in sorted(OUT.rglob("*"))
                                  if p.is_file() and p.name != "summary.json"}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

os.environ["PYTHONHASHSEED"] = "0"
os.environ["PYTHONIOENCODING"] = "utf-8"
done = []
for name, which, script, args in JOBS:
    run_dir = f"results/kaggle/{RUN_LABEL}/{name}"
    if (REPO / run_dir / "result.json").exists():
        done.append({"name": name, "status": "đã xong ở phiên bản trước"})
        print(done[-1], flush=True)
        continue
    left = JOB_DEADLINE_H - hours()
    if left < 0.25:
        done.append({"name": name, "status": f"không chạy: còn {left:.2f} giờ trước mốc {JOB_DEADLINE_H}"})
        print(done[-1], flush=True)
        continue
    py = PY[which]
    argv = [py, *(["-W", "ignore"] if which == "recbole" else []), script,
            *[x.replace("{GNN}", str(GNN_DIR)) for x in args], "--run-dir", run_dir]
    lp = LOGS / f"{name}_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    assert not lp.exists()
    t0 = time.time()
    with open(lp, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(argv) + "\n")
        f.flush()
        try:
            p = subprocess.run(argv, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, text=True, timeout=left * 3600)
            status = "xong" if p.returncode == 0 else f"lỗi (mã {p.returncode})"
        except subprocess.TimeoutExpired:
            status = f"ngắt ở mốc {JOB_DEADLINE_H} giờ -> chạy tiếp ở phiên bản sau (RESUME = True)"
    done.append({"name": name, "env": which, "script": script, "args": args, "status": status,
                 "result_json": (REPO / run_dir / "result.json").exists(),
                 "minutes": round((time.time() - t0) / 60, 1), "log": lp.name})
    print(done[-1], flush=True)
    collect(done)          # gom sau mỗi việc: phiên bị dừng giữa chừng vẫn còn phần đã xong
    if status.startswith("lỗi"):
        print("\n".join(lp.read_text(encoding="utf-8").splitlines()[-30:]))

# %%
# ===== Gom kết quả để lưu cùng phiên bản (checkpoint + result.json + log) =====
collect(done)
print(json.dumps(done, indent=2, ensure_ascii=False))
ok = all(d["status"] in ("xong", "đã xong ở phiên bản trước") for d in done) and len(done) == len(JOBS)
print(f"{sum(d['status'] == 'xong' for d in done)} / {len(JOBS)} việc xong trong phiên bản này; môi trường: "
      f"{ {k: v for k, v in env.items() if k.startswith('env_')} }")
if ACCOUNT == "kiem":
    assert ok and all(d.get("result_json", True) for d in done), "KIỂM MÔI TRƯỜNG: TRƯỢT (xem bảng trên và log)"
    print("KIỂM MÔI TRƯỜNG: ĐẠT — cài đặt, import, 1 epoch + 1 lần chấm val của mọi script đều chạy được")
