# OR Real-Life Test Matrix

Stand: `2026-06-28`

Zweck: schlanke Arbeitsmatrix fuer die naechsten echten OR-Alltagslaeufe auf den bereits bestaetigten `OR_PROPOSAL_FIRST`-Lanes. Fokus ist nicht weitere Grundsatzplanung, sondern eine ehrliche Reihenfolge fuer produktionsnahe Tests unter Codex-owned Finalentscheidung.

## Matrix

| Skill | Current OR seam | Preferred model/path | Best current evidence | Actual cost signal | Current confidence read | Live-test priority | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `janus-executioner` | bounded direct patch candidate, then Codex review/apply decision | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-EXEC-EVERYDAY-OR-2026-06-28` | `0.00063384` | high | `P1` | strongest direct worker seam; already produces reviewable bounded patch candidate with healthcheck PASS |
| `janus-spec-normalizer` | bounded normalized spec draft, then Codex local final write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-NORMALIZER-LIVE-REPEAT-2026-06-26` | `0.00018921` | high | `P1` | cheap, repeated live evidence, very good early everyday lane |
| `janus-feature-design` | bounded decision-summary draft or blocking question, then Codex final decision | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-FEATURE-DESIGN-CURRENT-002` | `0.00031` | medium-high | `P1` | good candidate for real everyday quota savings before implementation even starts |
| `janus-task-breakdown` | bounded single-target handoff draft, then Codex final handoff write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-TASK-BREAKDOWN-FIXTURE-CHECK-2026-06-26` | `0.00017092` | medium-high | `P2` | very cheap and clean, but still one step removed from code-changing work |
| `janus-spec-generator` | bounded structured spec draft, then Codex local final write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-GEN-CURRENT-002` | `0.00071` | medium | `P2` | useful and real, but more expensive than normalizer/feature-design and still draft-only |
| `janus-quickchange` | accepted-source write-apply derivative under bounded acceptance | accepted evidence path; patch-review side prefers `qwen/qwen3-coder-30b-a3b-instruct` | `WF-QUICKCHANGE-WRITE-APPLY-CURRENT-005` | current-shape proof has no fresh direct cost row at accepted-source layer | medium | `P2` | strategically important because it touches real tiny writes, but next live test should be a deliberately tiny real change |
| `janus-spec-to-task` | bounded task-compilation draft, then Codex final task write | `qwen/qwen3-coder-30b-a3b-instruct` | `WF-SPEC-TO-TASK-FIXTURE-CHECK-2026-06-26` | `0.00068685` | medium | `P3` | valid lane, but cost is relatively high for a still-draft artifact and should come after cheaper wins |

## Short reading

- `P1` should be the first real-life wave: `janus-executioner`, `janus-spec-normalizer`, `janus-feature-design`.
- `P2` is the second wave: `janus-task-breakdown`, `janus-spec-generator`, `janus-quickchange`.
- `P3` currently only contains `janus-spec-to-task`, because its seam is valid but not especially cheap for a draft-only step.

## Next practical move

1. Start with one bounded real-life run on `janus-spec-normalizer` or `janus-feature-design` for a cheap everyday proof.
2. Keep `janus-executioner` as the highest-value workhorse lane when the next bounded implementation slice appears.
3. Use `janus-quickchange` for the first tiny real write path after one explicit, harmless change target is bound.
