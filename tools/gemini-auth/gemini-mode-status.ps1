Clear-Host

$apiKey = [System.Environment]::GetEnvironmentVariable("GEMINI_API_KEY", "User")
$geminiModel = [System.Environment]::GetEnvironmentVariable("GEMINI_MODEL", "User")

Write-Host "AUTHENTIFIZIERUNGS- UND MODUS-STATUS"
Write-Host "------------------------------------"

if ($apiKey) {
    Write-Host "Aktiver Modus (konfiguriert): API-Key (kostenpflichtig)"
    Write-Host "  -> Die Gemini CLI wird versuchen, sich mit dem hinterlegten API-Key zu authentifizieren."
    Write-Host "  -> Konfiguriertes Modell fuer API-Key: $geminiModel"
    Write-Host "  -> WICHTIG: Ueberpruefen Sie Ihre Google Cloud Console fuer die tatsaechliche API-Nutzung und Kosten."
    Write-Host "  -> ACHTUNG: Das konfigurierte Modell kann durch das '--model'-Flag beim Start der Gemini CLI ueberschrieben werden."
    Write-Host "     Um sicherzustellen, dass 'gemini-2.5-flash' verwendet wird, starten Sie die CLI ohne explizites '--model'-Flag."
} else {
    Write-Host "Aktiver Modus (konfiguriert): Google-Login (OAuth) (kostenlos)"
    Write-Host "  -> Die Gemini CLI wird versuchen, sich ueber Ihr Google-Konto zu authentifizieren."
    Write-Host "  -> Standardmaessig startet die CLI mit 'gemini-2.5-pro' (kostenloses Kontingent)."
    Write-Host "  -> Bei Ueberschreitung des Kontingents oder hohem Traffic wechselt Google automatisch zu 'gemini-2.5-flash'."
    Write-Host "  -> WICHTIG: Bei jedem Neustart der Gemini CLI wird das Modell auf 'gemini-2.5-pro' zurueckgesetzt."
    Write-Host "  -> Das Modell kann auch durch Ihre lokalen '.gemini/settings.json' oder das '--model'-Flag beeinflusst werden."
}

# NEU: Abschliessende Statusmeldung
Write-Host "" # Leere Zeile
if ($apiKey) {
    Write-Host "Sie arbeiten ueber Ihren Key, die Arbeit ist kostenpflichtig!"
} else {
    Write-Host "Sie melden sich mit Auth an, Sie arbeiten kostenlos!"
}
Write-Host "Denken Sie daran, die Gemini CLI nach dem Wechsel neu zu starten, damit die Aenderungen wirksam werden."