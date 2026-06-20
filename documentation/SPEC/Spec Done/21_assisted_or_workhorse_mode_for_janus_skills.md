# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 61
confidence: HIGH
dashboard_hint: CAUTION
reason: The first rollout is closed to janus-debug and janus-test-pipeline with explicit user choice, telemetry, and local validation ownership.

## FEATURE IDENTITY
- Feature Name: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Feature Type: Workflow-Erweiterung fuer bestehende Janus-Skills
- Primary Goal: Bei geeigneten bounded Arbeitsschritten eine klare Wahl zwischen Codex und OpenRouter anbieten, ohne lokale Kontroll- und Validierungsgrenzen aufzugeben.
- Trigger Source: Skillseitiger Operator-Gate in einem OR-faehigen Janus-Schritt
- Primary Persona: Operator, der je nach Kontingent- und Kostensituation zwischen Codex und OR entscheiden will

## USER VALUE

Der Nutzer kann bei geeigneten Arbeitsschritten bewusst zwischen lokaler Codex-Ausfuehrung und einem guenstigeren OR-Arbeitspferd waehlen. Dadurch werden Codex-Kontingent und laufende OR-Kosten situativ steuerbar, ohne dass Janus dabei lokale Sicherheits-, Governance- oder Validierungshoheit verliert.

## TARGET SURFACE
- Primary Surface: Bestehende Janus-Skill-Workflows mit Operator-Gate
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: Skillseitige Betriebswahl, bounded OR-Worker-Aufruf, Telemetrie-/Ergebnisdarstellung und lokaler Fallback ausschliesslich in `janus-debug` und `janus-test-pipeline`
- Initial Allowed Skills: `janus-debug` und `janus-test-pipeline`; Analyse-Aufgaben gehoeren nur als bounded Schritte innerhalb dieser beiden Skills zum Pilotumfang
- Explicit Non-Surfaces: Alle anderen Janus-Skills, Produktionsrouting, kanonische Routing-Tabelle, autonomer Release-/Git-Pfad und freie Repo-Schreibdelegation

## USER ACTION SURFACE
- Entry Action: Der Skill zeigt bei einem geeigneten bounded Schritt die Wahl `1 = Codex` oder `2 = OR-Arbeitspferd`
- Required Inputs: Nutzerauswahl, angezeigte voraussichtliche OR-Kosten, angezeigter Zuverlaessigkeits-/Konfidenzhinweis
- Success Feedback: Janus zeigt den gewaehlten Ausfuehrungspfad, das Ergebnis des bounded OR-Schritts und die tatsaechlichen OR-Kosten an
- Failure Feedback: Janus zeigt klar an, dass OR wegen Cost-, Validation-, Reliability- oder Contract-Gates nicht akzeptiert wurde und auf Codex-only oder Manual Review zurueckfaellt
- Cancel / Undo Behavior: Vor Start des OR-Schritts kann der Nutzer den Codex-Pfad waehlen; nach einem fehlgeschlagenen OR-Schritt erfolgt kein automatischer Apply und kein persistenter Repo-Eingriff durch OR

## SYSTEM BEHAVIOR

Janus erweitert bestehende geeignete Skill-Schritte um einen assistierten OR-Arbeitspferd-Modus. Dieser Modus ist nur fuer bounded, review-first und lokal validierbare Arbeitsschritte zulaessig.

Im ersten Ausbau arbeitet OR nicht als autonomer Repo-Akteur, sondern als assistierter Worker mit genau einem strukturierten Arbeitsschritt pro Lauf. OR darf daher in einem einzelnen Lauf zum Beispiel eine Analyse, einen Test-Review-Hinweis, einen strukturierten Patch-Kandidaten oder einen einzelnen Tool-Vorschlag erzeugen, aber keinen mehrstufigen freien Agentenloop ausfuehren.

Lokale Ausfuehrungshoheit bleibt bei Janus/Codex/Runnern. Wenn OR einen Tool-Schritt oder einen bounded Ergebnisvorschlag erzeugt, wird dieser lokal ausgefuehrt, geprueft, akzeptiert oder verworfen. OR selbst fuehrt im ersten Ausbau keine autonome lokale Aktion aus.

