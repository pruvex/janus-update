### PHASE 3: Der Filesystem-Agent & Visuelle Interaktion
*Ziel: Ein voll funktionsfähiger Filesystem-Agent, der sprachgesteuert auf das lokale Dateisystem zugreifen kann, sowie die Fähigkeit, Dateien visuell im UI darzustellen.*

- [ ] **[JANUS] Filesystem-Agent (Backend):** Implementierung der Backend-Logik für den sprachgesteuerten Zugriff auf das lokale Dateisystem (lesen, schreiben, erstellen, löschen, umbenennen, verschieben von Dateien und Ordnern). Eine Sicherheits-Sandbox muss dabei Systemordner schützen.
- [ ] **[WÄCHTER] Filesystem-Agent testen:** Umfassende Tests für den Filesystem-Agenten, inklusive Tests für die Sicherheits-Sandbox.
- [ ] **[JANUS] Datei-Upload (Frontend):** Implementierung der UI-Komponenten für den Drag-and-Drop-Upload von Dateien in das Frontend.
- [ ] **[JANUS] Datei-Visualisierung (Frontend):** Implementierung von Widgets zur visuellen Darstellung von hochgeladenen Dateien (Text, Bild, PDF) im UI.
- [ ] **[JANUS] Kontext-Verknüpfung (Frontend):** Verknüpfung der Datei-Widgets mit dem Chat-Fenster, sodass der Agent den Inhalt der angezeigten Dateien als Kontext nutzen kann.
- [x] **[JANUS] Bilderzeugung (Backend):** Die Logik zur Anbindung an eine Bild-API (DALL-E 3) implementieren.
- [x] **[JANUS] Tool-Nutzung (Backend):** GPT-4o die Fähigkeit geben, die Bilderzeugungs-Funktion als Werkzeug selbstständig aufzurufen.
- [x] **[JANUS] Bildanzeige (Frontend):** Generierte Bilder direkt im Chatfenster als `<img>`-Element anzeigen.
- [x] **[JANUS] Bild speichern (Desktop):** Eine Funktion implementieren, die es dem Benutzer erlaubt, generierte Bilder über einen nativen Dialog auf der Festplatte zu speichern.
- [ ] **[GIT] Meilenstein-Commit:** Den funktionierenden Filesystem-Agenten und die visuelle Interaktion committen.