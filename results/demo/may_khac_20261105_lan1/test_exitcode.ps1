# Thử nhánh "dịch vụ thoát" của run_demo.ps1: lấy đúng các hàm Fail, Start-Logged, Show-Tail, Wait-Http từ file (AST),
# bật một tiến trình Python in lỗi ra stderr rồi thoát mã 3.
param([string]$Script, [string]$Py, [string]$LogDir)
$ErrorActionPreference = "Stop"
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Script, [ref]$null, [ref]$null)
$fns = $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false) |
    Where-Object { $_.Name -in @("Fail", "Start-Logged", "Show-Tail", "Wait-Http") }
foreach ($f in $fns) { . ([scriptblock]::Create($f.Extent.Text)) }
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$p = Start-Logged $Py @("-c", "`"import sys; print('loi gia lap', file=sys.stderr); sys.exit(3)`"") $LogDir "$LogDir/o.txt" "$LogDir/e.txt"
Wait-Http "http://127.0.0.1:59999/health" 30 $p "FastAPI" @("$LogDir/e.txt")
