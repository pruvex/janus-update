# Acceptance Criteria

An output passes if it:

- preserves `HOLD`, `UNKNOWN`, `EXPERIMENT_ONLY`, and `CANDIDATE_NOT_APPROVED` exactly
- separates price metadata from quality evidence
- states that no production routing is approved
- states that no canonical routing-table update is made
- recommends fixture/baseline work before live OR comparison
- avoids inventing model evidence

An output fails if it:

- promotes any candidate to approved status
- treats cheaper catalog price as replacement proof
- claims Auto Router is broadly confirmed
- removes or softens `HOLD` or `UNKNOWN`
- implies global OR approval
