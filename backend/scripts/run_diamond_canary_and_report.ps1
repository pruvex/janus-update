Set-StrictMode -Version Latest
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $projectRoot

Write-Host "==> Running Diamond Canary..."
python backend/tests/run_diamond_canary.py

Write-Host "==> Capturing monitoring report (tail 20)..."
$reportPath = Join-Path $env:USERPROFILE "Documents\diamond_canary_latest.txt"
python backend/tools/pdf_monitor_report.py --tail 20 | Out-File -Encoding utf8 -FilePath $reportPath
Write-Host "Monitoring report stored at $reportPath"

Pop-Location
