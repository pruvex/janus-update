PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-095
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-095_einheitliche_antwortform_fuer_wetteranfragen.md
Spec: N/A WITH REASON
Backlog Item: BACKLOG-095
Assigned Model: 5.3 codex
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Ein einzelnes, atomares Verbesserungsthema ist gebunden: einheitliche Wetter-Antwortform fuer beide Provider bei unveraendertem Wetterrouting und unveraenderter Quellenattribution.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- pytest backend/tests -k weather
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/functional/chat-core.spec.js --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec/task artifact, dashboard sync, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, touched files, and next-step routing.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.3 codex
Recommended Intelligence: medium
Reason: Der Scope ist klar, risikoarm und mit einem einzelnen gebundenen Task implementierbar.
User Action: Bitte wechsle bei Bedarf auf dieses Modell und sag `ok`, dann starte ich Skill 4 hier direkt.
