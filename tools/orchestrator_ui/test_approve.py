"""Integration test for approve_task logic."""
import sys
sys.path.insert(0, "tools/orchestrator_ui")

from parser import (
    _update_epic_task_checkbox,
    _update_registry_blocker,
    _find_next_blocker,
)

EPIC = """## 4. Master-Task-Liste
- [x] 1. `task_foo_01.md` (Done task)
- [ ] 2. `task_foo_02.md` (Target task)
- [ ] 3. `task_foo_03.md` (Next task)
"""

REGISTRY = """### Epic: My Epic (Ref: `documentation/features/epic_foo.md`)
*   **Status:** In Development
*   **Progress:** 1/3 Tasks
*   **NÄCHSTER BLOCKER:** `task_foo_02.md`

### Epic: Other Epic (Ref: `documentation/features/epic_bar.md`)
*   **NÄCHSTER BLOCKER:** `task_bar_01.md`
"""

# T1: checkbox update
result = _update_epic_task_checkbox(EPIC, "task_foo_02.md")
assert "- [x] 2. `task_foo_02.md`" in result, f"FAIL T1: {result}"
assert "- [ ] 3. `task_foo_03.md`" in result, "FAIL T1: next task was changed"
print("T1 checkbox update: PASS")

# T2: double-fire safety (already [x] must not change again)
result2 = _update_epic_task_checkbox(result, "task_foo_02.md")
assert result2 == result, "FAIL T2: idempotency broken"
print("T2 idempotency: PASS")

# T3: find next blocker
nxt = _find_next_blocker(result)
assert nxt == "task_foo_03.md", f"FAIL T3: {nxt}"
print("T3 find_next_blocker: PASS")

# T4: registry update
updated = _update_registry_blocker(
    REGISTRY, "documentation/features/epic_foo.md", "task_foo_03.md"
)
assert "`task_foo_03.md`" in updated, f"FAIL T4: {updated}"
assert "`task_bar_01.md`" in updated, "FAIL T4: other epic was modified"
print("T4 registry update: PASS")

# T5: other epic untouched
assert "task_foo_03.md" not in updated.split("epic_bar")[1], "FAIL T5: leak"
print("T5 no cross-epic leak: PASS")

# T6: CASCADE PREVENTION — approving task_foo_02 must NOT touch task_foo_03
multi_task_epic = """## 4. Master-Task-Liste
- [x] 1. `task_foo_01.md` (Done)
- [ ] 2. `task_foo_02.md` (Target)
- [ ] 3. `task_foo_03.md` (Must stay open)
- [ ] 4. `task_foo_04.md` (Must stay open)
"""
result_cascade = _update_epic_task_checkbox(multi_task_epic, "task_foo_02.md")
assert "- [x] 2. `task_foo_02.md`" in result_cascade, "FAIL T6: target not updated"
assert "- [ ] 3. `task_foo_03.md`" in result_cascade, "FAIL T6: task_03 cascaded!"
assert "- [ ] 4. `task_foo_04.md`" in result_cascade, "FAIL T6: task_04 cascaded!"
print("T6 cascade prevention: PASS")

print()
print("ALL INTEGRATION TESTS PASSED")
