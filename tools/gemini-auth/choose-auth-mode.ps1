Clear-Host
Write-Host @"
AUTHENTIFIZIERUNGSMODUS WÄHLEN
----------------------------------
[1] API-Key aktivieren (kostenpflichtig)
[2] Google-Login aktivieren (kostenlos)
[3] Aktiven Modus und Modell anzeigen
[4] Beenden
"@

$wahl = Read-Host "Bitte Option eingeben (1-4)"

switch ($wahl) {
    "1" {
        $scriptPath = Join-Path $PSScriptRoot "use-key.ps1"
        if (Test-Path $scriptPath) {
            try {
                & $scriptPath
            } catch {
                Write-Error @"
Fehler beim Ausführen von use-key.ps1: $($_.Exception.Message)
"@
            }
        } else {
            Write-Error @"
Skript use-key.ps1 nicht gefunden unter: $scriptPath
"@
        }
        # NEU: Status nach Auswahl anzeigen
        $statusScriptPath = Join-Path $PSScriptRoot "gemini-mode-status.ps1"
        if (Test-Path $statusScriptPath) {
            try {
                Write-Host "`n--- Aktueller Authentifizierungs- und Modus-Status ---"
                & $statusScriptPath
            } catch {
                Write-Error @"
Fehler beim Anzeigen des Status: $($_.Exception.Message)
"@
            }
        } else {
            Write-Error @"
Status-Skript gemini-mode-status.ps1 nicht gefunden unter: $statusScriptPath
"@
        }
    }
    "2" {
        $scriptPath = Join-Path $PSScriptRoot "use-auth.ps1"
        if (Test-Path $scriptPath) {
            try {
                & $scriptPath
            }
            catch {
                Write-Error @"
Fehler beim Ausführen von use-auth.ps1: $($_.Exception.Message)
"@
            }
        } else {
            Write-Error @"
Skript use-auth.ps1 nicht gefunden unter: $scriptPath
"@
        }
        # NEU: Status nach Auswahl anzeigen
        $statusScriptPath = Join-Path $PSScriptRoot "gemini-mode-status.ps1"
        if (Test-Path $statusScriptPath) {
            try {
                Write-Host "`n--- Aktueller Authentifizierungs- und Modus-Status ---"
                & $statusScriptPath
            } catch {
                Write-Error @"
Fehler beim Anzeigen des Status: $($_.Exception.Message)
"@
            }
        } else {
            Write-Error @"
Status-Skript gemini-mode-status.ps1 nicht gefunden unter: $statusScriptPath
"@
            }
    }
    "3" {
        $scriptPath = Join-Path $PSScriptRoot "gemini-mode-status.ps1"
        if (Test-Path $scriptPath) {
            try {
                & $scriptPath
            } catch {
                Write-Error @"
Fehler beim Ausführen von gemini-mode.ps1: $($_.Exception.Message)
"@
            }
        } else {
            Write-Error @"
Skript gemini-mode.ps1 nicht gefunden unter: $scriptPath
"@
        }
    }
    "4" {
        Write-Host @"
Beendet.
"@
    }
    default {
        Write-Host @"
Ungueltige Eingabe. Bitte eine Zahl zwischen 1 und 4 eingeben.
"@
    }
}