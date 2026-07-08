# TASK-INTENT-M1.3 Benchmark Uplift Proof

Generated at: `2026-07-08T13:14:10+00:00`

## Baseline Parity

- Checked-in baseline: `C:\KI\Janus-Projekt\documentation\test-runs\INTENT_BENCHMARK_BASELINE.md`
- Legacy current accuracy: `73.6%`
- Baseline reference accuracy: `73.6%`
- Flag-off parity: `PASS`

## M1.3 Proof Summary

- Baseline overall: `81/110` (`73.6%`)
- Auxiliary proof overall: `91/110` (`82.7%`)

## Required Subset Delta

| Subset | Baseline | M1.3 Proof | Delta (pp) |
| --- | ---: | ---: | ---: |
| contact | 55.0% | 90.0% | +35.0 |
| pet | 53.3% | 73.3% | +20.0 |
| recall | 80.0% | 80.0% | +0.0 |
| calendar | 53.3% | 53.3% | +0.0 |

## Latency

- P50 aux path latency: `2.67 ms`
- P95 aux path latency: `4.09 ms`
- Max aux path latency: `18.16 ms`

## Exit Gates

- Contact/Pet/Recall +12 pp gate: `FAIL`
- Calendar regression gate unchanged/green: `PASS`
- P95 latency < 400 ms: `PASS`
- Flag-off parity: `PASS`

## Notes

- This M1.3 proof stays local and deterministic: no live provider calls are required.
- The auxiliary proof path uses the integrated M1 classifier seam with a deterministic benchmark provider so the benchmark remains CI-runnable and reproducible.
- Final audit must still decide whether any remaining shortfall is acceptable or whether M1.3 stays blocked with evidence.
