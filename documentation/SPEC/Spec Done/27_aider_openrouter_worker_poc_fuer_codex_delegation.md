# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 42
confidence: HIGH
dashboard_hint: CAUTION
reason: A bounded internal worker POC changes Janus delegation workflow and governance, but stays timeboxed and non-production.

## FEATURE IDENTITY
- Feature Name: Aider/OpenRouter Worker POC fuer Codex-Delegation
- Feature Type: Interner Dev-Workflow-POC
- Primary Goal: Pruefen, ob ein einfacher Aider-basierter OpenRouter-Worker kleine Janus-Arbeiten guenstiger und robuster ausfuehren kann als der bisherige selbstgebaute OR-Agent-Ansatz.
- Trigger Source: Der Nutzer will die bestehende OR-Integrationsrichtung kritisch vereinfachen und einen klar begrenzten Proof of Concept statt eines neuen Agentenprojekts.
- Primary Persona: Janus-Operator, der Codex als planende und pruefende Instanz nutzt und einen guenstigen bounded Worker fuer kleine Aufgaben evaluieren will.

## USER VALUE

Der POC soll schnell und realistisch beantworten, ob Janus fuer kleine bis mittlere, klar begrenzte Aufgaben von einem einfachen Worker-Modell profitiert, ohne erneut viel Zeit in eigene Agenten-Infrastruktur zu investieren. Das Ergebnis soll eine belastbare Go/No-Go-Entscheidung fuer die naechste Vereinfachungsstufe liefern.

## TARGET SURFACE
- Primary Surface: interner Codex/Janus-Dev-Workflow
- Existing Surface: Ja
- Existence Confirmation: confirmed by user
- In-Scope Surfaces: manuell gestarteter bounded Worker-POC fuer eine harmlose Doku- oder Unit-Test-Aufgabe innerhalb eines engen erlaubten Dateibereichs
- Explicit Non-Surfaces: Janus-Produktoberflaechen, Endnutzer-Features, globale OR-Migration, OpenHands-Rollout, Roo-Code-Workflow, automatischer Git- oder Release-Pfad, produktive allgemeine Worker-Freigabe

## USER ACTION SURFACE
- Entry Action: Codex bereitet eine kleine erlaubte Aufgabe fuer den Worker vor und startet den POC manuell mit Aider und OpenRouter.
- Required Inputs: klar begrenzte Aufgabe, explizit erlaubter Dateibereich, OpenRouter-Zugang, definierte Erfolgskriterien, definierter Test- oder Check-Ausgang
- Success Feedback: der Worker liefert einen nachvollziehbaren Diff, einen kurzen Report, Test- oder Check-Ausgabe und bleibt innerhalb des erlaubten Scopes ohne Commit oder Push
- Failure Feedback: Scope-Drift, unbrauchbarer Diff, fehlende Governance-Einhaltung, nicht verwertbarer Report oder schwache Ergebnisqualitaet fuehren zu einem klaren No-Go fuer eine weitere Produktisierung
- Cancel / Undo Behavior: der POC kann nach einem einzelnen Lauf beendet werden; ohne produktive Git-Aktionen bleibt der Zustand lokal pruefbar und verwerfbar

## SYSTEM BEHAVIOR

Der POC fuehrt keinen neuen autonomen Janus-Agenten ein. Stattdessen wird ein vorhandener externer Worker bewusst eng und manuell eingesetzt, waehrend Codex weiterhin die planende, begrenzende und pruefende Instanz bleibt.

Der Worker darf ausschliesslich fuer eine harmlose Doku- oder Unit-Test-Aufgabe eingesetzt werden. Ziel ist nicht, Janus-Produktlogik im ersten Schritt zu automatisieren, sondern den Worker-Mechanismus selbst unter realistischen, aber risikoarmen Bedingungen zu bewerten.

Der Worker soll nur auf einen klar benannten erlaubten Dateibereich losgelassen werden. Der Lauf gilt nur dann als positiv, wenn das Ergebnis fachlich brauchbar ist und die Begrenzung praktisch eingehalten wird.

