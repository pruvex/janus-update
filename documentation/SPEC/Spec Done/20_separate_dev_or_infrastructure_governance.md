# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.4
recommended_reasoning: medium
new_chat: no
complexity_score: 52
confidence: HIGH
dashboard_hint: CAUTION
reason: Governance spec creates a new non-product work lane with migration rules and source-of-truth boundaries across Janus and Dev systems.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 52
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-06-19
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## FEATURE IDENTITY

- Feature Name: Strikte Trennung von Janus-Produktarbeit und Dev- OR-Infrastruktur-Governance
- Primary Goal: Janus-Produktarbeit dauerhaft von Dev-, OR-, Runner-, Tooling- und Umgebungsarbeit trennen und dafuer ein eigenes Steuerungs- und Dokumentationssystem festlegen.
- User Problem: Das aktuelle Janus-System vermischt Produktarbeit mit Dev- und OR-Infrastrukturthemen, wodurch Priorisierung, Pflege, Verantwortungsgrenzen und Source-of-Truth unscharf werden.
- Routing Decision: 5.4
- Routing Reasoning: medium
- Routing Confidence: HIGH
- Dashboard Hint: CAUTION

## USER VALUE

Der Nutzer bekommt ein klares Janus-Produktbacklog ohne Dev-Rauschen und kann Infrastrukturarbeit trotzdem strukturiert planen, nachverfolgen und spaeter sauber testen.

Die Trennung senkt das Risiko von Mischpriorisierung, doppelter Pflege und unklarer Verantwortung zwischen Produktworkflow und OR- beziehungsweise Tooling-Ausbau.

## TARGET SURFACE

- Primary Target Surface: Arbeitsorganisation und Dokumentationsstruktur fuer Janus-Produktarbeit versus Dev- OR-Infrastruktur
- Existing or New Surface: New Surface
- Existence Confirmation: confirmed by user
- Included Surfaces: Janus-Backlog-Grenze, eigener Top-Level-Dev-Bereich, eigenes Dev-Backlog, Migrationsregel fuer bestehende Dev- OR-Themen, schlanke Janus-Verweise auf Dev-Abhaengigkeiten
- Excluded Surfaces: konkrete Implementierung einzelner OR-Runner, Behebung laufender Backend-Umgebungsfehler, Produktfeature-Implementierungen, Git- oder Release-Ausfuehrung

## USER ACTION SURFACE

- User Trigger: Der Nutzer will, dass Dev-Arbeiten nicht mehr im Janus-Backlog und nicht mehr in der Janus-Produktdoku gefuehrt werden.
- Action Type: Codex etabliert fuer kuenftige und bestehende Dev- OR-Themen ein getrenntes Steuerungssystem und laesst Janus produktorientiert.
- Feedback: Janus zeigt kuenftig nur noch produktbezogene Backlog- und Statuseintraege; Dev- OR-Arbeit wird in einem separaten Bereich mit eigener Doku und eigenem Backlog sichtbar.
- Confirmation Behavior: Wenn ein Janus-Produktthema von Dev- OR-Infrastruktur abhaengt, bleibt im Janus-System nur ein kurzer Verweis auf den Dev-Source-of-Truth bestehen.
- Cancel / Undo Behavior: Wenn eine Aufgabe doch echte Produktarbeit ist, bleibt sie vollstaendig im Janus-System und wird nicht in das Dev-System verschoben.

## SYSTEM BEHAVIOR

Wenn eine Aufgabe Produktverhalten, Nutzeroberflaechen, Persistenzverhalten, Nutzerfeedback oder Release-Auswirkungen von Janus betrifft, bleibt sie im Janus-Backlog und in der Janus-Dokumentation.

Wenn eine Aufgabe primaer Dev-Umgebung, OR-Tooling, Runner, Modellrouting-Infrastruktur, Operator-Hilfen, Test-Harness, Healthcheck-Tooling oder andere nicht-produktseitige Arbeitsorganisation betrifft, wird sie kuenftig im separaten Dev-System gefuehrt.

Wenn bereits bestehende Janus-Backlog-Eintraege eigentlich Dev- oder OR-Infrastrukturthemen sind, werden sie aktiv aus dem Janus-System in das neue Dev-System ueberfuehrt, statt nur historisch liegen zu bleiben.

