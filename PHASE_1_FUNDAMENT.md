# PHASE 1: Das Stabile Fundament & "Hello World"

*Ziel: Am Ende dieser Phase haben wir ein leeres, aber startbares Anwendungs-Skelett. Ein Klick auf einen Knopf im Frontend sendet eine Anfrage an das Backend, und die Antwort wird im Frontend angezeigt. Das System ist stabil und versioniert.*

- [x] **[INFRASTRUKTUR] Git-Repository initialisieren:** Den `git init`-Befehl ausführen, um das Repository von Grund auf neu zu erstellen.

- [x] **[INFRASTRUKTUR] .gitignore-Datei erstellen:** Eine saubere, umfassende `.gitignore`-Datei anlegen, die alle temporären Artefakte (wie `node_modules`, `venv`, `dist`, `target`) ignoriert.

- [x] **[INFRASTRUKTUR] Projektstruktur anlegen:** Die leere Goldstandard-Struktur (`backend`, `janus`, `waechter` und deren Unterordner) erstellen.

- [x] **[INFRASTRUKTUR] Immunsystem anpassen (`health_check.py`):** Das existierende Skript anpassen, sodass es die vollständige, tiefe Goldstandard-Struktur (inkl. Unterordnern) überprüft.

- [ ] **[INFRASTRUKTUR] Frontend-Setup (Tauri & Vite):**
    - Eine saubere `package.json` basierend auf der recherchierten Blaupause erstellen.
    - `npm install` ausführen, um eine `package-lock.json` zu erzeugen.
    - Eine saubere `tauri.conf.json` und `vite.config.ts` erstellen und konfigurieren.

- [ ] **[INFRASTRUKTUR] Backend-Setup (Python & FastAPI):**
    - Die `venv` erstellen.
    - Eine `requirements.in`-Datei erstellen und daraus eine `requirements.txt` kompilieren.
    - Die Abhängigkeiten installieren.

- [ ] **[JANUS] "Hello World"-API-Endpunkt:** Im Backend einen `/api/health`-Endpunkt erstellen.

- [ ] **[WÄCHTER] "Hello World"-Test:** Einen Wächter-Test schreiben, der den `/api/health`-Endpunkt aufruft.

- [ ] **[JANUS] "Hello World"-UI:** Im Frontend eine simple `index.html` mit einem Knopf und einem Ausgabebereich erstellen.

- [ ] **[JANUS] Frontend mit Backend verbinden:** Ein Klick auf den Knopf ruft den `/api/health`-Endpunkt auf und zeigt die Antwort an.

- [ ] **[GIT] Stabilitäts-Commit:** Den funktionierenden "Hello World"-Zustand als ersten, goldenen Commit festhalten.