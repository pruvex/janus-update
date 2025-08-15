---

### 2025-08-15 - interactjs-Abhängigkeit in den frontend-Workspace verschoben (cd-Workaround)

- **Ziel:** `interactjs`-Abhängigkeit in den korrekten `frontend`-Workspace verschieben, unter Verwendung des `cd`-Workarounds.
- **Aktion:** `npm uninstall interactjs` wurde im Hauptverzeichnis ausgeführt, um sicherzustellen, dass es aus dem Root entfernt wird. Anschließend wurde `cd frontend && npm install interactjs` ausgeführt, um es sauber im Frontend zu installieren.
- **Ergebnis:** Die `interactjs`-Abhängigkeit ist nun korrekt dem `frontend`-Projekt zugeordnet und der Installationsprozess wurde an die Projektstruktur angepasst.

---

### 2025-08-15 - Bereinigung der Python-Abhängigkeiten (fastapi-cli)

- **Ziel:** Die ungenutzte `fastapi-cli`-Abhängigkeit aus der Python-Umgebung entfernen.
- **Aktion:** `fastapi-cli` wurde mittels `pip uninstall -y fastapi-cli` aus der virtuellen Umgebung entfernt.
- **Ergebnis:** Die `fastapi-cli`-Abhängigkeit und ihre exklusiven Unterabhängigkeiten wurden erfolgreich entfernt. Die `backend/requirements.txt` musste nicht angepasst werden, da `fastapi-cli` dort nicht direkt gelistet war.
