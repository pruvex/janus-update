---
name: janus-health-check
description: Run bounded Janus repository hygiene and drift checks. Use when the user asks for health check, hygiene check, system health, cleanup review, stale artifact scan, documentation consistency, backlog visibility, large-file scan, workflow drift, or safe cleanup candidates.
---

# Janus Health Check

## Purpose

Use this skill to answer: "Ist Janus gerade sauber genug, um weiterzuarbeiten?"

It checks repository hygiene, documentation drift, backlog visibility, stale artifacts, large files, and safe next actions. It is not a feature, bugfix, refactor, release, or architecture execution skill.
This is primarily a Codex-led bounded scan skill. ChatGPT uses it for triage or follow-up review when the scan finds drift, risk, or unclear evidence.

## Modes

Normalize user intent:

- `DAILY`: quick start-of-day hygiene check. Default when no mode is named.
- `WEEKLY`: broader structure check and concrete Backlog candidates.
- `MONTHLY`: bounded architecture hygiene and long-term risk review.

If the user asks which mode to use, recommend:

- `DAILY` for "can we keep working?"
- `WEEKLY` for "what should we clean up soon?"
- `MONTHLY` for "where is the architecture drifting?"

## Hard Rules

- Do not implement features or bugfixes.
- Do not refactor architecture.
- Do not delete files.
- Do not upgrade dependencies.
- Do not release, bump versions, tag, merge, or push.
- Do not run Auto-Fix changes unless the user explicitly approves exact paths/actions after the scan result.
- Do not run tests or builds as part of the healthcheck itself unless the user separately requests that after the scan.
- Do not perform Git actions; route Git risk to `janus-git-governance`.
- Do not mutate Backlog in `DAILY`; only propose candidates.
- In `WEEKLY` or `MONTHLY`, create Backlog items only after concrete evidence and only via `janus-backlog-intake`.
- Auto-fixes are proposal-only unless the user explicitly approves exact paths/actions.
- Never propose deleting non-empty scripts, executables, databases, logs, release artifacts, or unknown generated files as low risk.
- If uncertain, route to `janus-backlog-intake`, `janus-debug`, `janus-git-governance`, or `5.6 Sol` escalation instead of changing files.

## Bounded Scan Rules

Exclude by default:

```text
.git/
node_modules/
backend/venv/
venv/
.pytest_cache/
.ruff_cache/
playwright-report/
test-results/
__pycache__/
dist/
build/
.vercel/
```

Limits:

- Top 20 large files.
- Top 20 root hygiene findings.
- Top 20 documentation/task drift examples.
- Stop or summarize any scan that risks running longer than about 60 seconds.
- Never repeat the same failing command blindly.

## Snapshot Script

Run the helper first unless the user asked for a purely conceptual answer:

```powershell
python C:\Users\pruve\.codex\skills\janus-health-check\scripts\health_snapshot.py --repo C:\KI\Janus-Projekt --mode DAILY
```

Use `--mode WEEKLY` or `--mode MONTHLY` when selected. The script is read-only.

If a quick reminder check is all that is needed at session start, prefer `codex-start-of-work-check` instead of this skill.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

This skill's bounded health-check interpretation lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For one bounded read-only health-check interpretation slice, this skill now has the shared tri-modal operator gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane health_check_review `
  --task-id TASK-HC-001 `
  --workflow-id WF-HEALTH-CHECK-GATE-001 `
  --operator-choice prompt `
  --input-package-json development/openrouter-skill-tests/janus-health-check/health_check_input_package.json `
  --estimated-codex-saved-tokens 12000 `
  --estimated-delegation-overhead-tokens 4000
```

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only review slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_health_check_review_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.

Boundaries:

- no delegated file deletion
- no delegated Git or release action
- no delegated auto-fix authority
- Codex remains the final health-check owner

## DAILY Checklist

Check:

- Git branch, staged count, dirty count, large dirty files.
- Core artifacts exist: `AGENTS.md`, Backlog, migration plan, pipeline contract, dashboard snapshot.
- Open `IN PROGRESS` Backlog items are visible.
- Codex skill migration has no obvious missing repo directories for created skills.
- Root has no obvious temporary junk that blocks work.
- Skill usage log exists and entry count is visible.

No Backlog writes in `DAILY`.
No Git actions, auto-fixes, tests, or builds in `DAILY`.

## WEEKLY Checklist

Includes DAILY plus:

- large files over 500 KB excluding known generated/dependency folders
- stale or suspicious root artifacts
- documentation/task drift examples
- legacy migration gaps
- Backlog health signals such as many stale `IN PROGRESS`, `NEEDS INFO`, or blockers
- skill usage summary and repeated friction from `documentation/codex/SKILL_USAGE_LOG.md`

Concrete, non-speculative findings may be routed to `janus-backlog-intake`.
Do not execute fixes, tests, builds, or Git actions as part of the scan.

## MONTHLY Checklist

Includes WEEKLY plus bounded architecture review:

- oversized modules or services
- unclear ownership boundaries
- repeated failure patterns in documentation/test results
- release and update artifact consistency
- long-term maintainability risks
- repeated skill usage friction that suggests router or skill changes

Do not perform large fixes. Route to Backlog or recommend `5.6 Sol` review for high-risk ambiguity.
Do not execute fixes, tests, builds, or Git actions as part of the scan.

## Ampel

Report:

```text
Systemhealth: <0-100>% - GRUEN | GELB | ROT
```

Use:

- `GRUEN` 90-100: no blockers, no required action, only optional hygiene notes.
- `GELB` 70-89: usable but has non-blocking hygiene findings, dirty tree, warnings, or cleanup candidates.
- `ROT` 0-69: missing core artifacts, release blockers, security risk, destructive ambiguity, or work should stop.

If the working tree is dirty and cleanup candidates exist, max is `GELB`/89. If scans were incomplete, max is `GELB` unless core artifacts are missing.

## Model Routing

- Use `5.6 Terra` low for DAILY checks when the current `5.6 Terra` project context is warm.
- Use `5.6 Luna` only for separated low-risk healthcheck runs that are still likely cheaper than staying on warm `5.6 Terra`.
- Use `5.6 Terra` medium/high for WEEKLY or MONTHLY analysis with meaningful judgment.
- Recommend `5.6 Sol` only for security, privacy, architecture, release, or destructive ambiguity.

## Output

Use German for user-facing text:

```text
SYSTEM HEALTH REPORT
- Modus:
- Systemhealth:
- Arbeitsfaehigkeit:
- Scan-Abdeckung:
- Kernartefakte:
- Git-Zustand:
- Backlog-Sichtbarkeit:
- Doku-/Skill-Drift:
- Grosse Dateien:
- Findings:
- Auto-Fix-Kandidaten:
- Backlog-Kandidaten:
- Eskalationen:
- Operative Empfehlung:
- Naechster Skill:
- Modell-Empfehlung:
```

End with one concrete recommendation. Do not use vague "bei Bedarf" as the main recommendation.

## Handoff

If the actor or chat boundary changes, emit exactly one short fenced `text` block with the scan result and next gate.
Include `PASS`, `DRIFT_FOUND`, `BLOCKED`, or `NEEDS_INFO` explicitly.
A bare `ok` is never a valid handoff replacement.
