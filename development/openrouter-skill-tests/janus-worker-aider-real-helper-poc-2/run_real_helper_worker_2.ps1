param(
    [string]$Model = "openrouter/qwen/qwen3-coder-30b-a3b-instruct"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$sourceDir = Resolve-Path $PSScriptRoot
$tempWorkspace = Join-Path $env:TEMP ("janus-aider-real-helper2-" + [guid]::NewGuid().ToString("N"))
$logPath = Join-Path $sourceDir "test_output.log"
$reportPath = Join-Path $sourceDir "worker_report.md"
$realTargetPath = Join-Path $repoRoot "development\openrouter-skill-tests\janus-backlog-prioritization\lean_backlog_prioritization_eval.py"
$rootAiderBefore = @(Get-ChildItem -Force -Path $repoRoot -Filter ".aider*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$gitignorePath = Join-Path $repoRoot ".gitignore"
$gitignoreHashBefore = if (Test-Path $gitignorePath) { (Get-FileHash $gitignorePath).Hash } else { "" }
$allowedEdit = "lean_backlog_prioritization_eval.py"

if (-not $env:OPENROUTER_API_KEY) {
    throw "OPENROUTER_API_KEY is not set."
}

New-Item -ItemType Directory -Path $tempWorkspace | Out-Null
Copy-Item $realTargetPath (Join-Path $tempWorkspace "lean_backlog_prioritization_eval.py")
Copy-Item (Join-Path $sourceDir "test_real_helper_2.py") (Join-Path $tempWorkspace "test_real_helper_2.py")
Copy-Item (Join-Path $sourceDir "worker_task.md") (Join-Path $tempWorkspace "worker_task.md")

$baselineHashes = @{}
foreach ($file in @("lean_backlog_prioritization_eval.py", "test_real_helper_2.py")) {
    $baselineHashes[$file] = (Get-FileHash (Join-Path $tempWorkspace $file)).Hash
}

$env:OPENAI_API_KEY = $env:OPENROUTER_API_KEY
$env:OPENAI_API_BASE = "https://openrouter.ai/api/v1"

$preExit = 0
$postExit = 0

try {
    Push-Location $tempWorkspace

    "=== PRETEST ===" | Set-Content -Path $logPath -Encoding utf8
    & python -m pytest -q test_real_helper_2.py *>&1 | Tee-Object -FilePath $logPath -Append
    if ($LASTEXITCODE -ne 0) { $preExit = $LASTEXITCODE }

    "=== AIDER RUN ===" | Tee-Object -FilePath $logPath -Append
    & aider --model $Model --no-auto-commits --yes-always --message-file worker_task.md lean_backlog_prioritization_eval.py test_real_helper_2.py *>&1 | Tee-Object -FilePath $logPath -Append

    "=== POSTTEST ===" | Tee-Object -FilePath $logPath -Append
    & python -m pytest -q test_real_helper_2.py *>&1 | Tee-Object -FilePath $logPath -Append
    if ($LASTEXITCODE -ne 0) { $postExit = $LASTEXITCODE }

    Copy-Item (Join-Path $tempWorkspace "lean_backlog_prioritization_eval.py") $realTargetPath -Force
}
finally {
    if ((Get-Location).Path -eq $tempWorkspace) {
        Pop-Location
    }
}

$changedFiles = @()
foreach ($file in @("lean_backlog_prioritization_eval.py", "test_real_helper_2.py")) {
    $currentHash = (Get-FileHash (Join-Path $tempWorkspace $file)).Hash
    if ($currentHash -ne $baselineHashes[$file]) {
        $changedFiles += $file
    }
}

$scopeDrift = @($changedFiles | Where-Object { $_ -ne $allowedEdit })
$rootAiderAfter = @(Get-ChildItem -Force -Path $repoRoot -Filter ".aider*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$newRootAiderArtifacts = @($rootAiderAfter | Where-Object { $_ -notin $rootAiderBefore })
$gitignoreHashAfter = if (Test-Path $gitignorePath) { (Get-FileHash $gitignorePath).Hash } else { "" }
$gitignoreTouchedByRun = $gitignoreHashBefore -ne $gitignoreHashAfter

$pass = ($preExit -ne 0) -and ($postExit -eq 0) -and ($scopeDrift.Count -eq 0) -and ($newRootAiderArtifacts.Count -eq 0) -and (-not $gitignoreTouchedByRun)

$reportLines = @(
    "# Worker Report",
    "",
    "## POC Summary",
    "",
    "- Worker: aider",
    "- Model: $Model",
    "- Real helper target: development/openrouter-skill-tests/janus-backlog-prioritization/lean_backlog_prioritization_eval.py",
    "- Scope: isolated temp workspace outside the repository root",
    "",
    "## Test checks",
    "",
    "- Pretest exit code: $preExit",
    "- Posttest exit code: $postExit",
    "",
    "## Changed files inside temp workspace",
    "",
    "- Changed files: $(if ($changedFiles.Count) { ($changedFiles -join ', ') } else { 'none' })",
    "- Scope drift files: $(if ($scopeDrift.Count) { ($scopeDrift -join ', ') } else { 'none' })",
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
    "$(if ($pass) { 'Pass.' } else { 'Blocked.' })",
    "",
    "## Go/No-Go Answer",
    "",
    "- $(if ($pass) { 'Go: a second real repo-owned Lean-Dev helper file can be patched through the isolated temp-workspace pattern.' } else { 'No-Go: this second real-helper slice did not satisfy the bounded acceptance bar.' })"
)

Set-Content -Path $reportPath -Value ($reportLines -join "`r`n") -Encoding utf8
Remove-Item -LiteralPath $tempWorkspace -Recurse -Force

if (-not $pass) {
    exit 1
}
