#Requires -Version 5.1
<#
Janus /save Skill - Diamond backup checkpoint.

This helper is intentionally conservative:
- never stages with `git add .`
- requires explicit pathspecs and a commit message
- blocks normal saves on master
- runs Janus git governance checks before commit and push

Examples:
  .\scripts\save.ps1
  .\scripts\save.ps1 -Path "AGENTS.md","documentation/codex/CODEX_PROJECT_PROFILE.md" -Message "docs(codex): update profile"
#>

param(
    [string[]]$Path = @(),
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$TARGET_BRANCH = "develop"

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

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Host "[SAVE BLOCKED] Not inside a git repository." -ForegroundColor Red
    exit 1
}
Set-Location $repoRoot

$branch = (git branch --show-current).Trim()
if ($branch -eq "master") {
    Write-Host "[SAVE BLOCKED] Direct normal-development commits to master are forbidden." -ForegroundColor Red
    exit 1
}
if ($branch -ne $TARGET_BRANCH) {
    Write-Host "[SAVE BLOCKED] Current branch '$branch' is not '$TARGET_BRANCH'." -ForegroundColor Red
    exit 1
}

$status = git status --porcelain
if (-not $status) {
    Write-Host "[SAVE] Nothing to save. Working tree clean."
    exit 0
}

$guard = Join-Path $repoRoot "documentation/codex/skills/janus-git-governance/scripts/git_guard.py"
$proposer = Join-Path $repoRoot "documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py"
if (-not (Test-Path -Path $guard -ErrorAction SilentlyContinue)) {
    Write-Host "[SAVE BLOCKED] Missing git guard: $guard" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -Path $proposer -ErrorAction SilentlyContinue)) {
    Write-Host "[SAVE BLOCKED] Missing changeset proposer: $proposer" -ForegroundColor Red
    exit 1
}

Invoke-Step "git guard full-worktree" { python $guard $repoRoot }
Invoke-Step "changeset proposal" { python $proposer $repoRoot }
Invoke-Step "diff whitespace check" { git diff --check }

$alreadyStaged = git diff --cached --name-only
if ($alreadyStaged) {
    Write-Host "[SAVE BLOCKED] Staged files already exist. Commit or unstage them first." -ForegroundColor Red
    $alreadyStaged | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    exit 1
}

if (-not $Path -or $Path.Count -eq 0) {
    Write-Host "[SAVE BLOCKED] Explicit -Path values are required. Never use git add ." -ForegroundColor Red
    Write-Host "Use the proposed git add command above, then rerun with -Path and -Message."
    exit 1
}
if (-not $Message.Trim()) {
    Write-Host "[SAVE BLOCKED] A Conventional Commit -Message is required." -ForegroundColor Red
    exit 1
}

Write-Host "[SAVE] Staging explicit paths:" -ForegroundColor Cyan
$Path | ForEach-Object { Write-Host "  $_" }
git add -- @Path
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE BLOCKED] Explicit staging failed." -ForegroundColor Red
    exit 1
}

Invoke-Step "git guard staged-only" { python $guard $repoRoot --staged-only }
Invoke-Step "pre-commit hook" { powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/git-hooks/pre-commit.ps1" }

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE BLOCKED] Commit failed. Review staged files before retrying." -ForegroundColor Red
    exit 1
}

git push backup $branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[SAVE BLOCKED] Push to backup/$branch failed." -ForegroundColor Red
    exit 1
}

Write-Host "[SAVE OK] Committed and pushed to backup/$branch." -ForegroundColor Green
