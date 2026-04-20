#Requires -Version 5.1
<#
Janus /save Skill - Hardened Auto-Backup
  Step 0: Branch-Guard (nie auf master committen)
  Step 1: Dirty-Check (abort if nothing to save)
  Step 2: Blocker-Scan (>90MB)
  Step 3: git add/commit/push backup develop
#>
$ErrorActionPreference = "Stop"
$MAX_MB = 90
$TARGET_BRANCH = "develop"

# Step 0: Branch-Guard
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -eq "master") {
    Write-Host "[SAVE BLOCKED] Direct commit to 'master' forbidden. Switch to 'develop' first." -ForegroundColor Red
    exit 1
}
if ($branch -ne $TARGET_BRANCH) {
    Write-Host "[SAVE WARN] Current branch '$branch' != '$TARGET_BRANCH'. Proceeding anyway..." -ForegroundColor Yellow
}

# Step 1: Dirty-Check
$status = git status --porcelain
if (-not $status) {
    Write-Host "[SAVE] Nothing to save. Working tree clean."
    exit 0
}

# Step 2: Blocker-Scan (pro-actively; pre-commit hook is backup safety net)
$blockers = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt ($MAX_MB * 1MB) -and $_.FullName -notmatch "\\\.git\\" } |
    Where-Object {
        $rel = Resolve-Path -Relative $_.FullName
        git check-ignore -q $rel 2>$null | Out-Null
        $LASTEXITCODE -ne 0  # not ignored
    }
if ($blockers) {
    Write-Host "[SAVE BLOCKED] Files >$MAX_MB MB not in .gitignore:" -ForegroundColor Red
    $blockers | ForEach-Object {
        $mb = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  $($_.FullName) = $mb MB" -ForegroundColor Red
    }
    exit 1
}

# Step 3: Commit & Push
$date = Get-Date -Format "yyyy-MM-dd HH:mm"
git add .
git commit -m "Auto-Save $date"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE] Commit failed (pre-commit hook?)." -ForegroundColor Red
    exit 1
}
git push backup $branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE] Push failed." -ForegroundColor Red
    exit 1
}
Write-Host "[SAVE OK] Pushed to backup/$branch at $date" -ForegroundColor Green