Der OR-Pfad wird nur angeboten, wenn der aktuelle Schritt klar in eine zugelassene bounded Klasse faellt, vorab definierte Gates erfuellt, eine Kostenprognose vorliegt und ein Zuverlaessigkeitshinweis verfuegbar ist. Wenn eines dieser Elemente fehlt oder widerspruechlich ist, bleibt der Schritt Codex-only oder faellt in Manual Review.

Im ersten Rollout darf diese Pruefung nur innerhalb von `janus-debug` und `janus-test-pipeline` stattfinden. Jeder andere Janus-Skill bleibt Codex-only, auch wenn ein einzelner Schritt auf den ersten Blick bounded, review-first und lokal validierbar wirkt. Eine Erweiterung der erlaubten Skill-Menge ist eine spaetere, explizite Produktentscheidung.

Nach einem OR-Lauf zeigt Janus das Ergebnis inklusive tatsaechlicher Kosten, Validierungsstatus und Fallback-Status an. Ein nicht akzeptierter OR-Lauf darf keinen impliziten Erfolg behaupten.

## DATA / PERSISTENCE
- Stored Artifacts: Telemetrie, Kostenprognose, tatsaechliche Kosten, Zuverlaessigkeits-/Konfidenzwerte, Validierungsergebnis, Fallback-Status, Ergebnis-Klassifikation, Laufartefakte
- Persistence Scope: Lokale Workflow-, Healthcheck- und Evidenzartefakte innerhalb des bestehenden Janus-/Codex-Dokumentations- und Run-Artefakt-Systems
- State Mutation: OR darf im ersten Ausbau keine unkontrollierte autonome Repo-Mutation verursachen; persistente Repo-Aenderungen bleiben an lokale Review-/Apply-Gates gebunden
- Data Lifecycle: Jeder substantielle OR-Arbeitsblock erzeugt nachvollziehbare Evidenz fuer Kosten, Zuverlaessigkeit, Validierung und Akzeptanz oder Ablehnung

## CONSTRAINTS

- Nur bounded, review-first, lokal validierbare Schritte duerfen OR-faehig sein.
- Im ersten Rollout duerfen nur `janus-debug` und `janus-test-pipeline` einen OR-Pfad anbieten; alle anderen Skills bleiben Codex-only.
- Der erste Ausbau bleibt assistiert; kein freier mehrstufiger Tool-Agent.
- Ein OR-Lauf darf genau einen strukturierten Arbeitsschritt liefern.
- Lokale Validation, Apply/Reject und finale Annahme bleiben bei Codex/Janus.
- Es gibt keine Produktionsrouting-Aktivierung, keine globale OR-Freigabe und keine kanonische Routing-Tabellen-Aenderung in diesem Feature.
- Kosten- und Zuverlaessigkeitshinweise muessen vor der Nutzerwahl darstellbar sein.
- Tatsaechliche Kosten muessen nach einem OR-Lauf sichtbar gemacht werden, sofern vom Provider erfassbar oder sauber lokal rekonstruiert.

## SECURITY / PRIVACY
- Trust Boundary: OR bleibt externer assistierter Worker ohne autonome lokale Ausfuehrungs- oder Annahmehoheit
- Local Authority Owner: Codex/Janus/lokale Runner bleiben Owner fuer Tool-Ausfuehrung, Validation, Apply/Reject und Abschlussbewertung
- Sensitive Data Rule: Nur bounded, fuer den jeweiligen Schritt notwendiger Kontext darf an OR uebergeben werden
- Forbidden Actions: Keine freie Repo-Schreibgewalt, keine Release-/Git-Autoritaet, keine Produktionsrouting-Aktivierung, keine globale Modellfreigabe
- Auditability: Jeder OR-Lauf muss als akzeptiert, abgelehnt, fallback oder manual-review-beduerftig lokal nachvollziehbar dokumentierbar sein

## EDGE CASES

- Wenn ein Schritt nicht klar in eine zugelassene bounded Klasse faellt, wird OR gar nicht angeboten.
- Wenn der aktuelle Skill nicht `janus-debug` oder `janus-test-pipeline` ist, wird OR im ersten Rollout gar nicht angeboten.
- Wenn Kostenprognose oder Zuverlaessigkeitshinweis fehlen, bleibt der Schritt Codex-only.
- Wenn OR cap-ueberschreitend, trunciert, unparsebar oder validatorisch unzureichend liefert, wird der Schritt lokal als Fallback oder Manual Review behandelt.
- Wenn OR semantisch brauchbar, aber formal nicht akzeptierbar liefert, darf kein impliziter Erfolg behauptet werden.
- Wenn ein Skill-Schritt autoritativ, riskant, mehrdeutig oder scope-gefährdet ist, bleibt er Codex-only.

