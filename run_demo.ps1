# run_demo.ps1 -- Bật demo bằng một lệnh: FastAPI (dịch vụ mô hình, seed 1) -> Spring Boot -> React (Vite, chế độ api).
# Viết 28/10/2026. Cách chuẩn bị máy: README.md, mục "Chạy demo trên máy khác".
#
# Chạy từ thư mục camera-store (PowerShell):
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Build      # đóng gói lại Spring (sau khi đổi code backend)
# Mở http://127.0.0.1:5173, bấm "Tư vấn thiết bị". Nhấn Enter trong cửa sổ này để tắt cả ba.
# Luôn chạy chế độ api (React gọi Spring, Spring gọi mô hình thật). Chế độ dữ liệu mẫu chỉ có khi chạy Vite tay, và
# trang hiện nhãn "Dữ liệu mẫu".
# Log mỗi lần chạy: results/demo/run_demo_logs/<ngày_giờ>/ (thư mục mới, không ghi đè).

param(
    [int]$FastApiPort = 8001,
    [int]$SpringPort = 8080,
    [int]$VitePort = 5173,
    [string]$EmbDir = "results/service/emb_s1_20261021",
    [switch]$Build,
    # Giới hạn heap của Spring (chỉ chuyển tiếp JSON; đo 28/10 chạy được với 512 MB): để máy RAM ít không bị JVM
    # chiếm tới 1/4 RAM theo mặc định
    [string]$SpringHeap = "512m"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root
$Tag = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir = Join-Path $Root "results/demo/run_demo_logs/$Tag"
New-Item -ItemType Directory -Path $LogDir | Out-Null
$Procs = @()

function Fail($msg) { Write-Host "DỪNG: $msg" -ForegroundColor Red; exit 1 }

# Start-Process nối các tham số bằng dấu cách và không tự thêm ngoặc kép: tham số có dấu cách (đường dẫn như
# "D:\Do an\camera-store") phải bọc ngoặc kép, nếu không chương trình nhận sai tham số
function Q($s) { $s = "$s"; if ($s -match '\s') { "`"$s`"" } else { $s } }

function Wait-Http($url, $seconds, $proc, $name) {
    $t = [Diagnostics.Stopwatch]::StartNew()
    while ($t.Elapsed.TotalSeconds -lt $seconds) {
        if ($proc.HasExited) { Fail "$name thoát (mã $($proc.ExitCode)), xem log trong $LogDir" }
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                Write-Host ("  {0} sẵn sàng sau {1:N1} s" -f $name, $t.Elapsed.TotalSeconds)
                return
            }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    Fail "$name không lên sau $seconds s, xem log trong $LogDir"
}

function Stop-Tree($proc) {
    if ($proc -and -not $proc.HasExited) { & taskkill /PID $proc.Id /T /F | Out-Null }
}

# Khoảng cổng Windows giữ riêng (Hyper-V / WSL / Docker): không hiện là "đang nghe" nhưng không mở được
function Get-ExcludedPortRanges {
    $out = & netsh int ipv4 show excludedportrange protocol=tcp 2>$null
    foreach ($line in $out) {
        if ($line -match '^\s*(\d+)\s+(\d+)') { [pscustomobject]@{ Start = [int]$Matches[1]; End = [int]$Matches[2] } }
    }
}

# -- 1. Kiểm máy ---------------------------------------------------------------------------------------------------
Write-Host "Kiểm máy..."
$Py = Join-Path $Root "ai/.venv/Scripts/python.exe"
if (-not (Test-Path $Py)) { Fail "chưa có ai/.venv (cần Python 3.12: README.md, mục 'Chạy demo trên máy khác')" }
$PyVer = (& $Py -c "import sys; print('%d.%d' % sys.version_info[:2])")
if ($PyVer -ne "3.12") { Fail "ai/.venv là Python $PyVer, cần 3.12 (môi trường chuẩn ai/requirements-lock.txt)" }
foreach ($cmd in @("java", "node")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Fail "không thấy '$cmd' trong PATH" }
}
# Spring Boot 3 của backend cần JDK 21 trở lên (backend/pom.xml)
$JavaLine = (& cmd /c "java -version 2>&1" | Select-Object -First 1)
if ($JavaLine -match 'version "(\d+)') { $JavaMajor = [int]$Matches[1] } else { $JavaMajor = 0 }
if ($JavaMajor -lt 21) { Fail "cần JDK 21 trở lên, máy có: $JavaLine" }

# File dữ liệu không có trong git: embedding seed 1 phải đúng sha256 ghi trong meta.json
$Emb = Join-Path $Root "$EmbDir/embeddings.npz"
$Meta = Join-Path $Root "$EmbDir/meta.json"
if (-not (Test-Path $Emb) -or -not (Test-Path $Meta)) { Fail "thiếu $EmbDir/embeddings.npz hoặc meta.json (không có trong git)" }
$Want = (Get-Content $Meta -Raw -Encoding UTF8 | ConvertFrom-Json).embeddings_sha256
$Got = (Get-FileHash $Emb -Algorithm SHA256).Hash.ToLower()
if ($Got -ne $Want) { Fail "sha256 embeddings.npz = $Got, meta.json ghi $Want" }
Write-Host "  Python $PyVer, Java $JavaMajor, embeddings.npz đúng sha256 ($($Got.Substring(0, 12))...)"
# 4 file dữ liệu khác FastAPI đọc mà không có trong git (đo bằng ai/service/list_runtime_files.py, 28/10/2026)
$DataFiles = [ordered]@{
    "ai/data/processed/train.txt"     = "ebd29b03a4866cfca243edc1ee31539f16be19b756bfbd4c388e3f20ca06a5c5"
    "ai/data/processed/val.txt"       = "e8a47d06bd6e6977fe7eebc485cbf07eb75e7e9bdb651da955e8fd7f85a3a900"
    "ai/data/processed/test.txt"      = "410fc46cea72cdc5115a3e0413036456d1d1d59b8bcb7c63da6edd026e4da8ea"
    "ai/data/processed/item_map.json" = "c7ccd84b3fbcc5cf7cab85171fdf187dea8deccf3d36aaceb4877f06cfdaa63c"
}
foreach ($f in $DataFiles.Keys) {
    $path = Join-Path $Root $f
    if (-not (Test-Path $path)) { Fail "thiếu $f (không có trong git)" }
    if ((Get-FileHash $path -Algorithm SHA256).Hash.ToLower() -ne $DataFiles[$f]) { Fail "sha256 của $f khác bản chuẩn" }
}
Write-Host "  4 file ai/data/processed đúng sha256"

$Excluded = @(Get-ExcludedPortRanges)
foreach ($port in @($FastApiPort, $SpringPort, $VitePort)) {
    $busy = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($busy) {
        $owner = (Get-Process -Id ($busy | Select-Object -First 1).OwningProcess -ErrorAction SilentlyContinue).ProcessName
        Fail "cổng $port đang bị '$owner' dùng (tắt nó, hoặc đổi -FastApiPort / -SpringPort / -VitePort)"
    }
    foreach ($r in $Excluded) {
        if ($port -ge $r.Start -and $port -le $r.End) {
            Fail "cổng $port nằm trong khoảng Windows giữ riêng $($r.Start)-$($r.End) (netsh int ipv4 show excludedportrange protocol=tcp); đổi -FastApiPort / -SpringPort / -VitePort"
        }
    }
}
if (-not (Test-Path (Join-Path $Root "frontend/node_modules/vite"))) {
    Write-Host "Cài thư viện frontend (npm ci, lần đầu, cần mạng)..."
    Push-Location frontend; & npm ci; $code = $LASTEXITCODE; Pop-Location
    if ($code -ne 0) { Fail "npm ci lỗi" }
}
# Có jar rồi thì dùng luôn (không cần Maven / mạng khi demo); -Build hoặc chưa có jar thì đóng gói
$Jar = Join-Path $Root "backend/target/camera-store-backend-0.1.0.jar"
if ($Build -or -not (Test-Path $Jar)) {
    if (-not (Get-Command mvn -ErrorAction SilentlyContinue)) { Fail "chưa có $Jar và không thấy 'mvn' trong PATH" }
    Write-Host "Đóng gói Spring Boot (mvn -q -DskipTests package)..."
    Push-Location backend; & mvn -q -DskipTests package; $code = $LASTEXITCODE; Pop-Location
    if ($code -ne 0) { Fail "mvn package lỗi" }
} else {
    Write-Host ("  dùng jar có sẵn ({0:yyyy-MM-dd HH:mm}); đổi code backend thì chạy lại với -Build" -f (Get-Item $Jar).LastWriteTime)
}

try {
    # -- 2. FastAPI ------------------------------------------------------------------------------------------------
    Write-Host "Bật FastAPI seed 1 (http://127.0.0.1:$FastApiPort, ~15 s)..."
    $p = Start-Process -FilePath $Py -PassThru -NoNewWindow -WorkingDirectory $Root `
        -ArgumentList @((Q "ai/service/run_service.py"), "--emb-dir", (Q $EmbDir), "--port", $FastApiPort, "--log-file", (Q "$LogDir/fastapi.log")) `
        -RedirectStandardOutput "$LogDir/fastapi_stdout.txt" -RedirectStandardError "$LogDir/fastapi_stderr.txt"
    $Procs += $p
    Wait-Http "http://127.0.0.1:$FastApiPort/health" 300 $p "FastAPI"

    # -- 3. Spring Boot --------------------------------------------------------------------------------------------
    Write-Host "Bật Spring Boot (http://127.0.0.1:$SpringPort, heap tối đa $SpringHeap)..."
    $Cors = "http://localhost:$VitePort,http://127.0.0.1:$VitePort"
    # server.address=127.0.0.1: chỉ máy này gọi được /api (hợp đồng mục 1: chỉ chạy trong máy)
    $p = Start-Process -FilePath "java" -PassThru -NoNewWindow -WorkingDirectory (Join-Path $Root "backend") `
        -ArgumentList @("-Xmx$SpringHeap", "-jar", (Q $Jar), "--server.address=127.0.0.1", "--server.port=$SpringPort",
            "--model-service.base-url=http://127.0.0.1:$FastApiPort", "--cors.allowed-origins=$Cors") `
        -RedirectStandardOutput "$LogDir/spring.log" -RedirectStandardError "$LogDir/spring_stderr.txt"
    $Procs += $p
    Wait-Http "http://127.0.0.1:$SpringPort/api/health" 120 $p "Spring Boot"

    # -- 4. Vite ---------------------------------------------------------------------------------------------------
    Write-Host "Bật React / Vite (http://127.0.0.1:$VitePort, chế độ api)..."
    $env:VITE_RECOMMENDATION_SOURCE = "api"
    $env:VITE_API_URL = "http://127.0.0.1:$SpringPort/api"
    $p = Start-Process -FilePath "node" -PassThru -NoNewWindow -WorkingDirectory (Join-Path $Root "frontend") `
        -ArgumentList @("node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", $VitePort, "--strictPort") `
        -RedirectStandardOutput "$LogDir/vite.log" -RedirectStandardError "$LogDir/vite_stderr.txt"
    $Procs += $p
    Remove-Item Env:VITE_RECOMMENDATION_SOURCE, Env:VITE_API_URL
    Wait-Http "http://127.0.0.1:$VitePort" 60 $p "Vite"

    Write-Host ""
    Write-Host "Demo đang chạy: http://127.0.0.1:$VitePort  (bấm 'Tư vấn thiết bị')" -ForegroundColor Green
    Write-Host "  React -> Spring http://127.0.0.1:$SpringPort/api -> FastAPI http://127.0.0.1:$FastApiPort"
    Write-Host "  Bấm thử một lượt trước khi trình bày (lượt đầu nạp chậm hơn). Log: $LogDir"
    Read-Host "Nhấn Enter để tắt cả ba" | Out-Null
} finally {
    Write-Host "Tắt các tiến trình..."
    foreach ($p in $Procs) { Stop-Tree $p }
}
