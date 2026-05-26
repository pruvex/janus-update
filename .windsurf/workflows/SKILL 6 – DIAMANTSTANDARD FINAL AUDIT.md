---
description: Janus V3 — Skill 6 Final Audit. Release-Gate nach vollständiger Spec-Umsetzung; risikobasiertes Audit-Modell; Spec-Metadaten + Verschiebung nach Spec Done; keine Produktimplementation.
---

This skill follows the global rules in `documentation/pipeline/PIPELINE_CONTRACT.md`.

## Rolle

Finales **Qualitäts- und Release-Gate** nach Skill 4 (alle Tasks, Validierung, User-Sign-off laut gebundenem Paket). **Kein Code**, keine neuen Anforderungen aus Chat — nur Bewertung gegen **Artefakte** (Contract: SSOT).

## Modell (Audit Model Gate — gestrafft)

| Audit Risk | Audit Model To Use |
|------------|-------------------|
| LOW | `Kimi k2.5` oder `SWE 1.6` (lokaler, deterministischer Scope) |
| MEDIUM | `SWE 1.6` |
| HIGH / CRITICAL | **`GPT-5.5`** (Pflicht) |
| Unklar / widersprüchlich / fehlende Tests / Known Risks / mehrere Subsysteme | **`GPT-5.5`** |

- Gate aus **Compact Audit Package** übernehmen; fehlt es → konservativ klassifizieren (**Unklar → GPT-5.5**).
- Aktives Modell schwächer als `Audit Model To Use` → **STOP**, neuer Chat mit vorgeschriebenem Modell.
- Skill 6 **nur** gegen das Paket; kein voller Implementierungs-Chat als Quelle.

## Eingabe (Pflicht)

- Spec, Task(s), Pre-Check (Skill 3), geänderte Dateien, Diff, Testergebnisse, Auto-Verification / Evidence
- **Pipeline:** `Remaining Tasks: keine`, `Spec Implementation Complete: YES`, Gesamtvalidierung aus Skill 4 erledigt
- **User-Sign-off:** Evidence aus Skill-4-Gate (manueller UX-Check) wie im Audit-Paket dokumentiert; fehlt bindendes Evidence → **BLOCKED** / Paket unvollständig (kein Release)

Minimaler Aufruf: neuer Chat + empfohlenes Modell + kompaktes Paket (Spec-Pfad, Tasks, Pre-Check, Changed Files, Diff, Tests, Pipeline-Status, Manual Janus Evidence).

---

## Debug-Paket-Verwechslung (HARD)

Skill 6 darf keine Debug-Pakete, FAIL-/BLOCKED-Pakete oder offenen Auto-Verification-Failures
auditieren. Wenn der Input einen dieser Hinweise enthaelt, muss Skill 6 sofort blocken und zu
Skill 5 routen:

```text
FEATURE DEBUG
TASK EXECUTION BLOCKED
Auto-Verification FAILED
Verification Status: FAILED
LTC-002 FAILED
TC-005 FAILED
ASSERTION_MISMATCH
Context-Leakage
Provider-specific failure
Fix Applied
Issue:
Investigate
```

Verboten:

```text
FINAL AUDIT RESULT: PASS
PASS WITH FIXES
Spec Done
```

Pflichtoutput:

```text
FINAL AUDIT RESULT: BLOCKED
Reason: Debug/failure package was sent to Skill 6. This is not a final audit package.

NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Required Artifacts: Task, changed files, failed Auto-Verification, generated runner, evidence paths
Decision: HANDOFF
Reason: Open failure requires debug before final audit.
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] ...
```

---

## Skill-Nummer-Guard (HARD)

Dieser Skill heisst exakt:

```text
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]
```

Falsche Alias-/Nummernformen sind ungueltig:

```text
@[/SKILL 5 – DIAMANTSTANDARD FINAL AUDIT]
@[/SKILL 6 – FEATURE DEBUG]
Skill 6 Debug
Skill 6 Debug Iteration
```

Wenn ein Paket fachlich Final Audit verlangt, aber die Slash-Zeile `SKILL 5` nennt, ist das
kein inhaltlicher Audit-Blocker, sondern ein Handoff-Formatfehler. Korrigiere die Zielzeile
auf `@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]` oder fordere einen korrigierten Handoff an.

---

## Audit-Ablauf (Golden Path)

1. **Vollständigkeit** — alle Tasks erledigt? Spec complete? Sonst `FINAL AUDIT BLOCKED: SPEC NOT COMPLETE` → Handoff Skill 4 (nächster Task).
2. **Spec & AC** — Umsetzung vs. Spec; kein Scope-Drift, nichts Wesentliches fehlend/überschüssig.
3. **Code-Konsistenz** — Imports, tote Pfade, offensichtliche Brüche (lesend).
4. **Tests** — Unit/Integration/E2E wie nachgewiesen; keine Fake-Kernlogik-Tests.
5. **Regression** — keine unzulässigen Breaking Changes außerhalb deklarierten Scopes.
6. **Pre-Check-Compliance** — Skill-3-Vorgaben eingehalten.
7. **Entscheidung** — eine von: `PASS` | `PASS WITH FIXES` | `BLOCKED`.

---

## Entscheidungslogik (kurz)

- **PASS:** Spec erfüllt, Tests grün, keine relevanten Blocker/Regressionen.
- **PASS WITH FIXES:** kleine, sichere Nachbesserungen möglich **ohne** Architekturbruch und ohne Scope-Verletzung.
- **BLOCKED:** Spec/Test/Regression/unklare Evidence / nicht deterministisch bewertbar → **kein** Release, **kein** Skill 7.