Wenn ein Janus-Produktthema von einer Dev- oder OR-Infrastrukturabhaengigkeit blockiert oder beeinflusst wird, behaelt Janus nur den produktbezogenen Kontext und verweist fuer die Infrastruktur auf das Dev-System als Source of Truth.

Wenn eine Aufgabe sowohl Produkt- als auch Dev-Anteile hat, muessen Produktverhalten und Infrastrukturarbeit als getrennte Steuerungseinheiten sichtbar bleiben und duerfen nicht in einem einzigen gemischten Eintrag verschmelzen.

Wenn die neue Trennung aktiv ist, wird Janus nicht zum Sammelort fuer lokale Umgebungsarbeit, OR-Experimentlogik oder allgemeine Tooling-Steuerung.

## DATA / PERSISTENCE

- Created Data: Ein eigener Top-Level-Dev-Bereich mit Dev-Dokumentation, Dev-Backlog und zugehoerigen Governance-Artefakten
- Updated Data: Janus-Zustands- und Backlog-Artefakte koennen schlanke Verweise oder bereinigte Produkttexte erhalten, wenn Dev- OR-Themen migriert werden
- Deleted Data: Nicht zutreffend: Historische Evidenz muss nicht regulaer geloescht werden, sondern kann kontrolliert umgezogen oder referenziert werden
- Remembered Data: Dev- OR-Entscheidungen, laufende Infrastrukturarbeit und Migrationsstatus werden kuenftig im Dev-System fortgeschrieben
- Canonical Source Of Truth: Janus bleibt Source of Truth fuer Produktarbeit; das neue Dev-System wird Source of Truth fuer Dev- OR-Infrastrukturarbeit
- Failure Persistence: Unvollstaendige oder blockierte Dev- OR-Arbeit bleibt im Dev-System sichtbar und wird nicht als Produktstatus im Janus-System fortgeschrieben

## CONSTRAINTS

Die Trennung darf Janus-Produktarbeit nicht schlechter auffindbar machen.

Das Janus-Backlog darf kuenftig keine primaer infrastrukturellen Dev- oder OR-Themen mehr als normale Produktarbeit fuehren.

Das Dev-System muss ausserhalb von `documentation/` als eigener Top-Level-Bereich liegen.

Bestehende gemischte Dev- OR-Themen muessen aktiv migrierbar sein und duerfen nicht dauerhaft als Mischbestand bestehen bleiben.

Janus und Dev-System duerfen fuer dasselbe Infrastrukturthema keine konkurrierenden Detailbeschreibungen pflegen.

Die Trennung darf nicht als Vorwand genutzt werden, echte Produktentscheidungen unsichtbar aus dem Janus-System herauszunehmen.

## SECURITY / PRIVACY

- Sensitive Data Handling: Weder Janus noch das Dev-System duerfen Secrets, API-Keys, lokale Zugangsdaten oder private Maschineninformationen als normale Governance-Dokumentation persistieren.
- Boundary Protection: Die neue Trennung ist eine Governance-Grenze und verhindert, dass lokale Tooling-, OR- oder Umgebungsarbeit stillschweigend als Produktarbeit behandelt wird.
- Source Of Truth Risk: Doppelte Pflege zwischen Janus und Dev-System ist unzulaessig, weil sie zu widerspruechlichen Prioritaeten und falschen Arbeitsanweisungen fuehren kann.
- Migration Safety: Historische Dev- OR-Themen muessen so migriert werden, dass ihr Kontext erhalten bleibt, ohne neue irrefuehrende Produkt-Claims im Janus-System zu hinterlassen.
- Forbidden Authority: Das Dev-System darf keine stillschweigende Produktions-, Release- oder Produkt-Governance-Autoritaet fuer Janus beanspruchen.
- Transparency: Fuer abhaengige Janus-Produktthemen muss sichtbar bleiben, dass die Infrastrukturdetails im Dev-System liegen und Janus nur den Produktkontext fuehrt.

## EDGE CASES

Wenn ein Thema zunaechst wie Dev-Tooling aussieht, aber spaeter klares Nutzerverhalten von Janus aendert, muss der Produktanteil im Janus-System separat sichtbar werden.

Wenn ein historischer Janus-Eintrag sowohl Produkt- als auch Infrastrukturanteile enthaelt, darf die Migration den Produktkontext nicht verlieren.

