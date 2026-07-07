# Delegation Task List — Documentation, Quickchange, Health-Check, Feature-Design, Spec-Generator, Spec-Normalizer, Spec-Review, Spec-To-Task, Task-Breakdown, Preimplementation-Check, Executioner, Debug, Test-Pipeline

**Date:** 2026-07-05  
**Manifest:** `documentation/codex/model-routing/config/delegation_routing_manifest.json`  
**Machine-readable list:** `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json`

Operator gate everywhere:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Codex shows the recommendation from this list. Operator may override unless `operator_override_allowed: false`.
Task-specific option labels can narrow this generic gate; the main current exception is `TASK-EX-002`, where visible option `2` is `Deterministic Apply` rather than Cursor.

---

## Quick routing table

| Task ID | Skill | What | Recommend | Cursor model | OR model |
| --- | --- | --- | --- | --- | --- |
| TASK-DU-001 | janus-documentation-update | Dokumentations-Draft helper | **OR** | auto | gpt-5.4-sidecar |
| TASK-QC-001 | janus-quickchange | Tiny Patch-Review planen | **OR** | — | qwen3-coder-30b |
| TASK-HC-001 | janus-health-check | Daily-Healthcheck deuten | **OR** | auto | qwen3-coder-30b |
| TASK-FD-001 | janus-feature-design | Decision Summary konsolidieren | **OR** | auto | qwen3-coder-30b |
| TASK-SG-001 | janus-spec-generator | Locked Spec-Draft review | **OR** | auto | qwen3-coder-30b |
| TASK-SN-001 | janus-spec-normalizer | Draft-Spec mechanisch normalisieren | **OR** | auto | qwen3-coder-30b |
| TASK-SR-002 | janus-spec-review | Finalisierten Spec reviewen | **OR** | auto | qwen3-coder-30b |
| TASK-ST-001 | janus-spec-to-task | Task-Draft aus Spec ableiten | **OR** | auto | qwen3-coder-30b |
| TASK-TB-001 | janus-task-breakdown | Einen Target-Task verfeinern | **OR** | auto | qwen3-coder-30b |
| TASK-PC-001 | janus-preimplementation-check | Precheck-Paket reviewen | **OR** | auto | qwen3-coder-30b |
| TASK-DBG-001 | janus-debug | Hypothesen ranken | **OR** | auto | qwen3-coder-30b |
| TASK-DBG-002 | janus-debug | Repro + Debug mit Tools | **Cursor** | composer-2.5 | — |
| TASK-TP-001 | janus-test-pipeline | TestSpec → TestPlan | **Codex** | — | — |
| TASK-TP-002 | janus-test-pipeline | Generator review | **OR** | auto | gpt-oss-20b |
| TASK-TP-003 | janus-test-pipeline | Fixture schreiben + Checks | **Cursor** | composer-2.5 | kimi-k2.5 |
| TASK-TP-004 | janus-test-pipeline | Live Playwright | **Codex** | — | — |
| TASK-TP-005 | janus-test-pipeline | Failure triage | **OR** | auto | qwen3-coder-30b |
| TASK-TP-006 | janus-test-pipeline | Retest audit | **Codex** | — | — |
| TASK-EX-001 | janus-executioner | Patch vorschlagen | **Cursor** | composer-2.5 | kimi-k2.5 |
| TASK-EX-002 | janus-executioner | Accepted patch apply | **Deterministic Apply** | deterministic_local_apply | — |
| TASK-EX-003 | janus-executioner | Validation + completion | **Codex** | — | — |

---

## Typical flows

### Health-check flow

```text
1. TASK-HC-001  →  3=OR            Read-only Daily-Interpretation
2. Codex lokal  →  final hygiene judgement / next skill
```

### Feature-design flow

```text
1. TASK-FD-001  →  3=OR            Bounded Decision-Summary-Review
2. Codex lokal  →  final summary / next skill owner
```

### Quickchange flow

```text
1. TASK-QC-001  →  3=OR            Tiny bounded Patch-Review planen
2. Codex lokal  →  final validation / accept-reject / local apply
```

### Spec-generator flow

