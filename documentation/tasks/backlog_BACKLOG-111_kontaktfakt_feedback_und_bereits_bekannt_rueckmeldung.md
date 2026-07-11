BACKLOG-111
- Backlog Item: `BACKLOG-111`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-10

## Task

### BACKLOG-111 Kontaktfakt-Write-Feedback und Bereits-bekannt-Rueckmeldung haerten
- Ziel:
  - Stelle sicher, dass neue klare Kontaktfakten nach erfolgreicher lokaler Speicherung mit einer passenden Vermerk-/Speicherbestaetigung quittiert werden und dass erneut genannte bereits bekannte Kontaktfakten als bereits bekannt erkannt und entsprechend bestaetigt werden.
- Scope:
  - Touch only the existing chat-orchestration, response fallback, duplicate-detection, and contact-fact write feedback seams needed to fix the wrong confirmation behavior for local contact facts.
  - Keep the change bounded to confirmed local contact facts and duplicate acknowledgement.
  - Do not redesign provider selection, broader fact extraction, or the address-book data model.
- Files:
  - `backend/services/orchestrator/execution_engine.py`
  - `backend/services/orchestrator/response_finalizer.py`
  - `backend/services/contact_manager.py`
  - `backend/tools/memory_tools.py`
  - `backend/tests/test_provider_auth_fallback.py`
  - `backend/tests/test_contact_manager.py`
  - additional tightly related regression file only if strictly needed
- Steps:
  1. Trace why a successfully stored local contact fact can still yield a sources blocker or clarification-style response instead of a save confirmation.
  2. Ensure new clear local contact facts produce a concise confirmation such as local memory/address-book acknowledgement.
  3. Add bounded duplicate detection so re-mentioning the same known contact fact yields an already-known style response instead of re-saving or source-blocking.
  4. Add focused regression coverage for both new-fact confirmation and already-known repetition behavior.
- Acceptance Criteria:
  - New clear contact facts that are locally stored receive a matching save/remember confirmation instead of a sources blocker or unnecessary clarification.
  - Repeated already-known contact facts are recognized and answered with an already-known style acknowledgement.
  - The behavior remains limited to locally confirmed contact facts and does not over-confirm ambiguous statements.
- Tests:
  - `python -m pytest backend/tests/test_provider_auth_fallback.py -q`
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m py_compile backend/services/orchestrator/execution_engine.py backend/services/orchestrator/response_finalizer.py backend/services/contact_manager.py backend/tools/memory_tools.py backend/tests/test_provider_auth_fallback.py backend/tests/test_contact_manager.py`
- Model: 5.4
- Reason:
  - Small, bounded UX/orchestration bug on an existing local contact-fact path with clear acceptance criteria and low risk.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-111
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-111_kontaktfakt_feedback_und_bereits_bekannt_rueckmeldung.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/backlog/BACKLOG.md
  - documentation/test-results/TEST-RUN-2026-06-09-004_results.json
  - documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
- Dropped Context:
  - unrelated address-field mapping work
  - broad contact-memory recall contamination debugging
  - provider-cross-fallback history outside local contact-fact acknowledgement
