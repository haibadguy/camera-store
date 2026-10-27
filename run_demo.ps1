# run_demo.ps1 -- Bật demo bằng một lệnh: FastAPI (dịch vụ mô hình, seed 1) -> Spring Boot -> React (Vite, chế độ api).
# Viết 28/10/2026. Cách chuẩn bị máy: README.md, mục "Chạy demo trên máy khác".
#
# Chạy từ thư mục camera-store (PowerShell):
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Source mock      # React đọc frontend/src/mock, không gọi API
# Mở http://127.0.0.1:5173, bấm "Tư vấn thiết bị". Nhấn Enter trong cửa sổ này để tắt cả ba.
# Log mỗi lần chạy: results/demo/run_demo_logs/<ngày_giờ>/ (thư mục mới, không ghi đè).

param(
    [ValidateSet("api", "mock")] [string]$Source = "api",
    [int]$FastApiPort = 8001,
    [int]$SpringPort = 8080,
    [int]$VitePort = 5173,
    [string]$EmbDir = "results/service/emb_s1_20261021",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root
$Tag = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir = Join-Path $Root "results/demo/run_demo_logs/$Tag"
New-Item -ItemType Directory -Path $LogDir | Out-Null
$Procs = @()

function Fail($msg) { Write-Host "DỪNG: $msg" -ForegroundColor Red; exit 1 }

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

# -- 1. Kiểm máy ---------------------------------------------------------------------------------------------------
Write-Host "Kiểm máy..."
$Py = Join-Path $Root "ai/.venv/Scripts/python.exe"
if (-not (Test-Path $Py)) { Fail "chưa có ai/.venv (cần Python 3.12: README.md, mục 'Chạy demo trên máy khác')" }
$PyVer = (& $Py -c "import sys; print('%d.%d' % sys.version_info[:2])")
if ($PyVer -ne "3.12") { Fail "ai/.venv là Python $PyVer, cần 3.12 (môi trường chuẩn ai/requirements-lock.txt)" }
foreach ($cmd in @("java", "node")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Fail "không thấy '$cmd' trong PATH" }
}
if (-not $SkipBuild -and -not (Get-Command mvn -ErrorAction SilentlyContinue)) { Fail "không thấy 'mvn' trong PATH" }

# File dữ liệu không có trong git: embedding seed 1 phải đúng sha256 ghi trong meta.json
$Emb = Join-Path $Root "$EmbDir/embeddings.npz"
$Meta = Join-Path $Root "$EmbDir/meta.json"
if (-not (Test-Path $Emb) -or -not (Test-Path $Meta)) { Fail "thiếu $EmbDir/embeddings.npz hoặc meta.json (không có trong git)" }
$Want = (Get-Content $Meta -Raw -Encoding UTF8 | ConvertFrom-Json).embeddings_sha256
$Got = (Get-FileHash $Emb -Algorithm SHA256).Hash.ToLower()
if ($Got -ne $Want) { Fail "sha256 embeddings.npz = $Got, meta.json ghi $Want" }
Write-Host "  Python $PyVer, embeddings.npz đúng sha256 ($($Got.Substring(0, 12))...)"
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

foreach ($port in @($FastApiPort, $SpringPort, $VitePort)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        Fail "cổng $port đang có chương trình khác dùng (tắt nó, hoặc đổi -FastApiPort / -SpringPort / -VitePort)"
    }
}
if (-not (Test-Path (Join-Path $Root "frontend/node_modules/vite"))) {
    Write-Host "Cài thư viện frontend (npm ci, lần đầu)..."
    Push-Location frontend; & npm ci; $code = $LASTEXITCODE; Pop-Location
    if ($code -ne 0) { Fail "npm ci lỗi" }
}
$Jar = Join-Path $Root "backend/target/camera-store-backend-0.1.0.jar"
if (-not $SkipBuild) {
    Write-Host "Đóng gói Spring Boot (mvn -q -DskipTests package)..."
    Push-Location backend; & mvn -q -DskipTests package; $code = $LASTEXITCODE; Pop-Location
    if ($code -ne 0) { Fail "mvn package lỗi" }
}
if (-not (Test-Path $Jar)) { Fail "không có $Jar" }

try {
    # -- 2. FastAPI ------------------------------------------------------------------------------------------------
    Write-Host "Bật FastAPI seed 1 (http://127.0.0.1:$FastApiPort, ~15 s)..."
    $p = Start-Process -FilePath $Py -PassThru -NoNewWindow `
        -ArgumentList @("ai/service/run_service.py", "--emb-dir", $EmbDir, "--port", $FastApiPort, "--log-file", "$LogDir/fastapi.log") `
        -RedirectStandardOutput "$LogDir/fastapi_stdout.txt" -RedirectStandardError "$LogDir/fastapi_stderr.txt"
    $Procs += $p
    Wait-Http "http://127.0.0.1:$FastApiPort/health" 300 $p "FastAPI"

    # -- 3. Spring Boot --------------------------------------------------------------------------------------------
    Write-Host "Bật Spring Boot (http://127.0.0.1:$SpringPort)..."
    $Cors = "http://localhost:$VitePort,http://127.0.0.1:$VitePort"
    $p = Start-Process -FilePath "java" -PassThru -NoNewWindow -WorkingDirectory (Join-Path $Root "backend") `
        -ArgumentList @("-jar", "`"$Jar`"", "--server.port=$SpringPort", "--model-service.base-url=http://127.0.0.1:$FastApiPort", "--cors.allowed-origins=$Cors") `
        -RedirectStandardOutput "$LogDir/spring.log" -RedirectStandardError "$LogDir/spring_stderr.txt"
    $Procs += $p
    Wait-Http "http://127.0.0.1:$SpringPort/api/health" 120 $p "Spring Boot"

    # -- 4. Vite ---------------------------------------------------------------------------------------------------
    Write-Host "Bật React / Vite (http://127.0.0.1:$VitePort, nguồn dữ liệu: $Source)..."
    $env:VITE_RECOMMENDATION_SOURCE = $Source
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
    Write-Host "  Log: $LogDir"
    Read-Host "Nhấn Enter để tắt cả ba" | Out-Null
} finally {
    Write-Host "Tắt các tiến trình..."
    foreach ($p in $Procs) { Stop-Tree $p }
}