```text
1. TASK-SG-001  →  3=OR            Locked Spec-Draft review
2. TASK-SN-001  →  3=OR            Draft-Spec mechanisch normalisieren
3. Codex lokal  →  final spec write / next skill owner
```

### Spec review / compile flow

```text
1. TASK-SN-001  →  3=OR            Draft-Spec mechanisch normalisieren
2. TASK-SR-002  →  3=OR            Finalisierten Spec reviewen
3. TASK-ST-001  →  3=OR            Task-Draft aus approved Spec ableiten
4. TASK-TB-001  →  3=OR            Einen Target-Task fuer Precheck verfeinern
5. TASK-PC-001  →  3=OR            Precheck-Paket reviewen
6. Codex lokal  →  final precheck decision / next skill owner
```

### Debug flow

```text
1. TASK-DBG-001  →  3=OR (qwen)     Hypothesen sortieren
2. TASK-DBG-002  →  2=Cursor        Repro, Logs, bounded Fix-Vorschlag
3. Codex lokal   →  Validation, janus-final-audit handoff
```

### Test-pipeline flow

```text
1. TASK-TP-001  →  Codex           Compiler (deterministisch)
2. TASK-TP-002  →  3=OR            Generator review (optional)
3. TASK-TP-003  →  2=Cursor        Fixture/Helper + allowlisted checks
4. TASK-TP-004  →  Codex           Live test nach OK START LIVE TEST
5. TASK-TP-005  →  3=OR            Failure triage bei großem Bundle
6. TASK-TP-006  →  Codex           Retest audit / PASS BLOCKED
```

### Execution flow

```text
1. TASK-EX-001  →  2=Cursor        Patch proposal
   (Alternative: 3=OR kimi proposal-first)
2. Codex review →  accept/reject
3. TASK-EX-002  →  2=Deterministic Apply  bounded local apply (wenn accepted)
4. TASK-EX-003  →  Codex           validation + completion claim
```

---

## Model cheat sheet

| Cursor | Wann |
| --- | --- |
| `auto` | Triage, kleine Reviews, Assist-only |
| `composer-2.5` | Code, Tests, Debug-Repro, Execution |

| OpenRouter | Wann |
| --- | --- |
| `qwen/qwen3-coder-30b-a3b-instruct` | Beste aktuelle Default-Wahl fuer `spec_normalizer_review` und `precheck_review`; bei `spec_review` nur fuer substanzielle REVIEW_ONLY-Pakete |
| `openai/gpt-oss-20b` | Generator review |
| `moonshotai/kimi-k2.5` | Proposal-first patches, test fixture (Aider) |
| `deepseek/deepseek-v4-flash` | Nicht mehr fuer TASK-EX-002 priorisieren; OR bleibt Proposal-/Assist-Lane |

---

## Codex usage

At session start, tell Codex:

```text
Use delegation task list:
documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json

For each bounded task, show 1=Codex / 2=Cursor / 3=OR with the recommended backend from the task list. Invoke janus_delegate.py when implemented; until then use the lane-specific runners from the manifest.
```

Per task, Codex should:

1. Match work to `task_id` or `lane_id`
2. Show gate with recommendation
3. Wait for operator choice (or accept recommendation)
4. Delegate with correct model from `models` block
5. Review normalized result before accept

---

## ROI thresholds (hide external options when below)

| Lane | Min net saved tokens |
| --- | ---: |
| documentation_draft_review | 3000 |
| quickchange_patch_review | 3000 |
| health_check_review | 5000 |
| feature_design_review | 5000 |
| spec_generator_review | 5000 |
| spec_normalizer_review | 5000 |
| spec_review | 8000 |
| spec_to_task_review | 5000 |
| task_breakdown_review | 5000 |
| precheck_review | 5000 |
| debug_hypothesis_review | 5000 |
| debug_repro_investigation | 8000 |
| generator_review | 3000 |
| test_fixture_worker | 8000 |
| test_result_triage_review | 8000 |
| execution_patch_candidate | 10000 |
| execution_write_apply_candidate | 12000 |

---

## Never delegate

- `live_test_execution` (needs `OK START LIVE TEST`)
- `diamond_retest_audit`
- `EXECUTION_VALIDATION` / final completion claim
- `TESTSPEC_TO_TEST_PLAN` compiler step
- Git, release, final audit PASS
