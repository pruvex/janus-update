AGENTIC HANDLUNGSPLAN:
Dein Ziel: Korrigiere den ReferenceError: document is not defined-Fehler, indem du eine saubere Trennung zwischen dem "Main Process" und dem "Renderer Process" herstellst.
Relevante PHASE_X.md: C:\KI\Janus-Projekt\PHASE_1_FUNDAMENT.md
# Schritt-für-Schritt-Anweisungen:
Kontextbeschaffung/Analyse: Verifiziere, dass im frontend-Verzeichnis die index.html und die main.js existieren, aber wahrscheinlich noch keine main.electron.js (oder ähnliches) und keine package.json.
Implementierung/Modifikation (Die package.json erstellen): Erstelle die C:\KI\Janus-Projekt\frontend\package.json-Datei. Sie ist das Herzstück.
code
Code
'''
{
  "name": "janus-frontend",
  "version": "1.0.0",
  "description": "Frontend for Janus",
  "main": "main.electron.js",
  "scripts": {
    "start": "electron ."
  },
  "devDependencies": {
    "electron": "^28.0.0"
  }
}
'''
Wichtige Zeile: "main": "main.electron.js" sagt Electron: "Das ist die Datei, die du im Main Process laden sollst."
Implementierung/Modifikation (Den Main Process erstellen): Erstelle die Datei C:\KI\Janus-Projekt\frontend\main.electron.js, die das Fenster erstellt.
code
Code
'''
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
  });

  // Lade die index.html in das Fenster.
  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);
'''
Implementierung/Modifikation (index.html anpassen): Modifiziere die C:\KI\Janus-Projekt\frontend\index.html, um unsere andere main.js (die mit der document-Logik) im Renderer Process zu laden.
Ändere <script src="main.js"></script> zu <script src="main.js" defer></script>.
Installation & Test (Übergabe an Supervisor):
Pausiere den Plan: Gib die Meldung aus: `Die Electron-Struktur wurde korrigiert. Bitte führen Sie die finalen Schritte durch:
Führen Sie im 'frontend'-Verzeichnis 'npm install' aus.
Führen Sie danach im 'frontend'-Verzeichnis 'npm start' aus.
Berichten Sie das Ergebnis.`