# Normalized Response - openai/gpt-oss-20b

**1. Overall status**
- HOLD

**2. Perâ€‘model scoring summary**
| Model | Score | Status | Routing State | Disabled | Notes |
|-------|-------|--------|---------------|----------|-------|
| model_alpha | 88 | PASS | HOLD | No | Met schema & preservation; repeatability confirmation pending |
| model_beta | â€“ | UNKNOWN | HOLD | Yes | Disabled â€“ missing repeatability evidence; not scored as PASS |
| model_gamma | 74 | HOLD | HOLD | No | Partial preservation of disabledâ€‘state wording; no production activation |

**3. Disabled / UNKNOWN / HOLD notes**
- `model_beta` remains **disabled** (reason: missing repeatability evidence) and its status is **UNKNOWN**; it is **not** treated as PASS.
- `model_gamma` is **HOLD**; no production activation is allowed.
- All models have a routing state of **HOLD**; no routing approval is granted.

**4. Final governance note**
- `production_approved = false`
- `routing_approved = false`
- No routing decisions, no policy overrides, and no production activation are made.
