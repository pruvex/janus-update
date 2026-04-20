$envPath = "$HOME\.gemini\.env"
$disabledEnvPath = "$HOME\.gemini\.env.disabled"

# Prüfen, ob die .env-Datei existiert und umbenennen
if (Test-Path $envPath) {
    try {
        Move-Item -Path $envPath -Destination $disabledEnvPath -Force
        Write-Host "Datei '$envPath' wurde in '$disabledEnvPath' umbenannt."
    } catch {
        Write-Error "Fehler beim Umbenennen von '$envPath' zu '$disabledEnvPath': $($_.Exception.Message)"
        exit 1
    }
}

[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $null, "User")
# NEU: Setze das Modell auf null, wenn der API-Key deaktiviert wird
[System.Environment]::SetEnvironmentVariable("GEMINI_MODEL", $null, "User")
Write-Host "API-Key deaktiviert (Google-Login aktiviert) und Modell zurückgesetzt."