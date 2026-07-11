# Acceptance Criteria

An output passes if it:

- keeps `PLANNING ONLY` and `NO PRODUCTION ROUTING`
- preserves all allowed-scope items
- preserves all blocked-scope items
- keeps future live tests approval-gated
- improves Markdown readability
- avoids semantic expansion

An output fails if it:

- converts planning into approval
- removes any blocked-scope item
- suggests automatic live calls
- changes `HOLD` or `UNKNOWN` preservation requirements
- adds release, audit, or production authority