## DEFINITION OF DONE

- [x] Wenn ein geeigneter bounded Skill-Schritt erreicht wird, dann zeigt Janus beobachtbar die Wahl zwischen `1 = Codex` und `2 = OR-Arbeitspferd` an.
- [x] Wenn der aktuelle Skill `janus-debug` oder `janus-test-pipeline` ist und der Schritt alle lokalen Eligibility-Gates erfuellt, dann wird beobachtbar die Wahl zwischen `1 = Codex` und `2 = OR-Arbeitspferd` angezeigt.
- [x] Wenn OR angeboten wird, dann werden vor der Wahl beobachtbar voraussichtliche Kosten und ein Zuverlaessigkeits- oder Konfidenzhinweis angezeigt.
- [x] Wenn der Nutzer `2 = OR-Arbeitspferd` waehlt, dann startet beobachtbar genau ein assistierter, bounded OR-Arbeitsschritt und kein freier mehrstufiger Agentenloop.
- [x] Wenn OR ein Ergebnis liefert, dann werden beobachtbar Validierungsstatus, Fallback-Status und tatsaechliche OR-Kosten nach Abschluss angezeigt.
- [x] Wenn der OR-Lauf formale oder inhaltliche Gates verfehlt, dann faellt der Schritt beobachtbar auf Codex-only oder Manual Review zurueck, ohne impliziten Erfolg zu behaupten.
- [x] Wenn ein Schritt nicht bounded, nicht review-first oder nicht lokal validierbar ist, dann wird beobachtbar kein OR-Pfad angeboten.
- [x] Wenn der aktuelle Skill nicht `janus-debug` oder `janus-test-pipeline` ist, dann wird beobachtbar kein OR-Pfad angeboten.
- [x] Wenn ein OR-Lauf akzeptiert oder abgelehnt wird, dann bleibt beobachtbar die lokale Annahme- und Validierungshoheit bei Codex/Janus.

## TEST STRATEGY
- Validation Level: Workflow-, Gate-, Telemetrie- und Ergebnisfluss-Validierung
- Primary Evidence: Operator-Gate-Evidenz, Telemetrieartefakte, Kosten-/Konfidenzanzeige, Fallback-/Validation-Outcome, lokale Healthcheck-/Ingestion-Nachweise
- Required Automated Coverage: Gate-Eligibility, Cost-/Confidence-Anzeige, Single-Step-OR-Limit, Fallback-Pfad, Accepted-/Rejected-Outcome, Kostenanzeige nach Abschluss
- Manual Verification Need: Begrenzte Workflow-Sichtpruefung fuer die Nutzerwahl und die Ergebnisanzeige im echten Skill-Kontext
- Non-Goals For Testing: Keine Produktionsrouting- oder globale OR-Freigabevalidierung im Rahmen dieses Features

## OUT OF SCOPE

- Direkter frueher OR-Write-Worker mit autonomer lokaler Schreibausfuehrung
- Mehrstufige agentische Tool-Loops in der ersten Ausbaustufe
- Produktionsrouting-Aktivierung
- Kanonische Routing-Tabellen-Aenderung
- Globale OR-Freigabe fuer alle Skills
- OR-Angebote ausserhalb von `janus-debug` und `janus-test-pipeline` im ersten Rollout
- Unbegrenzter Repo-Zugriff fuer OR
- Release-, Git- oder Merge-Autoritaet fuer OR

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 14
- Architectural Risk: 16
- State / Persistence Complexity: 11
- Cross-System Dependencies: 15
- Ambiguity Level: 5
- Total Complexity Score: 61
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 61
- **Risk:** HIGH
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-20
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-06-20
- Final Audit Evidence: `documentation/tasks/TASK-SPEC21.4_final_audit.md`
- Final Slice Evidence: `documentation/tasks/TASK-SPEC21.4_skill_context_evidence.md`
