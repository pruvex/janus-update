"""Dry-run test for _update_registry_epic_completion."""
import sys
sys.path.insert(0, "tools/orchestrator_ui")

from parser import _update_registry_epic_completion, _update_registry_blocker

REGISTRY = """## 🚀 Epics in Entwicklung

### Epic: My Epic (Ref: `documentation/features/epic_foo.md`)
*   **Status:** In Development
*   **Progress:** 4/5 Tasks
*   **NÄCHSTER BLOCKER:** `task_foo_05.md`

### Epic: Other Epic (Ref: `documentation/features/epic_bar.md`)
*   **Status:** In Development
*   **Progress:** 1/3 Tasks
*   **NÄCHSTER BLOCKER:** `task_bar_02.md`
"""

EPIC_ALL_DONE = """## 4. Master-Task-Liste
- [x] 1. `task_foo_01.md` (Done)
- [x] 2. `task_foo_02.md` (Done)
- [x] 3. `task_foo_03.md` (Done)
- [x] 4. `task_foo_04.md` (Done)
- [x] 5. `task_foo_05.md` (Done)
"""

result = _update_registry_epic_completion(
    REGISTRY,
    "documentation/features/epic_foo.md",
    EPIC_ALL_DONE,
)

print("=== Updated Registry ===")
print(result)
print("========================")

# T1: Status updated
assert "✅ Completed" in result, "FAIL T1: Status not updated"
print("T1 Status → ✅ Completed: PASS")

# T2: Progress updated to 5/5
assert "5/5 Tasks" in result, f"FAIL T2: Progress not updated: {result}"
print("T2 Progress → 5/5 Tasks: PASS")

# T3: NÄCHSTER BLOCKER line removed
assert "BLOCKER" not in result.split("epic_foo")[1].split("### Epic:")[0], \
    "FAIL T3: BLOCKER line not removed"
print("T3 NÄCHSTER BLOCKER removed: PASS")

# T4: Other epic untouched
other_block = result.split("epic_bar.md")[1]
assert "In Development" in result.split("epic_bar")[1], "FAIL T4: other epic status changed"
assert "task_bar_02.md" in result, "FAIL T4: other epic blocker changed"
print("T4 Other epic untouched: PASS")

# T5: Normal task (not last) still uses _update_registry_blocker path
REGISTRY_MID = """### Epic: Mid Epic (Ref: `documentation/features/epic_mid.md`)
*   **Status:** In Development
*   **Progress:** 2/3 Tasks
*   **NÄCHSTER BLOCKER:** `task_mid_03.md`
"""
mid_result = _update_registry_blocker(REGISTRY_MID, "documentation/features/epic_mid.md", "task_mid_04.md")
assert "`task_mid_04.md`" in mid_result, "FAIL T5: blocker not updated"
assert "In Development" in mid_result, "FAIL T5: status changed unexpectedly"
print("T5 Mid-epic blocker update still works: PASS")

print()
print("ALL EPIC COMPLETION TESTS PASSED")
