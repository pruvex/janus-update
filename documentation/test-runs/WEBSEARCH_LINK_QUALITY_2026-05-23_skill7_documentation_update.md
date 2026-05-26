# Websearch Link Quality - Skill 7 Documentation Update

## Task
- **Task file:** skipped - chat-driven hardening, no formal task artifact was provided.
- **Implemented tasks:** central link-quality scoring, News detail-link filtering, provider-agnostic renderer/resolver integration, regression tests.
- **Final audit status:** PASS.

## Documentation Updated
- **Skill dossier:** updated `documentation/skills/system.rss_news.md` with Link-Qualitaet behavior and honest missing-link policy.
- **Final audit artifact:** added `documentation/test-runs/WEBSEARCH_LINK_QUALITY_2026-05-23_final_audit.md`.
- **Task file / Backlog / Dashboard snapshot:** skipped - no `BACKLOG-XXX` item was provided.
- **CHANGELOG / PROJECT_STATE / WHAT_I_LEARNED:** skipped for this focused incremental hardening because the surrounding worktree already contains broader uncommitted project-state changes outside this selected commit scope.

## Version
- **Old version:** unchanged.
- **New version:** unchanged.
- **Reason:** no formal release/version task was provided; version files are part of a larger dirty worktree outside this focused change.

## Validation Recorded
- `python -m pytest tests\renderers\test_renderers.py::TestRssNewsRenderer tests\renderers\test_renderers.py::TestWebsearchLinkQuality backend\tests\tools\test_system_skills_diamond.py::TestRssNewsService backend\tests\tools\test_websearch.py::test_news_update_query_prioritizes_rss_before_websearch -q` - PASS, 24/24.
- `python -m py_compile backend\services\websearch\link_quality.py backend\renderers\implementations\rss_news_renderer.py backend\tool_registry.py` - PASS.
- `git diff --check -- backend\services\websearch\link_quality.py backend\renderers\implementations\rss_news_renderer.py backend\tool_registry.py tests\renderers\test_renderers.py` - PASS.

## Completion State
- **Final Audit:** PASS.
- **Documentation Update:** COMPLETE.
- **Commit Scope:** focused Websearch/News link-quality files only; unrelated dirty worktree files intentionally excluded.
