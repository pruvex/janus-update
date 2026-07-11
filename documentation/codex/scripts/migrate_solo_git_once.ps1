#Requires -Version 5.1
<#
One-time migration to Janus Solo Git v2 (master + feature/*).

REQUIRES:
  - VM snapshot taken by operator BEFORE running
  - explicit operator approval on command line

Usage:
  .\documentation\codex\scripts\migrate_solo_git_once.ps1 -ArchiveMixedWip -IHaveVmSnapshot
#>

param(
    [switch]$ArchiveMixedWip,
    [switch]$IHaveVmSnapshot
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host "[MIGRATE] $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

if (-not $IHaveVmSnapshot) {
    Write-Host "[MIGRATE BLOCKED] Take a VM snapshot first, then rerun with -IHaveVmSnapshot" -ForegroundColor Red
    exit 1
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$branch = (git branch --show-current).Trim()
Write-Host "[MIGRATE] Current branch: $branch"

Invoke-Step "fetch remotes" { git fetch --all --prune }

# Archive dirty worktree FIRST on current branch so checkout master is safe.
if ($ArchiveMixedWip) {
    $dirty = git status --porcelain
    if ($dirty) {
        Write-Host "[MIGRATE] Archiving mixed WIP on $branch before branch switch..." -ForegroundColor Yellow
        git add -A
        git commit -m "$( @"
chore: archive mixed WIP before solo-git v2

One-time migration commit. Future work uses master + feature/* only.
See documentation/codex/JANUS_SOLO_GIT.md
"@ )"
        if ($LASTEXITCODE -ne 0) {
            throw "archive commit failed"
        }
    } else {
        Write-Host "[MIGRATE] Worktree already clean before archive step." -ForegroundColor Green
    }
} else {
    $dirtyCount = (git status --short | Measure-Object -Line).Lines
    if ($dirtyCount -gt 0) {
        Write-Host "[MIGRATE BLOCKED] Worktree has $dirtyCount dirty entries. Rerun with -ArchiveMixedWip or clean manually." -ForegroundColor Red
        exit 1
    }
}

# Bring master to develop's committed tip if develop exists and is ahead.
$developExists = git show-ref --verify --quiet refs/heads/develop; $hasDevelop = ($LASTEXITCODE -eq 0)
if ($hasDevelop) {
    $developTip = (git rev-parse develop).Trim()
    $masterTip = (git rev-parse master).Trim()
    Write-Host "[MIGRATE] develop=$developTip master=$masterTip"

    Invoke-Step "checkout master" { git checkout master }
    if ($developTip -ne $masterTip) {
        Invoke-Step "fast-forward master from develop" { git merge develop --ff-only }
    }
} else {
    Invoke-Step "checkout master" { git checkout master }
}

$remainingDirty = git status --porcelain
if ($remainingDirty) {
    Write-Host "[MIGRATE WARN] Unexpected dirty entries remain after migration:" -ForegroundColor Yellow
    git status --short
}

Write-Host ""
Write-Host "[MIGRATE OK] Solo Git v2 baseline ready on master." -ForegroundColor Green
Write-Host "Next steps (operator approval required):"
Write-Host "  1. git push backup master"
Write-Host "  2. .\documentation\codex\scripts\sync_codex_current_state.ps1"
Write-Host "  3. git checkout -b feature/<next-slice>"
Write-Host "  4. Optional: remove legacy develop after backup push: git branch -d develop"
Write-Host "  5. Optional: resolve M6 worktree separately (merge or remove)"
