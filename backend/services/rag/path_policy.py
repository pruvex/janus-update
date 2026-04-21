"""
RAG V2 Path Policy & Secret Guard

Security layer to prevent indexing of sensitive files and enforce workspace boundaries.

Hard denylist:
- .env, .pem, .key, .crt, .cert (secrets)
- node_modules, venv, .venv (dependency directories)
- .git (VCS metadata)
- .db, .sqlite, .sqlite3 (database files - they're for FTS/index, not content)
- __pycache__, .pytest_cache (build artifacts)

Path-Traversal protection:
- Resolves all paths to absolute
- Validates against allowed workspace root
- Rejects ../ or symlinks outside workspace

SecurityError is raised for violations.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger("janus_backend")


class SecurityError(Exception):
    """Raised when a file path violates security policy."""

    pass


# --- Hard Denylist (file names and extensions) ---

_DENYLIST_EXTENSIONS = frozenset(
    {
        # Secrets
        ".env",
        ".pem",
        ".key",
        ".crt",
        ".cert",
        ".p12",
        ".pfx",
        # Databases (indexed via FTS/index stores, not as content)
        ".db",
        ".sqlite",
        ".sqlite3",
    }
)

_DENYLIST_NAMES = frozenset(
    {
        # Secrets
        ".env",
        "secrets.json",
        "credentials.json",
        "api_key.txt",
        # Dependencies
        "node_modules",
        "venv",
        ".venv",
        ".virtualenv",
        # VCS metadata
        ".git",
        ".hg",
        ".svn",
        # Build artifacts
        "__pycache__",
        ".pytest_cache",
        ".tox",
        "dist",
        "build",
        # IDE
        ".idea",
        ".vscode",
        # OS
        ".DS_Store",
        "Thumbs.db",
    }
)

_DENYLIST_PATTERNS = frozenset(
    {
        # Hidden files (except .gitignore, .dockerignore which are safe)
        "*/.*/",
        # Lock files
        "package-lock.json",
        "yarn.lock",
        "poetry.lock",
    }
)


# --- Path-Traversal Protection ---

class PathPolicy:
    """
    Enforces path security policy for RAG ingestion.

    - Resolves paths to absolute
    - Validates against allowed workspace root
    - Checks denylist for sensitive files
    - Prevents path-traversal attacks (../, symlinks outside root)
    """

    def __init__(self, allowed_root: Path):
        """
        Initialize policy with allowed workspace root.

        Args:
            allowed_root: Absolute path to the workspace root.
                          All files to index must be within this directory.
        """
        self.allowed_root = Path(allowed_root).resolve()
        logger.debug(f"[PathPolicy] Allowed root set to: {self.allowed_root}")

    def is_allowed(self, file_path: Path) -> bool:
        """
        Check if a file path is allowed for indexing.

        Returns True if allowed, False if denied (without exception).
        """
        try:
            self.validate(file_path)
            return True
        except SecurityError:
            return False

    def validate(self, file_path: Path) -> None:
        """
        Validate a file path against security policy.

        Raises SecurityError if path violates policy.

        Args:
            file_path: File path to validate.
        """
        path = Path(file_path)

        # Resolve to absolute to catch symlinks and ../
        try:
            absolute = path.resolve()
        except Exception as e:
            raise SecurityError(f"Cannot resolve path '{file_path}': {e}")

        # Path-Traversal check: must be within allowed root
        try:
            absolute.relative_to(self.allowed_root)
        except ValueError:
            raise SecurityError(
                f"Path '{absolute}' is outside allowed workspace root '{self.allowed_root}'"
            )

        # Check denylist extensions
        ext = absolute.name.lower()
        if any(ext.endswith(d) for d in _DENYLIST_EXTENSIONS):
            raise SecurityError(f"File '{absolute}' has denied extension: {ext}")

        # Check denylist names
        name = absolute.name
        if name in _DENYLIST_NAMES:
            raise SecurityError(f"File '{absolute}' has denied name: {name}")

        # Check denylist patterns
        for pattern in _DENYLIST_PATTERNS:
            if pattern in str(absolute):
                raise SecurityError(f"File '{absolute}' matches denied pattern: {pattern}")

        # Additional check: hidden files (except allowlisted)
        if name.startswith(".") and name not in {".gitignore", ".dockerignore", ".env.example"}:
            raise SecurityError(f"File '{absolute}' is a hidden file (denied)")

    def get_denied_reason(self, file_path: Path) -> Optional[str]:
        """
        Get the reason a file is denied, or None if allowed.

        Useful for logging [SKIP] entries without raising exceptions.
        """
        path = Path(file_path)

        try:
            absolute = path.resolve()
        except Exception:
            return "Cannot resolve path"

        # Check root
        try:
            absolute.relative_to(self.allowed_root)
        except ValueError:
            return f"Outside allowed root: {self.allowed_root}"

        # Check denylist
        ext = absolute.name.lower()
        if any(ext.endswith(d) for d in _DENYLIST_EXTENSIONS):
            return f"Denied extension: {ext}"

        name = absolute.name
        if name in _DENYLIST_NAMES:
            return f"Denied name: {name}"

        for pattern in _DENYLIST_PATTERNS:
            if pattern in str(absolute):
                return f"Denied pattern: {pattern}"

        if name.startswith(".") and name not in {".gitignore", ".dockerignore", ".env.example"}:
            return "Hidden file denied"

        return None  # Allowed


# --- Singleton for global policy ---

_global_policy: Optional[PathPolicy] = None


def set_global_policy(allowed_root: Path) -> None:
    """Set the global path policy for RAG ingestion."""
    global _global_policy
    _global_policy = PathPolicy(allowed_root)
    logger.info(f"[PathPolicy] Global policy set to: {allowed_root}")


def get_global_policy() -> Optional[PathPolicy]:
    """Get the global path policy, or None if not set."""
    return _global_policy


def validate_path(file_path: Path) -> None:
    """
    Validate a file path using the global policy (if set).

    Raises SecurityError if policy is set and path violates it.
    """
    policy = get_global_policy()
    if policy:
        policy.validate(file_path)


def is_path_allowed(file_path: Path) -> bool:
    """
    Check if a file path is allowed using the global policy (if set).

    Returns True if allowed or no policy is set.
    """
    policy = get_global_policy()
    if policy:
        return policy.is_allowed(file_path)
    return True  # No policy = allow all (legacy behavior)
