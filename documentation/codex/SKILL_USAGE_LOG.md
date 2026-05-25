# Janus Codex Skill Usage Log

Dieses Log ist append-only und dokumentiert substantielle Janus-Skill-Laeufe. Es dient dazu, regelmaessig zu pruefen, ob Routing, Modellwahl, Kontextstrategie, Stop-Gates oder Automatisierung verbessert werden sollten.

Nicht jeder Chat-Satz wird geloggt. Geloggt werden nur echte Arbeitsbloecke mit Skill-Entscheidung, Artefaktbezug, Check, Handoff, Blocker oder Commit-Relevanz.

## Log Format

| Date | Skill | Trigger | Model | Intelligence | Chat | State | Artifacts | Checks | Friction | Optimization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| 2026-05-25 | janus-skill-router | Skill-Nutzungslog eingerichtet | 5.4 | medium | same | PASS | documentation/codex/SKILL_USAGE_LOG.md; documentation/codex/scripts | record dry-run PASS; summary PASS; skill validation PASS | usage log fehlte | Skill-Nutzung woechentlich auswerten |
| 2026-05-25 | janus-skill-router | WHAT_I_LEARNED gezielt in Skill-Prozess integriert | 5.4 | medium | same | PASS | WHAT_I_LEARNED.md; documentation/codex/scripts; janus-debug/executioner/final-audit/documentation-update | search helper PASS; append helper dry-run PASS; skill validation PASS | WHAT_I_LEARNED zu gross fuer Vollkontext | Gezielte Suche vor Debug/Audit/Build; append-only Patternpflege |
| 2026-05-25 | janus-skill-router | Wunsch-Intake fuer kleine Verbesserungen vs groessere Features dokumentiert | 5.3-codex | medium | same | PASS | AGENTS.md; documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md; documentation/codex/skills/janus-skill-router/SKILL.md; C:/Users/pruve/.codex/skills/janus-skill-router/SKILL.md | git diff reviewed; active router skill verified | none | User-Wuensche kuenftig automatisch als Backlog-Intake oder Feature-Design routen |
| 2026-05-25 | janus-skill-router | Plugin-Einsatz fuer Janus Workflow dokumentiert | 5.3-codex | medium | same | PASS | AGENTS.md; documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md; documentation/codex/skills/janus-skill-router/SKILL.md; C:/Users/pruve/.codex/skills/janus-skill-router/SKILL.md | git diff reviewed; active router plugin routing verified | Browser plugin in UI nicht sichtbar; als if-available dokumentiert | Plugins als Skill-Unterstuetzung fuer Evidenz Analyse und externe Artefakte routen |
