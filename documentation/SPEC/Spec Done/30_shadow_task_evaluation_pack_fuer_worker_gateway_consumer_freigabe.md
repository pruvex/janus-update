# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: high
new_chat: no
complexity_score: 54
confidence: HIGH
dashboard_hint: CAUTION
reason: Bounded worker evaluation pack with model comparison and consumer-release decision, but no product-code authority.

## FEATURE IDENTITY
- Feature Name: Shadow-Task Evaluation Pack fuer Worker-Gateway Consumer-Freigabe
- Feature Type: Interner Lean-Dev Evaluations- und Freigabeblock
- Primary Goal: Der Janus Worker Gateway soll ueber zwei realistische Shadow-Arbeitsklassen und einen kleinen Modellvergleich so bewertet werden, dass danach eine belastbare Freigabe- oder No-Go-Entscheidung fuer den ersten echten Worker-Consumer moeglich ist.
- Trigger Source: Nach dem abgeschlossenen Worker-Gateway-MVP will der Nutzer zuerst sichere skill-nahe Schattenaufgaben statt echten Janus-Produktcode testen.
- Primary Persona: Janus-Operator, der Codex als Reviewer und Gatekeeper nutzt und vor echtem Alltagseinsatz die praktische Worker-Tauglichkeit messen will.

## USER VALUE

Der Nutzer bekommt eine ruhige Zwischenstufe zwischen Infrastruktur-MVP und echtem Worker-Alltag. Statt direkt Produktcode zu riskieren, wird zuerst geprueft, ob die Delegationskette bei realistischen Arbeitsmustern stabil, guenstig und reviewbar bleibt.

Der Wert liegt nicht nur in einem technischen Pass, sondern in einer klaren Vergleichsaussage: welche Arbeitsklasse bereits gut passt, welches Modell wirtschaftlich sinnvoll wirkt und ob der erste echte Consumer schon verantwortbar ist.

## TARGET SURFACE
- Primary Surface: interner Janus/Codex Worker-Evaluationsworkflow
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: isolierte Shadow-Task-Laeufe fuer Doku/Fleissarbeit; isolierte Shadow-Task-Laeufe fuer Test-/Fixture-Arbeit; je Arbeitsklasse ein Vergleich von zwei festen Worker-Modellen; normierte Worker-Ergebnisartefakte; Codex-owned Vergleichsauswertung; finale Freigabe- oder No-Go-Empfehlung fuer den ersten echten Consumer
- Explicit Non-Surfaces: echter Janus-Produktcode; echte Skill-Schreibpfade; globale Worker-Freigabe; Git-, Release-, Publish- oder Dependency-Autoritaet; OpenCode/OpenHands; produktive Consumer-Aktivierung im selben Schritt

## USER ACTION SURFACE
- Entry Action: Codex bereitet einen gebundenen Evaluation-Pack mit zwei Shadow-Arbeitsklassen und je zwei festen Worker-Modellen vor und startet die Laeufe nacheinander.
- Required Inputs: definierte Shadow-Aufgaben; feste Klassenzuordnung; zwei feste Modelle pro Klasse; klare Akzeptanz- und Vergleichskriterien; isolierte Sandbox; Review-Regeln fuer Codex
- Success Feedback: fuer jede Arbeitsklasse liegen vergleichbare Worker-Artefakte, Qualitaetsbeobachtungen, Kostenwerte, Scope-Disziplin-Signale und eine zusammengefasste Freigabeempfehlung fuer den ersten echten Consumer vor
- Failure Feedback: wenn die Laeufe keine stabile Qualitaet, keine saubere Scope-Disziplin oder keine belastbare Vergleichbarkeit liefern, endet der Pack mit No-Go oder engerem Nachtest statt mit Consumer-Freigabe
- Cancel / Undo Behavior: Codex kann jeden einzelnen Lauf verwerfen, wiederholen oder die Evaluation abbrechen; kein Shadow-Lauf darf ohne Codex-Review in eine echte Produktfreigabe uebergehen

## SYSTEM BEHAVIOR

Der Evaluation-Pack prueft genau zwei Shadow-Arbeitsklassen: Doku-/Fleissarbeit und Test-/Fixture-Arbeit. Beide sollen echte Worker-Muster nachahmen, ohne direkt auf Janus-Produktcode oder produktive Skill-Artefakte zu schreiben.

Jede Arbeitsklasse wird mit genau zwei festen Worker-Modellen durchlaufen. Die Modelle duerfen innerhalb einer Klasse nicht dynamisch wechseln, damit Kosten, Qualitaet und Scope-Disziplin vergleichbar bleiben.

