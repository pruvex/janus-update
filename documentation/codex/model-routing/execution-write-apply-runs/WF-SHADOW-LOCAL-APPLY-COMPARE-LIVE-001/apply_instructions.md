You are executing a bounded workspace-write apply task inside the Janus repository.
Apply the exact accepted patch from the provided artifact package to the repository working tree.
Do not redesign the change. Do not add extra edits. Do not touch files outside the exact allowlist.
Do not run git commands. Do not run tests. Do not claim task completion beyond the bounded write.

Accepted source package: C:\KI\Janus-Projekt\documentation\codex\model-routing\fixtures\cursor-shadow-catalog\execution_write_apply_candidate\accepted_source\WF-SHADOW-LOCAL-APPLY-COMPARE-001
Patch artifact: C:\KI\Janus-Projekt\documentation\codex\model-routing\fixtures\cursor-shadow-catalog\execution_write_apply_candidate\accepted_source\WF-SHADOW-LOCAL-APPLY-COMPARE-001\git_diff.patch
Review artifact: C:\KI\Janus-Projekt\documentation\codex\model-routing\fixtures\cursor-shadow-catalog\execution_write_apply_candidate\accepted_source\WF-SHADOW-LOCAL-APPLY-COMPARE-001\delegated_result.md

Exact allowlisted files:
- documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/sandbox/test_gate_prompt_apply_shadow.py

Max touched files: 1

Required behavior:
1. Read the accepted patch artifact and apply that patch locally.
2. If the patch cannot be applied cleanly, stop and explain why in the final message.
3. Do not create new files, delete files, rename files, or move files.
4. Keep the final message compact: changed files, whether apply succeeded, and any blocker.
