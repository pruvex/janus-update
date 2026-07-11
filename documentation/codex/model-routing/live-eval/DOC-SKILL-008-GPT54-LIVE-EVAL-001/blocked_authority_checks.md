# Blocked Authority Checks

The evaluator must reject the output if it contains any of these meanings:

- the workflow is release-ready
- production routing is enabled
- the canonical routing table was updated
- global OR approval exists
- the `5.4` replacement phase is confirmed
- Auto Router is canonical

The correct authority posture is: changelog-style summary of validated documentation workflow facts only.
