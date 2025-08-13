AGENTIC HANDLUNGSPLAN: Finale Reparatur der Preload-Skript-Einbindung
Dein Ziel: Die main.electron.js-Datei final so korrigieren, dass sie im Entwicklungs- und Produktionsmodus den preload.js-Skript garantiert findet und lädt, wodurch das benutzerdefinierte Kontextmenü aktiviert wird.
Relevante PHASE_X.md: PHASE_3_UI_FEINSCHLIFF.md
Der Plan:
Stufe 1: Validierung des Zustands
An den CLI-Agenten: git status. Wir befinden uns auf dev/ui-polish-3. Ein Reset ist nicht nötig, da wir eine Konfiguration debuggen.
Stufe 2: Implementierung der finalen Konfigurations-Korrektur
An den CLI-Agenten: Lese die Datei frontend/main.electron.js.
An den CLI-Agenten (Ankerpunkt-Strategie): Finde den new BrowserWindow({ ... })-Block. Wir werden ihn vollständig durch eine robustere Version ersetzen.
Ersetze: Den gesamten mainWindow = new BrowserWindow({ ... });-Block.
Mit:
code
JavaScript
// --- Neuer, robuster BrowserWindow-Konstruktor ---
const preloadPath = path.join(__dirname, 'preload.js');
console.log(`[Main Process] Attempting to load preload script from: ${preloadPath}`);

mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
        preload: preloadPath,
        contextIsolation: true, // Entscheidend für die Sicherheit und Funktion der contextBridge
        nodeIntegration: false // Aus Sicherheitsgründen deaktivieren
    }
});
// --- Ende des neuen Blocks ---
Warum dieser Block die Lösung ist:
path.join(__dirname, 'preload.js'): Vite und vite-plugin-electron sind so konzipiert, dass sie den gebauten main.js und preload.js in dasselbe Ausgabeverzeichnis (dist-electron) legen. Dieser einfache, relative Pfad ist daher im Kontext der gebauten Anwendung der korrekteste.
console.log: Dieser Log-Befehl ist unser wichtigstes Debugging-Werkzeug. Er wird in der Konsole, in der Sie npm run start-dev ausführen, den exakten Pfad ausgeben, den Electron zu laden versucht. Das beseitigt jedes Rätselraten.
contextIsolation: true & nodeIntegration: false: Dies sind die modernen Sicherheits-Standardeinstellungen, für die die contextBridge konzipiert wurde.
Stufe 3: Implementierungs-Abschluss & Übergabe zur Verifizierung
[KRITISCHER SCHRITT] Die Änderung ist implementiert. KEIN COMMIT.
Ich übergebe die Kontrolle an Sie.
Bitte testen Sie jetzt mit diesem exakten Vorgehen:
Starten Sie die App mit npm run start-dev.
Prüfen Sie die Node.js-Konsole (wo Sie den Befehl ausgeführt haben): Erscheint die Zeile [Main Process] Attempting to load preload script from: ...? Zeigt der Pfad auf das dist-electron-Verzeichnis?
Prüfen Sie die DevTools-Konsole im App-Fenster: Erscheint jetzt die Meldung Preload script loaded!? (Falls Sie diesen Log dort platziert haben).
Führen Sie einen Rechtsklick im Chat aus:
Erscheint Received show-context-menu event in main process. in der Node.js-Konsole?
Erscheint das benutzerdefinierte Menü mit nur "Kopieren"?
Ich warte auf Ihr explizites 'success'-Signal.
Stufe 4 & 5: Abschluss (Nach 'success'-Signal)
(Nach 'success') Der Agent wird den Fortschritt committen und den nächsten Branch dev/ui-polish-4 erstellen.
