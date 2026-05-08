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
/SKILL 6 – FEATURE DEBUG

Skill 6 Debug Package:

Feature:
<Feature-Name>

Iteration:
1 | 2 | 3 | (optional – Skill 6 zählt automatisch, wenn nicht angegeben)

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
- Tatsächliches Ergebnis: <Ist>
- Screenshot/Log/Output: <falls vorhanden>

Backend Log:
<relevanter Auszug oder Pfad/Datei>

Frontend Log:
<N/A | Pfad zu gefilterter Frontend-Log-Datei, z. B. frontend_log.md>

Changed Files:
- <Datei 1>
- <Datei 2>

Test Results:
- <Testname>: PASS | FAIL | N/A

Known Risks:
- <falls vorhanden>
```

**Automatische Iterationszählung:**
- Wenn der User keine Iterationsnummer angibt, zählt Skill 6 die Iterationen basierend auf der Anzahl der Debug-Pakete im aktuellen Chat.
- Skill 6 speichert die Iterationsnummer im Output-Format und verwendet sie für die nächste Iteration.
- Zähle nur Iterationen derselben Fehlerkette, d. h. gleiches Feature, gleicher Task und gleicher Ist/Soll-Konflikt.
- Wenn eine frühere Skill-6-Ausgabe im aktuellen Chat `Iteration: N` für dieselbe Fehlerkette enthält, ist die nächste Iteration `N+1`.
- Eine vom User angegebene Iteration darf nur übernommen werden, wenn sie zur bisherigen Fehlerkette passt; bei Widerspruch muss Skill 6 die erkannte Zählung offen melden.
- Iteration 1-3 sind SWE-1.6-Debug-Iterationen. Nach einem fehlgeschlagenen Retest der dritten Iteration darf keine vierte SWE-1.6-Fixrunde gestartet werden.

Wenn Pflichtdaten fehlen:

```text
DEBUG PACKAGE INCOMPLETE

Missing:
- <konkrete fehlende Informationen>

Action:
â†’ Fehlende Debug-Artefakte nachreichen.
â†’ Keine CodeÃ¤nderung ohne reproduzierbaren Ist/Soll-Konflikt.
```

**Frontend-Log-Anforderung statt Konsolen-Copy:**
- Wenn der Fehler UI, Renderer, Browser-Konsole, DOM, Frontend-State, IPC, Streaming-Anzeige, Toast/Modal, Model-Switch-UI, Video-/Bild-Rendering oder Client-seitige API-Aufrufe betrifft, MUSS Skill 6 gezielt ein Frontend-Log-Artefakt anfordern.
- Der User soll NICHT das komplette Frontend-Console-Log in den Chat kopieren.
- Wenn der automatische Frontend-Log-Exporter verfügbar ist, MUSS Skill 6 den User auffordern, nach dem gezielten Repro-Test in Janus `Ctrl+Shift+L` zu drücken und den angezeigten Pfad zur erzeugten Markdown-Datei bereitzustellen.
- Wenn der automatische Frontend-Log-Exporter nicht verfügbar ist, MUSS Skill 6 den User auffordern, nach dem gezielten Repro-Test eine Datei mit relevantem Auszug bereitzustellen, bevorzugt:

```text
frontend_log.md
```

- Das Frontend-Log-Artefakt soll nur debuggingrelevante Informationen enthalten:
  - Zeitfenster des Repro-Tests
  - `error` / `warn`
  - fehlgeschlagene Netzwerk/API-Aufrufe
  - IPC-Events und IPC-Fehler
  - betroffene UI-Aktion
  - Stacktraces
  - relevante Console-Meldungen mit Prefix/Quelle
  - explizit ausgelassener Noise, falls bekannt
- Skill 6 MUSS dem User einen konkreten Repro-Auftrag geben, bevor es das Frontend-Log verlangt.
- Format:

```text
FRONTEND LOG REQUIRED

Bitte führe genau diesen Test aus:
1. <konkreter Klickpfad oder Prompt>
2. <erwarteter sichtbarer Zustand>
3. <abweichenden Zustand nicht korrigieren, App offen lassen>

