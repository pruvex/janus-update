# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 64
confidence: HIGH
dashboard_hint: CAUTION
reason: The feature adds a bounded OR lane for live local retests across test-pipeline gating, local auth handling, evidence contracts, and Codex-owned acceptance.

## FEATURE IDENTITY
- Feature Name: Bounded OR Lane fuer LIVE_TEST_EXECUTION
- Feature Type: Lean-Dev Workflow-Erweiterung fuer die Janus-Testpipeline
- Primary Goal: Einen sichtbaren bounded OR-Pfad fuer geeignete lokale Live-Retests im Modus `LIVE_TEST_EXECUTION` schaffen, waehrend Codex finale PASS/FAIL-Hoheit behaelt.
- Trigger Source: `BACKLOG-118` als Follow-up zu `BACKLOG-117` nach dem erfolgreichen, aber voll Codex-owned `BACKLOG-116`-Live-Retest.
- Primary Persona: Operator, der lokale Janus-Live-Retests bei passenden bounded Faellen bewusst an OR delegieren moechte, ohne Governance- oder Evidenzverlust.

## USER VALUE

Der Nutzer bekommt die bereits aufgebaute OR-Infrastruktur endlich auch an einem echten Live-Retest-Nutzungspunkt angeboten, statt nur in vorbereitenden oder assistiven Teilschritten.

Damit kann Codex-Kontingent bei klar begrenzten lokalen Retests gespart werden, ohne dass Review, Abschlussautoritaet und Janus-Governance verwischen.

## TARGET SURFACE
- Primary Surface: `janus-test-pipeline` im Modus `LIVE_TEST_EXECUTION`
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: sichtbares `1 = Codex / 2 = OR` Gate fuer eligible lokale Live-Retests; bounded Worker-Vertrag fuer `api/health`, Chat-Erzeugung, Prompt-Lauf und Evidenzsammlung; Review-Handoff an Codex
- Explicit Non-Surfaces: generische OR-Aktivierung fuer alle Live-Tests; unbounded Shell-Freiheit; finale PASS-/Release-/Git-/Routing-Autoritaet bei OR; globale Erweiterung auf externe oder nicht lokal bounded Testpfade

## USER ACTION SURFACE
- Entry Action: Der Nutzer startet in `janus-test-pipeline` einen eligible lokalen Live-Retest und sieht vor der Ausfuehrung die Wahl `1 = Codex` oder `2 = OR`.
- Required Inputs: explizite Operator-Wahl, gebundener Retest-Slice, erlaubte lokale Evidenzpfade und bestaetigter Live-Test-Kontext
- Success Feedback: Der Workflow zeigt den gewaehlten Pfad, die bounded OR-Lane, die erzeugten Evidenzartefakte und den finalen Codex-Review-Ausgang sichtbar an.
- Failure Feedback: Wenn Eligibility, lokaler Auth-Pfad, Worker-Vertrag oder Evidenzbedingungen nicht erfuellt sind, erscheint keine gueltige OR-Wahl oder der Ablauf faellt klar auf Codex-only zurueck.
- Cancel / Undo Behavior: Wenn der Nutzer Codex waehlt oder der OR-Pfad fail-closed endet, bleibt oder landet der Retest ohne delegierten Abschlussanspruch bei Codex.

## SYSTEM BEHAVIOR

Wenn `janus-test-pipeline` einen lokalen Live-Retest-Slice erkennt, der in einen klar bounded Vertrag fuer `LIVE_TEST_EXECUTION` faellt, darf ein sichtbares `1 = Codex / 2 = OR` Gate erscheinen.

Wenn der Nutzer `1 = Codex` waehlt, bleibt der bestehende Live-Retest-Ablauf unveraendert lokal bei Codex.

Wenn der Nutzer `2 = OR` waehlt, darf ein bounded Worker genau den erlaubten lokalen Retest-Ablauf ausfuehren. Dieser Ablauf umfasst nur die lane-spezifisch erlaubten Schritte wie lokalen Health-Check, kontrollierte Chat-Erzeugung, gebundene Prompt-Ausfuehrung und die Erzeugung review-faehiger Evidenzartefakte.

