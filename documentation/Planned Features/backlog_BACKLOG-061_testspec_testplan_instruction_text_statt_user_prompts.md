# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-061
- **Backlog Title:** TestSpec TestPlan Instruction-Text statt User-Prompts
- **Type:** IMPROVEMENT

## 2. Problem / Wunsch
TestSpec 05_ux_cost_safety_response_quality.md enthält im Functional Test Matrix Instruction-Text im "User Prompt / Action"-Feld statt echten User-Prompts. Der generierte TestPlan überträgt diese Instruction-Strings literal als prompt an Janus, was zu ASSERTION_MISMATCH führt.

## 3. Expected Behavior
TestSpec Functional Test Matrix muss konkrete User-Prompts enthalten (z.B. "Was kannst du?", "Mach das besser: Welcher Text?"), keine Meta-Instruktionen an den Testrunner ("Ask a simple Janus usage question").

## 4. Current Behavior
TestPlan enthält prompt: "Ask a simple Janus usage question", "Ask \"Mach das besser\" without target", "Ask a routine deterministic task". Der Testrunner sendet diese Strings literal an Janus, der mit Klärungsfragen antwortet. Die Test-Oracles erwarten Capability-Keywords, erhalten aber Klärungsantwortungen.

## 5. Scope
### IN SCOPE
- TestSpec 05_ux_cost_safety_response_quality.md Functional Test Matrix aktualisieren
- Instruction-Text durch konkrete User-Prompts ersetzen
- TestPlan neu generieren mit aktualisiertem TestSpec
- Validierung, dass neue TestPlan-Prompts echte User-Prompts sind

### OUT OF SCOPE
- TestPlan Generator ändern (nur TestSpec anpassen)
- Test-Oracles ändern (nur Prompts fixen)
- Andere TestSpecs

## 6. Functional Requirements
- Functional Test Matrix "User Prompt / Action"-Feld muss echte User-Prompts enthalten
- Keine Meta-Instruktionen wie "Ask a simple Janus usage question"
- TestPlan Generator muss aktualisierte Prompts korrekt übertragen

## 7. Acceptance Criteria
- [ ] TestSpec Functional Test Matrix enthält keine Instruction-Text-Prompts mehr
- [ ] Alle Prompts sind konkrete User-Prompts (z.B. "Was kannst du?", "Mach das besser: Welcher Text?")
- [ ] TestPlan neu generiert aus aktualisiertem TestSpec
- [ ] Neuer TestPlan enthält echte User-Prompts statt Instruction-Text
- [ ] TEST SKILL 1 zeigt keine Generator-Warnungen

## 8. Evidence
- documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md
- documentation/test-runs/TEST-RUN-2026-05-16-006_plan.json
- documentation/test-results/TEST-RUN-2026-05-16-006_results.json
- documentation/test-results/TEST-RUN-2026-05-16-006/TC-001-GPT_evidence.json
- documentation/test-results/TEST-RUN-2026-05-16-006/TC-002-GPT_evidence.json
- documentation/test-results/TEST-RUN-2026-05-16-006/SEC-002-GPT_evidence.json
- documentation/test-results/TEST-RUN-2026-05-16-006/SEC-003-GPT_evidence.json

## 9. Risks
- LOW: Nur TestSpec-Änderung, kein Produktcode

## 10. Validation Mapping
- Acceptance Criteria 1-2 → TestSpec Review
- Acceptance Criteria 3 → TEST SKILL 1 TestPlan-Generierung
- Acceptance Criteria 4 → TestPlan Validierung
- Acceptance Criteria 5 → TEST SKILL 1 Output-Check

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
