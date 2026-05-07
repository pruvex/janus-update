---
description: Skill 6 â€“ Iterativer Diamond-OS Feature-Debug nach manuellem Janus-Test mit SWE 1.6 und GPT-5.5 Eskalationshandover
---

# Skill 6 â€“ Feature Debug

Dieser Workflow ist der **iterative Debug-Gate** der Diamond-OS Pipeline nach Skill 5.

Skill 6 wird ausgefÃ¼hrt, nachdem Skill 5 eine manuelle Janus-Testanleitung geliefert hat und der Nutzer diesen Test in Janus durchgefÃ¼hrt hat.

## Zweck

Nutze Skill 6, wenn einer dieser FÃ¤lle eintritt:

- Skill 4 meldet `TASK EXECUTION FAILED`
- Skill 4 meldet `FIX LOOP LIMIT REACHED`
- Skill 5 meldet `BLOCKED`
- Skill 5 meldet `PASS WITH FIXES` und die Fixes sind nicht trivial oder nicht sicher isolierbar
- der manuelle Janus-Test aus Skill 5 weicht vom erwarteten Ergebnis ab
- ein Nutzer liefert tatsÃ¤chlichen Janus-Output, Logs oder Screenshot, der nicht zum erwarteten Ergebnis passt

## Modell

Standard:

```text
SWE 1.6
```

Eskalation:

```text
GPT-5.5
```

nur wenn die Ursache nicht deterministisch eingrenzbar ist oder mehrere plausible Root Causes existieren oder drei SWE-1.6-Iterationen nicht zum gewÃ¼nschten Verhalten gefÃ¼hrt haben.

## Required Input

Der User MUSS pro Iteration ein kompaktes Debug-Paket liefern:

```text
/SKILL 6 â€“ FEATURE DEBUG

Skill 6 Debug Package:

Feature:
<Feature-Name>

Iteration:
1 | 2 | 3

Task:
<task file / task id>

Spec:
<source spec file>

Pre-Check:
<PRE-CHECK PASSED oder relevante Pre-Check-Fehler>

Final Audit / Skill 5:
<PASS WITH FIXES | BLOCKED | relevante Findings>

Manueller Janus-Test:
- Prompt/Klickpfad: <was wurde getan>
- Erwartetes Ergebnis: <Soll>
- TatsÃ¤chliches Ergebnis: <Ist>
- Screenshot/Log/Output: <falls vorhanden>

Backend Log:
<relevanter Auszug oder Pfad/Datei>

Changed Files:
- <Datei 1>
- <Datei 2>

Test Results:
- <Testname>: PASS | FAIL | N/A

Known Risks:
- <falls vorhanden>
```

Wenn Pflichtdaten fehlen:

```text
DEBUG PACKAGE INCOMPLETE

Missing:
- <konkrete fehlende Informationen>

Action:
â†’ Fehlende Debug-Artefakte nachreichen.
â†’ Keine CodeÃ¤nderung ohne reproduzierbaren Ist/Soll-Konflikt.
```

## Hard Rules

- Keine neuen Features.
- Keine ArchitekturÃ¤nderungen.
- Kein Refactoring auÃŸerhalb des betroffenen Task-Scopes.
- Keine Spekulation ohne Ist/Soll-Vergleich.
- Nicht denselben Fix zweimal wiederholen.
- Maximal drei Skill-6-Iterationen mit SWE 1.6 pro Fehlerkette.
- Jede Iteration muss eine neue Nutzerbeschreibung, ein neues tatsÃ¤chliches Testergebnis oder ein aktualisiertes Backendlog enthalten.
- Nach jeder Fix-Iteration muss Skill 6 den User auffordern, den manuellen Janus-Test erneut auszufÃ¼hren.
- Wenn es nach der dritten Iteration nicht wie gewÃ¼nscht funktioniert: `SKILL 6 ESCALATION REQUIRED` melden und ein kompaktes GPT-5.5-Handover ausgeben.
- Debugging lÃ¤uft gegen Spec, Task, Pre-Check, Skill-5-Audit und tatsÃ¤chlichen Output.
- Chatverlauf ist nicht bindend; Artefakte sind bindend.

## Ablauf

### 1. Reproduktionscheck

PrÃ¼fe:

- Was war der erwartete Zustand?
- Was war der tatsÃ¤chliche Zustand?
- Ist der Fehler reproduzierbar?
- Betrifft der Fehler den validierten Task-Scope?

Wenn der Fehler nicht reproduzierbar ist:

```text
DEBUG BLOCKED â€“ NOT REPRODUCIBLE

Action:
â†’ exakten Prompt/Klickpfad, Output und Logs nachreichen.
```

### 2. Scope-Gate

PrÃ¼fe, ob der Fehler innerhalb des ursprÃ¼nglichen Task-Scopes liegt.

Wenn nein:

```text
DEBUG OUT OF SCOPE

Reason:
- <warum auÃŸerhalb des validierten Tasks>

Action:
â†’ neue Spec/Task Ã¼ber Skill 1/2 starten oder als separates Bugfix-Feature planen.
```

### 3. Root-Cause-Hypothese

Formuliere genau eine primÃ¤re Root Cause.

Format:

```text
Root Cause Candidate:
- Ursache: <konkret>
- Evidenz: <Datei/Test/Output/Log>
- Betroffene Datei(en): <Liste>
- Risiko: LOW | MEDIUM | HIGH
```

Wenn mehrere gleich plausible Ursachen existieren:

```text
MODEL SWITCH REQUIRED: SWE 1.6 â†’ GPT-5.5

Reason:
- Mehrere plausible Root Causes, keine deterministische Entscheidung mÃ¶glich.
```

### 4. Minimaler Fixplan

Erstelle nur einen minimalen Fixplan:

```text
Debug Fix Plan:
- Target File(s): <Liste>
- Change: <minimaler Fix>
- Tests: <gezielte Tests>
- Rollback Risk: LOW | MEDIUM | HIGH
```

### 5. Iteration und Fix-AusfÃ¼hrung

Implementiere nur, wenn Root Cause und Fixplan eindeutig sind.

Nach Fix:

- gezielte Tests ausfÃ¼hren
- den User ausdrÃ¼cklich auffordern, den manuellen Janus-Test erneut auszufÃ¼hren
- Ergebnis gegen erwartetes Verhalten prÃ¼fen
- wenn erfolgreich: zu Skill 7 Dokumentation Ã¼bergeben
- wenn nicht erfolgreich: nÃ¤chste Skill-6-Iteration mit neuer Fehlerbeschreibung und Backendlog starten

### 6. Eskalationsgrenze

Wenn Iteration 3 nicht zum gewÃ¼nschten Verhalten fÃ¼hrt:

```text
SKILL 6 ESCALATION REQUIRED

Reason:
- Drei SWE-1.6-Debug-Iterationen konnten das erwartete Janus-Verhalten nicht herstellen.

Action:
â†’ Skill 6 in neuem Chat mit GPT-5.5 ausfÃ¼hren.
â†’ Kein vollstÃ¤ndiges Backendlog Ã¼bergeben.
â†’ Nur das komprimierte Eskalationshandover verwenden.
```

Das Handover MUSS kompakt sein und groÃŸe Logs zusammenfassen.

Format:

```text
GPT-5.5 Skill-6 Escalation Handover:

Feature:
<Feature-Name>

Task/Spec:
- Spec: <Pfad>
- Task: <Pfad/ID>

Expected Behavior:
<Soll aus Skill 5/manuellem Test>

Actual Behavior After 3 Iterations:
<Ist kurz und konkret>

Iteration Summary:
1. <Root Cause Candidate, Fix, Test result>
2. <Root Cause Candidate, Fix, Test result>
3. <Root Cause Candidate, Fix, Test result>

Backend Log Compression:
- Hard Errors: <Liste der relevanten Fehlercodes/Tracebacks>
- Trace IDs: <falls vorhanden>
- Time Window: <Zeitfenster>
- Repeated Symptoms: <Muster>
- Excluded Noise: <was bewusst nicht relevant ist>

Changed Files:
- <Datei>: <kurzer Grund>

Tests:
- <Test>: PASS | FAIL | N/A

Open Question for GPT-5.5:
<eine prÃ¤zise Frage, die SWE 1.6 nicht deterministisch lÃ¶sen konnte>
```

## Output Format

```text
SKILL 6 DEBUG RESULT: FIXED | NEEDS RETEST | ESCALATION REQUIRED | BLOCKED | OUT OF SCOPE

Zusammenfassung:
- Feature: <Name>
- Task: <ID>
- Iteration: 1 | 2 | 3
- Fehler: <kurz>
- Root Cause: <konkret>

GeÃ¤nderte Dateien:
- <Datei>

Tests:
- <Test>: PASS | FAIL | N/A

Manueller Janus-Retest:
1. Ã–ffne Janus.
2. FÃ¼hre aus: <Prompt/Klickpfad>
3. Erwartetes Ergebnis: <Soll>
4. Wenn abweichend: tatsÃ¤chlichen Output und Backendlog erneut an Skill 6 geben.

NÃ¤chster Schritt:
- Wenn FIXED und Retest PASS und Skill 6 Code geÃ¤ndert hat: zuerst `/save` ausfÃ¼hren, dann Skill 7 Dokumentationsupdate.
- Wenn FIXED und Retest PASS und Skill 6 keinen Code geÃ¤ndert hat: Skill 7 Dokumentationsupdate ausfÃ¼hren.
- Wenn NEEDS RETEST: manuellen Janus-Test erneut ausfÃ¼hren.
- Wenn Retest FAIL und Iteration < 3: Skill 6 erneut mit SWE 1.6, neuer Fehlerbeschreibung und Backendlog ausfÃ¼hren.
- Wenn Retest FAIL und Iteration = 3: Skill 6 mit GPT-5.5 und kompaktem Eskalationshandover ausfÃ¼hren.
- Wenn BLOCKED: Skill 2 Re-Evaluation oder GPT-5.5 Eskalation.
- Wenn OUT OF SCOPE: neues Feature/Bugfix-Task Ã¼ber Skill 1/2 starten.

Atomic Save Gate:
- `/save` ist Pflicht nach einem erfolgreichen Skill-6-Fix mit CodeÃ¤nderung und bestandenem Janus-Retest.
- `/save` darf nicht ausgefÃ¼hrt werden, solange Skill 6 `NEEDS RETEST`, `ESCALATION REQUIRED`, `BLOCKED` oder `OUT OF SCOPE` meldet.
```

