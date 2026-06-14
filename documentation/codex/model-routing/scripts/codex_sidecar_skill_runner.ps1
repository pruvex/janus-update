param(
    [Parameter(Mandatory = $true)]
    [string]$RunDirectory,

    [Parameter(Mandatory = $true)]
    [string]$PromptPath,

    [Parameter(Mandatory = $true)]
    [string]$Model,

    [string]$WorkingDirectory = "C:\KI\Janus-Projekt",

    [ValidateSet("read-only", "workspace-write", "danger-full-access")]
    [string]$Sandbox = "read-only",

    [ValidateSet("untrusted", "on-request", "never")]
    [string]$ApprovalPolicy = "never",

    [int]$TimeoutSeconds = 120,

    [string]$CodexPath = "codex",

    [switch]$UseOss,

    [ValidateSet("", "ollama", "lmstudio")]
    [string]$LocalProvider = "",

    [string[]]$Config = @(),

    [switch]$JsonEvents,

    [switch]$Execute
)

$ErrorActionPreference = "Stop"

function ConvertTo-ProcessArgumentString {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList
    )

    $quoted = foreach ($argument in $ArgumentList) {
        if ($null -eq $argument) {
            '""'
        } elseif ($argument -match '[\s"]') {
            '"' + ($argument -replace '"', '\"') + '"'
        } else {
            $argument
        }
    }

    return ($quoted -join " ")
}

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $children = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ParentProcessId -eq $ProcessId }

    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

$resolvedRunDirectory = [System.IO.Path]::GetFullPath($RunDirectory)
$resolvedPromptPath = [System.IO.Path]::GetFullPath($PromptPath)
$resolvedWorkingDirectory = [System.IO.Path]::GetFullPath($WorkingDirectory)

if (-not (Test-Path -LiteralPath $resolvedPromptPath)) {
    throw "PromptPath does not exist: $resolvedPromptPath"
}

if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory)) {
    throw "WorkingDirectory does not exist: $resolvedWorkingDirectory"
}

New-Item -ItemType Directory -Force -Path $resolvedRunDirectory | Out-Null

$stdoutPath = Join-Path $resolvedRunDirectory "stdout.log"
$stderrPath = Join-Path $resolvedRunDirectory "stderr.log"
$exitCodePath = Join-Path $resolvedRunDirectory "exit_code.txt"
$lastMessagePath = Join-Path $resolvedRunDirectory "last_message.md"
$eventStreamPath = Join-Path $resolvedRunDirectory "event_stream.jsonl"
$promptCopyPath = Join-Path $resolvedRunDirectory "prompt.md"
$commandPath = Join-Path $resolvedRunDirectory "command.json"
$summaryPath = Join-Path $resolvedRunDirectory "summary.json"

Copy-Item -LiteralPath $resolvedPromptPath -Destination $promptCopyPath -Force

$arguments = @(
    "exec",
    "--cd", $resolvedWorkingDirectory,
    "--model", $Model,
    "--sandbox", $Sandbox,
    "--output-last-message", $lastMessagePath
)

if ($UseOss) {
    $arguments += "--oss"
}

if ($LocalProvider -ne "") {
    $arguments += @("--local-provider", $LocalProvider)
}

foreach ($entry in $Config) {
    $arguments += @("--config", $entry)
}

if ($JsonEvents) {
    $arguments += "--json"
}

$arguments += @("-")

$processExecutable = $CodexPath
$processArguments = $arguments
$resolvedCodexCommand = Get-Command $CodexPath -ErrorAction SilentlyContinue
if ($null -ne $resolvedCodexCommand -and
    $resolvedCodexCommand.CommandType -eq "ExternalScript" -and
    $resolvedCodexCommand.Path.EndsWith(".ps1", [System.StringComparison]::OrdinalIgnoreCase)) {
    $codexBaseDirectory = Split-Path -Parent $resolvedCodexCommand.Path
    $localNodePath = Join-Path $codexBaseDirectory "node.exe"
    $codexJavaScriptPath = Join-Path $codexBaseDirectory "node_modules/@openai/codex/bin/codex.js"
    if (Test-Path -LiteralPath $localNodePath) {
        $processExecutable = $localNodePath
    } else {
        $nodeCommand = Get-Command node.exe -ErrorAction Stop
        $processExecutable = $nodeCommand.Source
    }
    $processArguments = @($codexJavaScriptPath) + $arguments
}

