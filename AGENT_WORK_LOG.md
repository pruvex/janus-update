---

### 2025-08-15 - interactjs-Abhängigkeit in den frontend-Workspace verschoben (cd-Workaround)

- **Ziel:** `interactjs`-Abhängigkeit in den korrekten `frontend`-Workspace verschieben, unter Verwendung des `cd`-Workarounds.
- **Aktion:** `npm uninstall interactjs` wurde im Hauptverzeichnis ausgeführt, um sicherzustellen, dass es aus dem Root entfernt wird. Anschließend wurde `cd frontend && npm install interactjs` ausgeführt, um es sauber im Frontend zu installieren.
- **Ergebnis:** Die `interactjs`-Abhängigkeit ist nun korrekt dem `frontend`-Projekt zugeordnet und der Installationsprozess wurde an die Projektstruktur angepasst.