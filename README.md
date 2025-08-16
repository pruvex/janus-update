# Janus - Souveräner KI-Desktop-Assistent
Janus ist ein lokaler KI-Assistent für den Desktop, der als "Bring Your Own Key" (BYOK) Anwendung konzipiert ist. Er gibt dem Benutzer die volle Kontrolle über seine Daten, Kosten und die Wahl der KI-Anbieter.

## Architektur & Technologie-Stack
- **Desktop Framework:** Electron
- **Frontend:** Vanilla JavaScript (ESM), HTML, CSS
- **Backend:** Python mit FastAPI
- **Build-System:** Vite für das Frontend und die Electron-Prozesse
- **Paket-Manager:** npm Workspaces (Root-Projekt + `frontend`-Workspace)
- **Datenbank:** SQLite für das Kosten-Tracking

## Projektstruktur
- **/backend:** Enthält den gesamten Python/FastAPI-Code.
  - **/venv:** Die virtuelle Python-Umgebung.
- **/frontend:** Enthält den gesamten Frontend-Code (HTML, CSS, JS).
  - **/node_modules:** Node.js-Abhängigkeiten für das Frontend.
- **/tools:** Enthält Hilfsskripte (z.B. für die Authentifizierung).
- **/waechter:** Enthält die Test-Suiten (Backend-Tests und E2E-Tests).
- **`package.json` (Root):** Definiert die Projektstruktur, Entwicklungs-Abhängigkeiten und die zentralen `npm`-Skripte.

## Installation
1.  **Klone das Repository:**
    ```bash
    git clone [URL_DES_REPOSITORIES]
    cd Janus-Projekt
    ```
2.  **Richte die Python-Umgebung ein:**
    ```bash
    python -m venv backend/venv
    # Windows
    backend\venv\Scripts\activate
    # macOS/Linux
    source backend/venv/bin/activate
    ```
3.  **Installiere die Python-Abhängigkeiten:**
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Installiere die Node.js-Abhängigkeiten:**
    (Dieser Befehl installiert die Abhängigkeiten im Root und im `frontend`-Workspace)
    ```bash
    npm install
    ```

## Anwendung starten (Entwicklungsmodus)
Um die Anwendung im Entwicklungsmodus mit Hot-Reload für Frontend und Backend zu starten, führe den folgenden Befehl im Hauptverzeichnis aus:
```bash
npm run start-dev
```
Dieser Befehl startet parallel:
- Den Vite-Dev-Server für das Frontend.
- Den Electron-Hauptprozess (der nach dem Vite-Build automatisch startet).
- Den FastAPI/Uvicorn-Server für das Backend.

## Tests ausführen
**Backend-Tests:**
```bash
# Stelle sicher, dass die venv aktiviert ist
pytest backend/
```
**End-to-End-Tests:**
```bash
npm run test:e2e
```
