"""Unit tests for Task 027 JSON parsing in title_generator."""

from backend.services.orchestrator.title_generator import _parse_title_category_payload


def test_parse_plain_json():
    r = _parse_title_category_payload('{"title": "Hello World", "category": "research"}')
    assert r == ("Hello World", "research")


def test_parse_json_with_markdown_fence():
    raw = '```json\n{"title": "X", "category": "invalid_cat"}\n```'
    r = _parse_title_category_payload(raw)
    assert r is not None
    assert r[0] == "X"
    assert r[1] == "general"


def test_parse_missing_title_returns_none():
    assert _parse_title_category_payload('{"category": "coding"}') is None
    assert _parse_title_category_payload("not json") is None
