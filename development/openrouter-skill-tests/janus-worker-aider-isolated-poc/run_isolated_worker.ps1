param(
    [string]$Model = "openrouter/qwen/qwen3-coder-30b-a3b-instruct"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$sourceDir = Resolve-Path $PSScriptRoot
$tempWorkspace = Join-Path $env:TEMP ("janus-aider-isolated-" + [guid]::NewGuid().ToString("N"))
$logPath = Join-Path $sourceDir "test_output.log"
$reportPath = Join-Path $sourceDir "worker_report.md"
$targetName = "target_doc.md"
$taskName = "worker_task.md"
$rootAiderBefore = @(Get-ChildItem -Force -Path $repoRoot -Filter ".aider*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$gitignorePath = Join-Path $repoRoot ".gitignore"
$gitignoreHashBefore = if (Test-Path $gitignorePath) { (Get-FileHash $gitignorePath).Hash } else { "" }

if (-not $env:OPENROUTER_API_KEY) {
    throw "OPENROUTER_API_KEY is not set."
}

New-Item -ItemType Directory -Path $tempWorkspace | Out-Null
Copy-Item (Join-Path $sourceDir $targetName) (Join-Path $tempWorkspace $targetName)
Copy-Item (Join-Path $sourceDir $taskName) (Join-Path $tempWorkspace $taskName)

$env:OPENAI_API_KEY = $env:OPENROUTER_API_KEY
$env:OPENAI_API_BASE = "https://openrouter.ai/api/v1"

try {
    Push-Location $tempWorkspace
    & aider --model $Model --no-auto-commits --yes-always --message-file $taskName $targetName *>&1 | Tee-Object -FilePath $logPath
    Pop-Location

    Copy-Item (Join-Path $tempWorkspace $targetName) (Join-Path $sourceDir $targetName) -Force
}
finally {
    if ((Get-Location).Path -eq $tempWorkspace) {
        Pop-Location
    }
}

$rootAiderAfter = @(Get-ChildItem -Force -Path $repoRoot -Filter ".aider*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$newRootAiderArtifacts = @($rootAiderAfter | Where-Object { $_ -notin $rootAiderBefore })
$gitignoreHashAfter = if (Test-Path $gitignorePath) { (Get-FileHash $gitignorePath).Hash } else { "" }
$gitignoreTouchedByRun = $gitignoreHashBefore -ne $gitignoreHashAfter
$rootSideEffectsDetected = ($newRootAiderArtifacts.Count -gt 0) -or $gitignoreTouchedByRun

$reportLines = @(
    "# Worker Report",
    "",
    "## POC Summary",
    "",
    "- Worker: aider",
    "- Model: $Model",
    "- Scope: isolated temp workspace outside the repository root",
    "- Target file edited by worker: target_doc.md",
    "",
    "## What worked",
    "",
    "- The worker ran in a temporary workspace outside the repo root.",
    "- The worker produced a reviewable edit for target_doc.md.",
    "- The run log was captured locally in test_output.log.",
    "",
    "## Isolation checks",
    "",
    "- Repo-root .aider* artifacts before run: $($rootAiderBefore.Count)",
    "- Repo-root .aider* artifacts after run: $($rootAiderAfter.Count)",
    "- New repo-root .aider* artifacts: $(if ($newRootAiderArtifacts.Count) { ($newRootAiderArtifacts -join ', ') } else { 'none' })",
    "- .gitignore file hash changed during run: $(if ($gitignoreTouchedByRun) { 'yes' } else { 'no' })",
    "",
    "## Practical verdict",
    "",
    "$(if ($rootSideEffectsDetected) { 'Blocked.' } else { 'Pass.' })",
    "",
    "## Go/No-Go Answer",
    "",
    "- $(if ($rootSideEffectsDetected) { 'No-Go: isolation still leaked back into the repo root.' } else { 'Go for another bounded worker experiment on the same isolation pattern.' })"
)

Set-Content -Path $reportPath -Value ($reportLines -join "`r`n") -Encoding utf8
Remove-Item -LiteralPath $tempWorkspace -Recurse -Force
