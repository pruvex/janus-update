#Requires -Version 5.1
# Janus Git Pre-Commit - Git governance guard plus large-file blocker.
$MAX_MB = 90
$exitCode = 0

$repoRoot = (git rev-parse --show-toplevel).Trim()
$guard = Join-Path $repoRoot "documentation/codex/skills/janus-git-governance/scripts/git_guard.py"
if (-not (Test-Path -Path $guard -ErrorAction SilentlyContinue)) {
    Write-Host "[PRE-COMMIT BLOCKER] Missing git guard: $guard"
    exit 1
}

python $guard $repoRoot --staged-only
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[PRE-COMMIT BLOCKED] git_guard.py rejected the staged changes."
    Write-Host "Review staged paths or split unrelated scope before committing."
    exit $LASTEXITCODE
}

$staged = git diff --cached --name-only --diff-filter=AM
if (-not $staged) { exit 0 }
foreach ($f in $staged) {
    if (-not (Test-Path -Path $f -ErrorAction SilentlyContinue)) { continue }
    try {
        $sizeMB = [math]::Round((Get-Item -Path $f -ErrorAction SilentlyContinue).Length / 1MB, 2)
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
