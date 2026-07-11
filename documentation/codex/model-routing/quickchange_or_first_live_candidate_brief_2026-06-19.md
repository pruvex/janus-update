# Quickchange OR First Live Candidate Brief - 2026-06-19

Status: READY FOR LIVE-RUN APPROVAL / NO LIVE OR CALL EXECUTED YET

## Bound Candidate

Selected first real quickchange candidate for the first OpenRouter live test:

- skill: `janus-quickchange`
- bounded class: `quickchange_patch_review`
- selected OR model: `openai/gpt-oss-20b`
- target file: `frontend/index.html`
- exact bounded intent: change the chat input placeholder wording from `Nachricht an Janus senden...` to `Nachricht an Janus schreiben...` in both chat windows `A` and `B`

Reason this exact candidate is first:

- one user-visible intent only
- one file only
- two identical text replacements in the same UI cluster
- no backend/provider/persistence/API/auth/security/privacy impact
- clear reject path if the patch touches anything beyond these two placeholders

## Quickchange Brief

```text
QUICKCHANGE BRIEF
- Request: Passe den Chat-Placeholder in beiden Chatfenstern von "Nachricht an Janus senden..." auf "Nachricht an Janus schreiben..." an.
- Scope: Nur die beiden Chat-Input-Placeholder in Fenster A und Fenster B innerhalb von frontend/index.html.
- Expected Files: frontend/index.html
- Acceptance: Genau zwei Placeholder-Texte sind angepasst; keine weiteren Inhalte in frontend/index.html oder anderen Dateien werden verändert.
- Why Quickchange: Winzige reine Copy-Aenderung in einem bestehenden Frontend-Surface mit klarer Sichtpruefung und engem Diff.
- Reroute Trigger: Jede zusaetzliche UI-/Textaenderung ausserhalb der zwei Placeholder, jede zweite Datei, jede Strukturaenderung, jede Validierungsunsicherheit.
```

## Mini Test Plan

```text
MINI TEST PLAN
- Scope: Nur die beiden Chat-Placeholder in frontend/index.html
- Files Expected: frontend/index.html
- Checks:
  1. git diff -- frontend/index.html
  2. rg -n "Nachricht an Janus (senden|schreiben)\\.\\.\\." frontend/index.html
  3. changed_files.txt / git_diff.patch gegen Allowlist pruefen
- Visual Check: Placeholder in Chatfenster A und B zeigt nach Annahme "Nachricht an Janus schreiben..."
- N/A Reason: Kein Build/Testlauf noetig, weil es eine reine Copy-Aenderung ohne Logik- oder Laufzeitverhalten ist.
```

## Required Gate Parameters

- workflow id: `BOUNDED-QUICKCHANGE-OR-LIVE-001`
- task label: `chat placeholder wording senden -> schreiben`
- editable path: `frontend/index.html`
- max touched files: `1`
- normal target model: `5.4/medium`
- selected OR model: `openai/gpt-oss-20b`

## Reject Conditions

Reject the delegated result immediately if any of these occur:

- any touched file other than `frontend/index.html`
- any diff outside the two intended placeholder lines
- any delete, rename, or move
- any attempt to also modify the API key placeholder or unrelated wording in the same file
- incomplete run artifacts

## Validation Boundary

This candidate brief intentionally does not include the already-present `API-Schlüssel` wording diff in the same file.

For the first OR live run, the accepted scope is only:

- placeholder in chat window A
- placeholder in chat window B

Anything broader should be rejected and rerouted to Codex-only quickchange.

## Next Safe Step

Run the bounded dispatcher in prompt mode with:

- `quickchange_patch_review`
- `openai/gpt-oss-20b`
- `frontend/index.html`
- `max-touched-files=1`

and ask for explicit approval before the first live OpenRouter call.
