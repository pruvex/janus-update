"""
Code Adapter for RAG V2

P3: Code-Aware Chunking with tree-sitter AST parsing + Code-Prefixing.

Uses the central chunking engine (chunking.py) which provides:
1. Tree-sitter AST-based chunking (function/class boundaries)
2. Regex-based fallback for environments without tree-sitter
3. Blank-line fallback (guaranteed to work)

Each chunk is prefixed with:
- Module path
- Symbol name and node type (function/class)
- Extracted imports for context

This allows the vector search to retain context even for small snippets.
"""

import logging
from pathlib import Path
from typing import List

from .base import BaseAdapter, RawChunk
from ..chunking import chunk_code_file

logger = logging.getLogger("janus_backend")

# Supported code extensions
SUPPORTED_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".r", ".lua", ".sh", ".bash", ".ps1",
    ".sql", ".html", ".htm", ".xml",
    ".css", ".scss", ".less",
    ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".json", ".conf",
}


class CodeAdapter(BaseAdapter):
    """
    Adapter for source code files with AST-aware chunking.

    P3: Delegates to chunking.py for tree-sitter + regex + blank-line fallback.
    Each chunk includes Code-Prefixing (module path, symbol name, imports).
    """

    @classmethod
    def supports(cls, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTS

    def parse(self, path: Path) -> List[RawChunk]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        language = path.suffix.lstrip(".").lower()
        chunks = chunk_code_file(path, language=language)

        # Convert chunking.Chunk -> adapters.RawChunk
        raw_chunks: List[RawChunk] = []
        for chunk in chunks:
            meta = dict(chunk.metadata)
            meta["language"] = language
            meta["adapter"] = "code"
            raw_chunks.append(
                RawChunk(
                    text=chunk.text,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    metadata=meta,
                )
            )

        logger.info(
            f"CodeAdapter parsed {path}: {len(raw_chunks)} chunks "
            f"(mode={raw_chunks[0].metadata.get('chunking_mode', 'unknown') if raw_chunks else 'none'})"
        )
        return raw_chunks
