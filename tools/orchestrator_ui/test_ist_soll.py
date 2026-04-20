"""Dry-run test for IST/SOLL extraction."""
import sys
sys.path.insert(0, "tools/orchestrator_ui")

from parser import extract_metadata, get_task_content
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# T1: extract from real file
content = get_task_content("task_bug_websearch_xml.md", REPO_ROOT)
assert content is not None, "FAIL T1: task file not found"
print("T1 file loaded: PASS")

meta = extract_metadata(content)

# T2: IST extracted
assert meta.get("ist") is not None, f"FAIL T2: no ist in meta: {meta}"
assert "Sandwich-Drift" in meta["ist"], f"FAIL T2: wrong ist: {meta['ist']}"
print(f"T2 IST extracted: PASS  →  {meta['ist']}")

# T3: SOLL extracted
assert meta.get("soll") is not None, f"FAIL T3: no soll in meta: {meta}"
assert "korrekt" in meta["soll"], f"FAIL T3: wrong soll: {meta['soll']}"
print(f"T3 SOLL extracted: PASS  →  {meta['soll']}")

# T4: model + location still work
assert meta.get("model") == "Claude 4.6 Sonnet", f"FAIL T4: model={meta.get('model')}"
assert meta.get("location") is not None, f"FAIL T4: location={meta.get('location')}"
print(f"T4 model/location unchanged: PASS  →  {meta['model']} / {meta['location']}")

# T5: file without IST/SOLL returns None gracefully
content_no_ist = "# Task\n## 2. Ziel\nKein Kontext hier.\n"
meta2 = extract_metadata(content_no_ist)
assert meta2.get("ist") is None, "FAIL T5: should be None for missing IST"
assert meta2.get("soll") is None, "FAIL T5: should be None for missing SOLL"
print("T5 graceful None for missing IST/SOLL: PASS")

print()
print("ALL IST/SOLL EXTRACTION TESTS PASSED")
