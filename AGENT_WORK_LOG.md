---

### 2025-08-15 - interactjs-Abhängigkeit verschoben

- **Ziel:** `interactjs`-Abhängigkeit vom Root in den `frontend`-Workspace verschoben.
- **Aktion:** `interactjs` wurde aus der Root `package.json` deinstalliert und direkt in die `frontend/package.json` installiert.
- **Ergebnis:** Die `interactjs`-Abhängigkeit ist nun korrekt dem `frontend`-Projekt zugeordnet.

---

### 2025-08-15 - interactjs-Abhängigkeit in den frontend-Workspace verschoben (cd-Workaround)

- **Ziel:** `interactjs`-Abhängigkeit in den korrekten `frontend`-Workspace verschieben, unter Verwendung des `cd`-Workarounds.
- **Aktion:** `npm uninstall interactjs` wurde im Hauptverzeichnis ausgeführt, um sicherzustellen, dass es aus dem Root entfernt wird. Anschließend wurde `cd frontend && npm install interactjs` ausgeführt, um es sauber im Frontend zu installieren.
- **Ergebnis:** Die `interactjs`-Abhängigkeit ist nun korrekt dem `frontend`-Projekt zugeordnet und der Installationsprozess wurde an die Projektstruktur angepasst.
