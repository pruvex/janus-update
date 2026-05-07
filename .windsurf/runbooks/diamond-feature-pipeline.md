---
description: Kostenoptimierte 10/10 Diamond-Feature-Pipeline von ChatGPT-Spec bis Skill 5 Final Audit
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
Skill 5: GPT-5.5
Skill 6: SWE 1.6
Skill 7: SWE 1.6
Skill 8: SWE 1.6

Backlog Skill 1: SWE 1.6
Backlog Skill 2: GPT-5.5
Backlog Skill 3: SWE 1.6

System Health: SWE 1.6, escalate to GPT-5.5 if required
```

Rules:
- GPT-5.5 is not a regular execution model.
- GPT-5.5 is used for Skill 5 Final Audit and explicit escalation only.
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
- Skill 4 implementiert genau einen Target Task, stoppt danach und liefert Dateiliste plus Copy-Paste-Prompt fÃ¼r einen neuen GPT-5.5-Skill-5-Chat.
- Skill 5 lÃ¤uft mit GPT-5.5 in einem neuen Chat, nutzt nur das Compact Audit Package, liefert eine manuelle Janus-Testanleitung und danach einen Copy-Paste-Prompt fÃ¼r `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`.
- Skill 6 ist der iterative Debug-Gate nach Skill 5 und manuellem Janus-Test.
- Skill 6 lÃ¤uft mit SWE 1.6 fÃ¼r maximal drei Iterationen; danach gibt Skill 6 ein kompaktes GPT-5.5-Eskalationshandover aus.
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
→ BACKLOG SKILL 3 – EXECUTION HANDOFF
→ SKILL 1, SKILL 2 oder SKILL 3 je nach Handoff
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
- Backlog Skill 3 erzeugt den Diamond-Handoff.
- Skill 7 schließt erledigte Backlog-Items ab und verschiebt sie nach `DONE`.

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
- wenn weitere Tasks existieren: nÃ¤chster manueller Skill-3-Handoff
- wenn keine weiteren Tasks existieren: Skill-5-Dateiliste und Copy-Paste-Prompt fÃ¼r einen neuen GPT-5.5 Final-Audit-Chat

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

## 7. Repeat Skill 3/4 Per Task

For each task:

```text
Skill 3 Pre-Check
â†’ Skill 4 Execution
â†’ task validation evidence
â†’ /save
```

Proceed to Skill 5 only after all required tasks are completed or explicitly deferred by Spec/Task scope.

Wichtig:
- Nie mehrere Tasks in einem Skill-3-/Skill-4-Lauf validieren oder implementieren.
- Bei gemischten Modellen nach jedem Task stoppen und mit dem zugewiesenen Modell des nÃ¤chsten Tasks neu starten.
- Der User lÃ¶st jeden nÃ¤chsten Task bewusst aus.

---

## 8. Prepare Compact Skill 5 Audit Package

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
Pre-Check: <PRE-CHECK results>
Changed Files: <list>
Diff: <git diff or relevant excerpts>
Tests: <Unit/Integration/E2E results>
Known Risks: <if any>
```

---

## 9. Run Skill 5 â€“ Final Audit with GPT-5.5

Skill 5 should be started in a new GPT-5.5 chat.

Minimal invocation:

