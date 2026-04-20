param(
    [ValidateSet("smoke", "range", "openworld", "gate")]
    [string]$Mode = "smoke",
    [string]$Range = "",
    [string]$Image = "",
    [string]$MatrixDir = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Evaluator {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetMatrix,
        [string]$TargetRange,
        [string]$TargetImage,
        [switch]$KpiGate
    )

    $args = @("backend/tests/tools/vision_evaluator.py", "--matrix-dir", $TargetMatrix, "--e2e")
    if ($KpiGate) {
        $args += @("--kpi-gate", "--max-contradiction-rate", "0.0", "--min-source-map-coverage", "0.95")
    }
    if ($TargetRange) {
        $args += @("--range", $TargetRange)
    }
    if ($TargetImage) {
        $args += @("--image", $TargetImage)
    }

    Write-Host "Running: python $($args -join ' ')" -ForegroundColor Cyan
    & python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Vision evaluator failed with exit code $LASTEXITCODE"
    }
}

switch ($Mode) {
    "smoke" {
        Invoke-Evaluator -TargetMatrix "backend/tests/vision_matrix/Stresstest" -TargetImage "9.jpg" -KpiGate
    }
    "range" {
        if (-not $MatrixDir) {
            throw "For mode=range, set -MatrixDir."
        }
        if (-not $Range) {
            throw "For mode=range, set -Range (example: 1-10)."
        }
        Invoke-Evaluator -TargetMatrix $MatrixDir -TargetRange $Range -KpiGate
    }
    "openworld" {
        Invoke-Evaluator -TargetMatrix "backend/tests/vision_matrix/OpenWorldStandard" -KpiGate
    }
    "gate" {
        # Full gate (token-intensive). Use after smoke/range validation.
        Invoke-Evaluator -TargetMatrix "backend/tests/vision_matrix/Stresstest" -KpiGate
        Invoke-Evaluator -TargetMatrix "backend/tests/vision_matrix/OpenWorldStandard" -KpiGate
    }
}

Write-Host "Done." -ForegroundColor Green
