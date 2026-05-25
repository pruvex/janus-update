---
name: janus-health-check
description: Run bounded Janus repository hygiene and drift checks. Use when the user asks for health check, hygiene check, system health, cleanup review, stale artifact scan, documentation consistency, backlog visibility, large-file scan, workflow drift, or safe cleanup candidates.
---

# Janus Health Check

## Purpose

Use this skill to answer: "Ist Janus gerade sauber genug, um weiterzuarbeiten?"

It checks repository hygiene, documentation drift, backlog visibility, stale artifacts, large files, and safe next actions. It is not a feature, bugfix, refactor, release, or architecture execution skill.

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
- Do not mutate Backlog in `DAILY`; only propose candidates.
- In `WEEKLY` or `MONTHLY`, create Backlog items only after concrete evidence and only via `janus-backlog-intake`.
- Auto-fixes are proposal-only unless the user explicitly approves exact paths/actions.
- Never propose deleting non-empty scripts, executables, databases, logs, release artifacts, or unknown generated files as low risk.
- If uncertain, route to `janus-backlog-intake`, `janus-debug`, `janus-git-governance`, or `5.5` escalation instead of changing files.

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

## DAILY Checklist

Check:

- Git branch, staged count, dirty count, large dirty files.
- Core artifacts exist: `AGENTS.md`, Backlog, migration plan, pipeline contract, dashboard snapshot.
- Open `IN PROGRESS` Backlog items are visible.
- Codex skill migration has no obvious missing repo directories for created skills.
- Root has no obvious temporary junk that blocks work.
- Skill usage log exists and entry count is visible.

No Backlog writes in `DAILY`.

## WEEKLY Checklist

Includes DAILY plus:

- large files over 500 KB excluding known generated/dependency folders
- stale or suspicious root artifacts
- documentation/task drift examples
- legacy migration gaps
- Backlog health signals such as many stale `IN PROGRESS`, `NEEDS INFO`, or blockers
- skill usage summary and repeated friction from `documentation/codex/SKILL_USAGE_LOG.md`

Concrete, non-speculative findings may be routed to `janus-backlog-intake`.

## MONTHLY Checklist

Includes WEEKLY plus bounded architecture review:

- oversized modules or services
- unclear ownership boundaries
- repeated failure patterns in documentation/test results
- release and update artifact consistency
- long-term maintainability risks
- repeated skill usage friction that suggests router or skill changes

Do not perform large fixes. Route to Backlog or recommend `5.5` review for high-risk ambiguity.

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
