# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 66
confidence: HIGH
dashboard_hint: CAUTION
reason: The feature productizes the isolated Aider/OpenRouter worker lane with normalized artifacts, strict boundaries, and Codex-owned acceptance.

## FEATURE IDENTITY
- Feature Name: Janus Worker Gateway fuer isolierte Aider/OpenRouter Delegation
- Feature Type: Interner Lean-Dev Workflow und Delegations-Gateway
- Primary Goal: Codex soll klar begrenzte Fleißarbeiten an einen isolierten Aider/OpenRouter Worker delegieren koennen und danach ein normiertes Abnahmepaket statt rohem Agenten-Chat pruefen.
- Trigger Source: Der Nutzer hat nach Recherche Option A gelockt: zuerst den bestehenden Aider/OpenRouter-Pfad stabilisieren und OpenCode/OpenHands bewusst aus dem MVP ausklammern.
- Primary Persona: Janus-Operator, der Codex als Planer, Reviewer und Gatekeeper nutzt und guenstige Worker fuer kleine bis mittlere bounded Dev-Aufgaben einsetzen will.

## USER VALUE

Der Nutzer bekommt eine vertrauenswuerdige Delegationsschicht, die Codex-Kontingent bei klaren Fleißarbeiten sparen kann, ohne Janus-Governance, Review-Verantwortung oder Git-Sicherheit aufzugeben.

Der Wert liegt nicht in einem weiteren offenen Agenten-Experiment, sondern in einem engen Worker-Vertrag: Codex formuliert die Aufgabe, der Worker arbeitet isoliert, und Codex bewertet nur normierte Ergebnisartefakte.

## TARGET SURFACE
- Primary Surface: interner Janus/Codex Dev-Workflow fuer bounded Worker-Delegation
- Existing Surface: Ja
- Existence Confirmation: confirmed by repo/context
- In-Scope Surfaces: stabiler lokaler Worker-Gateway-Einstieg fuer Aider/OpenRouter; Task-Datei-Vertrag; isolierte Worker-Ausfuehrung; normierte Run-Artefakte; Codex-owned Review und Accept/Reject
- Explicit Non-Surfaces: OpenCode-Backend im MVP; OpenHands-Backend; globale OR-Freigabe; Janus-Produktoberflaechen; Endnutzerfunktionen; Git-, Release-, Publish- oder Dependency-Autoritaet fuer Worker

## USER ACTION SURFACE
- Entry Action: Codex erzeugt fuer einen geeigneten bounded Dev-Slice eine praezise Worker-Aufgabe und startet den lokalen Worker-Gateway-Einstieg mit einem benannten Profil.
- Required Inputs: gebundene Aufgabe, Worker-Profil, erlaubte Dateigrenzen, verbotene Aktionen, Akzeptanzkriterien und auszufuehrende Checks
- Success Feedback: Der Gateway-Lauf liefert einen maschinenlesbaren Status, eine menschenlesbare Zusammenfassung, einen review-faehigen Diff, Test-/Check-Ausgaben, geaenderte Dateien und soweit verfuegbar Kostenmetadaten.
- Failure Feedback: Der Gateway-Lauf endet mit `failed` oder `blocked`, wenn Scope, Tests, Modellantwort, Kosten-/Konfigurationsvoraussetzungen oder Artefaktqualitaet nicht ausreichen.
- Cancel / Undo Behavior: Codex kann den Worker-Lauf ablehnen, verwerfen, einen einmaligen engeren Retry formulieren oder lokal selbst fortfahren; keine Worker-Aenderung gilt ohne Codex-Review als akzeptiert.

## SYSTEM BEHAVIOR

Wenn Codex eine geeignete kleine oder mittlere Dev-Aufgabe mit klaren Dateigrenzen erkennt, darf der Worker-Gateway-Pfad als bewusster Delegationsschritt genutzt werden.

Der MVP nutzt ausschliesslich Aider/OpenRouter als Worker-Backend. Weitere Backends wie OpenCode bleiben bis nach einem erfolgreichen Live-Dev-Test ausserhalb des MVP.

Codex bleibt Owner fuer Aufgabenformulierung, Scope, Modellprofil-Auswahl, Review, Accept/Reject, Fallback und jede weitere Janus-Pipeline-Entscheidung.

Der Worker darf nur in einem isolierten Arbeitsbereich arbeiten und darf keine Commit-, Push-, Release-, Publish- oder Dependency-Aktionen ausfuehren.

Der Gateway-Lauf muss vor der Ausfuehrung die Aufgabe, die erlaubten Dateigrenzen, die verbotenen Aktionen und die auszufuehrenden Checks nachvollziehbar binden.

Der Gateway-Lauf muss nach der Ausfuehrung immer ein normiertes Ergebnispaket erzeugen, auch wenn die Ausfuehrung blockiert oder fehlgeschlagen ist.

Ein Lauf darf nur als `success` gelten, wenn keine verbotenen Dateien betroffen sind, die geforderten Checks erfolgreich sind oder ausdruecklich nicht gefordert wurden, keine Git-Governance-Aktion erfolgt ist und die Ergebnisartefakte vollstaendig review-faehig sind.

