# SKILL_COLLABORATION_MATRIX

## Purpose

This file defines the compact governance layer for future ChatGPT/Codex collaboration across the versioned repo skill sources under `documentation/codex/skills/`.

Scope rule:

- "Janus-Skills" in this matrix means only repo skill sources under `documentation/codex/skills/*/SKILL.md`.
- Local installed skills under `C:\Users\pruve\.codex\skills\` are not repo skills and must not be treated as such.
- Read local installed skills only when `CURRENT_STATE` or the user explicitly requires them.

Primary objective:

- maximum quality
- minimum token cost
- stable cache reuse
- predictable next-skill routing

## Global Handoff Standard

Mandatory boundary rule:

- Codex -> ChatGPT must provide a compact copyable handoff in one fenced `text` block.
- ChatGPT -> Codex must provide model/reasoning above the handoff and exactly one fenced `text` block.
- Do not hand off with "write ok", "say ok", or similar empty acknowledgements.

Required handoff shape:

- one compact context header above the code block when ChatGPT hands off to Codex
- one single copyable fenced `text` block
- short, cache-friendly, artifact-bound
- no broad chat-history recap

New-chat rule:

- if a new chat is recommended, the block must contain `NEW_CHAT_HANDOFF`
- if the same Codex context can continue safely, name `NEXT` clearly and keep the handoff minimal

Same-context Codex rule:

- for Codex -> Codex transitions inside the same warm context, naming the exact `NEXT` skill is enough
- use a broader copy-box only when a fresh chat, a hard boundary, or a context drop is actually needed

## Model / Reasoning Policy

- `5.4 mini` / `low`: compact normalization, light governance, mechanical documentation sync, cheap inventory work
- `5.4` / `medium`: normal Janus workhorse for routing, planning, specs, task shaping, evidence review, and mixed governance
- `5.5` / `high`: independent audit, security/privacy escalation, release-critical risk review, or high-uncertainty architecture judgment

Default bias:

- stay on warm `5.4` whenever context reuse beats a cheap model hop
- use `5.4 mini` only for clearly bounded low-risk mechanical work
- escalate to `5.5` only when risk or independence really justifies it

## Cache And Token Policy

- Prefer repo summary artifacts over full source artifacts when safe.
- Load only the bound artifact cluster needed for the current skill.
- Keep handoffs artifact-first, not chat-history-first.
- Avoid re-reading full skill files after this matrix unless a skill enters individual review.
- Do not confuse repo skill sources with local installed Codex development skills.
- Optimize for one skill, one goal, one next gate.

## Skill Role Matrix

| Skill | Primary Role | Purpose | When Use | Next Skill After Completion | Handoff Type | Handoff Pflicht | Handoff Format | Model | Reasoning | Minimal LOAD | Cost / Cache Hint | Review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `codex-audit-package-builder` | Codex | Build or refresh a compact audit package for a fresh final review. | Before independent final audit when changed files, validation, and known risks need a compact package. | `janus-final-audit` | `Codex -> Codex` | ja | `Std-CopyBox` when handing to a fresh audit chat, otherwise compact `NEXT` | `5.5` | `high` | changed files, validation evidence, existing audit notes | High-value cache saver because it replaces long raw history with one package. | `UNREVIEWED` |
| `codex-start-of-work-check` | Codex | Check whether Janus or Codex healthcheck reminders are due at session start. | First work message, resume, continue, plan, debug, implement, or review start. | `janus-skill-router` | `Codex -> Codex` | nein | short in-chat reminder only unless a fresh chat handoff is needed | `5.4 mini` | `low` | `CURRENT_STATE`, reminder timing context | Keep tiny; do not spend context on anything beyond due-reminder logic. | `UNREVIEWED` |
| `janus-backlog-handoff` | ChatGPT | Route a READY backlog item into the correct Diamond entry point and create the next prompt/handoff. | After prioritization, when a READY item is selected, or when dashboard-ready routing is needed. | `janus-feature-design` or `janus-preimplementation-check` or `janus-task-breakdown` | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` handoff block per prepared item; do not accept bare `ok` as a handoff substitute | `5.4` | `medium` | `BACKLOG_ACTIVE_SUMMARY`, selected READY item block in `BACKLOG.md`, contradiction check only if needed | Read summary first, then only the selected item block; avoid full backlog deep-reads unless routing evidence conflicts. | `UPDATED` |
| `janus-backlog-intake` | ChatGPT | Convert raw user wishes, bugs, and annoyances into structured backlog candidates without prioritizing or inventing product decisions. | When the user reports a bug, small change, annoyance, manual finding, or backlog-worthy request. | `janus-backlog-prioritization` on valid intake; otherwise `janus-feature-design` or `NEEDS INFO` follow-up | `ChatGPT -> ChatGPT` or `ChatGPT -> Codex` | ja | exactly one compact fenced `text` block if the next actor changes; do not accept bare `ok` as a substitute | `5.4` | `medium` | raw request, `BACKLOG_ACTIVE_SUMMARY`, targeted `BACKLOG.md` duplicate/status check | Raw-request-first and duplicate-check-bound; use summary first and read `BACKLOG.md` only for targeted contradiction or duplicate checks. | `UPDATED` |
| `janus-backlog-prioritization` | ChatGPT | Rank existing open backlog work, update evaluation cache fields, and recommend the next best item without inventing product scope or implementation routing. | After backlog intake, when existing open items need priority/cache refresh, or when "what next" must be answered from backlog state. | `janus-backlog-handoff` on a selected item; otherwise `janus-feature-design` or `NEEDS INFO` follow-up when ambiguity blocks ranking | `ChatGPT -> ChatGPT` or `ChatGPT -> Codex` | ja | exactly one compact fenced `text` block if the next actor or chat changes; do not accept bare `ok` as a substitute | `5.4` | `medium` | `BACKLOG_ACTIVE_SUMMARY`, targeted open item blocks in `BACKLOG.md`, intake context only when needed | Summary-first delta review; avoid full backlog deep-reads and route feature ambiguity back upstream instead of forcing fake prioritization. | `UPDATED` |
| `janus-build-release` | Codex | Build, verify, and optionally publish release artifacts behind strict release and Git gates. | After final audit and docs sync when packaging or release evidence is needed. | `janus-git-governance` on release-ready evidence; otherwise `janus-debug`, `janus-final-audit`, or caller review | `Codex -> ChatGPT` or `Codex -> Codex` | ja | exactly one compact release-evidence fenced `text` block on actor/chat boundary; do not accept bare `ok` as publish, tag, push, release, or handoff approval | `5.5` | `high` | final audit, docs evidence, git checkpoint, version source, release artifact targets | Release-artifact-bound gate; keep build/verify separate from publish/tag/push and require `janus-git-governance` for Git/release boundaries. | `UPDATED` |
| `janus-debug` | Codex | Debug one bounded failure slice with evidence-first iteration and no scope expansion. | After failed execution, failed tests, runtime/provider issues, or blocked final audit. | `janus-final-audit` or `janus-documentation-update` on validated fix; otherwise `janus-test-pipeline`, `janus-executioner`, or caller review | `Codex -> ChatGPT` or `Codex -> Codex` | ja | exactly one compact evidence-first fenced `text` block on actor/chat boundary; do not accept bare `ok` as a substitute | `5.4` | `medium` | one failure slice, failing evidence, changed file cluster, bound task/spec/backlog context | Keep to one failure slice only; block on contradictory or missing evidence and avoid broad history reconstruction. | `UPDATED` |
| `janus-documentation-update` | Shared | Synchronize backlog, state, changelog, registry, and closeout docs after validated work. | After validation passed and the result must be persisted into project documentation. | `janus-git-governance` | `ChatGPT -> Codex` or `Codex -> ChatGPT` | ja | compact copy-box for cross-actor closeout handoff; same-context `NEXT` is enough when Codex continues warm | `5.4 mini` | `low` | `CURRENT_STATE`, target marker, changed artifacts, validation evidence | Cheap sync step; keep document set minimal and bounded. | `UPDATED` |
| `janus-executioner` | Codex | Implement exactly one target task from bound artifacts. | After preimplementation check passed and one target task is ready. | `janus-final-audit` on success; otherwise `janus-debug` or `janus-test-pipeline` or caller review | `Codex -> ChatGPT` or `Codex -> Codex` | ja | execution result plus one compact handoff block; if ChatGPT takes over, emit exactly one compact `text` block and do not accept bare `ok` as a substitute | `5.4` | `medium` | target task, precheck, source spec/backlog, touched file cluster, bounded validation surface | Keep warm `5.4` cache; do not reload planning artifacts broadly and stop on scope growth beyond one task slice. | `UPDATED` |
| `janus-feature-design` | ChatGPT | Turn a vague feature idea into a locked decision summary. | When the user brainstorms or needs scope and product decisions clarified before spec work. | `janus-spec-generator` for locked feature decisions or `janus-backlog-intake` for simple backlog-worthy requests | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` decision handoff; do not accept bare `ok` as a substitute | `5.4` | `medium` | user goal, `CURRENT_STATE`, latest decision context if any | High leverage planning step; keep outcome small, user-goal-first, and spec-ready without broad repo rereads. | `UPDATED` |
| `janus-final-audit` | Shared | Decide PASS, PASS WITH FIXES, or BLOCKED against bound evidence only. | After implementation and validation, before docs sync or release. | `janus-documentation-update` on PASS/PASS WITH FIXES; otherwise `janus-debug`, `janus-executioner`, `janus-test-pipeline`, or caller review | `Codex -> ChatGPT` or `ChatGPT -> Codex` | ja | audit result plus one compact `text` handoff block when actor/chat changes; do not accept bare `ok` as a substitute | `5.5` | `high` | compact audit package, changed files, validation evidence, manual evidence, known risks | Prefer audit package over raw history; block on unclear evidence instead of reconstructing chat history. | `UPDATED` |
| `janus-git-governance` | Shared | Govern commit, push, checkpoint, branch, and release Git actions. | Whenever save, commit, push, split, checkpoint, PR, tag, or release Git decisions are needed. | caller resumes or `STOP` | `ChatGPT -> Codex` or `Codex -> ChatGPT` | ja | compact approval-oriented `text` block for cross-actor transitions; do not accept bare `ok` as Git approval | `5.4 mini` | `low` | git status, target changeset, branch/remote intent, `CURRENT_STATE` if substantial | Keep pathspec-scoped; never broaden to whole worktree unless required; explicit Git approval only. | `UPDATED` |
| `janus-health-check` | Codex | Check hygiene, drift, stale artifacts, and repo cleanliness before or between work. | At session start, on hygiene requests, or when worktree/docs drift is suspected. | `janus-skill-router` | `Codex -> ChatGPT` or `Codex -> Codex` | ja | short evidence-first handoff if another actor will decide next | `5.4 mini` | `low` | `CURRENT_STATE`, hygiene targets, targeted repo evidence | Cheap bounded scan; avoid reading whole repo state unless a blocker appears. | `UNREVIEWED` |
| `janus-preimplementation-check` | Codex | Validate exactly one task before code changes and produce an execution handoff. | Before implementation when one task/handoff is ready and scope/tests/model must be verified. | `janus-executioner` on PASS; otherwise `janus-task-breakdown` or caller review | `Codex -> Codex` or `Codex -> ChatGPT` | ja | compact precheck handoff block with exact target task; on non-PASS emit exactly one compact `text` block for ChatGPT and do not accept bare `ok` as a substitute | `5.4` | `medium` | target task, source spec/backlog, tests/evidence plan, matching handoff artifact if applicable | One-task gate; keep context to the implementation slice only and stop on multi-task scope. | `UPDATED` |
| `janus-quickchange` | Codex | Execute one tiny low-risk change with a mini validation plan. | For trivial, bounded edits that do not justify the full backlog/spec pipeline. | `janus-documentation-update` on success; otherwise `janus-backlog-intake` or `janus-feature-design` or `janus-preimplementation-check` or `janus-debug` | `Codex -> ChatGPT` or `Codex -> Codex` | ja | compact result handoff; same-context `NEXT` allowed if docs follow immediately; if ChatGPT takes over, emit exactly one compact `text` block and do not accept bare `ok` as a substitute | `5.4` | `low` | change request, small file cluster, mini-testplan, minimum validation surface | Stay on warm `5.4`; reroute immediately if scope grows or validation stops being tiny and obvious. | `UPDATED` |
| `janus-skill-router` | Shared | Choose the right Janus skill, model, context, and next gate. | Before substantial Janus work or when the correct process path is unclear. | routed skill | `ChatGPT -> Codex` or `Codex -> ChatGPT` | ja | always use explicit model/reasoning and one compact handoff when actor/chat changes | `5.4` | `medium` | `CURRENT_STATE`, router skill, one bound artifact or decision question | Highest leverage router; summary-first loading is mandatory. | `UPDATED` |
| `janus-spec-generator` | ChatGPT | Generate a deterministic feature spec from a locked decision source. | After feature design when a formal spec must be drafted. | `janus-spec-normalizer` on mechanical cleanup need, otherwise `janus-spec-review` | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` spec handoff block; do not accept bare `ok` as a substitute | `5.4` | `medium` | locked decision summary or equivalent locked source, target spec path, minimal routing note | Keep to the locked decision source; block on open product questions and do not re-brainstorm inside spec generation. | `UPDATED` |
| `janus-spec-normalizer` | ChatGPT | Convert one draft spec into parser-safe, copy-safe final markdown without changing product meaning. | After a draft spec exists and before review or task compilation. | `janus-spec-review` | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` handoff block if control passes to Codex; do not accept bare `ok` as a substitute | `5.4 mini` | `low` | one draft spec only, locked decision source if needed | Cheap cleanup step; block on missing or unclear draft and do not invent content. | `UPDATED` |
| `janus-spec-review` | ChatGPT | Review one feature spec for completeness, determinism, and task-readiness without inventing product decisions. | Before task compilation when a spec must be approved, revised, or blocked. | `janus-spec-to-task` on `APPROVED`; otherwise `janus-spec-generator` or `janus-feature-design` | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` approval or block handoff; do not accept bare `ok` as a substitute | `5.4` | `medium` | one feature spec only, targeted source note if needed | Keep to one spec; block on missing product decisions and avoid broad repo context. | `UPDATED` |
| `janus-spec-to-task` | ChatGPT | Compile one approved feature spec into deterministic task artifacts without inventing scope or decisions. | After spec review when execution tasks must be produced. | `janus-task-breakdown` on valid task artifacts; otherwise `janus-spec-review` or `janus-spec-generator` | `ChatGPT -> Codex` | ja | model/reasoning header plus exactly one compact `text` task-compilation handoff; do not accept bare `ok` as a substitute | `5.4` | `medium` | one approved feature spec only, optional backlog identity | Approved-spec-only compiler step; block on missing approval evidence and keep output deterministic for task-breakdown. | `UPDATED` |
| `janus-task-breakdown` | Shared | Refine one compiled task artifact or clear backlog handoff into exactly one precheck-ready target task. | After task compilation or backlog handoff when one implementation slice must be released. | `janus-preimplementation-check` on a valid target task; otherwise `janus-spec-to-task` or `janus-backlog-handoff` | `ChatGPT -> Codex` or `Codex -> Codex` | ja | exactly one compact fenced `text` target-task handoff block; do not accept bare `ok` as a substitute | `5.4` | `medium` | one task artifact or clear backlog handoff, source spec, one selected target task | Keep to one target task only; block on multiple plausible targets or unclear artifact identity. | `UPDATED` |
| `janus-test-pipeline` | Codex | Route TestSpec, TestPlan, TestRun, live execution, and retest evidence work without mixing testing and implementation context. | For deterministic testing work starting from `documentation/TEST_SPEC/`, `documentation/test-runs/`, or `documentation/test-results/`. | `janus-final-audit` on passing evidence; otherwise `janus-debug` or caller review | `Codex -> ChatGPT` or `Codex -> Codex` | ja | compact evidence-first fenced `text` block on actor/chat boundary; do not accept bare `ok` as a substitute | `5.4` | `medium` | one test-artifact bundle: TestSpec/TestPlan/TestRun/TestResult | Keep testing artifact-bound; block on unclear evidence or missing plan/run identity instead of improvising execution. | `UPDATED` |

