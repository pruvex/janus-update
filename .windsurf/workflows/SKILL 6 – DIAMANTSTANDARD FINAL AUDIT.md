---
description: Diamantstandard Phase 5 â€“ Final Audit & Release Gate mit risikobasiertem Audit-Modell. PrÃ¼ft vollstÃ¤ndige Implementierung aus Skill 4 gegen Task-Spec und Skill-3-Prechecks. Entscheidet Release-FÃ¤higkeit (PASS / PASS WITH FIXES / BLOCKED).
---

## ðŸŽ¯ PURPOSE

Dieser Skill ist das **finale QualitÃ¤ts- und Release-Gate** im Janus Diamantstandard Workflow.

Er entscheidet:

- Ist die gesamte Spec nach allen Subtasks wirklich fertig?
- Entspricht alles der Spec?
- Gibt es Regressionen oder Scope Drift?
- Darf Dokumentation/Release nach kompletter Umsetzung erfolgen?

KEINE IMPLEMENTATION. KEIN CODE.

WICHTIG:
- Skill 6 ist nur das finale Audit nach kompletter Spec-Umsetzung.
- Skill 6 darf nicht nach jedem Subtask verwendet werden.
- Skill 6 darf nur fortfahren, wenn das Audit-Paket `Remaining Tasks: keine` und `Spec Implementation Complete: YES` enthÃ¤lt.
- Solange weitere Tasks offen sind, muss der User zurÃ¼ck zu Skill 4 fÃ¼r den nÃ¤chsten Target Task.

---

## ðŸ¤– MODEL RULE

DEFAULT MODEL:
- Risikobasiert gemÃ¤ÃŸ `Audit Model Gate` aus Skill 4.
- GPT-5.5 bleibt Pflicht bei `Audit Risk: HIGH`, `Audit Risk: CRITICAL` oder unklarer Risikoklasse.

ALLOWED AUDIT MODELS:
- `Kimi k2.5` nur fÃ¼r LOW-Risk Audits mit deterministischem, lokalem Scope.
- `SWE 1.6` fÃ¼r LOW oder MEDIUM Risk Audits mit eindeutigem Scope und PASS-Validierung.
- `GPT-5.5` fÃ¼r HIGH, CRITICAL, unklare, widersprÃ¼chliche oder releasekritische Audits.

AUDIT MODEL GATE:
- Skill 6 MUSS zu Beginn das `Audit Model Gate` aus dem Compact Audit Package prÃ¼fen.
- Wenn kein `Audit Model Gate` enthalten ist, MUSS Skill 6 konservativ selbst klassifizieren.
- Wenn die Klassifizierung nicht eindeutig LOW oder MEDIUM ist, MUSS GPT-5.5 verwendet werden.
- Wenn das aktive Modell schwÃ¤cher ist als das erforderliche Audit-Modell, MUSS Skill 6 stoppen und den Modellwechsel verlangen.

RISK RULES:
- LOW:
  - reine Doku-/Text-/Workflow-Ã„nderung
  - kleine lokale UI-/CSS-/Label-Ã„nderung
  - einzelne deterministische Test-/Config-ErgÃ¤nzung
  - keine Backend-/Persistenz-/IPC-/Security-/Release-Ã„nderung
  - alle Validierungen PASS
  - erlaubt: `Kimi k2.5` oder `SWE 1.6`
- MEDIUM:
  - kleine bis mittlere mehrdateiige Ã„nderung
  - UI/API-Kopplung ohne Persistenz/Security/Release
  - Tests PASS und Scope eindeutig
  - erlaubt: `SWE 1.6`
- HIGH oder CRITICAL:
  - Backend-Kernlogik, Persistenz, DB, Migration, Auth/Security, Electron/IPC, Release/Packaging/Auto-Update, Model Routing, Provider, Tool Calls, Memory, Context, RAG oder mehrere Subsysteme
  - fehlende/fehlgeschlagene Tests, `PARTIAL`, Known Risks, Fix-Loop, unklare Akzeptanz oder mÃ¶gliche Regression
  - Pflicht: `GPT-5.5`

