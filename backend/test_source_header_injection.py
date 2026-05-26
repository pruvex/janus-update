"""
Test source header injection for aegypten.pdf
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.knowledge_service import query

print("=" * 70)
print("TEST: Source Header Injection for aegypten.pdf")
print("=" * 70)

# Test knowledge.query with filename
result = query(
    query_text="Ägypten",
    filename="aegypten.pdf",
    retrieval_mode="v2",
    top_k=3
)

print(f"\nStatus: {result.get('status')}")
print(f"Results: {result.get('num_results')}")

for idx, r in enumerate(result.get('results', [])[:3]):
    print(f"\n--- Result {idx+1} ---")
    text = r.get('text', '')
    print(f"Text preview (first 300 chars):")
    print(text[:300])
    if "[DOKUMENT-QUELLE:" in text:
        print("✅ Source header present!")
    else:
        print("❌ Source header MISSING!")

# Test knowledge.read_full_text via tool_executor
print("\n" + "=" * 70)
print("TEST: Fulltext Source Header Injection")
print("=" * 70)

import asyncio
from backend.services.tool_executor import _v2_fulltext_fallback
import time

async def test_fulltext():
    result = await _v2_fulltext_fallback("aegypten.pdf", started=time.perf_counter(), tags=["test"])
    if result:
        content = result.data.get("content", "")
        print(f"\nFulltext preview (first 300 chars):")
        print(content[:300])
        if "[DOKUMENT-QUELLE:" in content:
            print("✅ Source header present in fulltext!")
        else:
            print("❌ Source header MISSING in fulltext!")
    else:
        print("❌ Fulltext result is None")

asyncio.run(test_fulltext())
