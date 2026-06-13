param(
    [Parameter(Mandatory = $true)]
    [string]$RunDirectory,

    [Parameter(Mandatory = $true)]
    [string]$RequestBodyPath,

    [string]$Uri = "https://openrouter.ai/api/v1/chat/completions",
    [hashtable]$Headers = @{},
    [switch]$UseLocalFixture,
    [string]$LocalFixtureResponsePath = ""
)

$ErrorActionPreference = "Stop"

function Write-Artifact {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Value,
        [string]$Encoding = "utf8"
    )

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $Path -Value $Value -Encoding $Encoding
}

function Safe-JsonField {
    param(
        $Object,
        [string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

$runDir = [System.IO.Path]::GetFullPath($RunDirectory)
$requestPath = [System.IO.Path]::GetFullPath($RequestBodyPath)

if (-not (Test-Path $requestPath)) {
    throw "Request body path not found: $requestPath"
}

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$stdoutPath = Join-Path $runDir "stdout.log"
$stderrPath = Join-Path $runDir "stderr.log"
$exitCodePath = Join-Path $runDir "exit_code.txt"
$headersPath = Join-Path $runDir "response_headers.txt"
$bodyPath = Join-Path $runDir "response_body.json"
$summaryPath = Join-Path $runDir "response_summary.json"
$requestArtifactPath = Join-Path $runDir "request_body.json"

Copy-Item -LiteralPath $requestPath -Destination $requestArtifactPath -Force

$statusCode = $null
$responseHeaders = $null
$rawBody = ""
$summaryObject = $null

try {
    if ($UseLocalFixture) {
        if (-not $LocalFixtureResponsePath) {
            throw "UseLocalFixture requires LocalFixtureResponsePath"
        }
        $fixturePath = [System.IO.Path]::GetFullPath($LocalFixtureResponsePath)
        if (-not (Test-Path $fixturePath)) {
            throw "Local fixture response path not found: $fixturePath"
        }
        $statusCode = 200
        $responseHeaders = [ordered]@{
            "X-Capture-Mode" = "local_fixture"
            "Content-Type" = "application/json"
        }
        $rawBody = Get-Content -LiteralPath $fixturePath -Raw
    }
    else {
        $bodyJson = Get-Content -LiteralPath $requestPath -Raw
        $request = [System.Net.HttpWebRequest]::Create($Uri)
        $request.Method = "POST"
        $request.ContentType = "application/json"
        foreach ($key in $Headers.Keys) {
            switch -Regex ($key) {
                '^Authorization$' { $request.Headers['Authorization'] = [string]$Headers[$key] }
                '^HTTP-Referer$' { $request.Referer = [string]$Headers[$key] }
                '^User-Agent$' { $request.UserAgent = [string]$Headers[$key] }
                default { $request.Headers[$key] = [string]$Headers[$key] }
            }
        }
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)
        $request.ContentLength = $bytes.Length
        $requestStream = $request.GetRequestStream()
        try {
            $requestStream.Write($bytes, 0, $bytes.Length)
        }
        finally {
            $requestStream.Dispose()
        }

        try {
            $response = $request.GetResponse()
        }
        catch [System.Net.WebException] {
            if ($_.Exception.Response) {
                $response = $_.Exception.Response
            }
            else {
                throw
            }
        }

        try {
            $statusCode = [int]$response.StatusCode
            $responseHeaders = [ordered]@{}
            foreach ($name in $response.Headers.AllKeys) {
                $responseHeaders[$name] = $response.Headers[$name]
            }
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            try {
                $rawBody = $reader.ReadToEnd()
            }
            finally {
                $reader.Dispose()
            }
        }
        finally {
            $response.Dispose()
        }
    }

    Write-Artifact -Path $bodyPath -Value $rawBody
    Write-Artifact -Path $headersPath -Value (($responseHeaders | Out-String).Trim())

    $parsed = $rawBody | ConvertFrom-Json
    $usage = Safe-JsonField -Object $parsed -Name "usage"
    $summaryObject = [ordered]@{
        capture_mode = $(if ($UseLocalFixture) { "local_fixture" } else { "live_http" })
        http_status = $statusCode
        generation_id = Safe-JsonField -Object $parsed -Name "id"
        model = Safe-JsonField -Object $parsed -Name "model"
        usage = $usage
    }

    Write-Artifact -Path $summaryPath -Value ($summaryObject | ConvertTo-Json -Depth 20)
    Write-Artifact -Path $stdoutPath -Value "CAPTURE_OK`nrequest_body=$requestArtifactPath`nresponse_body=$bodyPath`nresponse_headers=$headersPath`nresponse_summary=$summaryPath"
    Write-Artifact -Path $stderrPath -Value ""
    Write-Artifact -Path $exitCodePath -Value "0" -Encoding "ascii"
}
catch {
    Write-Artifact -Path $stderrPath -Value ($_ | Out-String)
    if ($rawBody) {
        Write-Artifact -Path $bodyPath -Value $rawBody
    }
    if ($responseHeaders) {
        Write-Artifact -Path $headersPath -Value (($responseHeaders | Out-String).Trim())
    }
    Write-Artifact -Path $stdoutPath -Value "CAPTURE_FAILED`nrequest_body=$requestArtifactPath"
    Write-Artifact -Path $exitCodePath -Value "1" -Encoding "ascii"
    throw
}
