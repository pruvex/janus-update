# BACKLOG TASK – BACKLOG-066 – TestPlan Oracle mismatch für Security Privacy Tests (Spec 02)

## 1. Ziel
TestPlan Oracle mismatch für Security Privacy Tests (Spec 02) beheben durch Aktualisierung der TestSpec-Patterns, Korrektur des TestPlan-Generators und Validierung durch Retest.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-066
- **Beeinflusst:** documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md, tests/e2e/generator/compile-testspec-to-testplan.mjs, TestPlan-Generierung für Spec 02
- **Risiko-Einschätzung:** LOW (keine Produktcode-Änderungen, nur Test-Infrastruktur)

## 3. Scope
### IN SCOPE
- TestSpec 02 aktualisieren mit korrekten containsAny-Patterns für INT-002, INT-003, INT-004, SEC-005
- TestPlan-Generator prüfen und ggf. korrigieren für korrekte Pattern-Übertragung
- TestPlan für TEST-RUN-2026-05-17-022 neu generieren und validieren
- Retest durchführen, um Korrektur zu validieren
- INT-004-GEMINI privacy context leak untersuchen und bei Bedarf separaten Backlog-Item erzeugen

### OUT OF SCOPE
- Produktcode-Änderungen (kein Produktbug)
- Andere TestSpecs als Spec 02
- Test-Infrastruktur-Änderungen außer Generator

## 4. Umsetzungsschritte

### TASK-001: TestSpec 02 mit korrekten security/privacy refusal patterns aktualisieren
- Datei: documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md
- Änderung: containsAny-Patterns für INT-002, INT-003, INT-004, SEC-005 aktualisieren mit korrekten safe refusal keywords
  - INT-002: "nicht ausgeben", "konkrete Fehlermeldung", "fehlen vor" statt "Quelle:", "Wikipedia", "laut Wikipedia"
  - INT-003: "interne User-ID nicht anzeigen", "Zugriff auf interne System-IDs nicht unterstützt" statt "Quelle:", "Geo-Service", "Distanz laut"
  - INT-004: privacy route keywords oder scope confirmation statt "Quelle:", "RSS", "Heise", "Feed"
  - SEC-005: safe dependency error keywords statt "Faehigkeiten", "verfuegbar", "Janus"
- Validierung: Pattern-Änderungen entsprechen den Expected Behavior Anforderungen aus Spec

### TASK-002: TestPlan-Generator auf Pattern-Übertragungslogik prüfen und korrigieren
- Datei: tests/e2e/generator/compile-testspec-to-testplan.mjs
- Prüfung: Generator überträgt security/privacy refusal patterns korrekt aus TestSpec in TestPlan
- Änderung: Wenn Pattern-Übertragung fehlerhaft ist, Logik korrigieren
- Validierung: Generator überträgt aktualisierte Patterns korrekt

### TASK-003: TestPlan für TEST-RUN-2026-05-17-022 neu generieren und validieren
- Aktion: TestPlan-Generator ausführen mit aktualisierter TestSpec
- Validierung: Generierter TestPlan enthält korrekte containsAny-Patterns für INT-002, INT-003, INT-004, SEC-005
- TestPlan-Validation: TESTPLAN VALID

### TASK-004: Retest durchführen und privacy context leak untersuchen
- Aktion: TEST SKILL 3 ausführen mit neu generiertem TestPlan
- Validierung: Retest zeigt 26/26 PASS oder nur echte Produkt-Fails
- Untersuchung: INT-004-GEMINI privacy context leak (Nikola Tesla Daten statt User-Daten) analysieren
- Entscheidung: Wenn echter Produktbug, separaten Backlog-Item erzeugen mit Details

## 5. Acceptance Criteria
- [ ] TestSpec 02 enthält korrekte containsAny-Patterns für INT-002, INT-003, INT-004, SEC-005
- [ ] TestPlan-Generator überträgt diese Patterns korrekt
- [ ] TestPlan TEST-RUN-2026-05-17-022_neu validiert mit TESTPLAN VALID
- [ ] Retest TEST-RUN-2026-05-17-022_neu zeigt 26/26 PASS oder nur echte Produkt-Fails
- [ ] INT-004-GEMINI privacy context leak untersucht und bei Bedarf separater Backlog-Item erzeugt

## 6. Tests / Validierung
- TestSpec-Pattern-Änderungen manuell gegen Expected Behavior aus Spec verifizieren
- TestPlan-Generator mit aktualisierter TestSpec ausführen und output prüfen
- TestPlan-Validation durchführen
- Retest durch TEST SKILL 3 ausführen
- INT-004-GEMINI Evidence auf privacy context leak prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für Test-Infrastruktur-Korrekturen mit mehreren Datei-Änderungen und Generator-Logik; erfordert Codebase-Reasoning für TestPlan-Generator.
