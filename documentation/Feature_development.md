# 🚀 Feature-Entwicklungsprozess (Diamond-Standard V2.5)

Dieses Dokument definiert den verbindlichen Pfad für die Konzeption, Verifikation und Umsetzung neuer Features in Janus. Ziel ist maximale Code-Integrität durch mehrstufige, modell-übergreifende Validierung.

---

## Phasen der Feature-Härtung

### PHASE 1: Ziel-Definition (AI Studio)
- **Akteure:** Mensch & Janus (AI Studio)
- **Input:** Idee oder Anforderung.
- **Output:** Präzise Definition der Ziele, Funktionalitäten und gewünschten Ergebnisse in dieser Datei.

### PHASE 2: Erster Ablauf- & Designplan (AI Studio)
- **Akteur:** Janus (Prio: Claude 4.6 Sonnet / Gemini 3 Pro)
- **Output:** Initialer Architektur-Entwurf, Datenflüsse und benötigte Skills.

### PHASE 3: Codebase-Review (Windsurf/Agent)
- **Akteur:** Kimi/Agent (Prio: Claude 4.6 Opus / Gemini 3 Pro)
- **Input:** Janus' Designplan.
- **Prüfung:** Abgleich gegen `@backend/`. Suche nach Redundanzen, Fallstricken und Schema-Konflikten.
- **Output:** Detailliertes Feedback für Janus.

### PHASE 4: Optimierter Designplan (AI Studio)
- **Akteur:** Janus
- **Output:** Einarbeitung des Feedbacks in den zentralen Feature-Design-Plan.

### PHASE 5: Externer Risiko-Check (Mensch/Extern)
- **Akteur:** ChatGPT (oder anderes externes LLM)
- **Prüfung:** Kritische Bewertung hinsichtlich Risiken, unberücksichtigter Aspekte und Optimierungen.
- **Output:** Externes Feedback für Janus.

### PHASE 6: Finale Verfeinerung (AI Studio)
- **Akteur:** Janus
- **Output:** Maximal gehärteter, finaler Design-Plan.

### PHASE 7: Finale Abnahme (Windsurf/Agent)
- **Akteur:** Kimi/Agent (Großmodell)
- **Prüfung:** Letztes "Go/No-Go" zur technischen Umsetzbarkeit.
- **Output:** Bestätigung der Abnahme.

### PHASE 8: Task-Derivation & Operative Umsetzung
- **Akteur:** Janus & Agent
- **Prozess:** Zerlegung des Plans in atomare Tasks (`documentation/tasks/task_XXX.md`) via `bootstrap`-Befehl. Festlegung benötigter Skills und Testfälle.