Danach bitte bereitstellen:
- Datei: per `Ctrl+Shift+L` erzeugter Pfad oder `frontend_log.md`
- Inhalt: nur Logs aus dem Test-Zeitfenster, bevorzugt error/warn/API/IPC/Stacktrace
- Kein vollständiges DevTools-Console-Copy
```

## Hard Rules

- Keine neuen Features.
- Keine ArchitekturÃ¤nderungen.
- Kein Refactoring auÃŸerhalb des betroffenen Task-Scopes.
- Keine Spekulation ohne Ist/Soll-Vergleich.
- Nicht denselben Fix zweimal wiederholen.
- Maximal drei Skill-6-Iterationen mit SWE 1.6 pro Fehlerkette.
- Jede Iteration muss eine neue Nutzerbeschreibung, ein neues tatsÃ¤chliches Testergebnis oder ein aktualisiertes Backendlog enthalten.
- Bei frontendnahen Fehlern gilt ein neues oder aktualisiertes `frontend_log.md` als gültiges aktualisiertes Debug-Artefakt.
- Nach jeder Fix-Iteration muss Skill 6 den User auffordern, den manuellen Janus-Test erneut auszufÃ¼hren.
- Wenn es nach der dritten Iteration nicht wie gewünscht funktioniert: `SKILL 6 ESCALATION REQUIRED` melden und ein kompaktes GPT-5.5-Handover ausgeben.
- **Proaktive GPT-5.5-Empfehlung:** Bei Iteration 3 (oder wenn der Retest nach Iteration 3 fehlschlägt) MUSS Skill 6 proaktiv empfehlen, zu GPT-5.5 zu wechseln, und dabei angeben, ob ein neuer Chat zum Kostensparen sinnvoll ist.
- Debugging lÃ¤uft gegen Spec, Task, Pre-Check, Skill-5-Audit und tatsÃ¤chlichen Output.
- Chatverlauf ist nicht bindend; Artefakte sind bindend.
- **FRONTEND-LOG-DISZIPLIN:** Skill 6 darf bei frontendnahen Electron-/Renderer-Problemen nicht pauschal "komplette Console kopieren" verlangen. Stattdessen muss Skill 6 einen gezielten Repro-Test und ein kompaktes Frontend-Log-Artefakt (`frontend_log.md` oder konkreter Pfad) anfordern. Große Rohlogs müssen zusammengefasst oder gefiltert werden.
- **AUTOMATISCHE FIX-IMPLEMENTIERUNG:** Wenn Root Cause und Fixplan eindeutig sind (LOW oder MEDIUM Risiko), MUSS Skill 6 den Fix SOFORT implementieren, nicht nur einen Plan vorschlagen. Nur bei HIGH Risiko oder mehrdeutigen Root Causes darf Skill 6 nur einen Plan vorschlagen.
- **KEINE SCHEINFIXES:** Skill 6 darf niemals behaupten, Fixes seien umgesetzt, wenn keine Dateiänderung durchgeführt wurde. Ein Fix gilt nur als umgesetzt, wenn Skill 6 im selben Lauf ein Edit-Tool verwendet, die geänderten Dateien nennt und die Änderung im Output als Implementierungsnachweis zusammenfasst.
- **KEIN "AUF NACHFRAGE":** Wenn ein eindeutiger LOW/MEDIUM-Fix möglich ist, darf Skill 6 nicht zuerst nur einen Vorschlag ausgeben und auf eine spätere Nachfrage warten. Der Fix muss im aktuellen Skill-6-Lauf umgesetzt werden.
- **PLAN-ONLY IST KEIN FIX:** Wenn Skill 6 wegen HIGH Risiko, unklarer Root Cause oder fehlenden Artefakten nicht editiert, muss der Status `BLOCKED`, `OUT OF SCOPE` oder `ESCALATION REQUIRED` lauten. `FIXED` oder `NEEDS RETEST` sind dann verboten.
- **TEMPORÄRE ESKALATIONSDATEI:** Nach fehlgeschlagenem Retest der dritten SWE-1.6-Iteration muss Skill 6 eine temporäre Markdown-Datei unter `.windsurf/tmp/skill6_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md` erstellen. Diese Datei enthält das kompakte GPT-5.5-Handover und ersetzt das lange Backendlog.

## Ablauf

### 1. Reproduktionscheck

PrÃ¼fe:

- Was war der erwartete Zustand?
- Was war der tatsÃ¤chliche Zustand?
- Ist der Fehler reproduzierbar?
- Betrifft der Fehler den validierten Task-Scope?
- Ist der Fehler frontendnah und benötigt Renderer-/Frontend-Evidenz?

Wenn der Fehler frontendnah ist und kein `Frontend Log` vorliegt:

```text
FRONTEND LOG REQUIRED

Reason:
- Der Ist/Soll-Konflikt betrifft Frontend/Renderer/UI/IPC/Client-State und kann ohne Frontend-Log nicht deterministisch eingegrenzt werden.

