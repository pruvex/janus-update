### PHASE 3: Der Filesystem-Agent & Visuelle Interaktion
*Ziel: Ein voll funktionsfähiger Filesystem-Agent, der sprachgesteuert auf das lokale Dateisystem zugreifen kann, sowie die Fähigkeit, Dateien visuell im UI darzustellen.*

- [ ] **[JANUS] Filesystem-Agent (Backend):** Implementierung der Backend-Logik für den sprachgesteuerten Zugriff auf das lokale Dateisystem (lesen, schreiben, erstellen, löschen, umbenennen, verschieben von Dateien und Ordnern). Eine Sicherheits-Sandbox muss dabei Systemordner schützen.
- [ ] **[WÄCHTER] Filesystem-Agent testen:** Umfassende Tests für den Filesystem-Agenten, inklusive Tests für die Sicherheits-Sandbox.
- [ ] **[JANUS] Datei-Upload (Frontend):** Implementierung der UI-Komponenten für den Drag-and-Drop-Upload von Dateien in das Frontend.
- [ ] **[JANUS] Datei-Visualisierung (Frontend):** Implementierung von Widgets zur visuellen Darstellung von hochgeladenen Dateien (Text, Bild, PDF) im UI.
- [ ] **[JANUS] Kontext-Verknüpfung (Frontend):** Verknüpfung der Datei-Widgets mit dem Chat-Fenster, sodass der Agent den Inhalt der angezeigten Dateien als Kontext nutzen kann.
- [ ] **[GIT] Meilenstein-Commit:** Den funktionierenden Filesystem-Agenten und die visuelle Interaktion committen.