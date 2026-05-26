# BACKLOG TASKS – BACKLOG-037 – Gemini Klärungsfrage fehlt bei ambiger Anfrage (TC-005)

## TASK-037-01 – Gemini Ambiguity-Detection und Confidence-Blockade implementieren

**Ziel:**
Gemini-spezifische Ambiguity-Detection, Intent-Confidence-Threshold und Tool-Ausführungs-Blockade implementieren, um Provider-Parity mit GPT zu erreichen.

**Beschreibung:**
Aktuell antwortet Gemini auf ambige Anfragen ("Ich brauche Infos dazu") ohne Klärungsfrage, während GPT korrekt eine Klärungsfrage stellt. Diese konsolidierte Task implementiert alle notwendigen Komponenten: Gemini-spezifische Ambiguity-Detection in der Intent Engine, Intent-Confidence-Evaluierung mit Threshold, und Tool-Ausführungs-Blockade bei geringer Confidence.

## 2. Impact-Analyse
- **Basiert auf:** documentation/Planned Features/backlog_BACKLOG-037_gemini_ambiguity_clarification.md, documentation/backlog/BACKLOG.md#BACKLOG-037
- **Beeinflusst:** backend/services/orchestrator/intent_engine.py, backend/services/orchestrator/execution_dispatcher.py, backend/services/chat/context_builder.py, backend/services/llm_providers/gemini/service.py (falls nötig)
- **Risiko-Einschätzung:** MEDIUM

**Files:**
- backend/services/orchestrator/intent_engine.py
- backend/services/orchestrator/execution_dispatcher.py
- backend/services/chat/context_builder.py
- backend/services/llm_providers/gemini/service.py (falls nötig)

**Steps:**
1. Aktuelle Ambiguity-Detection-Logik in context_builder.py analysieren und GPT-Verhalten verstehen
2. Gemini-spezifische Ambiguity-Detection in intent_engine.py implementieren mit Provider-Unterscheidung
3. Intent-Confidence-Berechnung für Gemini hinzufügen (falls nicht vorhanden)
4. Intent-Confidence-Threshold für Gemini definieren und konfigurierbar machen
5. Tool-Ausführungs-Blockade in execution_dispatcher.py implementieren: Bei geringer Confidence für Gemini → Kein Tool-Call, stattdessen Klärungsfrage
6. System-Prompt für Gemini bei ambigen Anfragen anpassen (falls nötig für Klärungsfrage-Erzeugung)
7. Provider-spezifische Unterscheidung sicherstellen: Nur Gemini wird blockiert, GPT-Verhalten bleibt unverändert

**Acceptance Criteria:**
- [x] Intent Engine erkennt ambige Anfragen für Gemini
- [x] Intent-Confidence wird für Gemini evaluiert
- [x] Intent-Confidence-Threshold ist definiert und konfigurierbar
- [x] Tool-Ausführung wird bei geringer Confidence für Gemini blockiert
- [x] Gemini stellt stattdessen Klärungsfrage
- [x] GPT-Verhalten bleibt unverändert (Provider-Parity ohne Regression)
- [x] Code ist syntaktisch korrekt (py_compile bestanden)

**Status:** DONE (2026-05-14)

**Tests:**
- Unit Test: Ambiguity-Detection für Gemini wird getriggert
- Unit Test: Intent-Confidence-Berechnung für Gemini
- Integration Test: Tool-Ausführungs-Blockade bei geringer Confidence
- Backend-Log-Check: Ambiguity-Detection und Confidence werden geloggt

**Model:**
- **Assigned Model:** SWE 1.6
- **Reason:** Multi-file Backend-Logik mit Provider-spezifischen Unterscheidungen, erfordert Codebase-Verständnis und Intent-Engine-Expertise

---

## TASK-037-02 – TC-005-GEMINI Retest durchführen

**Ziel:**
TC-005-GEMINI mit dem Fix validieren und sicherstellen, dass "Clarification requested / No tool executed" erreicht wird.

**Beschreibung:**
Nach Implementierung der Gemini-spezifischen Ambiguity-Detection muss TC-005-GEMINI erneut getestet werden. Der Test muss zeigen, dass Gemini bei der ambigen Anfrage "Ich brauche Infos dazu" eine Klärungsfrage stellt und kein Tool ausführt.

**Files:**
- documentation/test-results/TEST-RUN-2026-05-13-002/TC-005-GEMINI_evidence.json (neu generieren)
- Test-Runner-Konfiguration (falls nötig)

**Steps:**
1. TC-005-GEMINI Test ausführen mit Prompt "Ich brauche Infos dazu"
2. Evidence-Datei analysieren
3. Validieren: "Clarification requested / No tool executed"
4. Vergleich mit TC-005-GPT (sollte weiterhin PASS)
5. Test-Ergebnis dokumentieren

**Acceptance Criteria:**
- [x] TC-005-GEMINI besteht mit "Clarification requested / No tool executed"
- [x] Keine Tool-Ausführung bei ambiger Anfrage
- [x] Klärungsfrage wird angezeigt
- [x] TC-005-GPT besteht weiterhin (keine Regression)

**Status:** DONE (2026-05-14) - PASS mit Context-Isolation-Fix

**Tests / Validierung:**
- Automated TestRun für TC-005-GEMINI
- Evidence-Check: response enthält Klärungsfrage
- Evidence-Check: tool_call_expected ist null oder keine Tools ausgeführt

**Model:**
- **Assigned Model:** SWE 1.6
- **Reason:** Test-Validierung und Evidence-Analyse, erfordert Verständnis des Test-Systems

---

## Zusammenfassung

Diese Tasks implementieren Gemini-spezifische Ambiguity-Detection, um Provider-Parity mit GPT zu erreichen. Der Fokus liegt auf:
1. Gemini-spezifische Logik in der Intent Engine
2. Intent-Confidence-Threshold für Gemini
3. Tool-Ausführungs-Blockade bei geringer Confidence
4. Validierung durch TC-005-GEMINI Retest

Die Tasks sind sequenziell auszuführen, da jede Task auf der vorherigen aufbaut.
