---
description: Kostenoptimierte 10/10 Diamond-Feature-Pipeline von ChatGPT-Spec bis Skill 6 Final Audit
---

# Diamond Feature Pipeline â€“ Cost-Optimized 10/10 Flow

Use this workflow when a new feature starts from a ChatGPT-generated Janus Feature Spec.

Goal:
- Keep GPT-5.5 usage minimal.
- Use artifact files instead of chat history.
- Prevent context bleed, scope creep, and blind fix loops.
- Ensure every release-relevant feature passes the same deterministic gate chain.
- Optionally route small bugs, changes, and enhancements through the Backlog Skill 1–3 intake before entering Skill 1–8.

---

## 0. Model Strategy

Default:

```text
Skill 1: SWE 1.6
Skill 2: SWE 1.6
Skill 3: SWE 1.6
Skill 4: SWE 1.6 or Kimi k2.5 only if explicitly assigned in the task
Skill 5: SWE 1.6
Skill 6: GPT-5.5
Skill 7: SWE 1.6
Skill 8: SWE 1.6

Backlog Skill 1: SWE 1.6
Backlog Skill 2: GPT-5.5
Backlog Skill 3: SWE 1.6

System Health: SWE 1.6, escalate to GPT-5.5 if required
```

Rules:
- GPT-5.5 is not a regular execution model.
- GPT-5.5 is used for Skill 6 Final Audit and explicit escalation only.
- Kimi k2.5 is only for deterministic single-file, data, string, or test tasks.
- SWE 1.6 is default for integration, multi-file, security, persistence, Electron/IPC, and codebase reasoning.

---

## 0.5 Diamond 10/10 Handoff Rules

Diese Regeln gelten fÃ¼r die komplette Pipeline:

- Jeder Skill arbeitet artefaktbasiert, nicht aus Chat-Erinnerung.
- Jeder Handoff muss eine klare Dateiliste enthalten.
- Jeder Handoff muss einen Copy-Paste-Prompt fÃ¼r den nÃ¤chsten Skill enthalten.
- Skill 2 darf immer nur genau einen nÃ¤chsten Target Task freigeben.
- Skill 3 validiert genau einen Target Task und liefert einen Copy-Paste-Prompt fÃ¼r Skill 4.
- Skill 4 implementiert genau einen Target Task, testet automatisch und liefert bei offenen Tasks einen Copy-Paste-Prompt fÃ¼r den nÃ¤chsten Skill-4-Lauf.
- Skill 4 liefert den Skill-6-Final-Audit-Handover erst nach Abschluss aller Tasks, automatischer Gesamtvalidierung und erfolgreichem manuellem Janus-Gesamttest.
- Skill 5 ist der iterative Debug-Gate, wenn Skill 4/Skill 6 blockiert oder der manuelle Janus-Gesamttest fehlschlÃ¤gt.
- Skill 5 lÃ¤uft mit SWE 1.6 fÃ¼r maximal drei Iterationen; danach gibt Skill 5 ein kompaktes GPT-5.5-Eskalationshandover aus.
- Skill 6 lÃ¤uft mit GPT-5.5 in einem neuen Chat, nutzt nur das finale Compact Audit Package und liefert danach einen Copy-Paste-Prompt fÃ¼r `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`.
- Skill 7 ist das Dokumentationsupdate und darf erst nach erfolgreichem Skill-5-/Skill-6-Gate laufen.
- Wenn eine Umsetzung aus einem `BACKLOG-XXX` Item stammt, aktualisiert Skill 7 das Backlog und verschiebt erledigte Items nach `DONE`.
- System Health prüft Hygiene, Struktur und technische Qualität; größere Findings gehen ins Backlog und werden danach über Backlog Skill 2/3 verarbeitet.
- `/save` ist der verpflichtende Atomic-State-Save an stabilen Savepoints und committed/pusht auf `backup develop`.
- `/save` ersetzt keinen Production Release und kein GitHub Publishing.
- User-facing Zusammenfassungen, Bewertungen, Next Steps und Testanleitungen werden auf Deutsch ausgegeben.
- Technische Namen, Pfade, Modellnamen und Fehlercodes bleiben unverÃ¤ndert.