## Review Queue

Initial review order for later targeted skill review:

1. `janus-skill-router`
2. `janus-documentation-update`
3. `janus-git-governance`
4. `janus-backlog-handoff`
5. `janus-preimplementation-check`
6. `janus-executioner`
7. `janus-final-audit`
8. `janus-feature-design`
9. `janus-spec-generator`
10. `janus-spec-review`
11. `janus-task-breakdown`
12. `janus-test-pipeline`
13. `janus-build-release`
14. `janus-debug`
15. `janus-quickchange`
16. `janus-backlog-prioritization`
17. `janus-backlog-intake`
18. `janus-spec-normalizer`
19. `janus-spec-to-task`
20. `janus-health-check`
21. `codex-audit-package-builder`
22. `codex-start-of-work-check`

Current status:

- all repo skills listed above are inventoried
- reviewed so far: `janus-skill-router`, `janus-documentation-update`, `janus-git-governance`, `janus-backlog-handoff`, `janus-preimplementation-check`, `janus-quickchange`, `janus-executioner`, `janus-final-audit`, `janus-feature-design`, `janus-spec-generator`, `janus-spec-normalizer`, `janus-spec-review`, `janus-spec-to-task`, `janus-task-breakdown`, `janus-test-pipeline`, `janus-debug`, `janus-build-release`, `janus-backlog-intake`, `janus-backlog-prioritization`
- no repo skill source was modified while creating this matrix

## Open Decisions

- Should `janus-final-audit` always use a fresh ChatGPT audit for release-critical work, or allow same-context Codex audit when evidence is compact and low risk?
- Should `janus-git-governance` also define a canonical compact approval block for commit/push/release asks, or keep only the shared boundary rule?
- Should `janus-documentation-update` and `janus-backlog-handoff` share one exact copy-box template to reduce handoff variance, or should backlog handoff stay slightly more routing-specific?
- Should `codex-start-of-work-check` stay purely reminder-only, or emit a minimal repo-skill collaboration reminder block when a new Janus chat starts?
