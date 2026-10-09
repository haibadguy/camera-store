# Hoàn thiện file Word sau build_docx.py: cập nhật mục lục (trường TOC), lưu lại,
# xuất PDF để xem, in số trang, số công thức Word (OMath) và trang bắt đầu của từng tiêu đề cấp 1.
# Cần Microsoft Word trên máy (COM). Chỉ đọc / ghi đúng file được chỉ định.
# Chạy: powershell -File ai/survey/report/word_finalize.ps1 -Docx E:\DATN\baocao\ban_thu.docx
param([Parameter(Mandatory = $true)][string]$Docx)

$ErrorActionPreference = "Stop"
$path = (Resolve-Path $Docx).Path
$pdf = [IO.Path]::ChangeExtension($path, ".pdf")
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($path)
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    "Số trang: {0}" -f $doc.ComputeStatistics(2)
    "Số công thức Word (OMath): {0}" -f $doc.OMaths.Count
    "Số bảng: {0}; số hình: {1}" -f $doc.Tables.Count, $doc.InlineShapes.Count
    "Trang bắt đầu của tiêu đề cấp 1:"
    foreach ($p in $doc.Paragraphs) {
        if ($p.OutlineLevel -eq 1) {
            "  trang {0,3}: {1}" -f $p.Range.Information(3), $p.Range.Text.Trim()
        }
    }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)
    "PDF: $pdf"
    $doc.Close()
}
finally {
    $word.Quit()
}
