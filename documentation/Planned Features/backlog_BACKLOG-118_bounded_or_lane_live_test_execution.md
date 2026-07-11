# JANUS FEATURE SPEC - DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-118
- **Backlog Title:** Bounded OR Lane fuer LIVE_TEST_EXECUTION in der Testpipeline
- **Type:** IMPROVEMENT
- **Source Trigger:** BACKLOG-116 live retest after debug on 2026-07-01
- **Follow-up zu:** BACKLOG-117 - Strong OR Agent Lane fuer echte ausgelagerte Testarbeit

## 2. Problem / Wunsch
Die Janus-Testpipeline hat bereits bounded OR-Lanes fuer Generator-Review, Triage und Strong Test Worker, aber nicht fuer den eigentlichen lokalen Live-Retest in `LIVE_TEST_EXECUTION`.

Wenn ein Retest nur aus lokalem Health-Check, Chat-Erzeugung, einem oder wenigen allowlisted Prompt-Laeufen und Evidenzsammlung besteht, muss Codex den Ablauf aktuell trotzdem selbst fahren.

## 3. Expected Behavior
`janus-test-pipeline` kann fuer eligible lokale Live-Retests ein sichtbares `1 = Codex / 2 = OR` Gate anbieten.

Wenn der Nutzer `2 = OR` waehlt, darf ein bounded Worker den lokalen Retest innerhalb eines klaren Vertrags ausfuehren, die erlaubten Evidenzdateien erzeugen und Codex eine review-faehige Zusammenfassung zur finalen PASS/FAIL-Entscheidung zurueckgeben.

## 4. Current Behavior
Der produktive `LIVE_TEST_EXECUTION`-Pfad ist Codex-owned.

Selbst ein sehr enger lokaler API-Retest wie bei `BACKLOG-116` musste komplett durch Codex laufen:

- `GET /api/health`
- `POST /api/chats`
- `POST /api/chat`
- lokale Header-/Auth-Behandlung
- Evidenz-JSON und Summary schreiben
- finale Assertion-Auswertung

Dadurch wird die bereits aufgebaute OR-Infrastruktur fuer genau diesen echten Live-Workflow noch nicht nutzbar.

## 5. Scope
### IN SCOPE
- sichtbare bounded OR-Lane fuer `janus-test-pipeline` im Modus `LIVE_TEST_EXECUTION`
- Eligibility-Regeln fuer kleine bis mittlere lokale Live-Retest-Slices
- allowlisted Worker-Paket fuer Health-/Chat-/Prompt-/Evidenz-Schritte
- bounded Behandlung des lokalen Dev-Auth-/Header-Pfads ohne versionierte Secret-Leaks
- Review-Handoff an Codex mit klarer finaler PASS/FAIL-Autoritaet bei Codex
- Regressionstests fuer Gate, Eligibility, Paketvertrag und Review-Artefakte

### OUT OF SCOPE
- breite Shell-Freiheit fuer OR
- delegierte finale PASS-/Release-/Git-/Routing-Entscheidungen
- Produktlogik-Fixes ausserhalb der Testpipeline-/OR-Infrastruktur
- generische Live-Test-Autoritaet fuer beliebige externe oder unbounded Provider-Workflows

## 6. Functional Requirements
- `janus-test-pipeline` beschreibt eine sichtbare OR-Option fuer eligible `LIVE_TEST_EXECUTION`-Slices.
- Die Lane bindet genau definierte Worker-Eingaben, erlaubte Commands, Copy-Back-Dateien und Review-Ausgaben.
- Der lokale Dev-API-Auth-Pfad wird bounded behandelt, ohne Secrets in versionierte Artefakte zu schreiben.
- Der Worker darf nur den erlaubten Retest-Ablauf und die Evidenzsammlung ausfuehren.
- Codex bleibt finaler Reviewer fuer PASS/FAIL, Backlog-Routing und alle Repo-Zustandsaenderungen.

## 7. Acceptance Criteria
- [ ] Fuer eligible `LIVE_TEST_EXECUTION`-Retests erscheint ein sichtbares `1 = Codex / 2 = OR` Gate.
- [ ] Der OR-Pfad nutzt einen bounded Worker-Vertrag statt offener Shell-Freiheit.
- [ ] Lokale Auth-/Header-Anforderungen sind im Lane-Design sauber abgesichert, ohne Secrets in versionierte Repo-Artefakte zu schreiben.
- [ ] Die Rueckgabe an Codex enthaelt review-faehige Evidenzartefakte und keinen delegierten Abschlussanspruch.
- [ ] Regressionstests decken Eligibility, Gate-Ausgabe, Worker-Paketvertrag und Review-Handoff ab.

## 8. Evidence
- `documentation/test-runs/BACKLOG-116_live_retest_after_debug_2026-07-01.md`
- `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_evidence.json`
- `documentation/codex/skills/janus-test-pipeline/SKILL.md`
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`

## 9. Risks
- Ein zu weiter Worker-Vertrag wuerde lokale Auth-, Shell- oder Evidenzgrenzen aufweichen.
- Ein zu enger Vertrag kann die Lane nutzlos machen und nur neue Operator-Komplexitaet erzeugen.
- Falsch versionierte oder indirekt geleakte Auth-/Header-Daten waeren fuer diese Lane inakzeptabel.

## 10. Validation Mapping
- sichtbares Gate -> Nutzer bekommt die OR-Option im richtigen Live-Retest-Fenster
- bounded Worker-Vertrag -> keine breite Shell- oder Repo-Autoritaet
- lokaler Auth-Pfad -> Live-Retest kann technisch laufen, ohne Secret-Leaks
- Review-Handoff -> Codex behaelt finale PASS/FAIL-Hoheit
- Regressionstests -> die Lane bleibt produktiv stabil

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

## NEXT STEP

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/backlog_BACKLOG-118_bounded_or_lane_live_test_execution.md
Backlog Item: BACKLOG-118
```
