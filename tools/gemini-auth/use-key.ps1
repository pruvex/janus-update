$envPath = "$HOME\.gemini\.env"
$disabledEnvPath = "$HOME\.gemini\.env.disabled"

# Prüfen, ob die .env.disabled-Datei existiert und umbenennen
if (Test-Path $disabledEnvPath) {
    try {
        Move-Item -Path $disabledEnvPath -Destination $envPath -Force
        Write-Host "Datei '$disabledEnvPath' wurde in '$envPath' umbenannt."
    } catch {
        Write-Error "Fehler beim Umbenennen von '$disabledEnvPath' zu '$envPath': $($_.Exception.Message)"
        exit 1
    }
}

# API-Key aus der (nun aktiven) .env-Datei lesen
if (Test-Path $envPath) {
    $keyLine = Get-Content -Path $envPath | Where-Object { $_ -match "^GEMINI_API_KEY=" }

    if (-not $keyLine) {
        Write-Host "Kein API-Key in $envPath gefunden."
        exit 1
    }

    # Den tatsächlichen API-Key-Wert extrahieren
    $apiKey = $keyLine -replace "GEMINI_API_KEY=", ""

    [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $apiKey, "User")
    # NEU: Setze das Modell auf gemini-2.5-flash, wenn der API-Key aktiv ist
    [System.Environment]::SetEnvironmentVariable("GEMINI_MODEL", "gemini-2.5-flash", "User")
    Write-Host "API-Key aktiviert und Modell auf 'gemini-2.5-flash' gesetzt."
} else {
    Write-Host "Weder '$envPath' noch '$disabledEnvPath' gefunden. Bitte stellen Sie sicher, dass eine der Dateien existiert."
    exit 1
}