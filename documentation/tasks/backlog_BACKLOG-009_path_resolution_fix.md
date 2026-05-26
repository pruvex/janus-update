# BACKLOG TASK – BACKLOG-009 – gpt-5.4-nano ist konservativ bei Pfad-Auflösung

## 1. Ziel
gpt-5.4-nano soll konservatives Pfad-Auflösungsverhalten überwinden und häufige Pfade wie "desktop" direkt auflösen können, ohne den User nach dem konkreten Pfad zu fragen.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-009
- **Beeinflusst:** Prompt-Engineering / Path-Resolution / Model-Verhalten / Orchestrator
- **Risiko-Einschätzung:** MEDIUM (Betrifft Prompt-Engineering und Model-Verhalten, könnte andere Prompts beeinflussen)

## 3. Scope
### IN SCOPE
- Prompt-Engineering für Filesystem-Operationen verbessern, damit gpt-5.4-nano "desktop" direkt auflöst
- Optionale Pfad-Auflösungs-Hilfe im System-Prompt oder Context hinzufügen
- Validierung durch manuellen Test mit dem BACKLOG-008 Reproduktions-Prompt

### OUT OF SCOPE
- Allgemeine RAG-System-Optimierung
- Änderungen an der Intent-Detection (BACKLOG-008 hat dieses Problem gelöst)
- Model-Selection für andere Intent-Typen
- Komplette Path-Resolution-Engine (zu groß für atomaren Fix)

## 4. Umsetzungsschritte
1. Analyse der aktuellen Prompt-Struktur für Filesystem-Operationen
2. Identifizierung von Möglichkeiten, um gpt-5.4-nano bei der Pfad-Auflösung zu unterstützen (z.B. System-Prompt, Context, Tool-Descriptions)
3. Implementierung der gewählten Lösung (z.B. Hinweis im System-Prompt dass "desktop" → "C:\Users\<username>\Desktop" aufgelöst werden kann)
4. Validierung durch manuellen Test mit dem BACKLOG-008 Reproduktions-Prompt

## 5. Acceptance Criteria
- [ ] gpt-5.4-nano löst "desktop" direkt zu "C:\Users\<username>\Desktop" auf ohne Nachfragen
- [ ] gpt-5.4-nano führt Filesystem-Tool-Calls aus ohne explizite Pfadangabe
- [ ] Filesystem-Operationen werden vollständig ausgeführt (Ordner erstellen + Dateien verschieben)

## 6. Tests / Validierung
- Manuellem Test mit BACKLOG-008 Reproduktions-Prompt: "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- Backend-Log Check: Tool-Calls werden ausgeführt ohne Pfad-Abfrage
- Validierung dass die Lösung nicht andere Prompts negativ beeinflusst

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix mit MEDIUM-Risiko (Prompt-Engineering Änderung)

## 8. POST-IMPLEMENTATION AUDIT TRAIL

### 8.1 Implementierte Änderungen
- **Datei:** `backend/services/orchestrator/prompt_registry.py`
  - Neue Direktive `path_resolution_hint` hinzugefügt (Zeilen 80-92)
  - Direktive enthält Hinweise für Auflösung von "desktop", "documents", "downloads", "pictures" zu Standard-Pfaden
  - `apply_verbosity_control` Funktion aktualisiert, um die neue Direktive automatisch einzufügen (Zeilen 274-282)

- **Datei:** `backend/tests/unit/test_prompt_registry_path_resolution.py`
  - Unit-Test für die neue Direktive erstellt
  - Tests prüfen: Existenz, Inhalt, Integration in apply_verbosity_control, Deduplication
  - Alle 4 Tests bestanden

### 8.2 Validierungsergebnisse
- **Unit-Tests:** 4/4 bestanden ✅
- **Manueller Test:** Pfad-Auflösung funktioniert ✅
  - Backend-Log: `Executing tool 'filesystem.list_directory' with args: {'path': 'C:\\Users\\pruve\\Desktop'}`
  - "desktop" wurde zu `C:\Users\pruve\Desktop` aufgelöst ohne Rückfrage
- **Manueller Test:** Vollständige Ausführung fehlt ❌
  - Assistant führte nur `list_directory` aus, nicht `create_directory` oder `move_files`
  - Antwort: "Ich konnte diesmal keine stabile Antwort erzeugen..."
  - Dieses Problem ist in BACKLOG-010 ausgelagert

### 8.3 Partial Completion
- **Erreicht:** Pfad-Auflösung funktioniert (BACKLOG-009 Ziel 1 ✅)
- **Nicht erreicht:** Vollständige Ausführung der Filesystem-Operationen (BACKLOG-009 Ziel 2-3 ❌)
- **Grund:** Das eigentliche Problem (Ausführung wird abgebrochen) ist ein separates Issue in der Execution Engine, nicht in der Pfad-Auflösung
- **Referenz:** BACKLOG-010 – gpt-5.4-nano führt Filesystem-Operationen nicht aus

### 8.4 Commit
- **Commit:** `BACKLOG-009: path_resolution_hint Direktive hinzugefügt für gpt-5.4-nano Pfad-Auflösung`
- **Hash:** 28822fb
- **Dateien:** `backend/services/orchestrator/prompt_registry.py`, `backend/tests/unit/test_prompt_registry_path_resolution.py`

### 8.5 Version
- **Version:** 0.4.17-beta.14
- **Status:** PARTIAL PASS
