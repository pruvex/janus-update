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

    [string[]]$EditablePath = @(),

    [int]$MaxTouchedFiles = 0,

    [switch]$CaptureGitDiff,

    [switch]$FailOnDeleteRenameMove,

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

function Start-RedirectedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,

        [Parameter(Mandatory = $true)]
        [string]$PromptInputPath,

        [Parameter(Mandatory = $true)]
        [string]$StdoutPath,

        [Parameter(Mandatory = $true)]
        [string]$StderrPath
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    $startInfo.Arguments = ConvertTo-ProcessArgumentString -ArgumentList $ArgumentList

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()

    $stdoutWriter = [System.IO.StreamWriter]::new($StdoutPath, $false, [System.Text.Encoding]::UTF8)
    $stderrWriter = [System.IO.StreamWriter]::new($StderrPath, $false, [System.Text.Encoding]::UTF8)

    try {
        Get-Content -LiteralPath $PromptInputPath -Raw | ForEach-Object {
            $process.StandardInput.Write($_)
        }
        $process.StandardInput.Close()

        $stdoutTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutWriter.BaseStream)
        $stderrTask = $process.StandardError.BaseStream.CopyToAsync($stderrWriter.BaseStream)

        return [pscustomobject]@{
            Process = $process
            StdoutTask = $stdoutTask
            StderrTask = $stderrTask
            StdoutWriter = $stdoutWriter
            StderrWriter = $stderrWriter
        }
    } catch {
        $stdoutWriter.Dispose()
        $stderrWriter.Dispose()
        if (-not $process.HasExited) {
            try {
                $process.Kill($true)
            } catch {
            }
        }
        $process.Dispose()
        throw
    }
}

function Get-GitTextOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$GitArguments,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $raw = & git -C $WorkingDirectory @GitArguments 2>$null
    if ($LASTEXITCODE -ne 0) {
        return ""
    }
    if ($null -eq $raw) {
        return ""
    }
    return (($raw | Out-String).TrimEnd())
}

function Get-GitArrayOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$GitArguments,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $raw = & git -C $WorkingDirectory @GitArguments 2>$null
    if ($LASTEXITCODE -ne 0 -or $null -eq $raw) {
        return @()
    }
    if ($raw -is [System.Array]) {
        return @($raw)
    }
    return @([string]$raw)
}

function Write-FileUtf8 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Content
    )

    $Content | Set-Content -LiteralPath $Path -Encoding UTF8
}

$resolvedRunDirectory = [System.IO.Path]::GetFullPath($RunDirectory)
$resolvedPromptPath = [System.IO.Path]::GetFullPath($PromptPath)
$resolvedWorkingDirectory = [System.IO.Path]::GetFullPath($WorkingDirectory)

$normalizedEditablePaths = @()
foreach ($editableEntry in $EditablePath) {
    if ($null -eq $editableEntry) {
        continue
    }
    foreach ($splitEntry in ($editableEntry -split ",")) {
        $trimmedEntry = $splitEntry.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmedEntry)) {
            $normalizedEditablePaths += $trimmedEntry
        }
    }
}
$EditablePath = $normalizedEditablePaths

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
$editablePathsPath = Join-Path $resolvedRunDirectory "editable_paths.txt"
$preRunStatusPath = Join-Path $resolvedRunDirectory "pre_run_status.txt"
$postRunStatusPath = Join-Path $resolvedRunDirectory "post_run_status.txt"
$changedFilesPath = Join-Path $resolvedRunDirectory "changed_files.txt"
$gitDiffPath = Join-Path $resolvedRunDirectory "git_diff.patch"
$validationSummaryPath = Join-Path $resolvedRunDirectory "validation_summary.json"

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
if ($null -ne $resolvedCodexCommand) {
    if ($resolvedCodexCommand.CommandType -eq "ExternalScript" -and
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
    } elseif ($resolvedCodexCommand.Path) {
        $processExecutable = $resolvedCodexCommand.Path
    } elseif ($resolvedCodexCommand.Source) {
        $processExecutable = $resolvedCodexCommand.Source
    }
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
    editable_paths = $EditablePath
    max_touched_files = $MaxTouchedFiles
    capture_git_diff = [bool]$CaptureGitDiff
    fail_on_delete_rename_move = [bool]$FailOnDeleteRenameMove
    execute = [bool]$Execute
}

$commandRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $commandPath -Encoding UTF8
Write-FileUtf8 -Path $editablePathsPath -Content (($EditablePath | ForEach-Object { $_ }) -join [Environment]::NewLine)

$gitArtifactMode = ($Sandbox -eq "workspace-write") -or $CaptureGitDiff -or ($EditablePath.Count -gt 0) -or ($MaxTouchedFiles -gt 0) -or $FailOnDeleteRenameMove
$preRunStatus = ""
if ($gitArtifactMode) {
    $statusArgs = @("status", "--short", "--") + $EditablePath
    $preRunStatus = Get-GitTextOutput -GitArguments $statusArgs -WorkingDirectory $resolvedWorkingDirectory
}

