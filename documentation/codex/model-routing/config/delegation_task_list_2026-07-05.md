# Delegation Task List - Documentation, Quickchange, Health-Check, Feature-Design, Spec-Generator, Spec-Normalizer, Spec-Review, Spec-To-Task, Task-Breakdown, Preimplementation-Check, Executioner, Debug, Test-Pipeline

**Date:** 2026-07-07
**Manifest:** `documentation/codex/model-routing/config/delegation_routing_manifest.json`  
**Machine-readable list:** `documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json`

Operator gate by default:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

Codex shows the recommendation from the manifest-backed gate. Operator may override unless `operator_override_allowed: false`.
Task-specific option labels can narrow this generic gate. Current important exceptions:

- `TASK-DBG-002`: visible gate is effectively `1 = Codex / 3 = Cursor Composer`; OpenRouter is intentionally hidden for this bounded repro/shell lane
- `TASK-EX-002`: visible option `2` is `Deterministic Apply` rather than OpenRouter

---

## Quick routing table

| Task ID | Skill | What | Recommend | Cursor model | OR model |
| --- | --- | --- | --- | --- | --- |
| TASK-DU-001 | janus-documentation-update | Dokumentations-Draft helper | **Cursor API** | gpt-5.4-mini-medium | gpt-5.4-sidecar |
| TASK-QC-001 | janus-quickchange | Tiny Patch-Review planen | **Cursor API** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-BH-001 | janus-backlog-handoff | Handoff review | **Cursor API** | glm-5.2-high | qwen3-coder-30b |
| TASK-HC-001 | janus-health-check | Daily-Healthcheck deuten | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-FD-001 | janus-feature-design | Decision Summary konsolidieren | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-SG-001 | janus-spec-generator | Locked Spec-Draft review | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-SN-001 | janus-spec-normalizer | Draft-Spec mechanisch normalisieren | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-SR-002 | janus-spec-review | Finalisierten Spec reviewen | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-ST-001 | janus-spec-to-task | Task-Draft aus Spec ableiten | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-TB-001 | janus-task-breakdown | Einen Target-Task verfeinern | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-PC-001 | janus-preimplementation-check | Precheck-Paket reviewen | **OR** | gpt-5.4-mini-medium | qwen3-coder-30b |
| TASK-DBG-001 | janus-debug | Hypothesen ranken | **OR** | glm-5.2-high | qwen3-coder-30b |
| TASK-DBG-002 | janus-debug | Repro + Debug mit Tools | **Cursor Composer** | composer-2.5 | - |
| TASK-TP-001 | janus-test-pipeline | TestSpec -> TestPlan | **Codex** | - | - |
| TASK-TP-002 | janus-test-pipeline | Generator review | **OR** | gpt-5.4-mini-medium | gpt-oss-20b |
| TASK-TP-003 | janus-test-pipeline | Fixture schreiben + Checks | **Cursor Composer** | composer-2.5 | qwen3-coder-30b |
| TASK-TP-004 | janus-test-pipeline | Live Playwright | **Codex** | - | - |
| TASK-TP-005 | janus-test-pipeline | Failure triage | **OR** | glm-5.2-high | qwen3-coder-30b |
| TASK-TP-006 | janus-test-pipeline | Retest audit | **Codex** | - | - |
| TASK-EX-001 | janus-executioner | Patch vorschlagen | **Cursor Composer** | composer-2.5 | qwen3-coder-30b |
| TASK-EX-002 | janus-executioner | Accepted patch apply | **Deterministic Apply** | deterministic_local_apply | - |
| TASK-EX-003 | janus-executioner | Validation + completion | **Codex** | - | - |

---

## Typical flows

### Health-check flow

```text
1. TASK-HC-001  ->  2=OR            Read-only Daily-Interpretation
2. Codex lokal  ->  final hygiene judgement / next skill
```

### Feature-design flow

```text
1. TASK-FD-001  ->  2=OR            Bounded Decision-Summary-Review
2. Codex lokal  ->  final summary / next skill owner
```

### Quickchange flow

```text
1. TASK-QC-001  ->  4=Cursor API    Tiny bounded Patch-Review planen
2. Codex lokal  ->  final validation / accept-reject / local apply
```

### Spec-generator flow

```text
1. TASK-SG-001  ->  2=OR            Locked Spec-Draft review
2. TASK-SN-001  ->  2=OR            Draft-Spec mechanisch normalisieren
3. Codex lokal  ->  final spec write / next skill owner
```