$commandRecord = [ordered]@{
    codex_path = $CodexPath
    arguments = $arguments
    process_executable = $processExecutable
    process_arguments = $processArguments
    run_directory = $resolvedRunDirectory
    prompt_path = $resolvedPromptPath
    working_directory = $resolvedWorkingDirectory
    model = $Model
    sandbox = $Sandbox
    approval_policy = $ApprovalPolicy
    timeout_seconds = $TimeoutSeconds
    use_oss = [bool]$UseOss
    local_provider = $LocalProvider
    json_events = [bool]$JsonEvents
    execute = [bool]$Execute
}

$commandRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $commandPath -Encoding UTF8

if (-not $Execute) {
    "" | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    "" | Set-Content -LiteralPath $stderrPath -Encoding UTF8
    "DRY_RUN" | Set-Content -LiteralPath $exitCodePath -Encoding UTF8
    "" | Set-Content -LiteralPath $lastMessagePath -Encoding UTF8
    "" | Set-Content -LiteralPath $eventStreamPath -Encoding UTF8
    $summary = [ordered]@{
        status = "DRY_RUN"
        exit_code = $null
        command_json = $commandPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        last_message = $lastMessagePath
        event_stream = $eventStreamPath
    }
    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Output ($summary | ConvertTo-Json -Depth 8)
    exit 0
}

try {
    $argumentString = ConvertTo-ProcessArgumentString -ArgumentList $processArguments
    $process = Start-Process `
        -FilePath $processExecutable `
        -ArgumentList $argumentString `
        -WorkingDirectory $resolvedWorkingDirectory `
        -RedirectStandardInput $promptCopyPath `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -NoNewWindow `
        -PassThru

    $completed = $process.WaitForExit($TimeoutSeconds * 1000)

    if (-not $completed) {
        Stop-ProcessTree -ProcessId $process.Id
        Start-Sleep -Seconds 1
    }

    $process.Refresh()
    if ($completed) {
        [string]$process.ExitCode | Set-Content -LiteralPath $exitCodePath -Encoding UTF8
    } else {
        "TIMEOUT" | Set-Content -LiteralPath $exitCodePath -Encoding UTF8
    }

    if ($JsonEvents) {
        $stdout = Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue
        $stdout | Set-Content -LiteralPath $eventStreamPath -Encoding UTF8
    } elseif (-not (Test-Path -LiteralPath $eventStreamPath)) {
        "" | Set-Content -LiteralPath $eventStreamPath -Encoding UTF8
    }

    if (-not (Test-Path -LiteralPath $lastMessagePath)) {
        "" | Set-Content -LiteralPath $lastMessagePath -Encoding UTF8
    }

    $stdout = Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue
    $stderr = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
    $lastMessage = Get-Content -LiteralPath $lastMessagePath -Raw -ErrorAction SilentlyContinue
    $lastMessagePresent = -not [string]::IsNullOrWhiteSpace($lastMessage)
    $stdoutPresent = -not [string]::IsNullOrWhiteSpace($stdout)
    $effectiveExitCode = if ($completed -and $null -ne $process.ExitCode) { [int]$process.ExitCode } else { $null }
    $artifactSuccess = $completed -and $null -eq $effectiveExitCode -and $lastMessagePresent -and $stdoutPresent
    $status = if (-not $completed) {
        "TIMEOUT"
    } elseif ($null -ne $effectiveExitCode) {
        if ($effectiveExitCode -eq 0) { "PASS" } else { "FAILED" }
    } elseif ($artifactSuccess) {
        "PASS"
    } else {
        "FAILED"
    }

    $summary = [ordered]@{
        status = $status
        exit_code = $effectiveExitCode
        timed_out = -not $completed
        timeout_seconds = $TimeoutSeconds
        artifact_success = $artifactSuccess
        last_message_present = $lastMessagePresent
        stdout_present = $stdoutPresent
        command_json = $commandPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        last_message = $lastMessagePath
        event_stream = $eventStreamPath
    }

    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Output ($summary | ConvertTo-Json -Depth 8)
    if ($completed -and $null -ne $effectiveExitCode) {
        exit $effectiveExitCode
    }
    if ($artifactSuccess) {
        exit 0
    }
    exit 124
} catch {
    $runnerError = $_ | Out-String
    "" | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    $runnerError | Set-Content -LiteralPath $stderrPath -Encoding UTF8
    "RUNNER_EXCEPTION" | Set-Content -LiteralPath $exitCodePath -Encoding UTF8
    "" | Set-Content -LiteralPath $lastMessagePath -Encoding UTF8
    "" | Set-Content -LiteralPath $eventStreamPath -Encoding UTF8

    $summary = [ordered]@{
        status = "RUNNER_EXCEPTION"
        exit_code = $null
        command_json = $commandPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        last_message = $lastMessagePath
        event_stream = $eventStreamPath
        error = $runnerError.Trim()
    }

    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Output ($summary | ConvertTo-Json -Depth 8)
    exit 1
}
