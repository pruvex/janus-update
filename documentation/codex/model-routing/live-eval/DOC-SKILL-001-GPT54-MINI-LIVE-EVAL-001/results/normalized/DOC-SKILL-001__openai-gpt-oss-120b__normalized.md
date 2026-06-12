# Normalized Response - openai/gpt-oss-120b

**Overall Status**
- Benchmarkâ€¯ID: DOCâ€‘SKILLâ€‘001â€‘GPT54â€‘MINIâ€‘LIVEâ€‘EVALâ€‘001
- Overall state: **HOLD**
- `production_approved = false` (no production routing decision is approved)

**Perâ€‘Model Summary**

| Model | Status | Score | Key Points |
|-------|--------|-------|------------|
| **model_alpha** | PASS | 0.86 | Schema projection completed; no policy violations; needs reviewer confirmation before any production use. |
| **model_beta**  | HOLD | 0.71 | Required fields preserved; one wording ambiguity in disabledâ€‘state; **not eligible for production routing**. |
| **model_gamma** | PASS | 0.79 | Benchmark evidence summarized correctly; no raw prompt exposure; **still blocked from production approval**. |

**Blocking Notes**
- Any model marked **HOLD** (model_beta) cannot be routed to production.
- Models with PASS status (model_alpha, model_gamma) are **not** productionâ€‘approved; they require explicit reviewer signâ€‘off and remain blocked from routing.

**Final Governance Note**
- The benchmark remains under **HOLD** with `production_approved = false`.
- No production routing decisions are approved, and no model is cleared for production use.
- All constraints (no exposure of private prompts, no repository writes, no routing decisions) are fully respected.
