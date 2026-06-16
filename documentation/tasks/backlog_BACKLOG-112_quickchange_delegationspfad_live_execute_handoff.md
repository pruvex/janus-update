# BACKLOG-112 Handoff

## Backlog Item
- **ID:** BACKLOG-112
- **Titel:** Quickchange-Delegationspfad fuehrt neuen OR-Pilot noch nur als Dry-Run statt als echten bounded Live-Execute aus
- **Typ:** TECH_DEBT
- **Status:** IN PROGRESS

## Entry Point
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Der fehlende Schritt ist ein klar begrenzter Infrastruktur- und Governance-Fix fuer den ersten echten bounded OR-Pilot auf `janus-quickchange`.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-06-16
- **Handoff:** documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-06-16

## Handoff Scope
- Enable a real bounded live-execute path for the existing quickchange delegation flow.
- Keep the exact editable-path allowlist, touched-file cap, delete/rename/move tripwire, diff capture, and validation capture boundaries.
- Preserve Codex final accept/reject authority.
- Do not expand into broader execution delegation or production routing.

## Evidence Paths
- `documentation/backlog/BACKLOG.md`
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- `documentation/codex/model-routing/codex_first_real_or_pilot_decision_summary_2026-06-16.md`

## Dropped Context
- Unrelated READY backlog items.
- Historical Spec-18 closeout narrative.
- Auto Router experiment thread context.

## Next Skill Copy Prompts
```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-112
Task: documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md
Backlog Item: BACKLOG-112
```

## Keep Context
- selected backlog item
- created handoff artifact
- exact next-skill prompt

## Drop Context
- unrelated READY items
- old DONE history
- broad backlog narrative