Der POC bleibt bewusst manuell. Es wird noch kein eigener `janus-worker`-Wrapper vorausgesetzt. Stattdessen soll zuerst geprueft werden, ob Aider in der einfachsten Form ueberhaupt sauber genug fuer den Janus-Kontext arbeitet.

Codex bleibt waehrend des gesamten Ablaufs Owner fuer Auftragsformulierung, Scope, Validierung, Review und Ergebnisbewertung. Der Worker ist nur der ausfuehrende Handwerker innerhalb enger Grenzen.

Ein rein technischer Start ohne brauchbare Ergebnisqualitaet reicht nicht aus. Der POC gilt nur dann als erfolgreich, wenn das Resultat gut genug ist, dass ein kleiner echter Janus-Task kuenftig plausibel an denselben Worker delegiert werden koennte.

Der POC ist timeboxed. Wenn der erste enge Lauf bereits zeigt, dass Scope-Disziplin, Ergebnisqualitaet oder Governance nicht sauber genug sind, endet der Versuch ohne weitere Produktisierung.

## DATA / PERSISTENCE
- Stored Artifacts: lokale POC-Artefakte wie Worker-Prompt oder Task-Beschreibung, Diff, kurzer Bewertungsreport und Test- oder Check-Ausgabe
- Persistence Scope: lokale Dev- und Bewertungsartefakte innerhalb des bestehenden Janus/Codex-Arbeitskontexts
- State Mutation: Nicht zutreffend: Der POC fuehrt keine neue Produktpersistenz oder Endnutzerdatenverarbeitung ein
- Data Lifecycle: Die POC-Artefakte bleiben nur so lange erhalten, wie sie fuer lokale Bewertung, Spec-Review und eine spaetere Go/No-Go-Entscheidung gebraucht werden

## CONSTRAINTS

- Der POC bleibt auf genau einen kleinen bounded Lauf begrenzt.
- Der erste Lauf darf nur eine harmlose Doku- oder Unit-Test-Aufgabe betreffen.
- Es wird kein eigener Worker-Wrapper im ersten Schritt vorausgesetzt.
- Der Worker darf keine Commit-, Push-, Release- oder sonstigen Git-Governance-Aktionen ausfuehren.
- Ein Ergebnis ausserhalb des erlaubten Dateibereichs gilt als Negativsignal fuer die Bewertung.
- Ein rein technischer "laeuft irgendwie"-Nachweis reicht nicht als Erfolg aus.
- Der POC soll schnell ausgewertet werden koennen und darf nicht selbst wieder zu einem langwierigen Infrastrukturprojekt werden.

## SECURITY / PRIVACY
- Trust Boundary: Der Worker bleibt ein externer bounded Ausfuehrungspfad ohne Autoritaet fuer Routing, Governance, Audit, Git oder finalen Abschluss
- Local Authority Owner: Codex bleibt Owner fuer Scope, Review, Validierung, Annahme oder Ablehnung und dokumentierte Entscheidung
- Sensitive Data Rule: An den Worker darf nur der fuer die kleine bounded Aufgabe notwendige Kontext gegeben werden
- Write Safety Rule: Der Worker darf nur innerhalb des explizit erlaubten Dateibereichs aendern und keine breiten Repo-Aktionen erhalten
- Forbidden Actions: kein Commit, kein Push, kein Release, keine allgemeine Repo-Autoritaet, keine Ausweitung auf Produktlogik im ersten POC, keine implizite produktive Freigabe
- Auditability: Diff, Report und Test- oder Check-Ausgabe muessen lokal nachvollziehbar und durch Codex bewertbar bleiben

## EDGE CASES

