#Requires -Version 5.1
<#
Janus /save Skill - Solo Git v2 checkpoint.

Conservative helper:
- never stages with `git add .`
- requires explicit pathspecs and a commit message
- allowed on feature/* branches and master (post-merge governance)
- runs targeted git checks before commit and push

Examples:
  .\scripts\save.ps1 -Path "AGENTS.md" -Message "docs(governance): solo git v2"
  .\scripts\save.ps1 -Path "backend/services/foo.py","backend/tests/test_foo.py" -Message "feat(foo): add slice"
#>

param(
    [string[]]$Path = @(),
    [string]$Message = "",
    [switch]$PushBackup,
    [switch]$SyncCodex
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host "[SAVE] $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Test-AllowedBranch {
    param([string]$BranchName)
    if ($BranchName -eq "master") { return $true }
    if ($BranchName -like "feature/*") { return $true }
    return $false
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Host "[SAVE BLOCKED] Not inside a git repository." -ForegroundColor Red
    exit 1
}
Set-Location $repoRoot

$branch = (git branch --show-current).Trim()
if (-not (Test-AllowedBranch -BranchName $branch)) {
    Write-Host "[SAVE BLOCKED] Branch '$branch' is not allowed. Use feature/* or master." -ForegroundColor Red
    Write-Host "See documentation/codex/JANUS_SOLO_GIT.md"
    exit 1
}

$status = git status --porcelain
if (-not $status) {
    Write-Host "[SAVE] Nothing to save. Working tree clean."
    exit 0
}

if (-not $Path -or $Path.Count -eq 0) {
    Write-Host "[SAVE BLOCKED] Explicit -Path values are required. Never use git add ." -ForegroundColor Red
    exit 1
}
if (-not $Message.Trim()) {
    Write-Host "[SAVE BLOCKED] A Conventional Commit -Message is required." -ForegroundColor Red
    exit 1
}

$alreadyStaged = git diff --cached --name-only
if ($alreadyStaged) {
    Write-Host "[SAVE BLOCKED] Staged files already exist. Commit or unstage them first." -ForegroundColor Red
    exit 1
}

Write-Host "[SAVE] Staging explicit paths:" -ForegroundColor Cyan
$Path | ForEach-Object { Write-Host "  $_" }
git add -- @Path
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE BLOCKED] Explicit staging failed." -ForegroundColor Red
    exit 1
}

Invoke-Step "diff whitespace check" { git diff --cached --check }

$preCommit = Join-Path $repoRoot "scripts/git-hooks/pre-commit.ps1"
if (Test-Path -LiteralPath $preCommit) {
    Invoke-Step "pre-commit hook" { powershell -NoProfile -ExecutionPolicy Bypass -File $preCommit }
}

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE BLOCKED] Commit failed." -ForegroundColor Red
    exit 1
}

Write-Host "[SAVE OK] Committed on $branch." -ForegroundColor Green

if ($PushBackup) {
    git push backup $branch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[SAVE BLOCKED] Push to backup/$branch failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "[SAVE OK] Pushed to backup/$branch." -ForegroundColor Green
}

if ($SyncCodex) {
    $syncScript = Join-Path $repoRoot "documentation/codex/scripts/sync_codex_current_state.ps1"
    if (-not (Test-Path -LiteralPath $syncScript)) {
        Write-Host "[SAVE BLOCKED] Missing sync script: $syncScript" -ForegroundColor Red
        exit 1
    }
    & $syncScript
}
