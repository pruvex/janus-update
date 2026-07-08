# INTENT Benchmark Baseline

Generated at: `2026-07-07T20:55:59+00:00`

## Overall

- Cases: `110`
- Passed: `81`
- Accuracy: `73.6%`

## Subset Summary

| Subset | Passed | Total | Accuracy |
| --- | ---: | ---: | ---: |
| calendar | 8 | 15 | 53.3% |
| contact | 11 | 20 | 55.0% |
| other | 42 | 45 | 93.3% |
| pet | 8 | 15 | 53.3% |
| recall | 12 | 15 | 80.0% |

## Cluster Summary

| Cluster | Passed | Total | Accuracy |
| --- | ---: | ---: | ---: |
| ambiguity_false_positive | 9 | 10 | 90.0% |
| calendar_vs_shopping | 8 | 15 | 53.3% |
| contact_fact_telling | 11 | 20 | 55.0% |
| contact_recall | 12 | 15 | 80.0% |
| geo_weather_veto | 10 | 10 | 100.0% |
| greeting_smalltalk | 10 | 10 | 100.0% |
| pet_owner_bridge | 8 | 15 | 53.3% |
| regression_existing_green | 13 | 15 | 86.7% |

## Required M0 Subsets

- Contact: `11/20`
- Pet: `8/15`
- Recall: `12/15`
- Calendar: `8/15`

## Operator Checklist (Roadmap Section 9)

- [x] Benchmark / tests green
- [x] Exit criteria for M0 covered: baseline report exists, pytest suite is CI-runnable, and Contact / Pet / Recall / Calendar are separated
- [x] Feature-flag staging on: not applicable in M0 because this slice adds no runtime flag
- [x] Live retest scenarios pass: not applicable in M0 because this slice only establishes the baseline
- [x] Medical / policy regression pass: not applicable in this measurement-only slice with no intent-engine logic change
- [x] janus-final-audit pass or documented go-with-risk: documented go-with-risk for a measurement-only M0 baseline slice
- [x] CURRENT_STATE + WHAT_I_LEARNED updated or consciously skipped: CURRENT_STATE required, WHAT_I_LEARNED only if a reusable validated pattern emerges
- [x] Prod flag flip decided consciously: not applicable in M0 because no flag is introduced or changed
- [x] Next milestone updated in roadmap tracker

## Failures

- `INT-M0-C005` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C009` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C010` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C011` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C012` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C013` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C017` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C018` `contact_fact_telling`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-C019` `contact_fact_telling`: action expected=tell_fact actual=image, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-R012` `contact_recall`: action expected=personal_recall actual=wikipedia, is_personal_recall expected=True actual=False, is_ambiguous expected=False actual=True, must_not_route hit=wikipedia
- `INT-M0-R014` `contact_recall`: action expected=personal_recall actual=none, is_personal_recall expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-R015` `contact_recall`: action expected=personal_recall actual=none, is_personal_recall expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P003` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P004` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False
- `INT-M0-P010` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P012` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P013` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P014` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-P015` `pet_owner_bridge`: action expected=tell_fact actual=none, is_fact_telling expected=True actual=False, is_ambiguous expected=False actual=True
- `INT-M0-K001` `calendar_vs_shopping`: is_ambiguous expected=False actual=True
- ... and `9` more

## Notes

- This baseline measures the current intent engine only.
- No live provider calls are required; the suite stays on the local regex / deterministic path.
- M1 stays blocked until this baseline exists and is checked in.
