# FEATURE_INSTALLER.md - Plan zur Erstellung eines Janus Installers (Überarbeitet)

## 1. Ziel
Erstellung eines benutzerfreundlichen, selbstinstallierenden `.exe`-Pakets für Windows, das die gesamte Janus-Anwendung (Frontend, Python Backend und alle Abhängigkeiten) bündelt. Ziel ist es, die Installation für technisch weniger versierte Nutzer zu vereinfachen.

## 2. Schlüsselüberlegungen & Designprinzipien

### 2.1. Sicherheit (API-Schlüssel)
*   **Problem:** API-Schlüssel dürfen nicht direkt im gebündelten Code oder in der ausführbaren Datei enthalten sein.
*   **Lösung:** Die bestehende `keyring`-Nutzung im Backend wird beibehalten. Es muss sichergestellt werden, dass `keyring` auch in der gebündelten Umgebung korrekt funktioniert und die Schlüssel sicher im Betriebssystem-Schlüsselspeicher abgelegt werden.
*   **Erster Start:** Beim ersten Start der Anwendung muss der Nutzer aufgefordert werden, seine API-Schlüssel einzugeben.

### 2.2. Dateisystemstruktur & Persistenz
*   **Problem:** Datenbank (`janus.db`), Konfigurationsdateien (`config.json`) und gespeicherte Bilder (`backend/static/images/`) dürfen nicht im Installationsverzeichnis (z.B. `C:\Program Files\Janus`) abgelegt werden, da dieses oft Schreibrechte erfordert und bei Updates überschrieben werden könnte.
*   **Lösung:** Diese Daten müssen in einem benutzerspezifischen Anwendungsdatenverzeichnis gespeichert werden (z.B. `C:\Users\<User>\AppData\Roaming\Janus` unter Windows).
    *   **Datenbank:** `janus.db`
    *   **Konfiguration:** `config.json` (als Vorlage im Bundle, Kopie in AppData)
    *   **Bilder:** Ein Unterverzeichnis für Bilder (z.B. `images/`)
    *   **Logs:** Ein Unterverzeichnis für Logs (z.B. `logs/`)
*   **Anpassung des Backends:** Das Backend muss so angepasst werden, dass es diese Pfade dynamisch zur Laufzeit ermittelt und verwendet.

### 2.3. Backend-Management durch Electron
*   **Problem:** Die Electron-Anwendung muss das Python-Backend starten, überwachen und bei Beendigung der Electron-App auch wieder sauber beenden.
*   **Lösung:**
    *   Electron startet das gebündelte Python-Backend als separaten Child-Prozess.
    *   Überwachung des Backend-Prozesses (z.B. auf Abstürze).
    *   Sicherstellung, dass der Backend-Prozess beendet wird, wenn die Electron-Anwendung geschlossen wird.
    *   Inter-Prozess-Kommunikation (IPC) zwischen Electron (Frontend) und dem Python-Backend für Statusmeldungen oder spezielle Befehle.

### 2.4. Updates
*   **Problem:** Wie werden zukünftige Updates der Anwendung verteilt und installiert?
*   **Lösung:** (Außerhalb des Scopes dieses MVPs, aber als zukünftige Überlegung zu notieren. `electron-updater` könnte eine Option sein.)

### 2.5. Abhängigkeiten
*   **Problem:** Alle Python- und Node.js-Abhängigkeiten müssen korrekt in das Installationspaket aufgenommen werden.
*   **Lösung:**
    *   `PyInstaller` für Python-Abhängigkeiten.
    *   `electron-builder` für Node.js/Frontend-Abhängigkeiten.

## 3. Technischer Ansatz (High-Level)

*   **Electron:** Dient als Haupt-Anwendungswrapper und stellt das Frontend bereit.
*   **PyInstaller:** Wird verwendet, um das Python FastAPI Backend in eine eigenständige ausführbare Datei zu kompilieren.
*   **`electron-builder`:** Das primäre Tool zur Erstellung des finalen `.exe`-Installers, der sowohl die Electron-App als auch das gebündelte Python-Backend enthält.

## 4. Detaillierte Schritte zur Umsetzung (Überarbeitet - Fokus auf iterative Stabilität)

### Phase 1: Backend-Bündelung Proof-of-Concept (PyInstaller) - Iterativ und Isoliert

**Ziel:** `janus_backend.exe` muss standalone ohne Fehler starten und grundlegende Funktionen ausführen können.

