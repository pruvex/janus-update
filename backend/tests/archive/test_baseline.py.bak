"""
Pytest integration for RAG V1 baseline evaluation.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_golden_queries_file_exists():
    """Test that golden_queries.jsonl exists and is readable."""
    golden_queries_path = Path(__file__).parent / "golden_queries.jsonl"
    assert golden_queries_path.exists(), "golden_queries.jsonl does not exist"
    
    import json
    queries = []
    with open(golden_queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    
    assert len(queries) == 30, f"Expected 30 queries, got {len(queries)}"
    
    # Verify distribution
    query_types = {q["query_type"] for q in queries}
    assert "code" in query_types, "Missing code queries"
    assert "prose" in query_types, "Missing prose queries"
    assert "mixed" in query_types, "Missing mixed queries"
    
    code_count = sum(1 for q in queries if q["query_type"] == "code")
    prose_count = sum(1 for q in queries if q["query_type"] == "prose")
    mixed_count = sum(1 for q in queries if q["query_type"] == "mixed")
    
    assert code_count == 10, f"Expected 10 code queries, got {code_count}"
    assert prose_count == 10, f"Expected 10 prose queries, got {prose_count}"
    assert mixed_count == 10, f"Expected 10 mixed queries, got {mixed_count}"


def test_harness_imports():
    """Test that harness module can be imported without errors."""
    from backend.tests.rag import harness
    assert hasattr(harness, 'load_golden_queries')
    assert hasattr(harness, 'calculate_metrics')
    assert hasattr(harness, 'generate_report')


def test_harness_loads_queries():
    """Test that harness can load golden queries."""
    from backend.tests.rag.harness import load_golden_queries
    
    golden_queries_path = Path(__file__).parent / "golden_queries.jsonl"
    queries = load_golden_queries(str(golden_queries_path))
    
    assert len(queries) == 30, f"Expected 30 queries, got {len(queries)}"
    
    # Verify each query has required fields
    for q in queries:
        assert "query" in q
        assert "expected_paths" in q
        assert "min_rank" in q
        assert "query_type" in q
        assert "confidence" in q


def test_legacy_chroma_read_only():
    """Test that legacy ChromaDB can be accessed in read-only mode."""
    import chromadb
    from backend.utils.paths import get_app_data_dir
    from chromadb.utils import embedding_functions
    
    chroma_path = os.path.join(get_app_data_dir(), "rag_chroma_db")
    assert os.path.exists(chroma_path), f"Legacy ChromaDB path does not exist: {chroma_path}"
    
    # Try to connect to legacy collection
    client = chromadb.PersistentClient(path=chroma_path)
    collection_names = client.list_collections()
    
    # Should have at least janus_global_documents
    collection_name_list = [c.name for c in collection_names]
    assert "janus_global_documents" in collection_name_list, "Legacy collection janus_global_documents not found"
