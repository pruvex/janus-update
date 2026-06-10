---
name: codex-start-of-work-check
description: Use at the start of a Codex work session or when the user sends their first message to begin, resume, continue, debug, plan, implement, review, or ask for work. Checks whether Codex or Janus healthcheck reminders are due before continuing. Reminder-only; does not run healthchecks without user confirmation.
metadata:
  short-description: Remind about due healthchecks at work start
---

# Codex Start Of Work Check

At the start of a work session, check whether a scheduled healthcheck reminder is due.

## Scope

- This is a reminder gate, not a healthcheck runner.
- It can mention Janus healthcheck reminders, but does not inspect or modify Janus code.
- It can mention Codex skill healthcheck reminders, but does not optimize skills directly.

## Workflow

1. Read `documentation/ai/CURRENT_STATE.md` first when this skill is used as part of substantial Janus work.
2. Run `scripts/due_healthchecks.py`.
3. If it reports no due reminders, continue with the user's request normally.
4. If it reports one or more due reminders, tell the user what is due and ask whether to start it now.
5. Only run a healthcheck after the user replies `ok`.

## Sync Source

For substantial Janus work, use `documentation/ai/CURRENT_STATE.md` as the primary sync source.

- Current remote sync source: `pruvex/Janus-Backup@develop:documentation/ai/CURRENT_STATE.md`
- `CURRENT_STATE.md` is a sync source, not a replacement for Spec, Backlog, TestSpec, or audit artifacts.
- Do not treat `pruvex/janus-update` or `origin/master` as the current Janus project state.
- For Git steps, use `janus-git-governance`.

## Reminder Text

Keep it short:

`Heute ist <weekday>; <healthcheck> ist faellig. Soll ich ihn jetzt starten? Antworte ok.`

If multiple checks are due, list both.

## Output

If due:

NEXT: run-due-healthcheck
MODEL: 5.4/low
PASS: due reminder id
DROP: unrelated work until user confirms

Change the model/reasoning to `5.4/low`, write `ok`, and the due healthcheck starts immediately.

## CURRENT_STATE Requirement

This reminder gate usually does not create a substantial Janus work block by itself.

Update `documentation/ai/CURRENT_STATE.md` only if this skill is used as part of a substantial Janus work block where at least one of these is true:

- files changed
- validation executed
- a blocker documented
- a formal next-skill handoff produced

Pure reminder-only replies, short status answers, and other mini-interactions do not require a CURRENT_STATE update.

If a CURRENT_STATE update is required, keep it concise and include:

- what changed
- which files changed
- which checks ran
- what remains risky or open
- what ChatGPT should review next
- what Codex should do next

Commit and push remain gated by `janus-git-governance` and explicit user approval.

If no push happens or push fails, the completion or handoff must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.