Wenn der Worker ausserhalb der erlaubten Grenzen arbeitet, Tests fehlschlagen, kein verwertbarer Diff entsteht oder die Modellantwort nicht dem Vertrag entspricht, muss der Lauf fail-closed bei Codex landen.

Codex soll fuer geeignete Aufgaben den Worker-Gateway-Pfad bevorzugt in Betracht ziehen, aber niemals Worker-Ergebnisse ohne Diff- und Evidenzpruefung uebernehmen.

## DATA / PERSISTENCE
- Created Data: Worker-Task-Artefakte, Run-Verzeichnisse, normierte Ergebnisdateien, Test-/Check-Logs, Diff-Artefakte, geaenderte-Dateien-Listen, Kosten- oder Usage-Metadaten soweit verfuegbar
- Updated Data: lokale Janus/Codex-Workflow-Artefakte und Usage-/State-Dokumentation, wenn der Lauf Teil eines substantiellen Janus-Arbeitsblocks ist
- Deleted Data: Nicht zutreffend: Das Gateway definiert keinen regulaeren Loeschpfad als Erfolgsbedingung
- Persistence Scope: lokale Dev- und Evidenzartefakte innerhalb des bestehenden Janus/Codex-Artefaktrahmens
- Canonical Review Record: Codex-Review, normiertes Worker-Ergebnis, Diff und Check-Logs bilden gemeinsam den kanonischen Bewertungsnachweis
- Failure Persistence: fehlgeschlagene oder blockierte Worker-Laeufe bleiben als Diagnose- und Optimierungssignal sichtbar und werden nicht stillschweigend ueberschrieben

## CONSTRAINTS

Der MVP bleibt auf Aider/OpenRouter als einziges Worker-Backend begrenzt.

Der Worker darf nur fuer klar begrenzte Aufgaben mit expliziten Dateigrenzen und Akzeptanzkriterien genutzt werden.

Der Worker darf keine Commit-, Push-, Tag-, Merge-, Release-, Publish-, Dependency-, Secret-, Auth-, Security-, Privacy- oder Migrationsentscheidungen ausfuehren.

Der Worker darf keine Architekturentscheidungen treffen und darf keine produktive Abschlussautoritaet erhalten.

Jeder Lauf muss mit einem fail-closed Ergebnis enden koennen, ohne dass Codex die rohe Modellantwort lesen muss.

Modellprofile muessen zentral beschreibbar sein, damit Codex Aufgaben ueber Profile und nicht ueber verstreute Modellnamen delegiert.

OpenRouter-Modellverfuegbarkeit, Kosten und Providerverhalten muessen als veraenderlich behandelt und vor breiterer Nutzung validiert werden.

## SECURITY / PRIVACY
- Trust Boundary: Aider/OpenRouter bleibt ein externer bounded Worker ohne eigene Janus-Governance-, Routing-, Git-, Release- oder Abschlussautoritaet.
- Local Authority Owner: Codex bleibt Owner fuer Scope, Review, Annahme, Ablehnung, Retry, Fallback und dokumentierten Abschluss.
- Sensitive Data Rule: Nur der fuer die konkrete bounded Aufgabe notwendige Kontext darf an den Worker gegeben werden; Secrets, Tokens und private lokale Maschinendetails duerfen nicht in Task- oder Ergebnisartefakte gelangen.
- Write Safety Rule: Worker-Aenderungen duerfen nur innerhalb der explizit erlaubten Dateigrenzen akzeptierbar sein und muessen ueber Diff und geaenderte-Dateien-Liste reviewbar bleiben.
- Forbidden Actions: keine Commits; keine Pushes; keine origin-Aktionen; keine Releases; keine Dependency- oder Secret-Aenderungen; keine Architekturumbauten; keine Produktentscheidungen; keine Aenderungen ausserhalb der erlaubten Grenzen
- Auditability: Jeder Worker-Lauf muss ueber normierte Artefakte, Check-Logs, Scope-Pruefung und Codex-owned Review-Ausgang nachvollziehbar bleiben.

## EDGE CASES

- Wenn Aider nicht verfuegbar oder nicht korrekt konfiguriert ist, endet der Gateway-Lauf als `blocked`.
- Wenn OpenRouter-Key, Modellprofil, Kostenbasis oder Providerzugriff fehlen, endet der Gateway-Lauf als `blocked` oder vor der Worker-Ausfuehrung als fail-closed.
- Wenn der aktuelle Worktree bereits relevante uncommitted Aenderungen enthaelt, muss der Gateway-Lauf seine Baseline sauber abgrenzen oder blockieren.
- Wenn der Worker Dateien ausserhalb der erlaubten Grenzen beruehrt, darf das Ergebnis nicht `success` sein.
- Wenn Tests oder Checks fehlschlagen, darf das Ergebnis nicht `success` sein, ausser die Aufgabe definiert ausdruecklich einen Analyse- oder No-op-Fall ohne Erfolgschecks.
- Wenn der Worker eine Architekturentscheidung benoetigt, muss er blockieren statt eigenmaechtig zu entscheiden.
- Wenn die Ergebnisartefakte fehlen, unvollstaendig sind oder nicht maschinenlesbar ausgewertet werden koennen, muss Codex den Lauf ablehnen oder lokal fallbacken.
- Wenn der Worker fachlich plausibel wirkt, aber die Evidenz nicht ausreicht, bleibt Codex verpflichtet, den Diff und die Checks kritisch zu pruefen.

