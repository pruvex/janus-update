#Requires -Version 5.1
# Janus Git Pre-Commit - Blocker-Check (>90MB)
$MAX_MB = 90
$exitCode = 0
$staged = git diff --cached --name-only --diff-filter=AM
if (-not $staged) { exit 0 }
foreach ($f in $staged) {
    if (-not (Test-Path -LiteralPath $f)) { continue }
    try {
        $sizeMB = [math]::Round((Get-Item -LiteralPath $f).Length / 1MB, 2)
    } catch { continue }
    if ($sizeMB -gt $MAX_MB) {
        Write-Host "[PRE-COMMIT BLOCKER] $f = $sizeMB MB > $MAX_MB MB"
        $exitCode = 1
    }
}
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "Commit blockiert. Optionen:"
    Write-Host "  1. Datei aus Index nehmen: git reset HEAD <file>"
    Write-Host "  2. In .gitignore aufnehmen und erneut stagen"
    Write-Host "  3. Git LFS verwenden"
}
exit $exitCode
