"""
Unit tests for RAG V2 adapters.
"""

import tempfile
from pathlib import Path

import pytest

from backend.services.rag.adapters.base import BaseAdapter, RawChunk
from backend.services.rag.adapters.code import CodeAdapter
from backend.services.rag.adapters.markdown import MarkdownAdapter


class TestCodeAdapter:
    """Test the CodeAdapter for various source files."""

    def test_supports_python(self):
        assert CodeAdapter.supports(Path("test.py"))
        assert CodeAdapter.supports(Path("test.PY"))

    def test_supports_javascript(self):
        assert CodeAdapter.supports(Path("test.js"))
        assert CodeAdapter.supports(Path("test.ts"))
        assert CodeAdapter.supports(Path("test.jsx"))

    def test_does_not_support_txt(self):
        assert not CodeAdapter.supports(Path("test.txt"))

    def test_parse_python_file(self):
        code = """def hello():
    print("Hello")


def world():
    print("World")
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            adapter = CodeAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) == 2
            assert "hello()" in chunks[0].text
            assert "world()" in chunks[1].text
            assert chunks[0].metadata["language"] == "py"
            assert chunks[0].start_line == 1
        finally:
            path.unlink()

    def test_parse_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            path = Path(f.name)

        try:
            adapter = CodeAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) == 1  # fallback chunk
            assert chunks[0].metadata.get("fallback") is True
        finally:
            path.unlink()

    def test_sha256_consistency(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            f.flush()
            path = Path(f.name)

        try:
            sha1 = BaseAdapter.compute_sha256(path)
            sha2 = BaseAdapter.compute_sha256(path)
            assert sha1 == sha2
            assert len(sha1) == 64  # hex digest length
        finally:
            path.unlink()


class TestMarkdownAdapter:
    """Test the MarkdownAdapter."""

    def test_supports_md(self):
        assert MarkdownAdapter.supports(Path("test.md"))
        assert MarkdownAdapter.supports(Path("test.markdown"))

    def test_does_not_support_py(self):
        assert not MarkdownAdapter.supports(Path("test.py"))

    def test_parse_headings(self):
        md = """# Title

Some intro text.

## Section 1

Content of section 1.

### Subsection

More content.

## Section 2

Final section.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md)
            f.flush()
            path = Path(f.name)

        try:
            adapter = MarkdownAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) >= 3  # Title, Section 1, Section 2
            # Check that headings are preserved in metadata
            headings = [c.metadata.get("headings", []) for c in chunks]
            assert any("Title" in h for h in headings)
            assert any("Section 1" in h for h in headings)
            assert any("Section 2" in h for h in headings)
        finally:
            path.unlink()

    def test_parse_no_headings(self):
        md = "Just some text without headings.\nMore text.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md)
            f.flush()
            path = Path(f.name)

        try:
            adapter = MarkdownAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) == 1
            assert "Just some text" in chunks[0].text
        finally:
            path.unlink()