---

## 0.4 Optional System Health Hygiene Check

Nutze diesen Skill unabhängig von Feature-Umsetzungen, um Systemordnung und technische Hygiene zu prüfen:

```text
SYSTEM HEALTH – HYGIENE CHECK
```

Modi:

```text
1) DAILY – Start-of-Day Hygiene Check
2) WEEKLY – Weekly Structure Check, empfohlen montags
3) MONTHLY – Monthly Architecture Hygiene Check, empfohlen am 1. des Monats
```

Regeln:
- Default Model: SWE 1.6.
- Wenn Architektur-/Strukturentscheidung nicht deterministisch ist, stoppt der Skill und fordert GPT-5.5-Eskalation.
- Keine großen Refactors, keine Features, kein Release, kein Version-Bump.
- Sichere Auto-Fixes nur nach expliziter Freigabe.
- Größere oder riskante Findings werden als `Quelle: System Health` in `documentation/backlog/BACKLOG.md` aufgenommen.

---

## 0.6 Optional Backlog Intake for Bugs, Changes, and Small Enhancements

Nutze diese Vorstufe, wenn kein vollständiger Feature-Spec vorliegt und der Nutzer nur einen Bug, eine kleine Änderung oder eine Ergänzung beschreibt:

```text
BACKLOG SKILL 1 – INTAKE TRIAGE
→ BACKLOG SKILL 2 – REVIEW PRIORISIERUNG
→ BACKLOG SKILL 3 – ROUTING_ENRICHMENT
→ BACKLOG SKILL 3 – SELECTED_HANDOFF für genau ein ausgewähltes Item
→ SKILL 1, SKILL 2, SKILL 3 oder SKILL 4 je nach Entry Point und Handoff
```

Backlog-Artefakte:

```text
documentation/backlog/BACKLOG.md
documentation/Planned Features/backlog_BACKLOG-XXX_<slug>.md
documentation/tasks/backlog_BACKLOG-XXX_<slug>.md
```

Regeln:
- Backlog Skill 1 sammelt und klassifiziert.
- Backlog Skill 2 bewertet und priorisiert.
- Backlog Skill 3 ergänzt im Default-Modus `ROUTING_ENRICHMENT` fehlende `Entry Point` Metadaten für Dashboard und Pipeline-Steuerung.
- Backlog Skill 3 erzeugt nur im expliziten Modus `SELECTED_HANDOFF` den Diamond-Handoff für genau ein ausgewähltes Item und verschiebt es nach `IN PROGRESS`.
- Skill 7 schließt erledigte Backlog-Items ab, verschiebt sie nach `DONE` und bewahrt Routing-/Handoff-Felder für die Dashboard-Historie.

---

## 1. Create Final Feature Spec

Create the Feature Spec in ChatGPT using the Janus Diamant Spec Generator prompt.

Wenn vor der Spec ein Brainstorming-Chat verwendet wurde:

- zuerst den ChatGPT Brainstorming Prompt verwenden
- am Ende eine eindeutige `DECISION SUMMARY` erzeugen
- der Spec Prompt darf nur die letzte `DECISION SUMMARY` als bindenden Input verwenden
- frÃ¼here Diskussionen, verworfene Optionen, alte EntwÃ¼rfe und nicht-summary Kontext ignorieren

If ChatGPT returns:

```text
# BLOCKING QUESTIONS
```

then answer only those questions and regenerate the final Spec.

Do not proceed until the final Spec contains:

```text
# JANUS FEATURE SPEC â€“ DIAMANTSTANDARD v2
```

and:

```text
12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
```

---

## 2. Save Spec Artifact

Save only the final Spec as a file:

```text
documentation/Planned Features/<FEATURE_NAME>.md
```

Do not include:
- Chat discussion
- Blocking-question history
- old drafts
- model notes
- implementation notes

The Spec file is the Single Source of Truth.

---

## 3. Run Skill 1 â€“ Spec to Task Compiler

Minimal invocation:

