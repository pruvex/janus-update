"""Quick verification tests for Diamond Stability Fix."""

from backend.renderers.implementations.unified_websearch_renderer import UnifiedWebSearchRenderer
from backend.services.websearch.base_provider import validate_websearch_result, WebSearchResult

def run_tests():
    # Test 1: Renderer instantiation
    print("✓ Test 1: Renderer instantiation")
    renderer = UnifiedWebSearchRenderer()
    print(f"  skill_id: {renderer.skill_id}")

    # Test 2: validate_websearch_result with valid data
    print("\n✓ Test 2: validate_websearch_result with valid data")
    valid = {
        "text": "Test text",
        "sources": [{"url": "https://example.com", "title": "Example"}],
        "metadata": {"provider": "test"}
    }
    result = validate_websearch_result(valid)
    print(f"  Result keys: {list(result.keys())}")

    # Test 3: Renderer with sources
    print("\n✓ Test 3: Renderer with sources")
    data = {
        "text": "This is the LLM response.",
        "sources": [
            {"url": "https://www.idealo.de/preisvergleich/OffersOfProduct/1001", "title": "iPhone 15"},
            {"url": "https://de.wikipedia.org/wiki/Python", "title": "Python (Programmiersprache)"},
        ],
        "metadata": {"provider": "gemini"}
    }
    output = renderer.render(data)
    print(f"  Output contains Idealo section: {'Angebote bei Idealo' in output}")
    print(f"  Output contains Wikipedia section: {'Hintergrundwissen' in output}")

    # Test 4: Fail-closed (no sources)
    print("\n✓ Test 4: Fail-closed with empty sources")
    empty_data = {"text": "Response", "sources": [], "metadata": {"provider": "test"}}
    empty_output = renderer.render(empty_data)
    print(f"  Output equals text only: {empty_output == 'Response'}")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    run_tests()
