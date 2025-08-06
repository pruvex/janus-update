# PHASE 2: Der Chat-Kern & Multi-Provider-Fähigkeit

*Ziel: Am Ende dieser Phase haben wir ein funktionierendes Chat-Fenster, das mit verschiedenen, vom Benutzer konfigurierten LLMs kommunizieren kann.*

- [x] **[JANUS] UI/UX-Grundgerüst:** Das statische HTML/CSS für das Dashboard, die einklappbare Sidebar und das (noch nicht funktionale) Einstellungs-Fenster umsetzen.

- [ ] **[JANUS] Key-Management (Backend):** Die Logik zur sicheren, verschlüsselten Speicherung von API-Keys (z.B. in einer lokalen `config.json` oder einer `.db`-Datei) implementieren.

- [ ] **[JANUS] Einstellungs-UI (Frontend):** Das UI zum Hinzufügen, Anzeigen (maskiert) und Löschen von API-Keys im Einstellungs-Fenster erstellen.

- [ ] **[JANUS] LLM-Gateway (Backend):** Das Kernmodul erstellen, das basierend auf einem Provider-Namen den korrekten API-Key lädt und eine Anfrage an die entsprechende LLM-API sendet.

- [ ] **[JANUS] Chat-API-Endpunkt:** Den `/api/chat`-Endpunkt erstellen, der eine Nachricht und einen Provider entgegennimmt und den LLM-Gateway aufruft.

- [ ] **[WÄCHTER] Chat-Endpunkt testen:** Einen Wächter-Test für den Chat-Endpunkt schreiben (ohne echte API-Calls, nur mit Mocks, um Kosten zu vermeiden).

- [ ] **[JANUS] Chat-UI-Logik (Frontend):** Die Logik implementieren, um Nachrichten aus einem Input-Feld zu senden, den Provider aus einem Dropdown auszuwählen und die gestreamte Antwort im Chatfenster anzuzeigen.

- [ ] **[GIT] Meilenstein-Commit:** Den funktionierenden Chat-Kern committen.