Bitte führe genau diesen Test aus:
1. <konkreter Prompt/Klickpfad aus dem manuellen Janus-Test>
2. <erwartetes Ergebnis>
3. <tatsächliche Abweichung beobachten>

Danach bitte bereitstellen:
- Frontend Log: nach dem Repro in Janus `Ctrl+Shift+L` drücken und den angezeigten Pfad zur automatisch erzeugten Frontend-Log-Datei angeben
- Inhalt: nur Test-Zeitfenster, error/warn, API/IPC-Fehler, Stacktraces und relevante Console-Meldungen
- Nicht nötig: vollständiges DevTools-Console-Log

Action:
→ Keine Codeänderung, bis das frontendnahe Debug-Artefakt vorliegt oder der Fehler anderweitig deterministisch belegbar ist.
```

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

Implementiere SOFORT mit den verfÃ¼gbaren Tools (edit, multi_edit, write_to_file), wenn Root Cause und Fixplan eindeutig sind.

**AUSNAHMEN (nur Plan vorschlagen, nicht implementieren):**
- Risiko = HIGH
- Mehrdeutige Root Causes (mehrere gleich plausible Ursachen)
- Root Cause nicht deterministisch eingrenzbar

**IMPLEMENTIERUNGS-PFLICHT:**
- Wenn Risiko = LOW oder MEDIUM und Root Cause eindeutig: MUSST du den Fix SOFORT implementieren, nicht nur einen Plan vorschlagen.
- Nutze die verfÃ¼gbaren Tools: edit, multi_edit, write_to_file.
- Keine manuelle Eingabe durch den User erforderlich.
- Vor dem finalen Skill-6-Output muss ein Implementierungsnachweis vorliegen:
  - geänderte Datei(en)
  - konkrete Änderung in 1-3 Sätzen
  - ausgeführte oder begründet übersprungene gezielte Tests
- Wenn kein Edit-Tool verwendet wurde, darf `Geänderte Dateien` nicht so klingen, als seien Änderungen umgesetzt worden. Verwende dann `Keine — Plan-only, nicht umgesetzt` und melde keinen `FIXED`/`NEEDS RETEST`-Status.

Nach Fix:

- gezielte Tests ausfÃ¼hren
- den User ausdrÃ¼cklich auffordern, den manuellen Janus-Test erneut auszufÃ¼hren
- Ergebnis gegen erwartetes Verhalten prÃ¼fen
- wenn erfolgreich: zu Skill 7 Dokumentation Ã¼bergeben
- wenn nicht erfolgreich: nÃ¤chste Skill-6-Iteration mit neuer Fehlerbeschreibung und Backendlog starten

### 6. Eskalationsgrenze

Wenn der Retest nach Iteration 3 nicht zum gewÃ¼nschten Verhalten fÃ¼hrt:

```text
SKILL 6 ESCALATION REQUIRED

Reason:
- Drei SWE-1.6-Debug-Iterationen konnten das erwartete Janus-Verhalten nicht herstellen.

Action:
→ Erstelle eine temporäre Eskalationsdatei unter `.windsurf/tmp/skill6_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md`.
→ Öffne GPT-5.5 in einem neuen Chatfenster, um Tokens zu sparen.
→ Übergib GPT-5.5 kein vollständiges Backendlog.
→ Verwende nur die temporäre Eskalationsdatei und den Copy-Paste-Handover unten.
```

**Kostenoptimierung bei GPT-5.5-Wechsel:**
- Nach dem fehlgeschlagenen Retest der dritten SWE-1.6-Iteration MUSS Skill 6 immer einen neuen GPT-5.5-Chat empfehlen.
- Der neue Chat nutzt nur die temporäre Eskalationsdatei als kompakten Kontext.
- Diese Empfehlung MUSS im Output Format unter "Nächster Schritt" enthalten sein.

Die temporäre Datei MUSS kompakt sein und große Logs zusammenfassen.

Temporäre Datei:

```text
Pfad:
.windsurf/tmp/skill6_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md