Alle Laeufe finden in einer isolierten Sandbox statt. Es gibt keinen echten Repo-Writeback ausserhalb der gebundenen Shadow-Oberflaeche, keine stillen Produktaenderungen und keine Freigabe durch blosses Modellvertrauen.

Codex bleibt in jedem Schritt Owner fuer Aufgabenformulierung, Start, Review, Vergleich, Abbruch, Retry und abschliessende Empfehlung. Der Worker liefert nur bounded Ausfuehrung und normierte Ergebnisartefakte.

Der Pack gilt nur dann als erfolgreich, wenn die beiden Arbeitsklassen vergleichbar ausgewertet werden koennen und daraus eine klare naechste Entscheidung entsteht: erster echter Consumer freigeben, engeren Nachtest fahren oder No-Go aussprechen.

## DATA / PERSISTENCE
- Created Data: Shadow-Task-Pakete; isolierte Run-Artefakte; Worker-Ergebnisverzeichnisse; Modellvergleichsnotizen; Kosten- und Qualitaetsvergleiche; ein Abschlussartefakt mit Consumer-Empfehlung
- Updated Data: lokale Janus/Codex-Evaluations- und Statusartefakte fuer diesen bounded Arbeitsblock
- Deleted Data: Nicht zutreffend: Der Evaluation-Pack braucht keinen regulaeren Loeschpfad als Erfolgsbedingung
- Persistence Scope: lokale Dev- und Evidenzartefakte innerhalb des bestehenden Worker- und Janus-Dokumentationsrahmens
- Canonical Review Record: normierte Worker-Ergebnisse pro Lauf plus Codex-Vergleichsauswertung und finale Freigabe- oder No-Go-Entscheidung
- Failure Persistence: fehlgeschlagene oder unklare Vergleichslaeufe bleiben als sichtbares Diagnose- und Optimierungssignal erhalten

## CONSTRAINTS

Der Pack bleibt auf genau zwei Shadow-Arbeitsklassen begrenzt.

Jede Arbeitsklasse wird mit genau zwei festen Worker-Modellen verglichen.

Es gibt keine echten Repo-Schreibpfade ausserhalb der isolierten Shadow-Sandbox.

Der Pack darf keine echte Skill-Freigabe, keine globale Modellfreigabe und keine automatische Ausweitung auf Code-Helfer-Slices implizit behaupten.

Der Evaluation-Pack darf nur dann einen ersten echten Consumer empfehlen, wenn Qualitaet, Scope-Disziplin, Reviewbarkeit und Kostenlage gemeinsam tragfaehig wirken.

## SECURITY / PRIVACY
- Trust Boundary: Der Worker bleibt ein externer bounded Ausfuehrungspfad ohne Janus-Governance-, Routing-, Git-, Release- oder Abschlussautoritaet
- Local Authority Owner: Codex bleibt Owner fuer Aufgabenbindung, Modellvergleich, Review, Freigabe, Ablehnung, Retry und Abschlussentscheidung
- Sensitive Data Rule: Shadow-Aufgaben duerfen keinen unnötigen echten Produkt- oder Geheimkontext enthalten
- Write Safety Rule: Alle Laeufe bleiben in isolierter Sandbox und duerfen keine produktiven Repo-Writebacks verursachen
- Forbidden Actions: keine Commits; keine Pushes; keine Releases; keine Produktcode-Freigabe; keine Skill-Schreibpfade; keine Dependency-Aenderungen; keine Architekturentscheide; keine Aenderungen ausserhalb der gebundenen Shadow-Oberflaeche
- Auditability: jeder Vergleichslauf muss ueber normierte Artefakte, Kostenhinweise, Qualitaetsbeobachtungen und Codex-owned Review dokumentiert bleiben

## EDGE CASES

Wenn beide Modelle in einer Arbeitsklasse fachlich schwach sind, darf der Pack trotzdem mit einem klaren No-Go fuer genau diese Klasse enden.

Wenn ein Modell billiger, aber deutlich unzuverlaessiger ist, muss die Auswertung das sichtbar gegenueber dem teureren Modell gewichten statt nur Kosten zu vergleichen.

Wenn eine Arbeitsklasse gute Inhalte liefert, aber die Scope-Disziplin verliert, darf sie nicht fuer den ersten echten Consumer freigegeben werden.

Wenn die Worker-Artefakte zwischen den zwei Modellen nicht ausreichend vergleichbar sind, muss die Evaluationsentscheidung blockieren oder einen engeren Nachtest verlangen.

Wenn eine Klasse funktioniert und die andere nicht, darf der Pack trotzdem eine partielle Freigabeempfehlung fuer nur den sichereren ersten Consumer abgeben.

## DEFINITION OF DONE

- [ ] Wenn der Evaluation-Pack gestartet wird, dann laufen beobachtbar genau zwei Shadow-Arbeitsklassen in isolierter Sandbox statt auf echten Produktpfaden.
- [ ] Wenn eine Arbeitsklasse bewertet wird, dann werden beobachtbar genau zwei feste Worker-Modelle fuer dieselbe gebundene Aufgabe verglichen.
- [ ] Wenn ein einzelner Shadow-Lauf endet, dann liegen beobachtbar normierte Worker-Ergebnisartefakte fuer Qualitaets- und Scope-Review vor.
- [ ] Wenn ein Modell ausserhalb der gebundenen Shadow-Grenzen arbeitet oder unzureichende Review-Evidenz liefert, dann wird es beobachtbar nicht als freigabefaehig bewertet.
- [ ] Wenn beide Modelle einer Arbeitsklasse abgeschlossen sind, dann entsteht beobachtbar ein vergleichbarer Kosten-, Qualitaets- und Scope-Disziplin-Befund fuer genau diese Klasse.
- [ ] Wenn der gesamte Evaluation-Pack abgeschlossen ist, dann liegt beobachtbar eine klare Empfehlung fuer den ersten echten Worker-Consumer oder ein klares No-Go beziehungsweise Nachtest-Signal vor.

## TEST STRATEGY
- Primary Validation Mode: isolierte Shadow-Laeufe mit normierten Worker-Ergebnissen, anschliessender Codex-Vergleichsauswertung und finaler Freigabe- oder No-Go-Entscheidung
- Required Evidence: zwei gebundene Shadow-Arbeitsklassen; je Klasse zwei feste Worker-Modelle; normierte Worker-Artefakte; Kostenhinweise; Qualitaetsvergleich; Scope-Disziplin-Befund; Abschlussentscheidung
- Success Cases: beide Shadow-Klassen bleiben isoliert und reviewbar; mindestens eine Klasse zeigt tragfaehige Qualitaet und Scope-Disziplin; die Modellvergleiche sind wirtschaftlich und praktisch auswertbar; der erste echte Consumer kann klar empfohlen oder sauber blockiert werden
- Failure Cases: unbrauchbare Worker-Qualitaet; fehlende Vergleichbarkeit; Scope-Verlust; inkonsistente Artefakte; keine belastbare Empfehlung; impliziter Drift in echte Repo- oder Produktpfade
- Regression Focus: kein stiller echter Repo-Writeback; keine Produktcode-Freigabe; kein Vergleich mit dynamisch wechselnden Modellen; keine Consumer-Empfehlung ohne klare Review- und Vergleichsevidenz

## OUT OF SCOPE

Echte Produktcode-Delegation.

Ein dritter Code-Helfer-Slice im ersten Evaluation-Pack.

Globale Worker-Freigabe fuer mehrere Skills.

OpenCode-, OpenHands- oder Mehrbackend-Rollout.

Automatische Git-, Release-, Publish-, Dependency-, Security- oder Privacy-Aktionen.

Produktive Consumer-Aktivierung im selben Arbeitsblock.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 54
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-02
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-07-03
- Validation Evidence:
  - `documentation/tasks/TASK-SPEC30.1_final_audit.md`
  - `documentation/tasks/TASK-SPEC30.2_final_audit.md`
  - `documentation/tasks/TASK-SPEC30.3_final_audit.md`
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/runs/WF-SPEC30-SHADOW-EVAL-001/evaluation_summary.json`
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/runs/WF-SPEC30-SHADOW-EVAL-001/docs_fleissarbeit/comparison_summary.json`
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/runs/WF-SPEC30-SHADOW-EVAL-001/test_fixture_arbeit/comparison_summary.json`
- Implementation Note: Spec 30 is sealed as a three-slice bounded shadow-evaluation block. The final recommendation stays intentionally narrow: `docs_fleissarbeit` is the first calm worker-consumer candidate, `openrouter/moonshotai/kimi-k2.5` is the preferred first fixed model for that consumer, and `test_fixture_arbeit` remains the tighter retest class. No productive worker-consumer activation, broad routing rollout, or measured cost-superiority claim is implied by this closeout.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 11
- Architectural Risk: 10
- State / Persistence Complexity: 8
- Cross-System Dependencies: 13
- Ambiguity Level: 12
- Total Complexity Score: 54
- Routing Decision: 5.4
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
