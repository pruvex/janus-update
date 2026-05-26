# BACKLOG TASK – BACKLOG-015 – Modell-Wechsel-Benachrichtigung bei nicht verfügbarem Modell

## 1. Ziel
Die Benachrichtigung bei Modellwechsel (nicht verfügbares Modell) wird transparenter, verständlicher und bietet dem Benutzer Handlungsoptionen oder zumindest eine klare Erklärung.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-015
- **Beeinflusst:** Frontend UI / Modell-Auswahl / Fehlermeldungen / Frontend
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Verbesserung der roten Benachrichtigung oben rechts bei Modellwechsel
- Klarere Kommunikation, warum das Modell nicht verfügbar ist (z.B. API-Fehler, Lizenzproblem)
- Optional: Handlungsoption für den Benutzer (alternatives Modell wählen oder Vorgang abbrechen)
- Optional: Nicht verfügbare Modelle aus der Auswahl entfernen oder als inaktiv kennzeichnen

### OUT OF SCOPE
- Änderungen am Backend-Modell-Validierungslogik
- Änderungen an Provider-Authentifizierung
- Globale Modell-Auswahl-Logik außerhalb der Benachrichtigung

## 4. Umsetzungsschritte
1. Frontend-Code identifizieren, der die rote Benachrichtigung oben rechts anzeigt (vermutlich in `frontend/js/` oder `frontend/src/`)
2. Aktuellen Benachrichtigungstext analysieren und verstehen, warum das Modell als nicht verfügbar markiert wird
3. Benachrichtigung erweitern:
   - Grund für Nichtverfügbarkeit hinzufügen (falls vom Backend geliefert)
   - Handlungsoptionen hinzufügen (z.B. "Anderes Modell wählen", "Abbrechen")
   - Oder persistentere Benachrichtigung statt kurzem Flash
4. Optional: Modell-Selection-UI erweitern, um nicht verfügbare Modelle zu deaktivieren oder zu kennzeichnen
5. Manuellem Test: Provider-Wechsel mit nicht verfügbarem Modell auslösen und neue Benachrichtigung prüfen

## 5. Acceptance Criteria
- [ ] Die Benachrichtigung über nicht verfügbare Modelle ist klar, verständlich und bietet dem Benutzer Handlungsoptionen.
- [ ] Der automatische Modellwechsel wird transparent kommuniziert oder vermieden.
- [ ] Der Benutzer hat mehr Kontrolle über die Auswahl des Modells, wenn das bevorzugte Modell nicht verfügbar ist.

## 6. Tests / Validierung
- Manuellem Test: Provider-Wechsel zu einem nicht verfügbaren Modell (z.B. `gemini-3-flash-preview`) auslösen
- Prüfen, dass die Benachrichtigung den Grund enthält oder Handlungsoptionen bietet
- Prüfen, dass der Benutzer das gewünschte Modell wählen oder den Vorgang abbrechen kann

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Frontend-UI-Improvement mit LOW-MEDIUM Risiko.

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** BACKLOG-015
- **Feature status:** DONE
- **Final audit status:** PASS

### Files Changed
- **frontend/js/app.js:** Verbesserte Benachrichtigung bei nicht verfügbaren Modellen, Provider-Wechsel-Probleme behoben

### What Was Done
Verbesserte Benachrichtigung bei nicht verfügbaren Modellen mit klarer Kommunikation und Handlungsoptionen. Provider-Wechsel-Probleme behoben (keine falschen Fehlermeldungen mehr, Dropdown nicht mehr leer). UX-Entscheidung: Kleinstes Modell beim Provider-Wechsel auswählen (sicherer).

### Validation Evidence
- **Manual Janus test:** PASS — Provider-Wechsel funktioniert ohne falsche Fehlermeldungen, verbesserte Benachrichtigung getestet
- **Skill 6:** N/A — kein Debugging nötig

### Final Audit Fixes
- **frontend/js/app.js:** Provider-Wechsel-Logik korrigiert, um falsche Fallback-Logik zu verhindern

### Version Bump
- **Old version:** 0.4.17-beta.17
- **New version:** 0.4.17-beta.18
- **Files changed:** package.json, backend/version.py, package-lock.json

### Remaining Risks
- None

## DEBUGGING LOG
- Keine Probleme.