if (-not $Execute) {
    "" | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    "" | Set-Content -LiteralPath $stderrPath -Encoding UTF8
    "DRY_RUN" | Set-Content -LiteralPath $exitCodePath -Encoding UTF8
    "" | Set-Content -LiteralPath $lastMessagePath -Encoding UTF8
    "" | Set-Content -LiteralPath $eventStreamPath -Encoding UTF8
    Write-FileUtf8 -Path $preRunStatusPath -Content $preRunStatus
    Write-FileUtf8 -Path $postRunStatusPath -Content $preRunStatus
    Write-FileUtf8 -Path $changedFilesPath -Content ""
    Write-FileUtf8 -Path $gitDiffPath -Content ""
    $dryRunValidationSummary = [ordered]@{
        status = "DRY_RUN"
        sandbox = $Sandbox
        editable_paths = $EditablePath
        touched_files = @()
        touched_file_count = 0
        max_touched_files = $MaxTouchedFiles
        deleted_paths = @()
        renamed_paths = @()
        moved_paths = @()
        allowlist_ok = $true
        touched_file_cap_ok = $true
        delete_rename_move_ok = $true
    }
    $dryRunValidationSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $validationSummaryPath -Encoding UTF8
    $summary = [ordered]@{
        status = "DRY_RUN"
        exit_code = $null
        command_json = $commandPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        last_message = $lastMessagePath
        event_stream = $eventStreamPath
        editable_paths = $editablePathsPath
        pre_run_status = $preRunStatusPath
        post_run_status = $postRunStatusPath
        changed_files = $changedFilesPath
        git_diff = $gitDiffPath
        validation_summary = $validationSummaryPath
    }
    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Output ($summary | ConvertTo-Json -Depth 8)
    exit 0
}