```text
/SKILL 1 â€“ Spec to Task Compiler mit folgender Spec-Datei:
documentation/Planned Features/<FEATURE_NAME>.md
```

Expected result:
- deterministic task file
- task coverage against Spec
- model annotation per task: `SWE 1.6` or `Kimi k2.5`
- keine eigenstÃ¤ndigen Analyse-/Design-/Verify-/Non-Regression-only Tasks
- Next Step nennt explizit: Skill 2 mit `SWE 1.6`
- Modellzuweisungen sind Task-AusfÃ¼hrungsmodelle fÃ¼r spÃ¤tere Skill-3-/Skill-4-LÃ¤ufe, nicht fÃ¼r Skill 2

Stop if Skill 1 returns:

```text
SPEC FILE INVALID
SPEC INSUFFICIENT
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5
```

---

## 4. Run Skill 2 â€“ Task Breakdown Engine

Minimal invocation:

```text
/SKILL 2 â€“ TASK BREAKDOWN ENGINE mit folgenden Artefakten:
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
```

Expected result:
- implementation-ready task definitions
- no new requirements
- no scope expansion
- validated model assignment
- Prozess-only Tasks wurden entfernt oder als Steps/Acceptance Criteria/Tests integriert
- `READY FOR SKILL 3 SINGLE-TASK PRE-CHECK`
- genau ein `Target Task`
- genau ein `Assigned Model`
- keine Batch-Freigabe spÃ¤terer Tasks

Stop if Skill 2 returns:

```text
TASK ARTIFACTS INVALID
TASK AMBIGUOUS â€“ NEED SPEC CLARIFICATION
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5
```

---

## 5. Run Skill 3 â€“ Pre-Implementation Verification

Minimal invocation:

```text
/SKILL 3 â€“ PRE-IMPLEMENTATION VERIFICATION mit folgenden Artefakten:
Target Task: TASK-XXX.Y
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Task: documentation/tasks/<TASK_FILE>.md
```

Expected result:

```text
PRE-CHECK PASSED
```

Skill 3 muss zusÃ¤tzlich ausgeben:
- Skill-4-Dateiliste
- Copy-Paste-Prompt fÃ¼r Skill 4
- zugewiesenes Modell fÃ¼r genau diesen Target Task
- Stop-Regel gegen automatische AusfÃ¼hrung spÃ¤terer Tasks

Stop if Skill 3 returns:

```text
PRE-CHECK ARTIFACTS INVALID
PRE-CHECK FAILED
PRE-CHECK BLOCKED
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5
```

No implementation may happen before Skill 3 passes.

---

## 6. Run Skill 4 â€“ Executioner

Minimal invocation:

```text
/SKILL 4 â€“ EXECUTIONER mit folgenden Artefakten:
Target Task: TASK-XXX.Y
Assigned Model: <SWE 1.6 | Kimi k2.5>
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Task: documentation/tasks/<TASK_FILE>.md
Pre-Check: <PRE-CHECK PASSED Ergebnis oder Datei, falls vorhanden>
```

Expected result:
- implementation only within validated task scope
- tests added/executed according to task
- no architecture changes outside task
- no new features
- Skill 4 stoppt nach genau diesem Task
- nach erfolgreichem Task mit PASS-Tests: `/save` ausfÃ¼hren, bevor der nÃ¤chste Skill gestartet wird
- wenn weitere Tasks existieren: Copy-Paste-Prompt fÃ¼r den nÃ¤chsten Skill-4-Lauf mit dem nÃ¤chsten Target Task
- wenn keine weiteren Tasks existieren: automatische Gesamtvalidierung, manueller Janus-Gesamttest und erst danach Skill-6-Dateiliste plus Copy-Paste-Prompt fÃ¼r einen neuen GPT-5.5 Final-Audit-Chat

Stop if Skill 4 returns:

```text
EXECUTION ARTIFACTS INVALID
TASK EXECUTION FAILED
FIX LOOP LIMIT REACHED
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5
```

Fix loop rule:
- after two failed targeted fix attempts on the same task, stop
- do not continue blind patching
- re-run Skill 2 or escalate with compact failure package

---

## 7. Repeat Skill 4 Per Task

