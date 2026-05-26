"""
Test robust filename matcher: needle variants must all resolve to the same file.
Also verifies warning guard module.
"""
import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.tool_executor import _v2_fulltext_fallback
from backend.services.orchestrator.warning_guard import (
    WARNING_MARKER,
    tool_output_contains_warning,
    model_acknowledged_warning,
    did_model_ignore_warning,
)

NEEDLES = [
    "aegypten",
    "aegypten.pdf",
    "AEGYPTEN.PDF",
    "Aegypten.Pdf",
    r"C:\Users\pruve\Desktop\JanusPDFs\aegypten.pdf",
]


async def test_needles():
    print("=" * 70)
    print("TEST: Robust filename matcher - multiple needle formats")
    print("=" * 70)
    ok = 0
    for needle in NEEDLES:
        result = await _v2_fulltext_fallback(needle, started=time.perf_counter(), tags=["test"])
        if result and result.data and "content" in result.data:
            content = result.data["content"]
            present = "aegypten.pdf" in content.lower()
            print(f"  needle={needle!r:60} -> hit={present}")
            if present:
                ok += 1
        else:
            print(f"  needle={needle!r:60} -> MISS")
    print(f"\nPassed: {ok}/{len(NEEDLES)}")


def test_warning_guard():
    print("\n" + "=" * 70)
    print("TEST: Warning guard")
    print("=" * 70)

    tool_results_with_warning = [
        {"content": f"{WARNING_MARKER}\nPfade:\n  - a.pdf\n  - b.pdf\n\nContent X"}
    ]
    tool_results_without = [{"content": "Plain content"}]

    # Case 1: warning ignored
    ignored = did_model_ignore_warning(tool_results_with_warning, "Hier ist der Inhalt: ...")
    print(f"  [1] warning ignored -> {ignored} (expected True)")

    # Case 2: warning acknowledged
    ack_text = "Hinweis: Ich habe 2 Versionen von X.pdf gefunden. Ich verwende hier die Datei aus a.pdf. Die anderen Fundorte sind: b.pdf."
    ignored = did_model_ignore_warning(tool_results_with_warning, ack_text)
    print(f"  [2] warning acknowledged -> {ignored} (expected False)")

    # Case 3: no warning in tool output
    ignored = did_model_ignore_warning(tool_results_without, "irgendwas")
    print(f"  [3] no warning -> {ignored} (expected False)")


async def main():
    await test_needles()
    test_warning_guard()


if __name__ == "__main__":
    asyncio.run(main())
