"""Integration test for approve_bug logic."""
import sys
sys.path.insert(0, "tools/orchestrator_ui")

from parser import _update_bug_status

REGISTRY = """## 🐛 Isolierte Bugfixes & Audits (Kein Epic)

*   **Task:** `task_bug_websearch_xml.md` (Ref: `system.websearch`)
*   **Status:** Geplant
*   **Priorität:** Hoch

*   **Task:** `task_bug_other.md` (Ref: `system.other`)
*   **Status:** Geplant
*   **Priorität:** Mittel
"""

# T1: status updated for target bug
result = _update_bug_status(REGISTRY, "task_bug_websearch_xml.md")
assert "✅ Erledigt" in result, f"FAIL T1: status not updated\n{result}"
print("T1 status update: PASS")

# T2: no cascade to other bug
idx = result.find("task_bug_other.md")
after = result[idx:]
other_status_line = [l for l in after.splitlines() if "**Status:**" in l][0]
assert "Erledigt" not in other_status_line, f"FAIL T2: cascade! {other_status_line}"
assert "Geplant" in other_status_line, f"FAIL T2: other status changed: {other_status_line}"
print("T2 no cascade: PASS")

# T3: idempotency — already done bug is not double-updated
result2 = _update_bug_status(result, "task_bug_websearch_xml.md")
assert result2.count("✅ Erledigt") == 1, f"FAIL T3: double entry"
print("T3 idempotency: PASS")

# T4: task line itself is preserved
assert "task_bug_websearch_xml.md" in result, "FAIL T4: filename removed"
assert "system.websearch" in result, "FAIL T4: ref removed"
print("T4 task line preserved: PASS")

print()
print("ALL BUG APPROVE TESTS PASSED")
