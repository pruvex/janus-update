"""
Test the V2 fuzzy fulltext fallback in get_full_document_text.
Simulates the LLM calling knowledge.read_full_text with just a filename.
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.tool_executor import _v2_fulltext_fallback, _read_file_fulltext
import time


async def main():
    print("=" * 70)
    print("TEST: V2 Fuzzy Fulltext Fallback")
    print("=" * 70)

    # Test 1: Plain filename
    print("\n[1] filename='rollooff.pdf'")
    result = await _v2_fulltext_fallback("rollooff.pdf", started=time.perf_counter(), tags=["test"])
    if result:
        data = result.data or {}
        content = data.get("content", "")
        print(f"  status={result.status}, chars={len(content)}, source={data.get('source')}")
        print(f"  file_path={data.get('file_path')}")
        print(f"  preview: {content[:200]!r}")
    else:
        print("  FAILED: returned None")

    # Test 2: Absolute path
    print("\n[2] absolute path")
    abs_path = r"C:\Users\pruve\Desktop\JanusPDFs\rollooff.pdf"
    result = await _read_file_fulltext(abs_path, started=time.perf_counter(), tags=["test"])
    if result:
        data = result.data or {}
        content = data.get("content", "")
        print(f"  status={result.status}, chars={len(content)}")
        print(f"  preview: {content[:200]!r}")
    else:
        print("  FAILED: returned None")

    # Test 3: non-existent filename
    print("\n[3] filename='does_not_exist.pdf'")
    result = await _v2_fulltext_fallback("does_not_exist.pdf", started=time.perf_counter(), tags=["test"])
    print(f"  Returned: {result}")


if __name__ == "__main__":
    asyncio.run(main())
