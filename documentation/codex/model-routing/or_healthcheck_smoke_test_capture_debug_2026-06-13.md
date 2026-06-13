# OR Healthcheck Smoke-Test Capture Debug - 2026-06-13

Status: DEBUG ONLY / NO NEW OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

This note debugs the shell-side capture path used for the single approved OR telemetry smoke test for:

- `DOC-SKILL-008`
- `qwen/qwen3.5-flash-02-23`

It does not execute another OR call. It only explains why the first call's response body, `generation_id`, and `response_usage` were not recoverable through the shell/tool path.

## Bound Inputs Reviewed

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/or_healthcheck_controlled_smoke_test_result_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_debug_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_controlled_smoke_test_plan_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_plan_2026-06-13.md`
- `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`
- the shell command pattern used for the smoke test

## Likely Root Cause

The most likely failure was the capture design, not the call authorization gate:

1. The smoke test relied on shell-returned stdout as the primary recovery path for the response object.
2. The command did not persist raw response artifacts to local files before returning control.
3. The command used `Invoke-RestMethod`, which is convenient for parsed JSON but is a weak fit when the real goal is durable forensic capture of:
   - raw body
   - response headers
   - status code
   - stderr
   - parsed usage block
   - parsed `generation_id`
4. Because no file-backed capture happened first, a shell/tool transport gap left the run with:
   - no recoverable response body
   - no recoverable `generation_id`
   - no recoverable `response_usage`

## Contributing Factors

### Tool-stdout was treated as storage

The command tried to return the response object through the shell tool instead of writing the response to disk first. That is fragile for a smoke test because the tool channel is good for operator summaries, not for being the only durable evidence path.

### No raw response artifact existed

The command did not first write:

- raw body JSON
- response headers
- parsed summary JSON
- stdout log
- stderr log
- exit code

Without those files, later reconciliation had nothing local to inspect.

### `Invoke-RestMethod` was not capture-oriented

`Invoke-RestMethod` parses JSON automatically, but unless extra variables or explicit file writes are added, it does not by itself guarantee a durable capture package. For a telemetry smoke test we need the opposite priority:

- preserve transport evidence first
- parse second
- summarize third

## Why `generation_id` And `response_usage` Were Lost

`generation_id` and usage are usually inside the response body. Once the raw body was not recoverable, these fields were lost with it. The previous fallback debug row therefore correctly left:

- `generation_id=""`
- `usage_source="fallback_estimate"`

That debug row should remain marked as debug failure evidence only.

## Capture-Safe Pattern

Use a file-first capture wrapper. The wrapper should always persist artifacts locally before trying to print a summary back to the shell.

Recommended artifact set per smoke-test run:

- `request_body.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `response_headers.txt`
- `response_body.json`
- `response_summary.json`

Recommended PowerShell pattern:

```powershell
$ErrorActionPreference = 'Stop'

$runDir = 'C:\KI\Janus-Projekt\documentation\codex\model-routing\smoke-test-capture\OR-SMOKE-2026-06-13-DOC-SKILL-008-001'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$requestPath = Join-Path $runDir 'request_body.json'
$stdoutPath = Join-Path $runDir 'stdout.log'
$stderrPath = Join-Path $runDir 'stderr.log'
$exitCodePath = Join-Path $runDir 'exit_code.txt'
$headersPath = Join-Path $runDir 'response_headers.txt'
$bodyPath = Join-Path $runDir 'response_body.json'
$summaryPath = Join-Path $runDir 'response_summary.json'

$bodyObject = @{
  model = 'qwen/qwen3.5-flash-02-23'
  messages = $messages
  temperature = 0
  max_tokens = 1200
}

$bodyJson = $bodyObject | ConvertTo-Json -Depth 20
Set-Content -Path $requestPath -Value $bodyJson -Encoding UTF8

$headers = @{
  Authorization = "Bearer $env:OPENROUTER_API_KEY"
  'Content-Type' = 'application/json'
  'HTTP-Referer' = 'https://janus.local'
  'X-OpenRouter-Title' = 'Janus Codex OR Telemetry Smoke Test'
}

try {
  $responseHeaders = $null
  $statusCode = $null
  $raw = Invoke-WebRequest `
    -Method Post `
    -Uri 'https://openrouter.ai/api/v1/chat/completions' `
    -Headers $headers `
    -Body $bodyJson `
    -ResponseHeadersVariable responseHeaders `
    -StatusCodeVariable statusCode `
    -SkipHttpErrorCheck

  $raw.Content | Set-Content -Path $bodyPath -Encoding UTF8
  ($responseHeaders | Out-String) | Set-Content -Path $headersPath -Encoding UTF8
  '0' | Set-Content -Path $exitCodePath -Encoding ASCII

  $parsed = $raw.Content | ConvertFrom-Json
  $summary = [ordered]@{
    http_status = $statusCode
    generation_id = $parsed.id
    model = $parsed.model
    usage = $parsed.usage
  }
  $summary | ConvertTo-Json -Depth 20 | Set-Content -Path $summaryPath -Encoding UTF8

  "CAPTURE_OK body=$bodyPath headers=$headersPath summary=$summaryPath" |
    Set-Content -Path $stdoutPath -Encoding UTF8
}
catch {
  ($_ | Out-String) | Set-Content -Path $stderrPath -Encoding UTF8
  if ($null -eq $LASTEXITCODE) { '1' | Set-Content -Path $exitCodePath -Encoding ASCII }
  else { "$LASTEXITCODE" | Set-Content -Path $exitCodePath -Encoding ASCII }
  throw
}
```

## Why This Pattern Is Safer

- stdout is no longer the only evidence path
- stderr is explicitly persisted
- exit code is explicitly persisted
- response headers are persisted separately
- raw body is preserved even if later parsing fails
- `generation_id` and `usage` are parsed from the saved body, not from a transient shell return

## Minimal Operator Summary Pattern

After file capture succeeds, only print a short shell summary such as:

```text
CAPTURE_OK
- exit_code: 0
- body: <path>
- headers: <path>
- summary: <path>
```

The shell tool should carry only the compact summary. The forensic data should live in files.

## Expected Fallback Behavior

If response body is missing:

- mark the run `debug failure evidence only`
- leave `generation_id` empty
- set `usage_source=fallback_estimate`
- do not treat the row as accepted operational telemetry

If body exists but usage is missing:

- preserve the body file
- try to recover `generation_id`
- parse usage if present later
- if usage still remains unavailable, use the documented fallback-estimate path
- keep the row non-operational until the smoke-test acceptance rule is satisfied

If body exists and usage exists:

- parse `usage.prompt_tokens`
- parse `usage.completion_tokens`
- parse `usage.cost`
- parse reasoning/cached token details if present
- promote the row from debug-only evidence to accepted telemetry only if all other smoke-test gates also pass

## Conclusion

The likely root cause was a shell-capture design gap: the smoke test tried to recover important OpenRouter fields from transient shell output instead of persisting raw response artifacts first. Future smoke-test execution should use a file-first capture wrapper so response body, headers, usage, and `generation_id` survive even if shell output transport is incomplete.