CHAT RULE:
- Skill 6 SOLL in einem neuen Chat gestartet werden.
- Der Nutzer soll explizit aufgefordert werden, einen neuen Audit-Chat mit dem empfohlenen Audit-Modell zu öffnen und nur das Compact Audit Handover aus Skill 4 einzufügen.
- Wenn Skill 6 im selben langen Implementierungs-Chat gestartet wird, MUSS der Skill trotzdem ausschließlich das Compact Audit Package verwenden und den übrigen Chatverlauf ignorieren.
- Kein vollständiger Chatverlauf, keine Debug-Diskussionen und keine nicht genannten Dateien als Audit-Grundlage verwenden.

ESCALATION RULE:

Wenn eine der folgenden Bedingungen erfÃ¼llt ist:

- Code / Logs / Tests nicht eindeutig interpretierbar
- widersprÃ¼chliche Task-Spec oder Skill-3 Output
- fehlende Deterministik in Bewertung mÃ¶glich
- mehrere plausible Interpretationen eines Fehlers
- Audit Risk ist HIGH/CRITICAL/unklar und aktives Modell ist nicht GPT-5.5

âž¡ï¸ STOP EXECUTION

OUTPUT:

MODEL SWITCH REQUIRED: <aktuelles Modell> â†’ <erforderliches Audit-Modell>  
Reason: <kurze technische BegrÃ¼ndung>  

FOLLOW-UP:
â†’ neuer Chat erforderlich
â†’ Skill 6 erneut ausfÃ¼hren mit gewÃ¤hltem Modell

---

## ðŸ“¥ INPUT

- kompletter Task-Set (aus Skill 2)
- Implementierung (Skill 4 Outputs)
- Pre-Check Ergebnisse (Skill 3)
- Repo-State / Codebase Snapshot
- Test Results (Unit / Integration / E2E)
- Pipeline Status mit `Completed Tasks = alle`, `Remaining Tasks = keine` und `Spec Implementation Complete: YES`

---

## ðŸ“Œ COMPACT AUDIT PACKAGE MODE

Skill 6 MUSS kostenbewusst arbeiten und darf keinen vollstÃ¤ndigen Chatverlauf als Audit-Grundlage verlangen. Das Modell richtet sich nach dem `Audit Model Gate`; GPT-5.5 bleibt Pflicht fÃ¼r HIGH/CRITICAL/unklare Audits.

Empfohlener Ablauf:
1. Neuen Chat öffnen.
2. Das im Skill-4-Handover empfohlene Audit-Modell auswählen.
3. Das von Skill 4 erzeugte `BEGIN COPY` / `END COPY` Compact Audit Handover einfügen.
4. Audit nur gegen diese Artefakte durchführen.

Wenn der Nutzer Spec, Task-Datei(en), Pre-Check Ergebnis, geÃ¤nderte Dateien, Diff und Testergebnisse nennt, sind diese Artefakte automatisch das verbindliche Audit-Paket.

Der Skill MUSS dann:

- die Feature-Spec als primÃ¤re Release-Anforderung verwenden
- Task-Datei(en) aus Skill 2 als Umsetzungsvertrag verwenden
- Pre-Check Ergebnisse als Gate-Nachweis prÃ¼fen
- Changed-Files-Liste und Diff nur gegen Spec/Tasks bewerten
- Testergebnisse als Validierungsnachweis verwenden
- Chatverlauf, frÃ¼here Diskussionen und zusÃ¤tzliche mÃ¼ndliche Nebeninformationen ignorieren, sofern sie den Artefakten widersprechen oder Ã¼ber sie hinausgehen
- keine neuen Requirements, ArchitekturvorschlÃ¤ge oder Nice-to-have-Ideen ergÃ¤nzen
- nur release-relevante Findings melden

