"""
Code Adapter for RAG V2

Parses source code files into RawChunks.

P1 Status: Placeholder implementation — structured parsing (AST/tree-sitter)
will be added in Phase P3 (Code-Aware Chunking). For P1, this adapter
reads the file as plain text and splits on blank lines to provide basic
paragraph-level chunks without syntax awareness.

Tree-sitter Integration (P3):
- Install tree-sitter bindings
- Parse AST for supported languages (Python, JavaScript, TypeScript, Markdown)
- Emit chunks aligned to function/class boundaries
- Store language metadata in RawChunk.metadata
"""

import logging
from pathlib import Path
from typing import List

from .base import BaseAdapter, RawChunk

logger = logging.getLogger("janus_backend")

# Supported code extensions for P1
SUPPORTED_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".r",
    ".lua",
    ".sh",
    ".bash",
    ".ps1",
    ".sql",
    ".html",
    ".htm",
    ".xml",
    ".css",
    ".scss",
    ".less",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".json",
    ".ini",
    ".conf",
}


class CodeAdapter(BaseAdapter):
    """
    Adapter for source code files.

    P1: Basic text splitting on blank lines.
    P3: Tree-sitter based structural chunking (function/class level).
    """

    @classmethod
    def supports(cls, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTS

    def parse(self, path: Path) -> List[RawChunk]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        text = self.read_text_safe(path)
        lines = text.splitlines(keepends=False)

        chunks: List[RawChunk] = []
        current_lines: List[str] = []
        current_start = 1

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped == "":
                # Blank line = chunk boundary
                if current_lines:
                    chunk_text = "\n".join(current_lines)
                    chunks.append(
                        RawChunk(
                            text=chunk_text,
                            start_line=current_start,
                            end_line=i - 1,
                            metadata={
                                "language": path.suffix.lstrip(".").lower(),
                                "source_path": str(path),
                            },
                        )
                    )
                    current_lines = []
                current_start = i + 1
            else:
                current_lines.append(line)

        # Don't forget trailing chunk
        if current_lines:
            chunk_text = "\n".join(current_lines)
            chunks.append(
                RawChunk(
                    text=chunk_text,
                    start_line=current_start,
                    end_line=len(lines),
                    metadata={
                        "language": path.suffix.lstrip(".").lower(),
                        "source_path": str(path),
                    },
                )
            )

        # P3 Guard: If tree-sitter is available, use it instead
        # (This is a placeholder for P3 integration)
        try:
            import tree_sitter
            # Tree-sitter is installed but we don't use it in P1
            # P3 will replace the blank-line splitting with AST-based chunking
            logger.debug(f"Tree-sitter available but not used in P1 for {path}")
        except ImportError:
            pass

        if not chunks:
            # Fallback: entire file as single chunk
            chunks.append(
                RawChunk(
                    text=text,
                    start_line=1,
                    end_line=len(lines) if lines else 1,
                    metadata={
                        "language": path.suffix.lstrip(".").lower(),
                        "source_path": str(path),
                        "fallback": True,
                    },
                )
            )

        logger.info(
            f"CodeAdapter parsed {path}: {len(chunks)} chunks, "
            f"{len(lines)} lines"
        )
        return chunks
