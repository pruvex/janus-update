# TASK-INTENT-M2.1 Confidence Routing Proof

Generated at: `2026-07-08T14:59:31+00:00`

## Baseline Parity

- Checked-in baseline: `C:\KI\Janus-Projekt\documentation\test-runs\INTENT_BENCHMARK_BASELINE.md`
- Legacy current accuracy: `73.6%`
- Baseline reference accuracy: `73.6%`
- Flag-off parity: `PASS`

## M2.1 Proof Summary

- Baseline overall: `81/110` (`73.6%`)
- Confidence-routing proof overall: `91/110` (`82.7%`)

## Required Subset Delta

| Subset | Baseline | M2.1 Proof | Delta (pp) |
| --- | ---: | ---: | ---: |
| contact | 55.0% | 95.0% | +40.0 |
| pet | 53.3% | 73.3% | +20.0 |
| recall | 80.0% | 80.0% | +0.0 |
| calendar | 53.3% | 66.7% | +13.4 |

## Latency

- P50 aux path latency: `2.73 ms`
- P95 aux path latency: `3.57 ms`
- Max aux path latency: `4.78 ms`

## Exit Gates

- Calendar false-ambiguity reduction: `PASS`
- Memory-routing uplift (contact/pet/recall): `PASS`
- P95 latency < 400 ms: `PASS`
- Flag-off parity: `PASS`

## Notes

- This M2.1 proof stays local and deterministic: no live provider calls are required.
- The benchmark measures confidence-routing behavior only; no transport or product-openrouter changes are involved.
