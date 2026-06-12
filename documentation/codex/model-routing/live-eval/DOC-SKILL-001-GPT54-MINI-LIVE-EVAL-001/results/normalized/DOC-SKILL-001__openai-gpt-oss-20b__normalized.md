# Normalized Response - openai/gpt-oss-20b

**1. Overall status**
- Benchmark result: **HOLD**
- Production approval: **false** (no models approved for production use)

**2. Perâ€‘model summary**

| Model | Status | Score | Notes |
|-------|--------|-------|-------|
| model_alpha | PASS | 0.86 | Completed schema projection; no policy violations; requires reviewer confirmation before production use |
| model_beta | HOLD | 0.71 | Output preserved required fields; one ambiguity in disabledâ€‘state wording; not eligible for production routing |
| model_gamma | PASS | 0.79 | Summarized benchmark evidence correctly; no raw prompt exposure; still blocked from production approval |

**3. Blocking notes**
- model_beta remains on HOLD and is explicitly not eligible for production routing.
- All models are blocked from production approval; no routing decisions are made.

**4. Final governance note**
- The benchmark is scoped to DOCâ€‘SKILLâ€‘001 only.
- No production routing decisions, approvals, or repository changes are made.
- Raw private prompts are not exposed or invented.
- The overall HOLD status and PASS entries are preserved as specified.