For each task:

```text
Skill 4 Execution
â†’ task validation evidence
â†’ /save
â†’ next Skill-4 Copy-Handover if tasks remain
```

Proceed to Skill 6 only after:
- all required tasks are completed
- `Remaining Tasks: keine`
- Skill 4 completed automatic Gesamtvalidierung
- user confirmed the manual Janus-Gesamttest

Wichtig:
- Nie mehrere Tasks in einem Skill-4-Lauf implementieren.
- Bei gemischten Modellen nach jedem Task stoppen und mit dem zugewiesenen Modell des nÃ¤chsten Tasks neu starten.
- Der User lÃ¶st jeden nÃ¤chsten Task bewusst aus.
- Skill 6 ist kein Subtask-Audit, sondern nur das finale Spec-Audit nach vollstÃ¤ndiger Umsetzung.

---

## 8. Prepare Compact Skill 6 Audit Package

Do not use full chat history.

Open a new chat for the audit:
- Use GPT-5.5.
- Paste only the Compact Audit Package generated by Skill 4.
- Do not paste the full implementation chat.
- The audit must ignore prior chat context and evaluate only the named artifacts.

Prepare:

```text
Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
Target Task: ALL COMPLETED
Pre-Check: <PRE-CHECK results>
Changed Files: <list>
Diff: <git diff or relevant excerpts>
Tests: <Unit/Integration/E2E results>
Gesamt-Test Results: <Build/Unit/Integration/E2E/Smoke results>
Manual Janus Test Evidence: PASS
Known Risks: <if any>
Pipeline Status:
- Completed Tasks: <alle>
- Remaining Tasks: keine
- Spec Implementation Complete: YES
```

---

## 9. Run Skill 6 â€“ Final Audit with GPT-5.5

Skill 6 should be started in a new GPT-5.5 chat.

Minimal invocation:

```text
/Skill 6 â€“ Diamantstandard Final Audit mit kompaktem Audit-Paket:
WICHTIG:
- Neuer Chat mit GPT-5.5.
- Nur dieses Compact Audit Package verwenden.
- Früheren Chatverlauf ignorieren.

Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
Target Task: ALL COMPLETED
Pre-Check: <PRE-CHECK Ergebnis oder Datei>
Changed Files: <Liste>
Diff: <Git Diff oder relevante AuszÃ¼ge>
Tests: <Unit/Integration/E2E Ergebnisse>
Gesamt-Test Results: <Gesamtvalidierung>
Manual Janus Test Evidence: PASS
Known Risks: <falls vorhanden>
Pipeline Status:
- Completed Tasks: <alle>
- Remaining Tasks: keine
- Spec Implementation Complete: YES
```

Allowed final states:

```text
FINAL AUDIT RESULT: PASS
FINAL AUDIT RESULT: PASS WITH FIXES
FINAL AUDIT RESULT: BLOCKED
```

Rules:
- PASS: post-implementation documentation may proceed.
- PASS WITH FIXES: apply only listed fixes, then targeted re-audit if needed.
- BLOCKED: no documentation finalization and no release.

Skill 6 muss zusÃ¤tzlich ausgeben:
- BestÃ¤tigung, dass die manuelle Janus-Test-Evidence aus Skill 4 vorhanden ist
- finale Audit-Entscheidung fÃ¼r die komplette Spec
- Copy-Paste-Prompt fÃ¼r `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`

---

## 10. Run Skill 5 â€“ Feature Debug Gate

Der manuelle Janus-Gesamttest findet nach dem letzten Skill-4-Task und vor Skill 6 statt.

Wenn der manuelle Janus-Gesamttest wie erwartet funktioniert:

```text
â†’ Skill 5 wird Ã¼bersprungen.
â†’ Weiter mit Skill 6 Final Audit.
```

Wenn der manuelle Janus-Gesamttest NICHT wie erwartet funktioniert, oder Skill 4/6 Debug verlangt:

- Skill 4 returns `TASK EXECUTION FAILED`
- Skill 4 returns `FIX LOOP LIMIT REACHED`
- Skill 6 returns `BLOCKED`
- Skill 6 returns non-trivial `PASS WITH FIXES`
- the manual Janus-Gesamttest from Skill 4 does not match the expected result