### Spec review / compile flow

```text
1. TASK-SN-001  ->  2=OR            Draft-Spec mechanisch normalisieren
2. TASK-SR-002  ->  2=OR            Finalisierten Spec reviewen
3. TASK-ST-001  ->  2=OR            Task-Draft aus approved Spec ableiten
4. TASK-TB-001  ->  2=OR            Einen Target-Task fuer Precheck verfeinern
5. TASK-PC-001  ->  2=OR            Precheck-Paket reviewen
6. Codex lokal  ->  final precheck decision / next skill owner
```

### Debug flow

```text
1. TASK-DBG-001  ->  2=OR (qwen)     Hypothesen sortieren
2. TASK-DBG-002  ->  3=Cursor        Repro, Logs, bounded Fix-Vorschlag
3. Codex lokal   ->  Validation, janus-final-audit handoff
```

Hinweis: `TASK-DBG-002` bleibt absichtlich bei `1 = Codex / 3 = Cursor Composer`. OpenRouter ist fuer diese bounded Repro-/Shell-Lane aktuell nicht als sichtbare Option aktiviert.

### Test-pipeline flow

```text
1. TASK-TP-001  ->  Codex           Compiler (deterministisch)
2. TASK-TP-002  ->  2=OR            Generator review (optional)
3. TASK-TP-003  ->  3=Cursor        Fixture/Helper + allowlisted checks
4. TASK-TP-004  ->  Codex           Live test nach OK START LIVE TEST
5. TASK-TP-005  ->  2=OR            Failure triage bei grossem Bundle
6. TASK-TP-006  ->  Codex           Retest audit / PASS BLOCKED
```

### Execution flow

```text
1. TASK-EX-001  ->  3=Cursor        Patch proposal
   (Alternative: 2=OR qwen proposal-first, 4=Cursor API kimi; if ROI is slightly negative, Codex may still be the recommendation while bounded external options remain visible as fallback capacity on this lane)
2. Codex review ->  accept/reject
3. TASK-EX-002  ->  2=Deterministic Apply  bounded local apply (wenn accepted)
4. TASK-EX-003  ->  Codex           validation + completion claim
```

---

## Model cheat sheet

| Cursor | Wann |
| --- | --- |
| `gpt-5.4-mini-medium` | Assist-only Drafts, Reviews, Quickchange-Review |
| `glm-5.2-high` | Kurze Handoff- und Triage-Reviews |
| `composer-2.5` | Code, Tests, Debug-Repro, Execution |
| `kimi-k2.7-code` | Cursor-API Code-Proposals |

| OpenRouter | Wann |
| --- | --- |
| `qwen/qwen3-coder-30b-a3b-instruct` | Default fuer bounded Assist- und Proposal-Fallbacks |
| `openai/gpt-oss-20b` | Generator review |
| `codex-cli/gpt-5.4-read-only-sidecar` | Dokumentations-Draft Fallback in der bestehenden Dispatcher-Kette |

---

## Codex usage

At session start, tell Codex:

```text
Use delegation task list:
documentation/codex/model-routing/config/delegation_task_list_2026-07-05.json

For each bounded task, show the manifest-backed cost-aware gate with 1=Codex / 2=OpenRouter / 3=Cursor Composer / 4=Cursor API where applicable. Invoke janus_delegate.py and keep EX-002 as 2=Deterministic Apply.
```

Per task, Codex should:

1. Match work to `task_id` or `lane_id`
2. Show gate with recommendation
3. Wait for operator choice (or accept recommendation)
4. Delegate with correct model from the manifest-backed choice
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

Hinweis: `execution_patch_candidate` darf trotz knapp negativer ROI bounded externe Optionen sichtbar halten, wenn die Lane technisch freigegeben ist und die Sichtbarkeit als alternative Arbeitskapazitaet dient. In diesem Fall bleibt `Codex` die kostenoptimierte Empfehlung, aber die Shared-Gate-Policy versteckt Cursor/OpenRouter nicht mehr automatisch.
| execution_write_apply_candidate | 12000 |

---

## Never delegate

- `live_test_execution` (needs `OK START LIVE TEST`)
- `diamond_retest_audit`
- `EXECUTION_VALIDATION` / final completion claim
- `TESTSPEC_TO_TEST_PLAN` compiler step
- Git, release, final audit PASS
