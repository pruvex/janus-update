"""
RAG V2 Code-Aware Chunking Engine

Provides AST-based chunking for source code files using tree-sitter
with a robust regex-based fallback for environments where tree-sitter
is not available or the parser fails.

Chunking Strategy:
- Top-level nodes: function_definition, class_definition, method_definition
- Each node becomes one Chunk with full source text
- Code-Prefixing: Module path + parent context + imports prepended to chunk text
- Fallback: Regex-based boundary detection (def/class/function)
- Ultimate fallback: Blank-line splitting (P1 behavior)
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("janus_backend")


# --- Local Chunk representation (avoids circular import with adapters.base) ---
@dataclass
class Chunk:
    """Local chunk representation — CodeAdapter maps these to RawChunk."""
    text: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def _read_text_safe(path: Path, encoding: str = "utf-8") -> str:
    """Read file as text with encoding fallback."""
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode failed for {path}, falling back to latin-1")
        return path.read_text(encoding="latin-1")


# --- Regex Patterns for Language-Specific Fallback Chunking ---
PYTHON_DEF_RE = re.compile(
    r"^(?:\s*@\w+(?:\([^)]*\))?\s*\n)*"  # decorators
    r"(?:async\s+)?(?:def|class)\s+\w+",    # def/class
    re.MULTILINE,
)

JS_TS_DEF_RE = re.compile(
    r"^(?:export\s+(?:default\s+)?)?"
    r"(?:async\s+)?"
    r"(?:function\s+\w+|class\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>|function))",
    re.MULTILINE,
)

JAVA_DEF_RE = re.compile(
    r"^(?:\s*(?:public|private|protected|static|final|abstract)\s+)*"
    r"(?:class|interface|enum|(?:\w+\s+)+\w+\s*\()",
    re.MULTILINE,
)

C_FAMILY_DEF_RE = re.compile(
    r"^(?:\s*(?:static|inline|extern|const)\s+)*"
    r"(?:\w+[\s\*]+)+\w+\s*\(|"
    r"^(?:class|struct|enum|union|namespace)\s+",
    re.MULTILINE,
)

GO_DEF_RE = re.compile(
    r"^func\s+(?:\([^)]*\)\s+)?\w+|^type\s+\w+\s+(?:struct|interface)",
    re.MULTILINE,
)

RUST_DEF_RE = re.compile(
    r"^(?:pub\s+)?(?:fn|struct|enum|impl|trait|type|mod|use)\s+",
    re.MULTILINE,
)


@dataclass
class SourceNode:
    """Represents a top-level code node extracted from source."""
    node_type: str
    name: str
    start_line: int
    end_line: int
    text: str
    parent: Optional[str] = None


# --- Tree-sitter Integration (with graceful fallback) ---

def _try_tree_sitter_chunk(path: Path, language: str) -> Optional[List[Chunk]]:
    """
    Attempt to parse the file with tree-sitter.

    Returns list of Chunks on success, None on failure.
    """
    try:
        import tree_sitter
        from tree_sitter import Language, Parser
        import tree_sitter_python as tspython
        import tree_sitter_javascript as tsjs
        import tree_sitter_typescript as tsts
    except ImportError:
        logger.debug(f"tree-sitter not installed, skipping AST parse for {path}")
        return None

    # Map file extension to tree-sitter language
    lang_map = {
        "py": tspython.language,
        "js": tsjs.language,
        "jsx": tsjs.language,
        "ts": tsts.language,
        "tsx": tsts.language,
    }

    lang = lang_map.get(language)
    if lang is None:
        logger.debug(f"No tree-sitter parser for language '{language}'")
        return None

    try:
        text = _read_text_safe(path)
        if not text.strip():
            return []

        parser = Parser(Language(lang))
        tree = parser.parse(bytes(text, "utf8"))
        root = tree.root_node

        chunks = []
        imports = _extract_imports_tree_sitter(root, text, language)
        import_block = "\n".join(imports) if imports else ""

        for node in root.children:
            node_type = node.type
            if node_type in ("function_definition", "class_definition", "decorated_definition"):
                # For decorated_definition, unwrap to get the actual def/class
                if node_type == "decorated_definition":
                    for child in node.children:
                        if child.type in ("function_definition", "class_definition"):
                            node = child
                            node_type = child.type
                            break

                name = _node_name(node, text) or "<anonymous>"
                start_line = node.start_point[0] + 1  # 0-indexed to 1-indexed
                end_line = node.end_point[0] + 1
                node_text = text[node.start_byte:node.end_byte]

                # Build context prefix
                prefix = _build_code_prefix(
                    source_path=str(path),
                    node_type=node_type,
                    name=name,
                    imports=imports,
                )

                chunk_text = f"{prefix}\n{node_text}" if prefix else node_text

                chunks.append(
                    Chunk(
                        text=chunk_text,
                        start_line=start_line,
                        end_line=end_line,
                        metadata={
                            "language": language,
                            "source_path": str(path),
                            "node_type": node_type,
                            "symbol_name": name,
                            "chunking_mode": "tree_sitter",
                        },
                    )
                )

        # If no top-level nodes found, fall back
        if not chunks:
            logger.debug(f"No top-level AST nodes found in {path}, falling back")
            return None

        logger.info(f"Tree-sitter parsed {path}: {len(chunks)} chunks")
        return chunks

    except Exception as e:
        logger.warning(f"Tree-sitter parse failed for {path}: {e}")
        return None


def _extract_imports_tree_sitter(root_node, text: str, language: str) -> List[str]:
    """Extract import statements from AST root."""
    imports = []
    import_types = {
        "py": ("import_statement", "import_from_statement"),
        "js": ("import_statement",),
        "jsx": ("import_statement",),
        "ts": ("import_statement",),
        "tsx": ("import_statement",),
    }
    target_types = import_types.get(language, ())

    for node in root_node.children:
        if node.type in target_types:
            import_text = text[node.start_byte:node.end_byte].strip()
            if import_text:
                imports.append(import_text)

    return imports


def _node_name(node, text: str) -> Optional[str]:
    """Extract the identifier name from an AST node."""
    for child in node.children:
        if child.type == "identifier":
            return text[child.start_byte:child.end_byte]
    return None


def _build_code_prefix(
    source_path: str,
    node_type: str,
    name: str,
    imports: List[str],
) -> str:
    """Build a context prefix for a code chunk."""
    lines = []
    lines.append(f"# Module: {source_path}")
    lines.append(f"# Symbol: {name} ({node_type})")
    if imports:
        lines.append(f"# Imports: {', '.join(imports[:5])}{'...' if len(imports) > 5 else ''}")
    return "\n".join(lines)


# --- Regex-Based Fallback Chunking ---

def _try_regex_chunk(path: Path, language: str) -> Optional[List[Chunk]]:
    """
    Attempt regex-based chunking for supported languages.

    Uses language-specific patterns to detect function/class boundaries.
    """
    pattern_map = {
        "py": PYTHON_DEF_RE,
        "js": JS_TS_DEF_RE,
        "jsx": JS_TS_DEF_RE,
        "ts": JS_TS_DEF_RE,
        "tsx": JS_TS_DEF_RE,
        "java": JAVA_DEF_RE,
        "c": C_FAMILY_DEF_RE,
        "cpp": C_FAMILY_DEF_RE,
        "h": C_FAMILY_DEF_RE,
        "hpp": C_FAMILY_DEF_RE,
        "cs": C_FAMILY_DEF_RE,
        "go": GO_DEF_RE,
        "rs": RUST_DEF_RE,
    }

    pattern = pattern_map.get(language)
    if pattern is None:
        logger.debug(f"No regex pattern for language '{language}', skipping regex fallback")
        return None

    try:
        text = _read_text_safe(path)
        if not text.strip():
            return []

        lines = text.splitlines(keepends=False)

        # Find all definition start positions
        matches = list(pattern.finditer(text))
        if len(matches) <= 1:
            logger.debug(f"Too few regex matches in {path}, falling back to blank-line")
            return None

        # Convert byte positions to line numbers
        line_starts = [0]
        for i, line in enumerate(lines):
            line_starts.append(line_starts[-1] + len(line) + 1)  # +1 for newline

        def byte_to_line(byte_pos: int) -> int:
            for i, start in enumerate(line_starts):
                if start > byte_pos:
                    return i
            return len(lines)

        chunks = []
        imports = _extract_imports_regex(text, language)

        for i, match in enumerate(matches):
            start_byte = match.start()
            start_line = byte_to_line(start_byte)

            if i + 1 < len(matches):
                end_byte = matches[i + 1].start()
                # Walk back to find a clean boundary (blank line or dedent)
                end_line = byte_to_line(end_byte)
            else:
                end_line = len(lines)

            # Extract the block text
            block_lines = lines[start_line - 1:end_line]
            block_text = "\n".join(block_lines)

            if not block_text.strip():
                continue

            # Try to extract name from first line
            first_line = block_lines[0] if block_lines else ""
            name = _extract_name_from_line(first_line, language) or "<block>"

            # Determine node type from pattern
            node_type = _infer_node_type(first_line, language)

            prefix = _build_code_prefix(
                source_path=str(path),
                node_type=node_type,
                name=name,
                imports=imports,
            )

            chunk_text = f"{prefix}\n{block_text}" if prefix else block_text

            chunks.append(
                Chunk(
                    text=chunk_text,
                    start_line=start_line,
                    end_line=end_line,
                    metadata={
                        "language": language,
                        "source_path": str(path),
                        "node_type": node_type,
                        "symbol_name": name,
                        "chunking_mode": "regex_fallback",
                    },
                )
            )

        if not chunks:
            return None

        logger.info(f"Regex fallback parsed {path}: {len(chunks)} chunks")
        return chunks

    except Exception as e:
        logger.warning(f"Regex fallback failed for {path}: {e}")
        return None


def _extract_imports_regex(text: str, language: str) -> List[str]:
    """Extract import statements using regex."""
    if language == "py":
        pattern = re.compile(r"^(?:from\s+\S+\s+import|import\s+\S+)", re.MULTILINE)
    elif language in ("js", "jsx", "ts", "tsx"):
        pattern = re.compile(r"^import\s+.*\s+from\s+['\"]", re.MULTILINE)
    elif language == "java":
        pattern = re.compile(r"^import\s+\S+;", re.MULTILINE)
    elif language == "go":
        pattern = re.compile(r"^import\s+(?:\(|\")", re.MULTILINE)
    elif language == "rs":
        pattern = re.compile(r"^use\s+\S+;", re.MULTILINE)
    else:
        return []

    return [m.group(0) for m in pattern.finditer(text)]


def _extract_name_from_line(line: str, language: str) -> Optional[str]:
    """Try to extract a symbol name from a definition line."""
    line = line.strip()

    # Python: def name( or class name:
    m = re.search(r"(?:def|class)\s+(\w+)", line)
    if m:
        return m.group(1)

    # JS/TS: function name( or class name { or const name =
    m = re.search(r"function\s+(\w+)|class\s+(\w+)|const\s+(\w+)", line)
    if m:
        return next((g for g in m.groups() if g), None)

    # Java/C#/Go/Rust: various patterns
    m = re.search(r"(?:fn|func|type)\s+(\w+)|(?:\w+\s+)*(\w+)\s*\(", line)
    if m:
        return next((g for g in m.groups() if g), None)

    return None


def _infer_node_type(line: str, language: str) -> str:
    """Infer whether a line starts a function or class."""
    line = line.strip().lower()
    if "class" in line:
        return "class_definition"
    if language == "py" and ("def " in line or "async def" in line):
        return "function_definition"
    if language in ("js", "jsx", "ts", "tsx") and "function" in line:
        return "function_definition"
    if language in ("go", "rs") and ("func " in line or "fn " in line):
        return "function_definition"
    if "struct" in line or "interface" in line or "enum" in line:
        return "type_definition"
    return "block"


# --- Blank-Line Fallback (P1 behavior) ---

def _blank_line_chunk(path: Path, language: str) -> List[Chunk]:
    """
    Ultimate fallback: split on blank lines (original P1 behavior).

    This ensures we always return chunks even when tree-sitter and regex both fail.
    """
    text = _read_text_safe(path)
    lines = text.splitlines(keepends=False)

    chunks: List[Chunk] = []
    current_lines: List[str] = []
    current_start = 1

    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            if current_lines:
                chunk_text = "\n".join(current_lines)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        start_line=current_start,
                        end_line=i - 1,
                        metadata={
                            "language": language,
                            "source_path": str(path),
                            "chunking_mode": "blank_line_fallback",
                        },
                    )
                )
                current_lines = []
            current_start = i + 1
        else:
            current_lines.append(line)

    if current_lines:
        chunk_text = "\n".join(current_lines)
        chunks.append(
            Chunk(
                text=chunk_text,
                start_line=current_start,
                end_line=len(lines),
                metadata={
                    "language": language,
                    "source_path": str(path),
                    "chunking_mode": "blank_line_fallback",
                },
            )
        )

    if not chunks:
        chunks.append(
            Chunk(
                text=text,
                start_line=1,
                end_line=len(lines) if lines else 1,
                metadata={
                    "language": language,
                    "source_path": str(path),
                    "chunking_mode": "blank_line_fallback",
                    "fallback": True,
                },
            )
        )

    logger.info(f"Blank-line fallback parsed {path}: {len(chunks)} chunks")
    return chunks


# --- Public API ---

def chunk_code_file(path: Path, language: Optional[str] = None) -> List[Chunk]:
    """
    Parse a code file into AST-aware chunks with cascading fallbacks.

    Strategy (in order):
    1. tree-sitter AST parsing (best quality)
    2. Regex-based boundary detection (good quality)
    3. Blank-line splitting (guaranteed to work)

    Each chunk includes:
    - Code context prefix (module path, symbol name, imports)
    - Full node text
    - Metadata (language, node_type, symbol_name, chunking_mode)
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if language is None:
        language = path.suffix.lstrip(".").lower()

    # Attempt 1: tree-sitter
    result = _try_tree_sitter_chunk(path, language)
    if result is not None:
        return result

    # Attempt 2: regex fallback
    result = _try_regex_chunk(path, language)
    if result is not None:
        return result

    # Attempt 3: blank-line fallback (guaranteed)
    return _blank_line_chunk(path, language)