## DEFINITION OF DONE

- [ ] Wenn Codex eine geeignete bounded Dev-Aufgabe delegiert, dann existiert beobachtbar ein stabiler lokaler Worker-Gateway-Einstieg fuer ein Aider/OpenRouter-Profil.
- [ ] Wenn ein Worker-Lauf startet, dann sind Aufgabe, erlaubte Dateigrenzen, verbotene Aktionen, Akzeptanzkriterien und Checks beobachtbar gebunden.
- [ ] Wenn ein Worker-Lauf endet, dann liegen beobachtbar normierte Ergebnisartefakte fuer Status, Zusammenfassung, Diff, Checks, geaenderte Dateien und Kosten-/Usage-Metadaten soweit verfuegbar vor.
- [ ] Wenn der Worker ausserhalb der erlaubten Grenzen arbeitet, dann wird der Lauf beobachtbar nicht als `success` akzeptiert.
- [ ] Wenn geforderte Tests oder Checks fehlschlagen, dann wird der Lauf beobachtbar nicht als `success` akzeptiert.
- [ ] Wenn ein Worker-Lauf erfolgreich ist, dann kann Codex beobachtbar zuerst das maschinenlesbare Ergebnis und danach Diff und Check-Logs pruefen, ohne den rohen Agenten-Chat als Primaerquelle zu brauchen.
- [ ] Wenn der Worker blockiert oder fehlschlaegt, dann kann Codex beobachtbar zwischen engerem Retry, lokalem Fallback oder Abbruch entscheiden.
- [ ] Wenn der MVP live erprobt wird, dann geschieht dies beobachtbar zuerst an einer kleinen, nicht release- oder sicherheitskritischen Dev-, Doku- oder Testaufgabe.

## TEST STRATEGY
- Primary Validation Mode: lokale Runner-/Gateway-Vertragsvalidierung, Artefaktvalidierung und mindestens ein bounded Live-Dev-Test mit anschliessender Codex-Review
- Required Evidence: gebundene Task-Datei; Profilwahl; isolierter Worker-Lauf; Ergebnisstatus; Diff; Check-Logs; geaenderte-Dateien-Liste; Kosten-/Usage-Metadaten soweit verfuegbar; Codex-owned Accept/Reject-Ausgang
- Success Cases: docs-only Aufgabe; test-only Aufgabe; kleine Code-Hilfsdatei mit klarer Allowlist; erfolgreicher Lauf mit vollstaendigen Artefakten; erfolgreicher Codex-Review ohne Rohchat-Abhaengigkeit
- Failure Cases: fehlender OpenRouter-Key; ungueltiges Profil; verbotene Datei beruehrt; rote Tests; fehlende Ergebnisartefakte; unbrauchbarer Modelloutput; bestehende relevante Worktree-Konflikte
- Regression Focus: keine Repo-Root-Seiteneffekte; keine Commits oder Pushes; keine Aenderungen ausserhalb der erlaubten Grenzen; kein stiller Erfolg bei roten Checks; OpenCode/OpenHands bleiben ausserhalb des MVP

## OUT OF SCOPE

OpenCode als zweites Backend im MVP.

OpenHands oder andere always-approve Agenten als erster Standardpfad.

Ein vollwertiger neuer Coding-Agent statt eines Gateway-Vertrags um vorhandene Worker.

Globale OR-Freigabe fuer alle Janus-Skills.

Produktlogik-Implementierungen ohne normale Janus-Pipeline aus Spec, Task, Precheck, Execution und Audit.

Automatische Git-, Release-, Publish-, Dependency-, Security-, Auth-, Privacy- oder Migrationsaktionen durch den Worker.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 66
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-02
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-07-02
- Validation Evidence:
  - `documentation/tasks/TASK-SPEC29.1_final_audit.md`
  - `documentation/tasks/TASK-SPEC29.2_final_audit.md`
  - `documentation/tasks/TASK-SPEC29.3_final_audit.md`
  - `python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"` - PASS (`27` tests)
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py` - PASS
  - `development/openrouter-skill-tests/janus-worker-gateway-live/runs/WF-JANUS-WORKER-GATEWAY-LIVE-001/RESULT.json`
- Implementation Note: The worker-gateway MVP is sealed with a normalized fail-closed contract, isolated Aider/OpenRouter backend wiring, tighter regression coverage, documented MVP profiles, and one bounded docs-only live-dev pilot. Codex remains the review and acceptance owner; broader coding-task evidence and additional backend families remain future work.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 14
- Architectural Risk: 15
- State / Persistence Complexity: 11
- Cross-System Dependencies: 16
- Ambiguity Level: 10
- Total Complexity Score: 66
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
