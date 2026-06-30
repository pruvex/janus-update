param(
    [string]$Model = "openrouter/qwen/qwen3-coder-30b-a3b-instruct"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$sourceDir = Resolve-Path $PSScriptRoot
$tempWorkspace = Join-Path $env:TEMP ("janus-aider-code-" + [guid]::NewGuid().ToString("N"))
$logPath = Join-Path $sourceDir "test_output.log"
$reportPath = Join-Path $sourceDir "worker_report.md"
$rootAiderBefore = @(Get-ChildItem -Force -Path $repoRoot -Filter ".aider*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
$gitignorePath = Join-Path $repoRoot ".gitignore"
$gitignoreHashBefore = if (Test-Path $gitignorePath) { (Get-FileHash $gitignorePath).Hash } else { "" }
$allowedEdit = "text_utils.py"
$taskFiles = @("text_utils.py", "test_text_utils.py", "worker_task.md")

if (-not $env:OPENROUTER_API_KEY) {
    throw "OPENROUTER_API_KEY is not set."
}

New-Item -ItemType Directory -Path $tempWorkspace | Out-Null
foreach ($file in $taskFiles) {
    Copy-Item (Join-Path $sourceDir $file) (Join-Path $tempWorkspace $file)
}

$baselineHashes = @{}
foreach ($file in @("text_utils.py", "test_text_utils.py")) {
    $baselineHashes[$file] = (Get-FileHash (Join-Path $tempWorkspace $file)).Hash
}

$env:OPENAI_API_KEY = $env:OPENROUTER_API_KEY
$env:OPENAI_API_BASE = "https://openrouter.ai/api/v1"

$preExit = 0
$postExit = 0

try {
    Push-Location $tempWorkspace

    "=== PRETEST ===" | Set-Content -Path $logPath -Encoding utf8
    & python -m pytest -q test_text_utils.py *>&1 | Tee-Object -FilePath $logPath -Append
    if ($LASTEXITCODE -ne 0) { $preExit = $LASTEXITCODE }

    "=== AIDER RUN ===" | Tee-Object -FilePath $logPath -Append
    & aider --model $Model --no-auto-commits --yes-always --message-file worker_task.md text_utils.py test_text_utils.py *>&1 | Tee-Object -FilePath $logPath -Append

    "=== POSTTEST ===" | Tee-Object -FilePath $logPath -Append
    & python -m pytest -q test_text_utils.py *>&1 | Tee-Object -FilePath $logPath -Append
    if ($LASTEXITCODE -ne 0) { $postExit = $LASTEXITCODE }

    Copy-Item (Join-Path $tempWorkspace "text_utils.py") (Join-Path $sourceDir "text_utils.py") -Force
}
finally {
    if ((Get-Location).Path -eq $tempWorkspace) {
        Pop-Location
    }
}

$changedFiles = @()
foreach ($file in @("text_utils.py", "test_text_utils.py")) {
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
    "- Scope: isolated temp workspace outside the repository root",
    "- Allowed edit target: text_utils.py",
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
    "- $(if ($pass) { 'Go for another bounded isolated code/test worker experiment on the same pattern.' } else { 'No-Go: this slice did not satisfy the bounded code/test acceptance bar.' })"
)

Set-Content -Path $reportPath -Value ($reportLines -join "`r`n") -Encoding utf8
Remove-Item -LiteralPath $tempWorkspace -Recurse -Force

if (-not $pass) {
    exit 1
}
