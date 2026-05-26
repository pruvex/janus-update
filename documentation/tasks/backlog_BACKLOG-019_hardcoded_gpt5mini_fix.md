# BACKLOG TASK – BACKLOG-019 – Hardcoded gpt-5-mini verursacht Fallback-Warnung nach OpenAI-Key-Eingabe

## 1. Ziel
Entferne alle hardcoded Modell-IDs (insbesondere gpt-5-mini) aus dem Backend-Code und ersetze sie durch dynamische Auswahl aus dem Model-Katalog.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-019
- **Beeinflusst:** backend/main.py (Zeile 654), backend/services/calendar/calendar_ai_engine.py (Zeilen 140, 145)
- **Risiko-Einschätzung:** MEDIUM (betrifft Config/Model-Selection, aber klar begrenzt auf 2 Dateien)

## 3. Scope
### IN SCOPE
- Entferne hardcoded "gpt-5-mini" in backend/main.py Zeile 654 (Default für last_used_model)
- Entferne hardcoded "gpt-5-mini" in backend/services/calendar/calendar_ai_engine.py Zeilen 140, 145 (Fallback)
- Implementiere dynamische Auswahl des ersten verfügbaren Modells aus dem Model-Katalog
- Stelle sicher, dass keine Warnung über nicht verfügbare Modelle nach Key-Eingabe erscheint

### OUT OF SCOPE
- Änderung an Tests (dort sind hardcoded IDs dokumentierte Ausnahmen)
- Änderung an anderen Dateien als main.py und calendar_ai_engine.py
- Änderung an der Model-Katalog-Struktur oder API
- Änderung an der Frontend-Modell-Auswahl

## 4. Umsetzungsschritte
1. backend/main.py: Ersetze Zeile 654 (`config["last_used_model"] = "gpt-5-mini"`) durch dynamische Auswahl des ersten verfügbaren Modells aus dem Model-Katalog
2. backend/services/calendar/calendar_ai_engine.py: Ersetze Zeilen 140, 145 (`or "gpt-5-mini"`) durch dynamische Auswahl aus dem Model-Katalog
3. Prüfe, ob eine Helper-Funktion für dynamische Modell-Auswahl existiert oder erstellt werden muss
4. Stelle sicher, dass die dynamische Auswahl robust ist gegen leere Kataloge (Fallback auf user request oder leeres Modell mit klarer Fehlermeldung)

## 5. Acceptance Criteria
- [ ] Keine hardcoded Modell-IDs im Code (außer in Tests oder dokumentierten Ausnahmen)
- [ ] System wählt dynamisch das erste verfügbare Modell aus dem Model-Katalog wenn keine Konfiguration existiert
- [ ] Calendar AI Engine wählt dynamisch aus dem Katalog statt hardcoded Fallback
- [ ] Keine Warnung über nicht verfügbare Modelle nach Key-Eingabe
- [ ] Lösung ist robust gegen Katalog-Updates (keine neuen hardcoded Referenzen)

## 6. Tests / Validierung
- Manuellem Test: Frische Installation oder Config-Reset → OpenAI-Key eingeben → Keine Warnung über nicht verfügbare Modelle
- Code-Review: Prüfe backend/main.py und calendar_ai_engine.py auf verbleibende hardcoded Modell-IDs
- Backend-Log: Prüfe, dass das dynamisch gewählte Modell im Log korrekt angezeigt wird

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix mit MEDIUM-Risiko und klar begrenztem Scope.