Minimaler gÃ¼ltiger User-Aufruf:

```text
/Skill 6 â€“ Diamantstandard Final Audit mit kompaktem Audit-Paket:
WICHTIG:
- Neuer Chat mit dem empfohlenen Audit-Modell aus Skill 4.
- Nur dieses Paket als Audit-Grundlage verwenden.
- Früheren Chatverlauf ignorieren.
- Wenn Audit Risk HIGH/CRITICAL/unklar ist: GPT-5.5 verwenden.

Audit Model Gate:
- Audit Risk: <LOW | MEDIUM | HIGH | CRITICAL>
- Recommended Audit Model: <Kimi k2.5 | SWE 1.6 | GPT-5.5>
- Reason: <kurze BegrÃ¼ndung>

Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
Target Task: ALL COMPLETED
Pre-Check: <PRE-CHECK Ergebnis oder Datei>
Changed Files: <Liste>
Diff: <Git Diff oder relevante AuszÃ¼ge>
Tests: <Unit/Integration/E2E Ergebnisse>
Known Risks: <falls vorhanden>
Pipeline Status:
- Completed Tasks: <Liste>
- Remaining Tasks: keine
- Spec Implementation Complete: YES
```

Wenn das Audit-Paket unvollstÃ¤ndig ist:

```text
FINAL AUDIT PACKAGE INCOMPLETE

Missing:
- <konkrete fehlende Artefakte>

Action:
â†’ fehlende Artefakte nachreichen
â†’ keinen Release-Entscheid treffen
```

---

## âš™ï¸ EXECUTION FLOW

---

### 1. SPEC ALIGNMENT CHECK

Vergleich:

- Task-Spec vs Implementierung
- Acceptance Criteria vs tatsÃ¤chliches Verhalten
- Edge Cases vs Implementierung

PrÃ¼fe:

- nichts fehlt
- nichts Ã¼berschÃ¼ssig implementiert
- keine Scope-Erweiterung

---

### 2. CODE CONSISTENCY CHECK

PrÃ¼fe:

- keine broken imports
- keine toten Codepfade
- keine inkonsistenten Module
- keine API/IPC mismatchs
- keine UI/Selector Drift

---

### 3. TEST VALIDATION

PrÃ¼fe:

- Unit Tests: PASS
- Integration Tests: PASS
- E2E Tests: PASS (falls definiert)

Validiere zusÃ¤tzlich:

- Tests testen echte Logik (kein Fake-Mocking der Kernlogik)
- Tests entsprechen Spec-Verhalten

---

### 4. REGRESSION CHECK

PrÃ¼fe:

- keine bestehenden Features beschÃ¤digt
- keine globalen Seiteneffekte
- keine Breaking Changes auÃŸerhalb Scope

---

### 5. SKILL 3 PRE-CHECK COMPLIANCE CHECK

Validiere:

- alle Pre-Checks eingehalten
- keine ignorierten Blocker
- keine Ã¼bersprungenen Validierungen

---

### 6. RELEASE DECISION ENGINE

Entscheidung:

### âœ… PASS
Wenn:

- alle Tests bestehen
- Spec vollstÃ¤ndig erfÃ¼llt
- keine Regressionen
- keine offenen Blocker

---

### âš ï¸ PASS WITH FIXES
Wenn:

- kleine, sichere Fixes mÃ¶glich
- keine ArchitekturÃ¤nderung nÃ¶tig
- keine Scope-Verletzung

---

### âŒ BLOCKED
Wenn:

- Spec nicht erfÃ¼llt
- Tests kritisch fehlschlagen
- Regression vorhanden
- Architekturproblem erkannt

---

### 6.1 FINAL-SPEC COMPLETION GATE (HARD REQUIREMENT)

Skill 6 MUSS vor dem Audit prÃ¼fen, ob die komplette Spec-Umsetzung abgeschlossen ist.

Skill 6 darf nur fortfahren, wenn gilt:

