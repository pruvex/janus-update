# Codex Weekly Health Check

Generated: 2026-06-08 13:36:53 UTC

## Status

WARN

## Validation

```text
VALIDATION PASSED
- C:\Users\pruve\.codex\skills\codex-dev-skill-template
- C:\Users\pruve\.codex\skills\codex-skill-cost-auditor
- C:\Users\pruve\.codex\skills\codex-audit-package-builder
- C:\Users\pruve\.codex\skills\codex-health-check
- C:\Users\pruve\.codex\skills\codex-start-of-work-check
```

## Cost Audit

Report: `C:\KI\Janus-Projekt\codex_weekly_skill_cost_audit.md`

```text
# Codex Skill Cost Audit

Root: `C:\Users\pruve\.codex\skills`
Editable personal non-Janus skills: 5
Editable skill words: 1406

## Highest ROI

| Priority | Skill | Words | Issues | Path |
|---:|---|---:|---|---|
| 0 | codex-audit-package-builder | 381 | none | `C:\Users\pruve\.codex\skills\codex-audit-package-builder\SKILL.md` |
| 0 | codex-dev-skill-template | 345 | none | `C:\Users\pruve\.codex\skills\codex-dev-skill-template\SKILL.md` |
| 0 | codex-skill-cost-auditor | 251 | none | `C:\Users\pruve\.codex\skills\codex-skill-cost-auditor\SKILL.md` |
| 0 | codex-start-of-work-check | 231 | none | `C:\Users\pruve\.codex\skills\codex-start-of-work-check\SKILL.md` |
| 0 | codex-health-check | 198 | none | `C:\Users\pruve\.codex\skills\codex-health-check\SKILL.md` |

## Recommended Next Step

Optimize only editable personal non-Janus skills with priority above 0. Keep managed plugin skills read-only.

NEXT: optimize-selected-skills
MODEL: 5.4/medium
PASS: this report; selected skill paths
DROP: raw scan noise

Change the model/reasoning to `5.4/medium`, write `ok`, and the next skill continues immediately.
```

## Run Log Summary

```text
Recent runs: 67
Statuses: {'success': 45, 'pass': 3, 'due': 6, 'clear': 10, 'warn': 3}
Skills: {'codex-skill-cost-auditor': 22, 'codex-health-check': 6, 'codex-start-of-work-check': 16, 'codex-audit-package-builder': 23}
Max duration ms: 441
Max issue count: 0
Warnings:
- Repeated changed audit package rebuilds: 13x C:\KI\Janus-Projekt\AUDIT_PACKAGE.md, size range 5695-16059 bytes, 8 unique versions.
- Repeated changed audit package rebuilds: 3x C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC15_AUDIT_PACKAGE.md, size range 21355-26017 bytes, 3 unique versions.
```

## Recommendation

Optimize the final-audit retry workflow: after a BLOCKED final audit, fix in the work chat, rebuild AUDIT_PACKAGE.md once, then continue in the same final-audit chat with only the updated package path and delta note.

## Next Handoff

NEXT: codex-skill-pipeline-optimization
MODEL: 5.4/low
PASS: C:\KI\Janus-Projekt\codex_weekly_healthcheck.md
DROP: raw logs

Change the model/reasoning to `5.4/low`, write `ok`, and the next skill continues immediately.
