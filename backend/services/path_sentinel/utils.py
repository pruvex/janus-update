"""Path Sentinel utility classes."""

import os
from pathlib import Path


class PathNormalizer:
    """Utility class for path normalization and comparison."""

    @staticmethod
    def normalize(path: str) -> str:
        """Normalize a path to absolute, case-folded (Windows), and normalized form."""
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        # Normalize path separators and resolve . and ..
        normalized = os.path.normpath(abs_path)
        # Case-fold for Windows (case-insensitive filesystem)
        return normalized.lower() if os.name == "nt" else normalized

    @staticmethod
    def is_subpath(parent: str, child: str) -> bool:
        """
        Check if child is a subpath of parent using prefix semantics.

        Examples:
            - 'D:\\Geheim' matches 'D:\\Geheim\\file.txt'
            - 'D:\\Geheim' does NOT match 'D:\\GeheimKram'

        Args:
            parent: The parent directory path
            child: The child path to check

        Returns:
            True if child is a subpath of parent, False otherwise
        """
        norm_parent = PathNormalizer.normalize(parent)
        norm_child = PathNormalizer.normalize(child)

        # Ensure parent ends with separator for proper prefix matching
        if not norm_parent.endswith(os.sep):
            norm_parent_with_sep = norm_parent + os.sep
        else:
            norm_parent_with_sep = norm_parent

        # Check if child starts with parent + separator
        if norm_child.startswith(norm_parent_with_sep):
            return True

        # Also check exact match
        return norm_child == norm_parent


class SystemPathBlocklist:
    """Blocklist for critical system paths that should never be accessed."""

    # Hardcoded critical Windows/System paths
    BLOCKED_PATTERNS = [
        "c:\\windows",
        "c:\\program files",
        "c:\\program files (x86)",
        "c:\\programdata",
        "%systemroot%",
        "%systemdrive%\\windows",
        "%systemdrive%\\program files",
        "%systemdrive%\\program files (x86)",
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
    ]

    @staticmethod
    def is_blocked(path: str) -> bool:
        """
        Check if a path is blocked by the system blocklist.

        Args:
            path: The path to check

        Returns:
            True if the path is blocked, False otherwise
        """
        norm_path = PathNormalizer.normalize(path)

        for blocked_pattern in SystemPathBlocklist.BLOCKED_PATTERNS:
            # Expand environment variables if present
            expanded_pattern = os.path.expandvars(blocked_pattern)
            norm_pattern = PathNormalizer.normalize(expanded_pattern)

            # Check if path is a subpath of blocked pattern or exact match
            if PathNormalizer.is_subpath(norm_pattern, norm_path) or norm_path == norm_pattern:
                return True

            # Also check if blocked pattern is a subpath of the path (e.g., accessing .git/config)
            if PathNormalizer.is_subpath(norm_path, norm_pattern):
                return True

            # Check if any path component matches the blocked pattern (for nested cases like subdir/.git)
            path_parts = norm_path.split(os.sep)
            for part in path_parts:
                if part == norm_pattern or part == blocked_pattern.lower():
                    return True

        return False