Die Lane darf nicht als allgemeiner Live-Test-Delegationsmodus erscheinen. Sie gilt nur fuer lokale, bounded, allowlisted Retest-Slices mit explizitem Vertragsrahmen.

Der lokale Dev-API-Auth-Pfad muss fuer diese Lane technisch nutzbar bleiben, ohne versionierte Secrets oder broad authority in Repo-Artefakte oder Worker-Kontexte zu leaken.

Wenn Eligibility, lokaler Auth-Kontext, Evidenzpfade oder Worker-Grenzen nicht erfuellt sind, muss der Einstieg fail-closed auf Codex-only bleiben.

Wenn ein OR-Lauf abgeschlossen ist, bleibt Codex immer die finale autoritative Instanz fuer Review, PASS/FAIL-Interpretation, Backlog-Routing und jeden dokumentierten Abschluss.

## DATA / PERSISTENCE
- Created Data: bounded Live-Retest-Run-Artefakte, review-faehige Evidenzzusammenfassungen, lane-spezifische Gate- und Outcome-Artefakte
- Updated Data: bestehende `documentation/test-runs/`, `documentation/test-results/` und lane-spezifische OR-Artefakte fuer den gebundenen Live-Retest-Fall
- Deleted Data: Nicht zutreffend: Die Lane definiert keinen regulaeren Loeschpfad als Erfolgsbedingung
- Persistence Scope: lokale Testpipeline- und OR-Evidenzpfade innerhalb des bestehenden Janus-/Codex-Artefaktrahmens
- Canonical Review Record: Codex-Review plus die bounded Live-Retest-Evidenz bilden gemeinsam den kanonischen Abschlussnachweis
- Failure Persistence: fehlgeschlagene oder abgelehnte OR-Live-Runs bleiben als bounded Evidenz sichtbar und gelten nicht stillschweigend als akzeptierter Testabschluss

## CONSTRAINTS

Die Lane darf nur fuer lokale und eindeutig gebundene `LIVE_TEST_EXECUTION`-Slices erscheinen.

Der Worker-Vertrag muss allowlisted sein und darf keine broad Shell-Freiheit oder generische Repo-Autoritaet erzeugen.

Der OR-Pfad darf zwar Health-/Chat-/Prompt-/Evidenz-Schritte ausfuehren, aber keine finale PASS-/Release-/Git-/Routing-Entscheidung treffen.

Lokale Auth-/Header-Anforderungen duerfen technisch nutzbar gemacht werden, aber nicht als versionierte Secrets oder frei wiederverwendbare Repo-Artefakte materialisieren.

Wenn Kosten-, Confidence-, Eligibility- oder Evidenzbedingungen fuer den konkreten Lane-Fall nicht erfuellt sind, erscheint keine normale OR-Wahl.

## SECURITY / PRIVACY
- Trust Boundary: OR bleibt ein externer bounded Worker ohne eigene Governance-, Routing-, Git-, Release- oder Abschlussautoritaet.
- Local Authority Owner: Codex bleibt Owner fuer Eligibility, Review, PASS/FAIL-Interpretation, Fallback und dokumentierten Abschluss.
- Sensitive Data Rule: Nur der fuer den gebundenen lokalen Live-Retest notwendige Kontext darf an OR gegeben werden; Secrets und wiederverwendbare Auth-Daten duerfen nicht in versionierte Artefakte gelangen.
- Write Safety Rule: Der Worker darf nur erlaubte lane-spezifische Evidenzpfade und bounded Retest-Artefakte bearbeiten.
- Forbidden Actions: keine broad Shell-Freiheit; keine generische Delegation beliebiger Live-Tests; keine finale PASS-/Release-/Git-/Routing-Hoheit; keine Secret-Exfiltration ueber Worker-Pakete oder Ergebnisartefakte
- Auditability: Jeder delegierte Live-Retest muss ueber file-first Evidenz, Gate-Artefakte und Codex-owned Review-Ausgang lokal nachvollziehbar bleiben.