try {
    $startedProcess = Start-RedirectedProcess `
        -FilePath $processExecutable `
        -ArgumentList $processArguments `
        -WorkingDirectory $resolvedWorkingDirectory `
        -PromptInputPath $promptCopyPath `
        -StdoutPath $stdoutPath `
        -StderrPath $stderrPath

    $process = $startedProcess.Process
    $completed = $process.WaitForExit($TimeoutSeconds * 1000)

    if (-not $completed) {
        Stop-ProcessTree -ProcessId $process.Id
        Start-Sleep -Seconds 1
    }

    [System.Threading.Tasks.Task]::WaitAll(@($startedProcess.StdoutTask, $startedProcess.StderrTask))
    $startedProcess.StdoutWriter.Dispose()
    $startedProcess.StderrWriter.Dispose()

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

    $postRunStatus = ""
    $changedFiles = @()
    $deletedPaths = @()
    $renamedPaths = @()
    $movedPaths = @()
    $allowlistOk = $true
    $touchedFileCapOk = $true
    $deleteRenameMoveOk = $true

    if ($gitArtifactMode) {
        $statusArgs = @("status", "--short", "--") + $EditablePath
        $postRunStatus = Get-GitTextOutput -GitArguments $statusArgs -WorkingDirectory $resolvedWorkingDirectory

        $nameOnlyArgs = @("diff", "--name-only", "--") + $EditablePath
        $changedFiles = Get-GitArrayOutput -GitArguments $nameOnlyArgs -WorkingDirectory $resolvedWorkingDirectory |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

        $nameStatusArgs = @("diff", "--name-status", "--") + $EditablePath
        $nameStatusLines = Get-GitArrayOutput -GitArguments $nameStatusArgs -WorkingDirectory $resolvedWorkingDirectory

        foreach ($line in $nameStatusLines) {
            $trimmed = $line.Trim()
            if ([string]::IsNullOrWhiteSpace($trimmed)) {
                continue
            }
            $parts = $trimmed -split "\s+"
            if ($parts.Count -lt 2) {
                continue
            }
            $statusCode = $parts[0]
            if ($statusCode -eq "D") {
                $deletedPaths += $parts[1]
            } elseif ($statusCode.StartsWith("R")) {
                if ($parts.Count -ge 3) {
                    $renamedPaths += ($parts[1] + " -> " + $parts[2])
                } else {
                    $renamedPaths += $parts[1]
                }
            }
        }

        $statusChangeLines = @()
        if (-not [string]::IsNullOrWhiteSpace($postRunStatus)) {
            $statusChangeLines = $postRunStatus -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        }

        foreach ($statusLine in $statusChangeLines) {
            if ($statusLine.Length -lt 4) {
                continue
            }
            $pathText = $statusLine.Substring(3).Trim()
            if ($pathText -like "* -> *") {
                $movedPaths += $pathText
            }
        }

        if ($EditablePath.Count -gt 0) {
            foreach ($changedFile in $changedFiles) {
                $normalizedChanged = $changedFile.Replace("\", "/")
                $matched = $false
                foreach ($allowedPath in $EditablePath) {
                    $normalizedAllowed = $allowedPath.Replace("\", "/").Trim()
                    if ([string]::IsNullOrWhiteSpace($normalizedAllowed)) {
                        continue
                    }
                    if ($normalizedChanged -eq $normalizedAllowed -or $normalizedChanged.StartsWith($normalizedAllowed.TrimEnd("/") + "/")) {
                        $matched = $true
                        break
                    }
                }
                if (-not $matched) {
                    $allowlistOk = $false
                    break
                }
            }
        }

        if ($MaxTouchedFiles -gt 0 -and $changedFiles.Count -gt $MaxTouchedFiles) {
            $touchedFileCapOk = $false
        }

        if ($FailOnDeleteRenameMove -and (($deletedPaths.Count -gt 0) -or ($renamedPaths.Count -gt 0) -or ($movedPaths.Count -gt 0))) {
            $deleteRenameMoveOk = $false
        }

        $diffArgs = @("diff", "--binary", "--") + $EditablePath
        $diffText = Get-GitTextOutput -GitArguments $diffArgs -WorkingDirectory $resolvedWorkingDirectory
        Write-FileUtf8 -Path $gitDiffPath -Content $diffText
    } else {
        Write-FileUtf8 -Path $gitDiffPath -Content ""
    }

    Write-FileUtf8 -Path $preRunStatusPath -Content $preRunStatus
    Write-FileUtf8 -Path $postRunStatusPath -Content $postRunStatus
    Write-FileUtf8 -Path $changedFilesPath -Content (($changedFiles | ForEach-Object { $_ }) -join [Environment]::NewLine)

    $validationSummary = [ordered]@{
        status = "PASS"
        sandbox = $Sandbox
        editable_paths = $EditablePath
        touched_files = $changedFiles
        touched_file_count = $changedFiles.Count
        max_touched_files = $MaxTouchedFiles
        deleted_paths = $deletedPaths
        renamed_paths = $renamedPaths
        moved_paths = $movedPaths
        allowlist_ok = $allowlistOk
        touched_file_cap_ok = $touchedFileCapOk
        delete_rename_move_ok = $deleteRenameMoveOk
    }
    $validationSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $validationSummaryPath -Encoding UTF8

    $stdout = Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue
    $stderr = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
    $lastMessage = Get-Content -LiteralPath $lastMessagePath -Raw -ErrorAction SilentlyContinue
    $lastMessagePresent = -not [string]::IsNullOrWhiteSpace($lastMessage)
    $stdoutPresent = -not [string]::IsNullOrWhiteSpace($stdout)
    $effectiveExitCode = if ($completed -and $null -ne $process.ExitCode) { [int]$process.ExitCode } else { $null }
    $artifactSuccess = $completed -and $effectiveExitCode -eq 0 -and $lastMessagePresent -and $stdoutPresent
    if (-not $allowlistOk -or -not $touchedFileCapOk -or -not $deleteRenameMoveOk) {
        $artifactSuccess = $false
        $validationSummary.status = "FAILED"
        $validationSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $validationSummaryPath -Encoding UTF8
    }
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
        editable_paths = $editablePathsPath
        pre_run_status = $preRunStatusPath
        post_run_status = $postRunStatusPath
        changed_files = $changedFilesPath
        git_diff = $gitDiffPath
        validation_summary = $validationSummaryPath
        allowlist_ok = $allowlistOk
        touched_file_cap_ok = $touchedFileCapOk
        delete_rename_move_ok = $deleteRenameMoveOk
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
    Write-FileUtf8 -Path $preRunStatusPath -Content $preRunStatus
    Write-FileUtf8 -Path $postRunStatusPath -Content ""
    Write-FileUtf8 -Path $changedFilesPath -Content ""
    Write-FileUtf8 -Path $gitDiffPath -Content ""
    $exceptionValidationSummary = [ordered]@{
        status = "RUNNER_EXCEPTION"
        sandbox = $Sandbox
        editable_paths = $EditablePath
        touched_files = @()
        touched_file_count = 0
        max_touched_files = $MaxTouchedFiles
        deleted_paths = @()
        renamed_paths = @()
        moved_paths = @()
        allowlist_ok = $false
        touched_file_cap_ok = $false
        delete_rename_move_ok = $false
    }
    $exceptionValidationSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $validationSummaryPath -Encoding UTF8

    $summary = [ordered]@{
        status = "RUNNER_EXCEPTION"
        exit_code = $null
        command_json = $commandPath
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        last_message = $lastMessagePath
        event_stream = $eventStreamPath
        editable_paths = $editablePathsPath
        pre_run_status = $preRunStatusPath
        post_run_status = $postRunStatusPath
        changed_files = $changedFilesPath
        git_diff = $gitDiffPath
        validation_summary = $validationSummaryPath
        error = $runnerError.Trim()
    }

    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Output ($summary | ConvertTo-Json -Depth 8)
    exit 1
}
