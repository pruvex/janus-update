# BACKLOG TASKS – BACKLOG-036 – Gemini Halluzination: Geo-Distanz ohne Tool-Call (TC-003)

## Spec Source
- **Spec:** documentation/Planned Features/backlog_BACKLOG-036_gemini_geo_distance_hallucination.md
- **Backlog ID:** BACKLOG-036
- **Type:** BUG
- **Skill-2 Status:** TASK DESIGN COMPLETE

---

## TASK-036-01 – Gemini Intent-Routing für Geo-Distanz reparieren

### Ziel
Gemini ruft system.routing Tool bei Geo-Distanz-Abfragen auf und zeigt "Quelle: OSRM" Attribution an, wie GPT es tut.

### Beschreibung
Der Bug zeigt, dass Gemini bei Geo-Distanz-Intents ("Wie weit ist Berlin von München?") das system.routing Tool nicht aufruft, sondern mit Halluzination antwortet. GPT funktioniert korrekt. Dieser Task implementiert den Fix basierend auf Analyse der Intent-Routing- und Tool-Selection-Logik für Gemini, damit Gemini wie GPT system.routing aufruft.

### Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-036
- **Beeinflusst:** backend/services/intent_engine.py, backend/services/skill_selector.py, backend/llm_providers/gemini/service.py, backend/tools/routing_tools.py, backend/services/attribution_service.py
- **Risiko-Einschätzung:** MEDIUM

### Files
- `backend/services/intent_engine.py` (Intent-Erkennung und Routing-Logik)
- `backend/services/skill_selector.py` (Skill/Tool-Selection)
- `backend/llm_providers/gemini/service.py` (Gemini-spezifische Tool-Handling)
- `backend/tools/routing_tools.py` (system.routing Tool-Definition)
- `backend/services/attribution_service.py` (Attribution-Logik)

### Umsetzungsschritte
1. **Root Cause Analyse (als Step integriert):**
   - Prüfe Intent-Erkennung für Geo-Distanz-Queries in `intent_engine.py`
   - Vergleiche Intent-Result für Gemini vs GPT bei gleicher Query
   - Prüfe ob Geo-Distanz-Intent für Gemini korrekt als "routing" klassifiziert wird
   - Prüfe Skill-Selector Output für Gemini: wird system.routing in relevant_skill_ids aufgenommen?

2. **Tool-Selection Analyse (als Step integriert):**
   - Prüfe `skill_selector.py`: werden routing-relevant Skills für Gemini in allowed_skill_ids übernommen?
   - Prüfe Gemini-spezifische Tool-Filterung in `gemini/service.py` (Name-Sanitization, Filter-Logik)
   - Prüfe ob system.routing nach Sanitization/Filterung noch in der Tool-Liste enthalten ist

3. **Fix Implementierung:**
   - Wenn Intent-Klassifizierung für Gemini unvollständig: Ergänze Intent-Präzedenz für routing-Intents
   - Wenn Skill-Selector system.routing für Gemini nicht aufnimmt: Ergänze mandatory-Skill-Liste für routing-Intents
   - Wenn Gemini-Tool-Filter system.routing entfernt: Fix Filter-Logik (z.B. DIAMOND-CORE-ROUTING-FORCE Pattern aus BACKLOG-034/031 anwenden)
   - Wenn Attribution-Logik für Gemini fehlt: Ergänze Attribution-Erkennung für system.routing Tool-Results

4. **Provider-Parity Sicherstellung:**
   - Prüfe dass der Fix GPT-Verhalten nicht ändert (keine Regression)
   - Teste mit Gemini und GPT bei gleichen Geo-Distanz-Queries

### Acceptance Criteria
- [ ] Gemini ruft system.routing Tool bei Geo-Distanz-Abfragen auf
- [ ] Gemini zeigt "Quelle: OSRM" Attribution an
- [ ] Tool-Routing funktioniert für Gemini wie für GPT
- [ ] GPT-Verhalten ist unverändert (keine Regression)

### Tests / Validierung
- Manueller Janus Test mit Gemini: "Wie weit ist Berlin von München?" → Erwartet: system.routing Tool-Call + Attribution
- Manueller Janus Test mit GPT: gleicher Query → Erwartet: unverändertes Verhalten (weiterhin korrekt)
- Vergleich der Intent-Result-Logs zwischen Gemini und GPT

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Multi-file Integration mit Intent-Engine, Skill-Selector, Gemini-Provider und Attribution-Logik. Erfordert breites Codebase-Reasoning und Provider-spezifische Logik.

---

## TASK-036-02 – Test für Gemini Geo-Distance Routing erstellen

### Ziel
Automatisierter Test verifiziert, dass Gemini system.routing Tool bei Geo-Distanz-Queries aufruft.

### Beschreibung
Ergänze den bestehenden Test-Plan oder erstelle einen neuen Test, der spezifisch Gemini-Geo-Distance-Routing validiert. Der Test sollte reproduzierbar zeigen, dass der Fix funktioniert.

### Files
- `tests/e2e/generated/` (neuer Test-Case oder Erweiterung)
- `config/skill_tests/` (Test-Konfiguration falls benötigt)

### Umsetzungsschritte
1. Test-Case für Geo-Distanz-Query erstellen mit Gemini als Provider
2. Verifiziere dass system.routing Tool aufgerufen wird
3. Verifiziere dass "Quelle: OSRM" Attribution in der Antwort erscheint
4. Optional: Gleichen Test mit GPT als Regression-Check

### Acceptance Criteria
- [ ] Test-Case für Gemini Geo-Distanz existiert
- [ ] Test verifiziert system.routing Tool-Call
- [ ] Test verifiziert Attribution
- [ ] Test ist reproduzierbar und automatisiert ausführbar

### Tests / Validierung
- Test-Ausführung mit Playwright oder Test-Runner
- Überprüfung der Test-Evidence-Logs

### Model
- **Assigned Model:** Kimi k2.5
- **Reason:** Deterministischer Single-File Test-Erstellung mit klarer Struktur und bekannten Test-Patterns.

---

## Ausführungskette
- Reihenfolge: TASK-036-01 → TASK-036-02 (sequenziell: Fix zuerst, dann Test)

## Zugewiesene Modelle
- **SWE 1.6:** TASK-036-01
- **Kimi k2.5:** TASK-036-02

## Modell-Bedeutung
- Diese Zuweisungen sind Task-Ausführungsmodelle für spätere einzelne Skill-3-/Skill-4-Läufe.
- Sie sind NICHT das Modell für Skill 2.
