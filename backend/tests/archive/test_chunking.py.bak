"""
Unit tests for RAG V2 Code-Aware Chunking (chunking.py).

Tests:
- Boundary-Test: Chunks must not split mid-function
- Breadcrumb-Test: Markdown header path must be in chunk text
- AST-Resilience: Invalid code must still produce sensible chunks
"""

import tempfile
from pathlib import Path

import pytest

from backend.services.rag.chunking import chunk_code_file
from backend.services.rag.adapters.markdown import MarkdownAdapter
from backend.services.rag.adapters.code import CodeAdapter


class TestChunkingBoundary:
    """Test that chunks align with function/class boundaries."""

    def test_python_function_boundary(self):
        """A chunk must contain a complete function, not split mid-def."""
        code = (
            "def helper():\n"
            "    return 42\n"
            "\n"
            "def main():\n"
            "    x = helper()\n"
            "    print(x)\n"
            "\n"
            "class MyClass:\n"
            "    def method(self):\n"
            "        return self.x\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="py")
            assert len(chunks) >= 3  # helper, main, MyClass

            for chunk in chunks:
                text = chunk.text
                # No chunk should end with an incomplete def statement
                lines = text.splitlines()
                last_line = lines[-1] if lines else ""
                # An incomplete function would end with something like "def foo("
                # but our chunks are based on regex/AST boundaries
                assert not last_line.strip().startswith("def "), \
                    f"Chunk ends mid-function: {last_line[:40]}"

            # Each top-level symbol should be in its own chunk
            symbol_names = []
            for chunk in chunks:
                name = chunk.metadata.get("symbol_name", "")
                if name and name != "<block>":
                    symbol_names.append(name)

            assert "helper" in symbol_names
            assert "main" in symbol_names
            assert "MyClass" in symbol_names

        finally:
            path.unlink()

    def test_javascript_function_boundary(self):
        """JS functions should be chunked at boundaries."""
        code = (
            "function helper() {\n"
            "    return 42;\n"
            "}\n"
            "\n"
            "function main() {\n"
            "    const x = helper();\n"
            "    console.log(x);\n"
            "}\n"
            "\n"
            "class MyClass {\n"
            "    method() {\n"
            "        return this.x;\n"
            "    }\n"
            "}\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="js")
            assert len(chunks) >= 3

            symbol_names = [c.metadata.get("symbol_name", "") for c in chunks]
            assert "helper" in symbol_names
            assert "main" in symbol_names
            assert "MyClass" in symbol_names
        finally:
            path.unlink()

    def test_chunk_contains_code_prefix(self):
        """Each code chunk must include the module path and symbol context."""
        code = (
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "def process():\n"
            "    return Path('.')\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="py")
            # At least one chunk should have the process function
            process_chunks = [c for c in chunks if "process" in c.text]
            assert len(process_chunks) >= 1

            for chunk in process_chunks:
                # Code-Prefixing: Module path must be in text
                assert "# Module:" in chunk.text, f"Missing module prefix in: {chunk.text[:100]}"
                assert "# Symbol:" in chunk.text, f"Missing symbol prefix in: {chunk.text[:100]}"
                # Imports should be mentioned
                assert "import" in chunk.text.lower() or "Imports:" in chunk.text
        finally:
            path.unlink()


class TestChunkingResilience:
    """Test that chunking handles invalid/edge-case code gracefully."""

    def test_invalid_python_fallback(self):
        """Syntactically invalid Python must still produce chunks (fallback)."""
        # Missing colon, unclosed bracket — tree-sitter would fail
        code = (
            "def broken_func(\n"  # missing closing paren and colon
            "    print('hello'\n"  # unclosed bracket
            "\n"
            "def okay_func():\n"
            "    return 42\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="py")
            # Must not crash and must return at least one chunk
            assert len(chunks) >= 1
            # Fallback mode should be recorded
            modes = {c.metadata.get("chunking_mode", "") for c in chunks}
            assert "tree_sitter" in modes or "regex_fallback" in modes or "blank_line_fallback" in modes
        finally:
            path.unlink()

    def test_empty_file(self):
        """Empty file must return empty list or single fallback chunk."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="py")
            assert len(chunks) <= 1
        finally:
            path.unlink()

    def test_no_functions_fallback(self):
        """A Python file with no functions should use blank-line fallback."""
        code = (
            "x = 1\n"
            "y = 2\n"
            "\n"
            "z = x + y\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="py")
            assert len(chunks) >= 1
            # Should fall back since no def/class found
            modes = {c.metadata.get("chunking_mode", "") for c in chunks}
            assert "blank_line_fallback" in modes or "regex_fallback" in modes
        finally:
            path.unlink()

    def test_unsupported_language_fallback(self):
        """An unsupported language extension should use blank-line fallback."""
        code = "line one\n\nline two\n\nline three\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            chunks = chunk_code_file(path, language="xyz")
            assert len(chunks) >= 1
        finally:
            path.unlink()


class TestMarkdownBreadcrumbs:
    """Test that Markdown chunks include header breadcrumbs in text."""

    def test_breadcrumb_in_chunk_text(self):
        """The header path must be prefixed in the chunk text."""
        md = (
            "# Main Title\n"
            "\n"
            "Intro text here.\n"
            "\n"
            "## Section A\n"
            "\n"
            "Content of section A.\n"
            "\n"
            "### Subsection A1\n"
            "\n"
            "Deep content.\n"
            "\n"
            "## Section B\n"
            "\n"
            "Content of section B.\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md)
            f.flush()
            path = Path(f.name)

        try:
            adapter = MarkdownAdapter()
            chunks = adapter.parse(path)

            # Find the subsection chunk
            subsection_chunks = [c for c in chunks if "Subsection A1" in c.text]
            assert len(subsection_chunks) >= 1

            for chunk in subsection_chunks:
                # The breadcrumb must be in the chunk text
                assert "##" in chunk.text, f"Missing breadcrumb prefix: {chunk.text[:80]}"
                assert "Main Title" in chunk.text, f"Missing parent heading: {chunk.text[:80]}"
                assert "Section A" in chunk.text, f"Missing parent heading: {chunk.text[:80]}"
                assert "Subsection A1" in chunk.text, f"Missing own heading: {chunk.text[:80]}"

            # Check metadata too
            for chunk in chunks:
                if chunk.metadata.get("breadcrumb"):
                    assert chunk.metadata["breadcrumb"] in chunk.text
        finally:
            path.unlink()

    def test_no_heading_file(self):
        """Markdown without headings should not add breadcrumb prefix."""
        md = "Just some text.\nMore text.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md)
            f.flush()
            path = Path(f.name)

        try:
            adapter = MarkdownAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) == 1
            # No heading = no breadcrumb prefix
            assert not chunks[0].text.startswith("##")
        finally:
            path.unlink()


class TestCodeAdapterIntegration:
    """Test that CodeAdapter properly delegates to chunking.py."""

    def test_adapter_uses_chunking(self):
        code = (
            "def foo():\n"
            "    return 1\n"
            "\n"
            "def bar():\n"
            "    return 2\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            adapter = CodeAdapter()
            chunks = adapter.parse(path)
            assert len(chunks) >= 2

            # All chunks must have chunking_mode metadata
            for chunk in chunks:
                assert "chunking_mode" in chunk.metadata
                assert chunk.metadata.get("language") == "py"
                assert chunk.metadata.get("adapter") == "code"
        finally:
            path.unlink()
