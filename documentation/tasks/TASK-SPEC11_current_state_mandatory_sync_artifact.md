TASK-SPEC11
- Source Spec: `documentation/SPEC/11_current_state_mandatory_sync_artifact.md`
- Backlog Item: `N/A`
- Feature: CURRENT_STATE als verpflichtendes Janus-Sync-Artefakt
- Generated At: 2026-06-10

## Generated Tasks

### TASK-SPEC11.1 Introduce CURRENT_STATE artifact and bind it into Janus governance docs
- Ziel:
  - Fuehre `documentation/ai/CURRENT_STATE.md` als kompaktes Pflichtartefakt fuer substantielle Janus-Arbeitsbloecke ein und verankere die Regel in den zentralen Governance-Dokumenten.
- Scope:
  - Nur Workflow-/Governance-Dokumentation und das initiale CURRENT_STATE-Artefakt. Keine Git-Automatisierung, keine JSON-Erweiterung und keine Ausweitung auf jede Mini-Interaktion.
- Files:
  - `AGENTS.md`
  - `documentation/ai/CURRENT_STATE.md`
  - `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
  - weitere zentrale Janus-Governance-Dokumente nur falls fuer Konsistenz zwingend noetig
- Steps:
  1. Lege `documentation/ai/CURRENT_STATE.md` mit einem kompakten initialen Snapshot an, der nur die in der Spec erlaubten Kernfelder enthaelt.
  2. Ergaenze in `AGENTS.md` eine bindende CURRENT_STATE-Regel, die den Begriff "substantieller Janus-Arbeitsblock" deterministisch ueber geaenderte Dateien, ausgefuehrte Validierung, dokumentierte Blocker oder formale Next-Skill-Handoffs definiert.
  3. Stelle in den zentralen Governance-Regeln klar, dass CURRENT_STATE Pflicht fuer substantielle Arbeitsbloecke ist, aber Backlog, Spec, Test-, Audit- und Dashboard-Artefakte nicht ersetzt.
  4. Stelle klar, dass Commit und Push weiterhin nur ueber `janus-git-governance` und explizite User-Freigabe laufen.
  5. Verankere den Nicht-Push-Fall so, dass Abschluesse/Handoffs explizit sagen muessen, wenn ein Remote wie GitHub noch nicht den neuesten CURRENT_STATE enthaelt.
- Acceptance Criteria:
  - `documentation/ai/CURRENT_STATE.md` existiert mit den definierten Kernfeldern fuer Ziel, Phase, letzte Arbeit, geaenderte Dateien, Validierung, Risiken, naechste Schritte und Zeitstempel.
  - `AGENTS.md` enthaelt eine bindende CURRENT_STATE-Regel mit deterministischer Definition von "substantiell".
  - Zentrale Governance-Dokumentation stellt klar, dass CURRENT_STATE ein kompakter Rolling Snapshot ist und keine anderen Single Sources of Truth ersetzt.
  - Git-Governance bleibt unveraendert: kein automatischer Commit/Push ohne bestehendes Gate.
  - Der Nicht-Push-Fall verlangt einen expliziten Hinweis, dass ein Remote-Stand eventuell noch nicht aktuell ist.
- Tests:
  - `rg -n "CURRENT_STATE|substantiell|substantial|GitHub.*aktuell|janus-git-governance" AGENTS.md documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md documentation/ai/CURRENT_STATE.md`
  - Manuelle Sichtpruefung, dass `documentation/ai/CURRENT_STATE.md` kurz bleibt und keine Tagebuchstruktur oder Secret-Beispiele enthaelt.
- Model: 5.4
- Reason:
  - Bounded governance/documentation implementation with cross-file consistency requirements but no architecture or code risk.

### TASK-SPEC11.2 Update Janus skills to require CURRENT_STATE on substantial completion
- Ziel:
  - Richte die relevanten Janus-Skills so aus, dass CURRENT_STATE vor Abschluss substantielle Arbeitsbloecke konsistent eingefordert wird.
- Scope:
  - Nur die in der Spec betroffenen Workflow-Skills und eng benachbarte Completion-Regeln. Keine generelle Skill-Refaktorierung und keine neue Automatisierungslogik.
- Files:
  - `documentation/codex/skills/janus-skill-router/SKILL.md`
  - `documentation/codex/skills/janus-executioner/SKILL.md`
  - `documentation/codex/skills/janus-final-audit/SKILL.md`
  - `documentation/codex/skills/janus-documentation-update/SKILL.md`
  - `documentation/codex/skills/janus-git-governance/SKILL.md`
  - `documentation/codex/skills/janus-build-release/SKILL.md`
  - `documentation/codex/skills/janus-quickchange/SKILL.md`
  - `documentation/codex/skills/codex-start-of-work-check/SKILL.md`
  - zusaetzlich nur die installierten Arbeitskopien unter `C:\Users\pruve\.codex\skills\...`, falls diese im Janus-Prozess synchron gehalten werden muessen
- Steps:
  1. Ergaenze in jedem relevanten Skill eine knappe CURRENT_STATE-Abschlussregel, die nur fuer substantielle Arbeitsbloecke gilt.
  2. Stelle sicher, dass die Skills dieselbe Deterministik fuer "substantiell" verwenden wie `AGENTS.md`.
  3. Verlange in den Skill-Abschlussregeln die kompakten Kerninhalte: was geaendert wurde, welche Dateien betroffen sind, welche Checks liefen, welche Risiken offen sind und was ChatGPT/Codex als naechstes tun soll.
  4. Halte in Git-nahen Skills fest, dass Commit/Push weiterhin nur ueber bestehende Governance und mit expliziter Freigabe laufen.
  5. Verankere den Remote-Hinweis fuer lokale-only CURRENT_STATE-Updates dort, wo Skills Completion/Handoff-Outputs definieren.
- Acceptance Criteria:
  - Alle im Scope genannten Skills enthalten eine CURRENT_STATE-Regel fuer substantielle Abschluesse.
  - Die Skill-Texte widersprechen weder `AGENTS.md` noch der Spec beim Git-Gate oder beim Nicht-Push-Fall.
  - Kein Skill fordert CURRENT_STATE fuer reine Kurzantworten, Routing-only oder Mini-Status.
  - Skill-Abschluesse nennen weiterhin evidenzbasierten Zustand statt pauschaler Erfolgsmeldungen.
- Tests:
  - `rg -n "CURRENT_STATE|substantiell|substantial|Remote|GitHub|janus-git-governance" documentation/codex/skills/janus-*/SKILL.md documentation/codex/skills/codex-start-of-work-check/SKILL.md`
  - Manuelle Vergleichspruefung, dass die CURRENT_STATE-Regeln ueber die betroffenen Skills konsistent sind und keine Auto-Push-Pflicht einfuehren.
- Model: 5.4
- Reason:
  - Multi-file skill governance alignment with deterministic wording, but still fully inside the normal Janus documentation lane.
