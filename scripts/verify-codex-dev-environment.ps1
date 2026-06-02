#Requires -Version 5.1
<#
Verify the Janus Codex development environment guardrails.

This script checks local clone setup, versioned governance helpers, installed
skill script synchronization, and the active pre-commit hook path.
#>

$ErrorActionPreference = "Stop"
$failures = 0

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail = ""
    )
    $status = if ($Passed) { "PASS" } else { "FAIL" }
    $color = if ($Passed) { "Green" } else { "Red" }
    Write-Host "[$status] $Name" -ForegroundColor $color
    if ($Detail) {
        Write-Host "       $Detail"
    }
    if (-not $Passed) {
        $script:failures += 1
    }
}

function Invoke-CheckCommand {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host "[RUN ] $Name" -ForegroundColor Cyan
    & $Command
    Add-Result $Name ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
}

$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
Add-Result "inside git repository" ([bool]$repoRoot) $repoRoot
if (-not $repoRoot) {
    exit 1
}

Set-Location $repoRoot
Add-Result "expected Janus root" ($repoRoot -eq "C:/KI/Janus-Projekt" -or $repoRoot -eq "C:\KI\Janus-Projekt") $repoRoot

$branch = (git branch --show-current).Trim()
Add-Result "branch is develop for normal work" ($branch -eq "develop") $branch

$hooksPath = (git config --get core.hooksPath 2>$null).Trim()
Add-Result "core.hooksPath points to scripts/git-hooks" ($hooksPath -eq "scripts/git-hooks") ($hooksPath -or "<unset>")

$requiredFiles = @(
    "AGENTS.md",
    "documentation/codex/CODEX_PROJECT_PROFILE.md",
    "documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md",
    "documentation/codex/skills/janus-git-governance/scripts/git_guard.py",
    "documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py",
    "scripts/git-hooks/pre-commit",
    "scripts/git-hooks/pre-commit.ps1",
    "scripts/save.ps1"
)
foreach ($file in $requiredFiles) {
    Add-Result "required file exists: $file" (Test-Path -Path $file -ErrorAction SilentlyContinue)
}

$installedRoot = "C:\Users\pruve\.codex\skills\janus-git-governance\scripts"
$syncPairs = @(
    @("documentation/codex/skills/janus-git-governance/scripts/git_guard.py", "$installedRoot\git_guard.py"),
    @("documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py", "$installedRoot\propose_changesets.py")
)
foreach ($pair in $syncPairs) {
    $repoFile = $pair[0]
    $installedFile = $pair[1]
    if (-not (Test-Path -Path $repoFile) -or -not (Test-Path -Path $installedFile)) {
        Add-Result "installed skill script synced: $repoFile" $false "missing repo or installed copy"
        continue
    }
    $repoHash = (Get-FileHash -Algorithm SHA256 -Path $repoFile).Hash
    $installedHash = (Get-FileHash -Algorithm SHA256 -Path $installedFile).Hash
    Add-Result "installed skill script synced: $repoFile" ($repoHash -eq $installedHash) "repo=$repoHash installed=$installedHash"
}

Invoke-CheckCommand "git guard full-worktree" { python "documentation/codex/skills/janus-git-governance/scripts/git_guard.py" $repoRoot }
Invoke-CheckCommand "git guard staged-only" { python "documentation/codex/skills/janus-git-governance/scripts/git_guard.py" $repoRoot --staged-only }
Invoke-CheckCommand "changeset proposer" { python "documentation/codex/skills/janus-git-governance/scripts/propose_changesets.py" $repoRoot }
Invoke-CheckCommand "pre-commit hook" { powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/git-hooks/pre-commit.ps1" }
Invoke-CheckCommand "diff whitespace check" { git diff --check }

if ($failures -gt 0) {
    Write-Host "[VERIFY FAILED] $failures check(s) failed." -ForegroundColor Red
    exit 1
}

Write-Host "[VERIFY PASS] Janus Codex development environment is configured." -ForegroundColor Green
exit 0
