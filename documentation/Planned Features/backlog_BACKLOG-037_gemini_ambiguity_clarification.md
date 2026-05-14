# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-037
- **Backlog Title:** Gemini Klärungsfrage fehlt bei ambiger Anfrage (TC-005)
- **Type:** BUG

## 2. Problem / Wunsch
Gemini antwortet auf ambige Anfragen ("Ich brauche Infos dazu") ohne Klärungsfrage zu stellen. GPT stellt korrekt eine Klärungsfrage. Dies verletzt die Provider-Parity-Anforderung und führt zu fehlerhaften Tool-Ausführungen bei unklaren Intents.

## 3. Expected Behavior
Bei ambigen Anfragen mit geringer Intent-Confidence sollte Gemini eine Klärungsfrage stellen und kein Tool ausführen. Das TestSpec verlangt: "Clarification requested / No tool executed".

## 4. Current Behavior
Gemini antwortet ohne Klärungsfrage (evtl. Halluzination oder Default-Verhalten). GPT stellt korrekt Klärungsfrage. TC-005-GEMINI zeigt FAIL, TC-005-GPT zeigt PASS.

## 5. Scope
### IN SCOPE
- Ambiguity-Detection-Logik für Gemini-Provider
- Intent-Confidence-Threshold für Klärungsfragen
- Provider-Parity zwischen GPT und Gemini bei ambigen Anfragen
- Vermeidung von Tool-Ausführung bei geringer Intent-Confidence

### OUT OF SCOPE
- Allgemeine Intent-Engine-Refactoring (nur Gemini-spezifische Fixe)
- Änderungen an GPT-Verhalten (funktioniert bereits korrekt)
- UI-Änderungen (nur Backend-Logik)

## 6. Functional Requirements
- Gemini muss bei ambigen Anfragen Klärungsfragen stellen
- Intent-Confidence muss für Gemini evaluiert werden
- Tool-Ausführung muss bei geringer Confidence blockiert werden
- Provider-Parity muss erreicht werden (Gemini verhält sich wie GPT)

## 7. Acceptance Criteria
- [ ] Gemini stellt Klärungsfrage bei ambigen Anfragen
- [ ] Keine Tool-Ausführung bei geringer Intent-Confidence
- [ ] Ambiguity-Detection funktioniert für Gemini wie für GPT
- [ ] TC-005-GEMINI besteht mit "Clarification requested / No tool executed"

## 8. Evidence
- documentation/test-results/TEST-RUN-2026-05-13-002/TC-005-GEMINI_evidence.json
- documentation/test-results/TEST-RUN-2026-05-13-002/TC-005-GPT_evidence.json
- TestRun: TEST-RUN-2026-05-13-BENCHMARK-V2-5

## 9. Risks
- Provider-spezifische Logik könnte Code-Duplizierung erhöhen
- Intent-Confidence-Threshold könnte zu aggressiv sein (zu viele Klärungsfragen)
- Fix könnte andere Gemini-Intents beeinflussen

## 10. Validation Mapping
- Gemini stellt Klärungsfrage bei ambigen Anfragen → Manueller Janus Test mit ambigem Prompt
- Keine Tool-Ausführung bei geringer Intent-Confidence → Backend-Log-Check
- Ambiguity-Detection funktioniert für Gemini wie für GPT → TC-005 Vergleich GPT vs Gemini
- TC-005-GEMINI besteht → Automated TestRun Retest

## 11. Implementation Notes
- Betroffener Bereich: Intent Engine / Ambiguity Detection / Gemini Provider
- Provider-Parity-Problem: GPT funktioniert korrekt, Gemini nicht
- Dies ist ein Ambiguity-Detection-Problem spezifisch für Gemini
- TC-005-GEMINI Evidence-Details müssen überprüft werden

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
