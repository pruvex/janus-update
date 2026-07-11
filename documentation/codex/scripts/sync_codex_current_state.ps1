#Requires -Version 5.1
<#
Sync documentation/ai/CURRENT_STATE.md to origin/codex-sync for ChatGPT.

Usage (Operator approval required):
  .\documentation\codex\scripts\sync_codex_current_state.ps1
  .\documentation\codex\scripts\sync_codex_current_state.ps1 -Message "sync: cursor hardening closeout"
#>

param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$StatePath = "documentation/ai/CURRENT_STATE.md"
$SyncBranch = "codex-sync"
$ReturnBranch = ""

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host "[CODEX-SYNC] $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Host "[CODEX-SYNC BLOCKED] Not inside a git repository." -ForegroundColor Red
    exit 1
}
Set-Location $repoRoot

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Host "[CODEX-SYNC BLOCKED] Missing $StatePath" -ForegroundColor Red
    exit 1
}

$ReturnBranch = (git branch --show-current).Trim()
if (-not $ReturnBranch) {
    Write-Host "[CODEX-SYNC BLOCKED] Detached HEAD; checkout master or a feature branch first." -ForegroundColor Red
    exit 1
}

if (-not $Message.Trim()) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $Message = "sync: update CURRENT_STATE ($stamp)"
}

$stashCreated = $false
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "[CODEX-SYNC] Stashing dirty worktree before branch switch..." -ForegroundColor Yellow
    git stash push -u -m "codex-sync auto-stash"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[CODEX-SYNC BLOCKED] Stash failed." -ForegroundColor Red
        exit 1
    }
    $stashCreated = $true
}

try {
    Invoke-Step "fetch origin $SyncBranch" { git fetch origin $SyncBranch }

    $localSyncExists = git show-ref --verify --quiet "refs/heads/$SyncBranch"; $hasLocal = ($LASTEXITCODE -eq 0)
    if ($hasLocal) {
        Invoke-Step "checkout local $SyncBranch" { git checkout $SyncBranch }
    } else {
        $remoteExists = git show-ref --verify --quiet "refs/remotes/origin/$SyncBranch"; $hasRemote = ($LASTEXITCODE -eq 0)
        if ($hasRemote) {
            Invoke-Step "checkout tracking $SyncBranch" { git checkout -b $SyncBranch "origin/$SyncBranch" }
        } else {
            Invoke-Step "create orphan $SyncBranch" { git checkout --orphan $SyncBranch }
            git reset --hard
            if ($LASTEXITCODE -ne 0) { throw "orphan reset failed" }
        }
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatePath) | Out-Null
    git checkout "$ReturnBranch" -- $StatePath
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read CURRENT_STATE from $ReturnBranch"
    }

    git add -- $StatePath
    $staged = git diff --cached --name-only
    if (-not $staged) {
        Write-Host "[CODEX-SYNC] No CURRENT_STATE change to publish." -ForegroundColor Yellow
    } else {
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) {
            throw "commit failed"
        }
        Invoke-Step "push origin $SyncBranch" { git push origin $SyncBranch }
        Write-Host "[CODEX-SYNC OK] Published CURRENT_STATE to origin/$SyncBranch" -ForegroundColor Green
    }
}
finally {
    Invoke-Step "return to $ReturnBranch" { git checkout $ReturnBranch }
    if ($stashCreated) {
        Write-Host "[CODEX-SYNC] Restoring stashed worktree..." -ForegroundColor Yellow
        git stash pop
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[CODEX-SYNC WARN] Stash pop had conflicts; resolve manually." -ForegroundColor Yellow
        }
    }
}