- `Remaining Tasks: keine`
- `Spec Implementation Complete: YES`
- Skill 4 hat eine automatische Gesamtvalidierung ausgefÃ¼hrt.
- Skill 4 hat einen erfolgreichen manuellen Janus-Gesamttest als Evidence geliefert.

Wenn noch Tasks offen sind:

```text
FINAL AUDIT BLOCKED: SPEC NOT COMPLETE

Reason:
- Es sind noch offene Tasks vorhanden.

Action:
â†’ Starte Skill 4 mit dem nÃ¤chsten offenen Target Task.
â†’ Final Audit erst nach Abschluss aller Tasks ausfÃ¼hren.
```

Pflichtstatus im Audit:

```text
Pipeline Completion Status:
- Completed Tasks: <Liste>
- Remaining Tasks: keine
- Spec Implementation Complete: YES
```

Bei `Spec Implementation Complete: NO` ist Skill 6 BLOCKED und Skill 7 verboten.

---

### 7. MANUAL JANUS TEST EVIDENCE CHECK (HARD REQUIREMENT)

Skill 6 MUSS prÃ¼fen, ob Skill 4 nach automatischer Validierung einen realen manuellen Janus-Test durch den User eingefordert und als erfolgreich bestÃ¤tigt bekommen hat.

Wenn ein manueller Janus-Test bereits im Skill-4-Audit-Paket enthalten ist:

- Skill 6 darf keinen zweiten identischen manuellen Test verlangen.
- Skill 6 MUSS die Test-Evidence im Audit berÃ¼cksichtigen.
- Skill 6 MUSS bei Abweichungen `BLOCKED` oder Skill-5-Debug empfehlen.

Wenn kein manueller Janus-Test im Skill-4-Audit-Paket enthalten ist:

- Skill 6 darf nicht `READY FOR RELEASE` melden.
- Skill 6 MUSS `FINAL AUDIT PACKAGE INCOMPLETE` oder `BLOCKED: MANUAL JANUS TEST MISSING` ausgeben.
- Skill 6 MUSS den User zurÃ¼ck zum Manual-Janus-Test-Gate aus Skill 4 schicken.

Nur wenn `Spec Implementation Complete: YES` ist, darf Skill 6 zusÃ¤tzlich einen finalen Smoke-Test fÃ¼r die gesamte Feature-Spec empfehlen.

Dieser finale Smoke-Test MUSS enthalten:

- Startpunkt im Produkt
- konkrete User-Aktion
- erwartetes Gesamtergebnis
- Abweichungsregel zu Skill 5

```text
Finaler Janus-Smoke-Test, nur nach letztem Task:
1. Ã–ffne Janus.
2. Stelle sicher, dass <relevanter Zustand> aktiv ist.
3. FÃ¼hre den vollstÃ¤ndigen Feature-Flow aus:
   <Klickpfad/Prompt>
4. Erwartetes Ergebnis:
   <konkreter sichtbarer Gesamtzustand>
5. Falls das Ergebnis abweicht:
   - Starte Skill 5 mit Fehlerbeschreibung und relevanten Logs.
```

Wenn ein manueller Produkttest fÃ¼r das Feature nicht sinnvoll mÃ¶glich ist, MUSS Skill 6 das explizit begrÃ¼nden und stattdessen die beste verifizierbare Evidence nennen.

---

## ðŸ“¤ OUTPUT FORMAT

