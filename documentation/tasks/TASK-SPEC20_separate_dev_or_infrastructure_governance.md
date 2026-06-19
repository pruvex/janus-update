TASK-SPEC20
- Source Spec: documentation/SPEC/20_separate_dev_or_infrastructure_governance.md
- Backlog Item: N/A
- Feature: Strikte Trennung von Janus-Produktarbeit und Dev- OR-Infrastruktur-Governance
- Generated At: 2026-06-19

## Generated Tasks

### TASK-SPEC20.1 Establish separate top-level Dev governance home
- Ziel: Einen eigenstaendigen Top-Level-Bereich fuer Dev- und OR-Infrastrukturarbeit schaffen, der kuenftig als kanonische Source of Truth ausserhalb der Janus-Produktdoku dient.
- Scope: Neue Dev-Top-Level-Struktur, kanonische Einstiegsdoku, laufender Dev-Status und eigenstaendiges Dev-Backlog ohne Vermischung mit Janus-Produktdokumentation.
- Files:
  - development/README.md
  - development/DEV_STATE.md
  - development/DEV_BACKLOG.md
- Steps:
  - Einen neuen Top-Level-Bereich `development/` als kanonisches Zuhause fuer Dev- und OR-Infrastrukturarbeit anlegen.
  - Eine klare Einstiegsdoku schreiben, die Scope, Source-of-Truth-Regeln und Nicht-Zustaendigkeiten gegenueber Janus festhaelt.
  - Einen laufenden `DEV_STATE`-Snapshot fuer aktive Infrastrukturarbeit definieren.
  - Ein eigenstaendiges `DEV_BACKLOG` mit klaren Statusregeln fuer Dev- und OR-Themen anlegen.
- Acceptance Criteria:
  - Der neue Dev-Bereich liegt ausserhalb von `documentation/`.
  - `development/README.md` beschreibt klar die Trennlinie zwischen Janus-Produktarbeit und Dev- OR-Infrastrukturarbeit.
  - `development/DEV_STATE.md` und `development/DEV_BACKLOG.md` existieren als kanonische Startartefakte.
  - Die neue Struktur beansprucht keine Produkt- oder Release-Autoritaet fuer Janus.
- Tests:
  - Sichtpruefung der neuen Top-Level-Struktur
  - `git diff --check` fuer alle neu angelegten Dev-Artefakte
  - Konsistenzpruefung der Source-of-Truth-Regeln zwischen README, DEV_STATE und DEV_BACKLOG
- Model: 5.4
- Reason: Dies ist ein klar begrenzter Dokumentations- und Governance-Slice mit mehreren eng gekoppelten Artefakten, aber ohne Architektur- oder Produktimplementierung.

### TASK-SPEC20.2 Migrate mixed Dev-OR backlog topics out of Janus backlog
- Ziel: Bereits vermischte Dev- und OR-Infrastrukturthemen aktiv aus dem Janus-Backlog in das neue Dev-System ueberfuehren, ohne Produktkontext zu verlieren.
- Scope: Identifikation und Migration rein infrastruktureller Backlog-Themen, Migrationsprotokoll, Bereinigung der Janus-Backlog-Texte und schlanke Restverweise statt Doppelpflege.
- Files:
  - documentation/backlog/BACKLOG.md
  - development/DEV_BACKLOG.md
  - development/migrations/janus_dev_or_backlog_migration_2026-06-19.md
- Steps:
  - Den bestehenden Mischbestand im Janus-Backlog auf primaer infrastrukturelle Dev- und OR-Themen sichten.
  - Solche Themen in das neue `DEV_BACKLOG` ueberfuehren und im Migrationsprotokoll nachvollziehbar festhalten.
  - Im Janus-Backlog nur dort schlanke Restverweise belassen, wo Produktkontext oder laufende Produktabhaengigkeiten sichtbar bleiben muessen.
  - Verhindern, dass Janus- und Dev-System nach der Migration konkurrierende Detailbeschreibungen desselben Infrastrukturthemas behalten.
- Acceptance Criteria:
  - Primaer infrastrukturelle Dev- oder OR-Themen sind nicht mehr als normale Produktarbeit im Janus-Backlog gefuehrt.
  - Das `DEV_BACKLOG` enthaelt die migrierten Themen nachvollziehbar.
  - Das Migrationsprotokoll dokumentiert, was umgezogen wurde und welche Janus-Restverweise bestehen bleiben.
  - Produktrelevante Janus-Eintraege verlieren durch die Migration ihren Produktkontext nicht.
- Tests:
  - Backlog-Diff-Pruefung fuer entfernte oder bereinigte Dev- OR-Mischthemen
  - Konsistenzpruefung zwischen `documentation/backlog/BACKLOG.md`, `development/DEV_BACKLOG.md` und dem Migrationsprotokoll
  - `git diff --check` fuer die Migrationsartefakte
- Model: 5.4
- Reason: Dieser Slice ist inhaltlich heikel, aber noch rein dokumentarisch; er braucht sorgfaeltige, nachvollziehbare Migration statt breite Implementierungslogik.

### TASK-SPEC20.3 Harden Janus governance docs to enforce the separation rule
- Ziel: Die aktiven Janus-Governance-Dateien so nachziehen, dass neue Dev- und OR-Infrastrukturthemen kuenftig nicht wieder in Janus-Produktworkflow und Janus-Doku zurueckrutschen.
- Scope: Janus-Arbeitsregeln, Workflow-Playbook und CURRENT_STATE-Verweislogik auf die neue Trennung abstimmen, ohne die neue Dev-Doku zu duplizieren.
- Files:
  - AGENTS.md
  - documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md
  - documentation/ai/CURRENT_STATE.md
- Steps:
  - `AGENTS.md` um eine klare Regel ergaenzen, dass primaer infrastrukturelle Dev- und OR-Themen nicht ins Janus-Backlog oder in die Janus-Produktdoku gehoeren.
  - Das Workflow-Playbook so aktualisieren, dass Routing zwischen Janus-Produktarbeit und Dev-System fuer kuenftige Sessions eindeutig bleibt.
  - `CURRENT_STATE` nur noch als schlanken Verweisort fuer produktrelevante Dev-Abhaengigkeiten beschreiben und nicht als Dev-Source-of-Truth.
  - Sicherstellen, dass die Janus-Governance-Dateien auf das Dev-System verweisen, ohne dessen Inhalte parallel zu spiegeln.
- Acceptance Criteria:
  - `AGENTS.md` und das Workflow-Playbook erzwingen die neue Trennlinie explizit.
  - `CURRENT_STATE` bleibt ein Janus-Sync-Artefakt und wird nicht zur Dev-Tiefendoku erweitert.
  - Die Janus-Governance-Dokumente verweisen auf das Dev-System, ohne konkurrierende Detailregeln zu erzeugen.
  - Neue Dev- oder OR-Infrastrukturthemen koennen kuenftig nicht mehr plausibel als normale Janus-Produktarbeit geroutet werden.
- Tests:
  - Gezielter Text- und Diff-Check auf Trennregel und Verweislogik
  - `rg`-Pruefung auf klare Dev-System-Referenzen in den Janus-Governance-Dateien
  - `git diff --check` fuer die geaenderten Janus-Governance-Dateien
- Model: 5.4
- Reason: Dieser Slice haertet die dauerhafte Prozessgrenze zwischen Janus und Dev-System und ist damit governance-relevant, aber noch gut bounded.
