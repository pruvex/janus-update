# DEBUG PACKAGE - TASK-M6.5 Test Collection Prerequisites

Failure Code: `M6_5_TEST_COLLECTION_PREREQUISITE_CHAIN`
Iteration: 1
Expected: `python -m pytest --noconftest backend/tests/test_streaming_tool_loop_runner.py -q` collects and executes the focused regression.
Actual: collection first fails in ChromaDB Rust SQLite (`range start index 10 out of range for slice of length 9`); a process-only Chroma stub then exposes `ModuleNotFoundError: backend.data.schemas_intent`.
Bound Scope: test-collection prerequisites only. No M6 provider/stream behavior, flag semantics, or Phase-B work.
Evidence: `documentation/tasks/TASK-M6.5_validation.md` and `documentation/tasks/TASK-M6.5_final_audit.md`.
Allowed Candidate Files: `backend/services/vector_service.py`, `backend/data/schemas_intent.py`, `backend/tests/test_streaming_tool_loop_runner.py`.
Forbidden: product streaming edits, provider gateways, dependency updates, database deletion, Git, release, secrets, auth, security, privacy, migrations, or architecture changes.
Required Evidence: root-cause summary, changed files, exact focused command result, and any remaining blocker.