## EDGE CASES

- Wenn ein Live-Test zwar lokal ist, aber mehr als den bounded Retest-Vertrag benoetigt, erscheint keine OR-Wahl.
- Wenn der lokale Auth-/Header-Pfad fuer den Worker nicht sauber bounded bereitgestellt werden kann, bleibt der Retest Codex-only.
- Wenn ein OR-Lauf zwar Antworttext liefert, aber die Evidenzartefakte unvollstaendig oder nicht review-faehig sind, darf Codex ihn nicht als gueltigen Abschluss akzeptieren.
- Wenn mehrere Prompts, breite manuelle Exploration oder ungeplante Folgeaktionen notwendig werden, faellt der Slice aus dieser Lane heraus.
- Wenn Kosten-, Confidence- oder Health-Gates fuer den konkreten Retest fehlen, bleibt der Einstieg fail-closed bei Codex.

## DEFINITION OF DONE

- [ ] Wenn ein lokaler `LIVE_TEST_EXECUTION`-Retest in den bounded Lane-Vertrag faellt, dann erscheint beobachtbar die Wahl `1 = Codex` und `2 = OR`.
- [ ] Wenn der konkrete Live-Retest nicht in den bounded Lane-Vertrag faellt, dann erscheint beobachtbar keine normale OR-Wahl.
- [ ] Wenn der Nutzer `2 = OR` waehlt, dann fuehrt der Worker beobachtbar nur die erlaubten lokalen Health-/Chat-/Prompt-/Evidenz-Schritte aus.
- [ ] Wenn der OR-Pfad lokale Auth-/Header-Unterstuetzung benoetigt, dann bleibt diese beobachtbar bounded und leakt keine versionierten Secrets in Repo-Artefakte.
- [ ] Wenn ein delegierter Live-Retest endet, dann bleibt beobachtbar Codex die finale Instanz fuer Review, PASS/FAIL-Interpretation und dokumentierten Abschluss.
- [ ] Wenn Evidenz, Eligibility oder Worker-Grenzen nicht stimmen, dann faellt der Retest beobachtbar fail-closed auf Codex-only oder Codex-review-backed Reject zurueck.

## TEST STRATEGY
- Primary Validation Mode: lokale Eligibility-, Gate-, Worker-Vertrags-, Evidenz- und Review-Handoff-Validierung fuer `janus-test-pipeline` `LIVE_TEST_EXECUTION`
- Required Evidence: sichtbares Gate fuer eligible und nicht eligible Faelle; bounded Worker-Paketnachweise; review-faehige Live-Retest-Evidenz; Codex-owned Accept/Reject-Ausgaenge
- Success Cases: eligible lokaler Retest mit sichtbarer OR-Wahl; erfolgreicher bounded OR-Live-Retest mit vollstaendiger Evidenz; lokaler Retest ausserhalb der Eligibility ohne OR-Wahl
- Failure Cases: fehlender lokaler Auth-Kontext; unzulaessiger Worker-Umfang; unvollstaendige Evidenz; fehlende Confidence-/Cost-/Eligibility-Daten; OR-Ergebnis ohne review-faehigen Abschluss
- Regression Focus: bestehender Codex-only Live-Retest bleibt intakt; keine broad Shell-Freiheit; keine Secret-Leaks; keine delegierte finale PASS-/Release-/Git-/Routing-Autoritaet

## OUT OF SCOPE

Globale OR-Freigabe fuer alle Live-Tests.

Beliebige externe Provider- oder Browser-Retests ohne bounded lokalen Vertrag.

Delegierte finale PASS-/Release-/Git-/Routing-Entscheidungen.

Produktlogik-Fixes ausserhalb der OR-/Testpipeline-Infrastruktur.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 64
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-01
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 13
- Architectural Risk: 14
- State / Persistence Complexity: 9
- Cross-System Dependencies: 16
- Ambiguity Level: 12
- Total Complexity Score: 64
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