```text
/Skill 5 â€“ Diamantstandard Final Audit mit kompaktem Audit-Paket:
WICHTIG:
- Neuer Chat mit GPT-5.5.
- Nur dieses Compact Audit Package verwenden.
- Früheren Chatverlauf ignorieren.

Spec: documentation/Planned Features/<FEATURE_NAME>.md
Tasks: documentation/tasks/<TASK_FILE>.md
Pre-Check: <PRE-CHECK Ergebnis oder Datei>
Changed Files: <Liste>
Diff: <Git Diff oder relevante AuszÃ¼ge>
Tests: <Unit/Integration/E2E Ergebnisse>
Known Risks: <falls vorhanden>
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

Skill 5 muss zusÃ¤tzlich ausgeben:
- manuelle Janus-Testanleitung mit Prompt/Klickpfad
- erwartetes Ergebnis
- Debug-Handoff an SWE 1.6 bei Abweichung
- Copy-Paste-Prompt fÃ¼r `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`

---

## 10. Run Skill 6 â€“ Feature Debug Gate

Nach Skill 5 fÃ¼hrt der User die manuelle Janus-Testanleitung aus.

Wenn der manuelle Janus-Test wie erwartet funktioniert:

```text
â†’ Skill 6 wird Ã¼bersprungen.
â†’ Weiter mit Skill 7 Dokumentationsupdate.
```

Wenn der manuelle Janus-Test NICHT wie erwartet funktioniert, oder Skill 4/5 Debug verlangt:

- Skill 4 returns `TASK EXECUTION FAILED`
- Skill 4 returns `FIX LOOP LIMIT REACHED`
- Skill 5 returns `BLOCKED`
- Skill 5 returns non-trivial `PASS WITH FIXES`
- the manual Janus test from Skill 5 does not match the expected result

Use:

```text
/SKILL 6 â€“ FEATURE DEBUG
```

Required package:

```text
Debug Package:
Feature: <Feature-Name>
Iteration: 1 | 2 | 3
Task: <task file / task id>
Spec: <source spec file>
Pre-Check: <PRE-CHECK result>
Final Audit / Skill 5: <result/findings>
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
- Skill 6 is not a normal happy-path implementation step; it is a manual-test/debug gate.
- Skill 6 always runs before Skill 7.
- Skill 6 uses SWE 1.6 by default.
- After each Skill-6 fix, Skill 6 must ask the user to rerun the Janus manual test.
- If the retest passes and Skill 6 changed code, run `/save`, then proceed to Skill 7.
- If the retest fails and iteration is below 3, rerun Skill 6 with updated actual behavior and backend log.
- If the retest fails after iteration 3, Skill 6 must output `SKILL 6 ESCALATION REQUIRED` plus compact GPT-5.5 handover.
- Do not give GPT-5.5 the full backend log; use Skill 6's compressed escalation handover.

---

## 11. Run Skill 7 â€“ Dokumentationsupdate with Automatic Version Bump

Run only if Skill 5 or `/2_final-audit` returned `PASS` or `PASS WITH FIXES`.

Additionally, one of these must be true:

- manual Janus test passed and Skill 6 was not needed
- Skill 6 returned `SKILL 6 DEBUG RESULT: FIXED` and the user retest passed
- manual Janus test was explicitly marked `N/A` or deferred by Skill 5 with a non-blocking reason

After Skill 7 completed successfully:

```text
â†’ /save
```

Do not proceed to release before `/save` completed successfully.

Use:

```text
/SKILL 7 â€“ DOKUMENTATIONSUPDATE
```

Use the Copy-Paste-Prompt from Skill 5. It must include:
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
- manual Janus test failed and Skill 6 has not resolved it
- Skill 5 requested re-run of Skill 4
- there is no clear final audit package
- Skill 6 returned `ESCALATION REQUIRED`, `BLOCKED`, or `OUT OF SCOPE`

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
- Skill 5 returns BLOCKED.
- Skill 6 needs escalation, is blocked, or still needs retest.
- Skill 7 version bump is blocked or version files are inconsistent.
- Skill 7 completed but `/save` did not complete.
- Required release artifacts are missing.

---

## Cost Rules

- Do not paste full chat history into any skill.
- Use artifact files as handoff boundaries.
- Use GPT-5.5 only for Skill 5 or explicit escalation.
- Prefer re-generating a better Spec over expensive implementation fixes.
- Use targeted diffs and test outputs for audits.
- Do not read `WHAT_I_LEARNED.md` fully; search targeted patterns only when needed.

