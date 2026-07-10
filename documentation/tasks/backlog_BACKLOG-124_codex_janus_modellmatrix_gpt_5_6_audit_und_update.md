# BACKLOG-124 Task

- **Backlog Item:** BACKLOG-124 - Codex-/Janus-Modellmatrix auf neue lokale GPT-5.6-Modelle auditieren und gezielt aktualisieren
- **Status:** DONE
- **Erstellt:** 2026-07-10
- **Aktualisiert:** 2026-07-10
- **Abgeschlossen:** 2026-07-10
- **Kurzbeschreibung:** Die bestehende Janus-Modellmatrix und die dazugehoerigen Governance-/Skill-Empfehlungen sollen gegen die drei neu sichtbaren lokalen `GPT-5.6`-Modelle geprueft werden, damit die Repo-Wahrheit nicht hinter der realen Codex-Umgebung herlaeuft und zugleich keine vorschnelle blinde Migration entsteht.
- **Ziel:** Einen bounded Lean-Dev-Audit liefern, der die neuen lokalen `GPT-5.6`-Modelle gegen die bestehenden Rollen `5.4`, `5.4 mini`, `5.5` und `5.2` bewertet und danach entweder eine konsistente gezielte Matrix-Aktualisierung oder eine bewusst begruendete Beibehaltung der aktuellen Matrix festschreibt.
- **Scope:** Repo-gebundene Modellmatrix-, Governance- und Skill-Empfehlungstexte fuer Codex/Janus, inklusive Erfassung der real verfuegbaren lokalen `GPT-5.6`-Modelle und ihrer sinnvollen Rollen. Keine Janus-Produktlogik, kein Release-/Publish-Schritt, keine blinde globale Umstellung aller Skills ohne Evidenz und keine nicht gebundene Vollrepo-Migration.
- **Files:**
  - `AGENTS.md`
  - `documentation/codex/CODEX_PROJECT_PROFILE.md`
  - `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
  - `documentation/codex/CODEX_MODEL_MIGRATION_2026-06-02.md`
  - `documentation/backlog/BACKLOG.md`
  - `documentation/ai/CURRENT_STATE.md`
  - `documentation/codex/SKILL_USAGE_LOG.md`
- **Steps:**
  - Die drei in Codex sichtbaren lokalen `GPT-5.6`-Modelle mit exakten Namen und verfuegbaren Reasoning-/Intelligenzstufen als Repo-Evidenz erfassen.
  - Die aktuelle gebundene Matrix in `AGENTS.md`, `CODEX_PROJECT_PROFILE.md`, `CODEX_WORKFLOW_PLAYBOOK.md` und der bisherigen Migrationsnotiz gegen diese neuen Modelle spiegeln.
  - Die Rollen getrennt bewerten: Workhorse, mechanisch/mini, Audit-/Risiko und einfache Status-/Kurztexte.
  - Entscheiden, ob die bestehende Matrix bewusst bestehen bleibt oder ob genau begrenzte Updates noetig sind; die Entscheidung danach konsistent in den bindenden Governance-Dateien dokumentieren.
  - Falls die Matrix geaendert wird, den Update-Scope klein halten und nur die betroffenen Governance-/Skill-Empfehlungsquellen anpassen, nicht ad hoc alle historischen Artefakte umschreiben.
- **Akzeptanzkriterien:**
  - [x] Es gibt einen gebundenen Audit, der die drei neuen lokalen `GPT-5.6`-Modelle gegen die aktuellen Rollen `5.4`, `5.4 mini`, `5.5` und `5.2` bewertet statt blind umzuschalten.
  - [x] Die Entscheidung behandelt mindestens Workhorse-, Mini-/mechanische, Audit-/Risiko- und einfache Status-Rollen getrennt.
  - [x] Die betroffenen Governance-/Routing-Dateien und aktiven Skill-Empfehlungen wurden konsistent auf die GPT-5.6-Matrix aktualisiert.
  - [x] Die Runtime-Grenze fuer Sol ist mit dem Terra-Fallback und einer konkreten Revisit-Regel dokumentiert.
  - [x] Der Slice blieb Lean-Dev ohne Janus-Produktlogik, Release-Status oder Git-/Publish-Schritt.
- **Fehlende Informationen:**
  - Keine fuer diesen abgeschlossenen Scope. Die Sol-Ausfuehrbarkeit bleibt bewusst pro Codex-Account-/Workspace-Run zur Laufzeit zu pruefen.
- **Betroffener Bereich:** Codex-Governance / Janus Skill-Routing / Modellmatrix / Cache-Strategie / Lean-Dev-Infrastruktur
- **Nachweise:** `documentation/backlog/BACKLOG.md`; `AGENTS.md`; `documentation/codex/CODEX_PROJECT_PROFILE.md`; `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`; `documentation/codex/CODEX_MODEL_MIGRATION_2026-06-02.md`; `documentation/ai/CURRENT_STATE.md`
- **Notizen:** Das ist bewusst ein bounded Audit-/Update-Slice nach abgeschlossenem Spec-31-Produktblock. Erst Evidenz, dann Matrixentscheidung; kein reflexhafter Austausch von `5.4`/`5.5` nur wegen neuer sichtbarer UI-Optionen.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-124
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-124_codex_janus_modellmatrix_gpt_5_6_audit_und_update.md
- Required Next Skill: SKILL 3
- Evidence Paths:
  - AGENTS.md
  - documentation/codex/CODEX_PROJECT_PROFILE.md
  - documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md
  - documentation/codex/CODEX_MODEL_MIGRATION_2026-06-02.md
- Dropped Context:
  - abgeschlossene Spec-31-Produktimplementierung ausser als Freigabekontext fuer den Zeitpunkt dieses Lean-Dev-Slices
  - allgemeine historische Modellwechsel, die nicht direkt die aktuelle `GPT-5.6`-Frage betreffen

@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-124
Task: documentation/tasks/backlog_BACKLOG-124_codex_janus_modellmatrix_gpt_5_6_audit_und_update.md
Backlog Item: BACKLOG-124

## Completion

- **Completed by task:** `documentation/tasks/BACKLOG-124_final_audit.md`
- **Completed at:** 2026-07-10
- **Final audit:** PASS
- **Documentation update:** `documentation/tasks/BACKLOG-124_documentation_update.md`
- **Validation evidence:** `validate_precheck.py` PASS; `validate_execution_result.py` PASS; `validate_final_audit.py` PASS; targeted hard-Sol and `5.4/low` start-gate scans PASS; scoped `git diff --check` PASS.
- **Completion note:** `5.6 Luna` is the mechanical/documentation default, `5.6 Terra` the workhorse and supported audit fallback, and `5.6 Sol` remains the high-risk audit escalation only when the current Codex execution can actually start it. Runtime rejection is recorded as `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` and falls back to `5.6 Terra/high`.
