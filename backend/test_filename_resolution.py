"""
Test fuzzy filename resolution for PDF files
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag.index_store import IndexStore
from backend.utils.paths import get_app_data_dir

db_path = os.path.join(get_app_data_dir(), "knowledge_index_v2.db")
print(f"Testing with database at: {db_path}")

store = IndexStore(db_path=db_path)

# Test fuzzy filename resolution
test_filename = "rollooff.pdf"
print(f"\nTesting fuzzy filename resolution for: {test_filename}")

results = store.find_by_filename(test_filename)
print(f"Found {len(results)} files matching '{test_filename}':")

for file in results:
    print(f"  - {file.path}")
    print(f"    SHA256: {file.sha256[:16]}...")
    print(f"    Format: {file.format}")
    print(f"    Chunks: {len(file.chunk_ids)}")

# Test with just the basename without extension
test_filename2 = "rollooff"
print(f"\nTesting fuzzy filename resolution for: {test_filename2}")

results2 = store.find_by_filename(test_filename2)
print(f"Found {len(results2)} files matching '{test_filename2}':")

for file in results2:
    print(f"  - {file.path}")

store.close()

# Test knowledge.query with filename parameter
print("\n\nTesting knowledge.query with filename parameter:")
from backend.services.knowledge_service import query

result = query(
    query_text="Wetter",
    filename="rollooff.pdf",
    retrieval_mode="v2",
    top_k=5
)

print(f"Results: {result['num_results']}")
for r in result.get('results', [])[:3]:
    print(f"  - {r.get('source_path', 'N/A')}")