```text id="skill5_output"
FINAL AUDIT RESULT: PASS | PASS WITH FIXES | BLOCKED

Zusammenfassung:
- Feature: <name>
- Tasks: <IDs>
- Overall Status: <status>

Spec-Compliance:
- OK | PARTIAL | FAIL

Testergebnisse:
- Unit: PASS | FAIL
- Integration: PASS | FAIL
- E2E: PASS | FAIL

Findings:
- <bullet issues>

Angewendete Fixes (falls vorhanden):
- <list>

RegressionsprÃ¼fung:
- CLEAN | ISSUES FOUND

Risiko-Level:
- LOW | MEDIUM | HIGH

Empfehlung:
- READY FOR RELEASE | NEEDS FIXES | DO NOT RELEASE

Manual Janus Test Evidence:
- Status: PRESENT | MISSING | N/A WITH REASON
- Source: Skill 4 Manual Janus Validation Gate
- Ergebnis: PASS | FAIL | N/A

Finaler Janus-Smoke-Test:
- Nur wenn Spec Implementation Complete: YES
- Startpunkt: <wo im Produkt>
- Aktion: <konkrete Schritte>
- Erwartetes Ergebnis: <sichtbarer Soll-Zustand>
- Wenn Ergebnis abweicht: <Skill-6-Handoff an SWE 1.6 mit tatsÃ¤chlichem Output und Backendlog>

NÃ¤chster Schritt:
- Wenn Final Audit PASS oder PASS WITH FIXES ist: Skill 7 `/SKILL 7 â€“ DOKUMENTATIONSUPDATE` ausfÃ¼hren.
- Wenn Skill 6 BLOCKED ist: keine Dokumentation, kein Release.

Pipeline Completion Status:
- Completed Tasks: <Liste>
- Remaining Tasks: keine
- Spec Implementation Complete: YES

Copy-Paste-Prompt fÃ¼r Skill 7 `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`:

Nur ausgeben, wenn `Spec Implementation Complete: YES` und Final Audit `PASS` oder `PASS WITH FIXES` ist.

```text
@[/SKILL 7 – DOKUMENTATIONSUPDATE]

Post-Implementation Package:

Feature:
<Feature-Name>

Final Audit:
FINAL AUDIT RESULT: <PASS | PASS WITH FIXES>
Recommendation: <READY FOR RELEASE | NEEDS FIXES>

Spec:
<source spec file>

Task:
<task file>

Changed Files:
- <Datei 1>
- <Datei 2>

Test Results:
- <Unit/Integration/E2E Ergebnisse>

Version:
- Skill 7 soll die Version automatisch erhÃ¶hen.
- Kein manueller Version-Bump im Release-Skill.

Manueller Janus-Test:
- Status: <noch auszufÃ¼hren | PASS | FAIL>
- Anleitung: <kurze Testanleitung aus Skill 6>
- Falls FAIL: Skill 7 stoppen und Skill 5 `/SKILL 5 â€“ FEATURE DEBUG` mit SWE 1.6 starten.

Skill 5:
- Status: <not needed | FIXED + retest PASS | required>
- Falls required: Skill 7 nicht ausfÃ¼hren.

Capability Sync:
- PrÃ¼fe, ob eine neue user-visible Capability entstanden ist.
- Falls nein: "Keine neue Capability erforderlich."
- Falls ja: Produktsprachlich in Capability Registry synchronisieren, ohne Implementierungsdetails.

WHAT_I_LEARNED:
- Nur ergÃ¤nzen, wenn ein wiederverwendbares technisches Learning entstanden ist.
- Kein vollstÃ¤ndiges WHAT_I_LEARNED lesen; nur gezielte Duplikats-/Pattern-Suche.

Scope:
Nur validierte Ã„nderungen aus diesem Final Audit dokumentieren.
```
ðŸš« RESTRICTIONS
keine neuen Features
keine ArchitekturÃ¤nderungen
keine Task-Neudefinition
keine Scope-Erweiterung
keine â€žVerbesserungsideenâ€œ
ðŸ§  ERROR HANDLING

Wenn Task oder Code nicht eindeutig prÃ¼fbar:

BLOCKED: NON-DETERMINISTIC AUDIT STATE

â†’ kein Release mÃ¶glich

ðŸ§  OUTPUT GUARANTEE

Dieser Skill liefert immer:

deterministische Release-Entscheidung
klare BegrÃ¼ndung
keine Interpretationsfreiheit