---

## Spec Done & Metadaten (hart)

Nur bei **`FINAL AUDIT RESULT: PASS`** oder **`PASS WITH FIXES`**:

1. Spec-Datei aus dem Paket aktualisieren: Block **`## SPEC IMPLEMENTATION METADATA`** ersetzen oder am Ende anfügen:

```markdown
## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** <PASS | PASS WITH FIXES>
- **Completed At:** <YYYY-MM-DD>
- **Completed By:** SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
- **Validation Evidence:** <Skill 4 Auto-Verification + User-Sign-off; bei Re-Audit nach Skill 5: Skill 5 FIXED + Retest-Evidence>
```

2. Spec nach **`documentation/SPEC/Spec Done/<original-filename>.md`** verschieben (Ordner anlegen falls nötig).
3. **Kollision:** Zieldatei existiert bereits → **`BLOCKED: SPEC DONE TARGET EXISTS`** (nichts überschreiben).
4. Output **muss** neuen Spec-Pfad nennen; alle Folge-Handoffs (Skill 7) nutzen **diesen** Pfad.

Bei `BLOCKED` / unvollständigem Paket: **kein** Metadaten-Block, **kein** Verschieben.

---

## Output-Skelett

```text
FINAL AUDIT RESULT: PASS | PASS WITH FIXES | BLOCKED
Audit Model To Use: <…>
Zusammenfassung / Findings / Testmatrix / Regression: …
Manual Janus Test Evidence: PRESENT | MISSING | N/A WITH REASON
Pipeline Completion Status: Completed Tasks … / Remaining: keine / Spec Implementation Complete: YES
Spec Done: JA | NEIN (+ neuer Pfad documentation/SPEC/Spec Done/…)
```

Freie Status-Synonyme sind verboten:

```text
STATUS: READY FOR PRODUCTION
Audit Result: APPROVED
Recommendation: APPROVE FOR SKILL 7
READY FOR AUDIT
```

Stattdessen muss Skill 6 immer einen Contract-State ausgeben:

```text
FINAL AUDIT RESULT: PASS
```

oder:

```text
FINAL AUDIT RESULT: PASS WITH FIXES
```

oder:

```text
FINAL AUDIT RESULT: BLOCKED
```

---

## Handover (P2)

### Skill 7 (nach PASS / PASS WITH FIXES, Spec Done)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 7 – DOKUMENTATIONSUPDATE
Canonical State: HANDOFF
Required Artifacts: Spec oder N/A WITH REASON, Task, Backlog Item, Final Audit Result, Changed Files, Test Results, Evidence Paths, Manual Janus Evidence-Status, Version/Changelog Scope
Evidence Paths: <Playwright/Generator/Validator/TestResult/Report-Pfade>
Failure Code: N/A
Changed Files: <geänderte Dateien>
Decision: HANDOFF
Reason: FINAL AUDIT RESULT PASS | PASS WITH FIXES; Dokumentation/Backlog/Changelog/Version aktualisieren.
Copy Prompt:
@[/SKILL 7 – DOKUMENTATIONSUPDATE]
Task: <task id>
Backlog Item: <BACKLOG-XXX>
Final Audit Result: PASS | PASS WITH FIXES
Changed Files:
- <file>
Evidence Paths:
- <path>
Documentation Scope:
- Backlog Status/DONE und Completion-Felder aktualisieren
- CHANGELOG/WHAT_I_LEARNED/Version prüfen
- Relevante Spec/Task-Dokumentation aktualisieren
```

### Skill 5 (Fix nötig / BLOCKED mit reproduzierbarem Bug)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 5 – FEATURE DEBUG
Required Artifacts: Spec, Task, Audit-Findings, Ist/Soll, Logs/Evidence-Pfade
Decision: HANDOFF
Reason: BLOCKED oder PASS WITH FIXES mit nicht-trivialen Fixes
Copy Prompt: @[/SKILL 5 – FEATURE DEBUG] … Debug Package …
```

### Skill 4 (noch offene Tasks)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 4 – EXECUTIONER
Required Artifacts: Spec, Task-Datei, nächste Target Task ID
Decision: BLOCKED
Reason: SPEC NOT COMPLETE — offene Tasks
Copy Prompt: @[/SKILL 4 – EXECUTIONER] …
```

### Modellwechsel (Audit)

```text
NEXT_SKILL_HANDOFF
Target Skill: SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
Required Artifacts: gleiches Compact Audit Package
Decision: NEEDS_INFO
Reason: MODEL SWITCH REQUIRED — aktives Modell < X > erfüllt Audit Model To Use < Y > nicht
Copy Prompt: Neuer Chat mit <Y>; Paket erneut einfügen …
```

---

## Optional: Finaler Smoke-Test-Hinweis

Nur wenn sinnvoll: ein kurzer manueller Gesamtflow (Startpunkt, Aktion, Soll) — **kein** Ersatz für gebundene Test-/Playwright-Evidence. Wenn nicht sinnvoll: `N/A WITH REASON` + beste alternative Evidence.

---

## Final State

Jeder Lauf endet in genau einem Contract-State: **PASS**-Pfad (inkl. Spec Done + P2 Skill 7), **BLOCKED** + P2 Skill 5/4, oder **NEEDS_INFO** / Modellwechsel mit P2.
