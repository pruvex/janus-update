"""Source-first websearch v3 pipeline.

Phase 1 intentionally supports one narrow path: a single verified news source.
The existing websearch v2 stack remains separate/default unless v3 is explicitly enabled.
"""

from .pipeline import WebSearchV3Pipeline, execute_single_verified_news

__all__ = ["WebSearchV3Pipeline", "execute_single_verified_news"]
