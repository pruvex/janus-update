"""
Test for metadata sanitization to ensure ChromaDB compatibility.

This test validates that _sanitize_metadata() correctly converts
list and dict values to JSON strings for ChromaDB compatibility.
"""

from backend.services.rag.ingestion import _sanitize_metadata


def test_sanitize_metadata_with_list():
    """Test that list values are converted to JSON strings."""
    metadata = {
        "language": "python",
        "imports": ["os", "sys", "json"],
        "score": 0.95,
    }
    sanitized = _sanitize_metadata(metadata)
    
    assert sanitized["language"] == "python"
    assert sanitized["imports"] == '["os", "sys", "json"]'
    assert sanitized["score"] == 0.95
    print("✅ List sanitization test passed")


def test_sanitize_metadata_with_dict():
    """Test that dict values are converted to JSON strings."""
    metadata = {
        "file_info": {"name": "test.py", "size": 1024},
        "is_code": True,
    }
    sanitized = _sanitize_metadata(metadata)
    
    assert sanitized["file_info"] == '{"name": "test.py", "size": 1024}'
    assert sanitized["is_code"] is True
    print("✅ Dict sanitization test passed")


def test_sanitize_metadata_with_nested_structures():
    """Test that nested structures are converted to JSON strings."""
    metadata = {
        "nested": {"list": [1, 2, 3], "dict": {"key": "value"}},
        "simple": "string",
    }
    sanitized = _sanitize_metadata(metadata)
    
    assert '"list": [1, 2, 3]' in sanitized["nested"]
    assert '"dict": {"key": "value"}' in sanitized["nested"]
    assert sanitized["simple"] == "string"
    print("✅ Nested structure sanitization test passed")


def test_sanitize_metadata_with_primitives():
    """Test that primitive values are left unchanged."""
    metadata = {
        "string": "hello",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
    }
    sanitized = _sanitize_metadata(metadata)
    
    assert sanitized["string"] == "hello"
    assert sanitized["int"] == 42
    assert sanitized["float"] == 3.14
    assert sanitized["bool"] is True
    assert sanitized["none"] is None
    print("✅ Primitive values test passed")


if __name__ == "__main__":
    test_sanitize_metadata_with_list()
    test_sanitize_metadata_with_dict()
    test_sanitize_metadata_with_nested_structures()
    test_sanitize_metadata_with_primitives()
    print("\n✅ All metadata sanitization tests passed")