1.  **PyInstaller installieren:** `pip install pyinstaller` im Backend-Venv.
2.  **`resource_path` Funktion implementieren:** Diese Funktion ist entscheidend, um Pfade zu Ressourcen korrekt aufzulösen, egal ob im Entwicklungsmodus oder im gebündelten Zustand.
    *   **Ort:** `backend/utils/paths.py` (neu erstellen) oder direkt in `backend/main.py` für den POC.
    *   **Inhalt:**
        ```python
        import sys
        import os

        def resource_path(relative_path):
            """ Ermittelt den absoluten Pfad zu einer Ressource, funktioniert für Entwicklung und PyInstaller. """
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        ```
3.  **Pfadanpassung im Backend (für Konfiguration und Modelle):**
    *   **`backend/main.py`:**
        *   Importiere `resource_path`.
        *   Definiere `APP_NAME`, `APP_AUTHOR`.
        *   Definiere `DATA_DIR` (benutzerspezifisch, z.B. `user_data_dir(APP_NAME, APP_AUTHOR)`).
        *   Definiere `CONFIG_FILE` und `MODEL_CATALOG_FILE` als Pfade innerhalb von `DATA_DIR`.
        *   Passe `load_config()` und `load_model_catalog()` an:
            *   Wenn die Datei in `DATA_DIR` nicht existiert, kopiere sie aus dem *gebündelten Template-Pfad* (ermittelt mit `resource_path`) nach `DATA_DIR`.
            *   **Wichtig:** Die `model_catalog` und `context_manager` Initialisierung muss von der Modulebene entfernt und in eine FastAPI-Abhängigkeit (`get_context_manager`) verschoben werden, die erst bei Bedarf geladen wird.
    *   **`backend/database.py`:** Passe `DATABASE_URL` und `COSTS_DATABASE_URL` an, um Pfade innerhalb von `DATA_DIR` zu verwenden.
    *   **`backend/crud.py`:** Passe `IMAGE_DIR` an, um Pfade innerhalb von `DATA_DIR` zu verwenden.
4.  **`main.spec` anpassen (für Daten-Assets):**
    *   Füge `config.json` und `model_catalog.json` als `datas` hinzu, die in das Root-Verzeichnis des Bundles kopiert werden (z.B. `('backend/config.json', '.')`).
    *   Füge den Cache-Ordner des `SentenceTransformer`-Modells als `datas` hinzu (z.B. `(r'C:\Users\pruve\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\<hash>', 'sentence-transformers/all-MiniLM-L6-v2')`).
    *   **Wichtig:** Stellen Sie sicher, dass `datas` und `hiddenimports` in `main.spec` syntaktisch korrekt sind und keine Duplikate oder Fehler enthalten.
5.  **`vector_service.py` anpassen:** Ändern Sie den `SentenceTransformer`-Aufruf, um das Modell aus dem gebündelten Pfad zu laden (ermittelt mit `resource_path`).
6.  **Build und Test des Backends (Iterativ):**
    *   `rm -rf build dist` (oder `rd /s /q build` und `rd /s /q dist` unter Windows).
    *   `pyinstaller main.spec`.
    *   Testen Sie `dist/janus_backend.exe` direkt. Beheben Sie alle Fehler, bevor Sie fortfahren.

### Phase 2: Electron-Integration (Nachdem Backend standalone läuft)

1.  **Backend-Startskript in Electron (`main.electron.js`):**
    *   Verwenden Sie `app.getAppPath()` um den Basispfad der installierten Anwendung zu finden.
    *   Starten Sie `janus_backend.exe` als Child-Prozess.
    *   Leiten Sie `stdout`/`stderr` des Backends zur Fehlerbehebung um.
    *   Implementieren Sie eine Logik zum Beenden des Backends beim Schließen der Electron-App.
2.  **Frontend-Anpassung:** Sicherstellen, dass das Frontend API-Aufrufe an den korrekten lokalen Port des gestarteten Backends sendet.

### Phase 3: Installer-Konfiguration (`electron-builder`)

1.  **`package.json` konfigurieren:**
    *   `build`-Sektion mit `appId`, `productName`, `directories`.
    *   `files`: Stellen Sie sicher, dass alle benötigten Frontend-Dateien und das gebündelte Backend (`janus_backend.exe`) enthalten sind.
    *   `extraFiles`: Verwenden Sie dies, um `janus_backend.exe` in das Root-Verzeichnis des Electron-Bundles zu kopieren.
    *   `win`: Windows-spezifische Einstellungen (Installer-Typ, Icons).
    *   `asarUnpack`: Stellen Sie sicher, dass `janus_backend.exe` und alle nativen Node-Module entpackt werden.
2.  **Build-Skript (`npm run build-all`):** Orchestrieren Sie den PyInstaller-Build, den Vite-Build und den `electron-builder`-Build.

### Phase 4: Testen

1.  **Build-Prozess testen:** Sicherstellen, dass der Build ohne Fehler durchläuft.
2.  **Installations-/Deinstallations-Test:** Die generierte `.exe` installieren und deinstallieren.
3.  **Funktionstest:** Die installierte Anwendung starten und alle Kernfunktionen testen.
4.  **Pfad-Validierung:** Überprüfen, ob Datenbank, Konfiguration und Bilder korrekt in den benutzerspezifischen Datenverzeichnissen abgelegt werden.

---
*Letzte Aktualisierung: 2025-08-24*