- Wenn Aider lokal noch nicht verfuegbar ist, darf der POC nicht als fachlicher Erfolg gewertet werden, sondern nur als vorbereitungsbeduerftig.
- Wenn OpenRouter-Zugang oder Modellkonfiguration fehlen, bleibt der POC blockiert statt mit unscharfen Ersatzpfaden zu verwischen.
- Wenn der Worker zusaetzliche Dateien ausserhalb des erlaubten Bereichs aendert, gilt der Lauf als negatives Governance-Signal.
- Wenn das Ergebnis technisch erfolgreich, aber fachlich schwach ist, gilt der POC nicht als praktischer Erfolg.
- Wenn der aktuelle Worktree zu verrauscht ist, muss der Lauf auf einen besonders kleinen und klaren Dateibereich begrenzt werden, damit die Auswertung nicht verfremdet wird.

## DEFINITION OF DONE

- [ ] Wenn der POC gestartet wird, dann bearbeitet der Worker beobachtbar nur die explizit freigegebene harmlose Doku- oder Unit-Test-Aufgabe.
- [ ] Wenn der Worker Aenderungen erzeugt, dann bleiben diese beobachtbar innerhalb des erlaubten Dateibereichs.
- [ ] Wenn der Lauf endet, dann liegen beobachtbar ein verwertbarer Diff, ein kurzer Report und eine Test- oder Check-Ausgabe fuer die Bewertung vor.
- [ ] Wenn der Worker-Lauf abgeschlossen wird, dann sind beobachtbar kein Commit, kein Push und keine sonstige Git-Governance-Aktion erfolgt.
- [ ] Wenn das Ergebnis fachlich und organisatorisch brauchbar ist, dann ist beobachtbar eine belastbare Go/No-Go-Einschaetzung moeglich, ob kleine echte Janus-Tasks kuenftig plausibel ueber denselben Worker delegiert werden koennen.
- [ ] Wenn Scope-Disziplin oder Ergebnisqualitaet nicht ausreichen, dann endet der POC beobachtbar ohne implizite Produktisierung als No-Go oder Rework-Signal.

## TEST STRATEGY
- Primary Validation Mode: ein einzelner lokaler bounded POC-Lauf mit anschliessender Codex-Review der Aenderungen und der erzeugten Laufartefakte
- Required Evidence: klarer erlaubter Dateibereich, Worker-Ausgang, Diff, kurzer Report, Test- oder Check-Ausgabe, dokumentierte Go/No-Go-Bewertung
- Success Cases: der Worker bleibt im Scope, liefert brauchbare Aenderungen fuer die harmlose Aufgabe, erzeugt verwertbare Artefakte und zeigt genug Qualitaet fuer kleine spaetere Janus-Tasks
- Failure Cases: Aider fehlt oder ist nicht konfigurierbar; OpenRouter-Zugang fehlt; Scope-Drift; unbrauchbare oder schwache Aenderungen; fehlende Artefakte; Git-Governance-Verletzung
- Regression Focus: kein stiller Rueckfall in einen grossen Eigenbau-Agenten, keine unbemerkte Scope-Ausweitung, keine implizite produktive Freigabe aus einem einmaligen Testlauf

## OUT OF SCOPE

Ein vollwertiger eigener Coding-Agent, ein allgemeiner produktiver `janus-worker`, Migration der gesamten bestehenden OR-Infrastruktur, OpenHands als erster Standardpfad, Roo Code als delegierter Subagent, automatische Git-Aktionen, produktive Janus-Feature-Implementierungen im ersten POC und jede nicht timeboxed Ausbauphase.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 42
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-30
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-06-30
- **Validation Evidence:** `documentation/tasks/TASK-SPEC27.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-SPEC27.1_execution_result.md`, `development/openrouter-skill-tests/janus-worker-aider-poc/worker_report.md`
- **Implementation Note:** The bounded docs-only worker POC completed successfully and produced a conditional go for a future isolated worker experiment. Direct repo-root execution remains explicitly not approved for casual reuse.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 7
- Architectural Risk: 10
- State / Persistence Complexity: 4
- Cross-System Dependencies: 12
- Ambiguity Level: 9
- Total Complexity Score: 42
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION
