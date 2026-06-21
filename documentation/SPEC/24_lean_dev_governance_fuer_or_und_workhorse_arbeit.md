# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 47
confidence: HIGH
dashboard_hint: CAUTION
reason: Internal Dev governance needs one bounded rule-set so OR and workhorse infrastructure can move faster without weakening Janus product controls.

## FEATURE IDENTITY
- Feature Name: Lean Dev-Governance fuer OR- und Workhorse-Infrastrukturarbeit
- Feature Type: Governance-Regel fuer internen Dev-Arbeitsmodus
- Primary Goal: Kleine und mittlere bounded Dev-Slices deutlich schlanker abwickeln, ohne Janus-Produktarbeit oder Sicherheitsgrenzen aufzuweichen.
- Trigger Source: Arbeit an Dev-/OR-/Workhorse-Infrastruktur statt an Janus-Produktlogik
- Primary Persona: Operator und Codex bei interner Dev- und OR-Infrastrukturarbeit

## USER VALUE

Unsere Arbeit an OR- und Workhorse-Infrastruktur wird deutlich schneller, weil kleine und mittlere gebundene Dev-Slices nicht mehr automatisch den vollen Janus-Produktprozess durchlaufen muessen. Gleichzeitig bleiben genug Validation, Statusklarheit und sichere Checkpoints erhalten, damit der Fortschritt nicht chaotisch wird.

## TARGET SURFACE
- Primary Surface: interner Dev-/OR-/Workhorse-Arbeitsmodus
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: interne Dev-Governance fuer bounded OR-/Workhorse-Infrastrukturarbeit, schlankere Prozessregeln fuer kleine und mittlere Dev-Slices, definierte Pflicht-Evidenz und definierte Rueckfall-Gates in den strengen Modus
- Explicit Non-Surfaces: Janus-Produktarbeit, Produktfeatures, Release-Flow, Security-/Privacy-Eskalationen, allgemeine Aufweichung der Diamond-Pipeline fuer Janus selbst

## USER ACTION SURFACE
- Entry Action: Ein interner Dev-Slice wird als bounded Dev-/OR-/Workhorse-Arbeit erkannt.
- Required Inputs: klare Scope-Zuordnung als Dev-Arbeit statt Janus-Produktarbeit
- Success Feedback: Der Slice darf im Lean-Flow laufen und verlangt nur die festgelegten Minimalpflichten statt der vollen Pipeline.
- Failure Feedback: Wenn eine Eskalationsbedingung greift, endet der Lean-Flow und der Schritt wird wieder in den strengen Modus geroutet.
- Cancel / Undo Behavior: Wenn die Scope-Zuordnung nicht sauber ist oder spaeter driftet, wird der Lean-Flow beendet und die Arbeit wird nicht stillschweigend weiter im schlanken Modus behandelt.

## SYSTEM BEHAVIOR

Interne Dev-/OR-/Workhorse-Infrastrukturarbeit darf kuenftig in einem schlankeren Governance-Modus laufen als Janus-Produktarbeit. Dieser Lean-Flow gilt fuer kleine und mittlere bounded Dev-Slices, solange sie keine Janus-Produktlogik veraendern und keine Hochrisiko-Grenzen beruehren.

Der Lean-Flow reduziert Prozess-Overhead, ersetzt aber nicht alle Sicherheitsleisten. Pflicht bleiben Validation, ein kompakter `CURRENT_STATE`-Nachweis und ein sauberer Git-Checkpoint bei sinnvollen Lieferbloecken.

Der Lean-Flow endet automatisch, sobald eine definierte Eskalationsbedingung erreicht wird. Dazu gehoeren Beruehrung von Janus-Produktlogik, Security/Privacy-Themen, Release- oder Git-Governance-Risiken, unklarer Scope oder neue produktive Freigaben.

Innerhalb des Lean-Flows sollen kleine und mittlere bounded Dev-Slices nicht jedes Mal den vollen Spec-, Audit- und Doku-Apparat der Janus-Produktpipeline ausloesen. Stattdessen gilt ein leichterer, aber weiterhin nachvollziehbarer Modus.

Diese Regel aendert nichts an der Janus-Produktpipeline selbst. Sobald echte Janus-Produktarbeit betroffen ist, bleibt oder wird automatisch wieder der strenge Modus aktiv.

## DATA / PERSISTENCE
- Stored Artifacts: kompakte Validation-Nachweise, `CURRENT_STATE`, passende Git-Checkpoints bei Lieferbloecken
- Persistence Scope: interne Dev-/OR-/Workhorse-Arbeitsdokumentation und Git-Nachvollziehbarkeit
- State Mutation: Nicht zutreffend: Die Regel aendert den Arbeitsmodus, nicht direkt Produktdaten oder Endnutzer-Persistenz.
- Data Lifecycle: Lean-Dev-Arbeit bleibt nachvollziehbar, aber mit weniger Pflichtartefakten als die volle Janus-Produktpipeline.

## CONSTRAINTS

- Janus-Produktarbeit bleibt vollstaendig im strengen Modus.
- Lean gilt nur fuer kleine und mittlere bounded Dev-Slices.
- Validation bleibt Pflicht.
- `CURRENT_STATE` bleibt Pflicht fuer substantielle Arbeitsbloecke.
- Ein sauberer Git-Checkpoint bleibt bei sinnvollen Lieferbloecken Pflicht.
- Lean endet automatisch bei Janus-Produktlogik, Security/Privacy, Release/Git-Governance, unklarem Scope oder neuer produktiver Freigabe.

## SECURITY / PRIVACY
- Trust Boundary: Der Lean-Flow lockert keine Security- oder Privacy-Grenzen.
- Local Authority Owner: Codex und der definierte Dev-Governance-Prozess bleiben Owner der Scope-Entscheidung.
- Sensitive Data Rule: Security- oder Privacy-relevante Dev-Arbeit darf nicht im Lean-Flow verbleiben.
- Write Safety Rule: Lean darf nie als Freifahrtschein fuer unkontrollierte oder schlecht nachvollziehbare Aenderungen dienen.
- Forbidden Actions: keine Aufweichung der Janus-Produktpipeline, keine Lean-Behandlung fuer Release- oder Security-kritische Arbeit, keine stillschweigende Scope-Verschiebung
- Auditability: Auch im Lean-Flow muessen Validation, Status und sinnvolle Checkpoints nachvollziehbar bleiben.

## EDGE CASES

- Wenn ein Slice als Dev-Arbeit startet, aber spaeter Janus-Produktlogik beruehrt, endet Lean sofort.
- Wenn der Scope nicht klar als Dev-Arbeit abgrenzbar ist, darf Lean nicht verwendet werden.
- Wenn ein neuer produktiver Consumer oder eine neue produktive Freigabe betroffen ist, endet Lean und es gilt wieder der strenge Modus.
- Wenn ein Slice klein beginnt, aber zu breit oder risikoreich wird, endet Lean automatisch.

## DEFINITION OF DONE

- [ ] Wenn ein bounded Dev-Slice keine Janus-Produktlogik und keine Hochrisiko-Grenze beruehrt, dann darf er in einem schlanken Dev-Flow laufen.
- [ ] Wenn ein Lean-Dev-Slice laeuft, dann bleiben Validation und `CURRENT_STATE` fuer substantielle Bloecke Pflicht.
- [ ] Wenn ein Lean-Dev-Slice einen sinnvollen Lieferblock erreicht, dann bleibt ein sauberer Git-Checkpoint Pflicht.
- [ ] Wenn Janus-Produktlogik, Security/Privacy, Release/Git-Governance, unklarer Scope oder neue produktive Freigabe betroffen sind, dann endet Lean automatisch.
- [ ] Wenn Lean endet, dann wird der Schritt wieder in den strengen Modus zurueckgefuehrt.
- [ ] Wenn Janus-Produktarbeit ausgefuehrt wird, dann bleibt die volle Janus-Pipeline unveraendert streng.

## TEST STRATEGY
- Primary Validation Mode: Governance- und Workflow-Validierung ueber klare Scope-Regeln, Pflichtnachweise und Eskalationsbedingungen
- Required Evidence: dokumentierte Lean-Regeln, dokumentierte Eskalationsbedingungen, Nachweis der Minimalpflichten
- Success Cases: bounded Dev-Slice bleibt lean; bounded Dev-Slice erreicht Validation plus `CURRENT_STATE` plus Git-Checkpoint; Dev-Slice eskaliert korrekt in den strengen Modus
- Failure Cases: unklarer Scope bleibt faelschlich lean; Janus-Produktlogik oder Security-Thema bleibt zu lange im Lean-Flow; fehlende Minimalpflichten trotz Lean-Freigabe
- Regression Focus: keine Aufweichung der Janus-Produktpipeline; keine stillschweigende Lean-Ausweitung auf Produkt-, Release- oder Security-Arbeit

## OUT OF SCOPE

Jede Aenderung an der strengen Janus-Produktpipeline selbst, neue Janus-Produktfeatures, Release-Protokolle, Security-Ausnahmeprozesse, globale Abschaffung von Specs oder Audits und jede ungebundene Beschleunigung ohne klare Sicherheitsleine.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 47
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-21
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 9/20
- Architectural Risk: 8/20
- State / Persistence Complexity: 6/20
- Cross-System Dependencies: 11/20
- Ambiguity Level: 13/20
- Total Complexity Score: 47/100
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
