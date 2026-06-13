# Normalized Response - openai/gpt-oss-120b

**1. Overall status**
- **HOLD** (as indicated in the report).

**2. Perâ€‘model scoring summary**

| Model | Score | Status | Routing state | Disabled | Notes |
|-------|-------|--------|---------------|----------|-------|
| **model_alpha** | 88 | PASS | HOLD | No | Met schema & preservation checks; repeatability confirmation still required before any routing discussion. |
| **model_beta** | â€“ (no score) | **UNKNOWN** | HOLD | **Yes** (disabled) â€“ missing repeatability evidence. | Do not treat as PASS; disabled state must be preserved. |
| **model_gamma** | 74 | **HOLD** | HOLD | No | Partial preservation of disabledâ€‘state wording; no production activation allowed. |

**3. Disabled / UNKNOWN / HOLD notes**
- **model_beta** is **disabled = true** and its status remains **UNKNOWN**; it must not be marked PASS.
- **model_gamma** remains in **HOLD** status.
- The overall report is in **HOLD**; no change to this state is permitted.

**4. Final governance note**
- **production_approved = false** â€“ production use must not be activated.
- **routing_approved = false** â€“ routing cannot be approved.
- No routing approval, policy override, or production activation is performed.
- No private evidence is interpreted (the report contains none).

All required HOLD, UNKNOWN, and disabled states are preserved per the DOCâ€‘SKILLâ€‘002 constraints.