Wenn ein laufender Produktblock technisch durch Dev-Umgebung oder OR-Infrastruktur blockiert ist, bleibt der Produktblock im Janus-System offen, waehrend die technische Ursache im Dev-System verwaltet wird.

Wenn eine Aufgabe nur ein lokaler Maschinen- oder Werkzeugzustand ist und kein Janus-Produktverhalten betrifft, gehoert sie nicht in das Janus-Backlog.

Wenn eine Dev- OR-Arbeit spaeter formale Janus-Auswirkungen bekommt, darf Janus nur den relevanten Produkt- oder Governance-Ausschnitt spiegeln und nicht die gesamte technische Tiefendoku duplizieren.

## DEFINITION OF DONE

- [ ] Wenn eine Aufgabe primaer Janus-Produktverhalten betrifft, dann bleibt sie vollstaendig im Janus-System sichtbar und wird nicht in das Dev-System verschoben.
- [ ] Wenn eine Aufgabe primaer Dev- oder OR-Infrastruktur betrifft, dann wird sie in einem getrennten Dev-System ausserhalb von `documentation/` gefuehrt.
- [ ] Wenn ein bestehender Janus-Backlog-Eintrag eigentlich Dev- oder OR-Infrastruktur ist, dann kann er kontrolliert in das Dev-System migriert werden.
- [ ] Wenn ein Janus-Produktthema von Dev- oder OR-Infrastruktur abhaengt, dann bleibt im Janus-System nur ein schlanker Verweis auf das Dev-System statt doppelter Detailpflege.
- [ ] Wenn die Trennung aktiv ist, dann enthaelt das Janus-Backlog keine neuen primaer infrastrukturellen Dev- oder OR-Themen mehr als normale Produktarbeit.
- [ ] Wenn Janus und Dev-System dasselbe Infrastrukturthema beruehren, dann gibt es genau ein kanonisches Detailsystem und keine konkurrierenden Parallelbeschreibungen.

## TEST STRATEGY

- Unit Tests: Nicht zutreffend: Dies ist eine Governance- und Dokumentationsspec ohne produktseitige Logikfunktion
- Integration Tests: Struktur- und Artefaktpruefung fuer getrennte Janus- und Dev-Source-of-Truth-Pfade nach Einfuehrung
- Negative Tests: neue Dev- OR-Themen erscheinen faelschlich im Janus-Backlog, doppelte Detailpflege in Janus und Dev-System, Produktthemen werden unzulaessig in das Dev-System ausgelagert
- Manual Test: Ein echter Janus-Produktwunsch und ein echter Dev- OR-Infrastrukturwunsch werden nach Einfuehrung bewusst in unterschiedliche Systeme einsortiert und bleiben dort nachvollziehbar
- Regression Tests: Bestehende Janus-Produktpipelines bleiben unveraendert nutzbar, waehrend das Dev-System nur Infrastruktur- und Werkzeugarbeit uebernimmt

## OUT OF SCOPE

Die sofortige technische Implementierung des neuen Dev-Bereichs in diesem Spec-Schritt.

Die Behebung des aktuellen Backend-Umgebungsblockers oder anderer laufender Runtime-Probleme.

Ein OR-Modellentscheid, Routing-Experiment oder produktive Aktivierung von OpenRouter-Pfaden.

Die Ausarbeitung einzelner Dev-Backlog-Items, Runner-Features oder Operator-Flows.

Git-Commits, Pushes, Releases oder Umstrukturierungen ausserhalb der hier beschriebenen Governance- und Source-of-Truth-Grenzen.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 10
- Architectural Risk: 11
- State / Persistence Complexity: 9
- Cross-System Dependencies: 12
- Ambiguity Level: 10
- Total Complexity Score: 52

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-06-19
- **Audit Package:** `documentation/tasks/TASK-SPEC20.1_AUDIT_PACKAGE.md`
- **Final Audit Report:** `documentation/tasks/TASK-SPEC20.1_final_audit.md`
- **Validation Evidence:** `git diff --check -- development/README.md development/DEV_STATE.md development/DEV_BACKLOG.md documentation/tasks/TASK-SPEC20.1_AUDIT_PACKAGE.md documentation/tasks/TASK-SPEC20.1_execution_result.md`: PASS; `rg -n "Source of Truth|Source Of Truth|product|authority|Dev- and OR-infrastructure" development`: PASS; `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC20.1_execution_result.md`: PASS