Regeln:
- Datei nur bei `SKILL 6 ESCALATION REQUIRED` erstellen.
- Keine vollständigen Backendlogs einfügen.
- Nur harte Fehler, Trace IDs, Zeitfenster, wiederholte Symptome, ausgeschlossenen Noise und geänderte Dateien zusammenfassen.
- Am Ende vermerken: "Diese Datei ist temporär und muss von Skill 7 nach abgeschlossenem Debug-/Dokumentations-Gate gelöscht werden."
```

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

Frontend Log Compression:
- Frontend Log File: <Pfad oder N/A>
- Time Window: <Zeitfenster>
- Hard Errors: <Console/API/IPC/Stacktrace-Auszüge>
- Repeated Symptoms: <Muster>
- Excluded Noise: <was bewusst nicht relevant ist>

Changed Files:
- <Datei>: <kurzer Grund>

Tests:
- <Test>: PASS | FAIL | N/A

Open Question for GPT-5.5:
<eine prÃ¤zise Frage, die SWE 1.6 nicht deterministisch lÃ¶sen konnte>
```

Zusätzlich muss Skill 6 dem User diesen Copy-Paste-Handover für den neuen GPT-5.5-Chat ausgeben:

```text
BEGIN COPY FOR NEW GPT-5.5 CHAT
/SKILL 6 – FEATURE DEBUG

Modell: GPT-5.5

Bitte lies zuerst diese temporäre Eskalationsdatei:
<Pfad zu .windsurf/tmp/skill6_escalation_...md>

Führe Skill 6 auf Basis dieser Datei aus.
Wichtig:
- Verwende die temporäre Datei als kompaktes Debug-Handover.
- Fordere nicht das vollständige Backendlog an, außer die Datei enthält eine klar benannte fehlende Evidenz.
- Debugge nur die dort beschriebene Fehlerkette.
- Wenn du einen eindeutigen LOW/MEDIUM-Fix findest, implementiere ihn direkt und behaupte keine Umsetzung ohne tatsächliche Dateiänderung.
END COPY FOR NEW GPT-5.5 CHAT
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

Implementierungsnachweis:
- Edit-Tool verwendet: JA | NEIN
- Tatsächlich geänderte Dateien: <Liste oder Keine>
- Änderung umgesetzt: JA | NEIN
- Wenn NEIN: Status darf nicht FIXED oder NEEDS RETEST sein.

Tests:
- <Test>: PASS | FAIL | N/A

Frontend Log:
- Benötigt: JA | NEIN
- Datei: <frontend_log.md | Pfad | N/A>
- Status: VORHANDEN | ANGEFORDERT | N/A

Manueller Janus-Retest:
1. Ã–ffne Janus.
2. FÃ¼hre aus: <Prompt/Klickpfad>
3. Erwartetes Ergebnis: <Soll>
4. Wenn abweichend: tatsÃ¤chlichen Output und Backendlog erneut an Skill 6 geben.
5. Wenn frontendnah: danach `frontend_log.md` oder den konkreten Frontend-Log-Pfad bereitstellen; keine komplette DevTools-Konsole kopieren.

NÃ¤chster Schritt:
- Wenn FIXED und Retest PASS und Skill 6 Code geändert hat: zuerst `/save` ausführen, dann Skill 7 Dokumentationsupdate.
- Wenn FIXED und Retest PASS und Skill 6 keinen Code geändert hat: Skill 7 Dokumentationsupdate ausführen.
- Wenn NEEDS RETEST: manuellen Janus-Test erneut ausführen.
- Wenn Retest FAIL und Iteration < 3: Skill 6 erneut mit SWE 1.6, neuer Fehlerbeschreibung und Backendlog ausführen.
- Wenn Retest FAIL und Iteration = 3:
  - **Proaktive Empfehlung:** Wechsle zu GPT-5.5, da drei SWE-1.6-Iterationen nicht zum Ziel geführt haben.
  - **Kostenoptimierung:** Starte immer einen neuen GPT-5.5-Chat und verwende nur die temporäre Eskalationsdatei statt des langen Logs.
  - **Temporäre Datei:** `.windsurf/tmp/skill6_escalation_<feature-or-task>_<YYYYMMDD-HHMM>.md` wurde erstellt.
  - **Copy-Paste-Handover:** Gib dem User den vollständigen `BEGIN COPY FOR NEW GPT-5.5 CHAT` Block aus.
- Wenn BLOCKED: Skill 2 Re-Evaluation oder GPT-5.5 Eskalation.
- Wenn OUT OF SCOPE: neues Feature/Bugfix-Task über Skill 1/2 starten.

Atomic Save Gate:
- `/save` ist Pflicht nach einem erfolgreichen Skill-6-Fix mit Codeänderung und bestandenem Janus-Retest.
- `/save` darf nicht ausgeführt werden, solange Skill 6 `NEEDS RETEST`, `ESCALATION REQUIRED`, `BLOCKED` oder `OUT OF SCOPE` meldet.
```