Use:

```text
/SKILL 5 â€“ FEATURE DEBUG
```

Required package:

```text
Debug Package:
Feature: <Feature-Name>
Iteration: 1 | 2 | 3
Task: <task file / task id>
Spec: <source spec file>
Pre-Check: <PRE-CHECK result>
Final Audit / Skill 6: <result/findings>
Manueller Janus-Test:
- Prompt/Klickpfad: <was wurde getan>
- Erwartetes Ergebnis: <Soll>
- TatsÃ¤chliches Ergebnis: <Ist>
Backend Log: <relevanter Auszug oder Pfad/Datei>
Changed Files: <Liste>
Test Results: <Liste>
Known Risks: <falls vorhanden>
```

Rules:
- Skill 5 is not a normal happy-path implementation step; it is a manual-test/debug gate.
- Skill 5 always runs before Skill 7 when debug is required.
- Skill 5 uses SWE 1.6 by default.
- After each Skill-5 fix, Skill 5 must ask the user to rerun the Janus manual test.
- If the retest passes and Skill 5 changed code, run `/save`, then proceed to Skill 6 Re-Audit.
- If the retest fails and iteration is below 3, rerun Skill 5 with updated actual behavior and backend log.
- If the retest fails after iteration 3, Skill 5 must output `SKILL 5 ESCALATION REQUIRED` plus compact GPT-5.5 handover.
- Do not give GPT-5.5 the full backend log; use Skill 5's compressed escalation handover.

---

## 11. Run Skill 7 â€“ Dokumentationsupdate with Automatic Version Bump

Run only if Skill 6 or `/2_final-audit` returned `PASS` or `PASS WITH FIXES`.

Additionally, one of these must be true:

- manual Janus test passed and Skill 5 was not needed
- Skill 5 returned `SKILL 5 DEBUG RESULT: FIXED` and the user retest passed
- manual Janus test was explicitly marked `N/A` or deferred by Skill 6 with a non-blocking reason

After Skill 7 completed successfully:

```text
â†’ /save
```

Do not proceed to release before `/save` completed successfully.

Use:

```text
/SKILL 7 â€“ DOKUMENTATIONSUPDATE
```

Use the Copy-Paste-Prompt from Skill 6. It must include:
- Final Audit result
- Spec
- Task
- Changed Files
- Test Results
- Manual Janus Test status
- Skill 7 automatic version bump result
- Capability Sync decision
- WHAT_I_LEARNED decision

Stop if final audit is `BLOCKED`.

Also stop if:
- manual Janus test failed and Skill 5 has not resolved it
- Skill 6 requested re-run of Skill 4
- there is no clear final audit package
- Skill 5 returned `ESCALATION REQUIRED`, `BLOCKED`, or `OUT OF SCOPE`

---

## 12. Release Production

Run only after:
- final audit is `PASS` or `PASS WITH FIXES`
- post-implementation documentation completed
- Skill 7 automatic version bump completed and version files are consistent
- `/save` completed after Skill 7

Use:

```text
/SKILL 8 – BUILD RELEASE
```

Publishing still requires explicit user approval.

---

## Hard Stop Rules

Never continue if:
- Spec has blocking questions.
- Skill 1 reports insufficient Spec.
- Skill 2 reports ambiguous task.
- Skill 3 does not pass Pre-Check.
- Skill 4 reaches fix loop limit.
- Skill 6 returns BLOCKED.
- Skill 5 needs escalation, is blocked, or still needs retest.
- Skill 7 version bump is blocked or version files are inconsistent.
- Skill 7 completed but `/save` did not complete.
- Required release artifacts are missing.

---

## Cost Rules

- Do not paste full chat history into any skill.
- Use artifact files as handoff boundaries.
- Use GPT-5.5 only for Skill 6 or explicit escalation.
- Prefer re-generating a better Spec over expensive implementation fixes.
- Use targeted diffs and test outputs for audits.
- Do not read `WHAT_I_LEARNED.md` fully; search targeted patterns only when needed.

