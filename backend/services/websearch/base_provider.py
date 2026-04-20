"""WebSearchResult Contract - Diamond Standard Normalization Layer.

This module defines the provider-agnostic WebSearchResult contract that all
websearch providers MUST return. No rendering happens in providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, NotRequired, Optional, TypedDict


class WebSearchSource(TypedDict):
    """A single source from web search results."""
    url: str
    title: str
    snippet: NotRequired[str]
    confidence: NotRequired[float]  # 0.0-1.0, provider-optional


class WebSearchMetadata(TypedDict):
    """Metadata about the web search execution."""
    provider: str  # "openai" | "gemini" | "duckduckgo" | ...
    model: NotRequired[str]
    query_count: NotRequired[int]
    usage: NotRequired[Dict[str, Any]]
    cost: NotRequired[Dict[str, Any]]


class WebSearchResult(TypedDict):
    """Provider-agnostic web search result contract.
    
    All providers MUST return this exact structure. No Markdown, no HTML,
    no emojis in 'text'. Raw data only.
    """
    text: str  # Raw text WITHOUT rendering artifacts (no links, no formatting)
    sources: List[WebSearchSource]  # Normalized sources, never None (empty list OK)
    metadata: WebSearchMetadata


class BaseWebSearchProvider(ABC):
    """Abstract base class defining the interface for all web search providers.
    
    Implementations MUST return WebSearchResult with:
    - 'text' as raw content (no Markdown links, no HTML)
    - 'sources' as normalized list (empty if no sources available)
    - 'metadata' with provider identification
    """
    
    @abstractmethod
    async def search(
        self,
        api_key: str,
        query: str,
        model: Optional[str] = None
    ) -> WebSearchResult:
        """Execute web search and return normalized WebSearchResult.
        
        Returns:
            WebSearchResult with raw text, normalized sources, and metadata.
            NEVER returns None. On failure, raise RuntimeError.
        """
        pass


def validate_websearch_result(data: Any) -> WebSearchResult:
    """Validate that data conforms to WebSearchResult contract.
    
    Args:
        data: Any data structure to validate
        
    Returns:
        Validated WebSearchResult
        
    Raises:
        ValueError: If contract is violated with descriptive message
    """
    if not isinstance(data, dict):
        raise ValueError(f"WebSearchResult must be dict, got {type(data).__name__}")
    
    # Validate 'text' field
    if "text" not in data:
        raise ValueError("WebSearchResult missing required field 'text'")
    if not isinstance(data["text"], str):
        raise ValueError(f"WebSearchResult 'text' must be str, got {type(data['text']).__name__}")
    
    # Validate 'sources' field
    if "sources" not in data:
        raise ValueError("WebSearchResult missing required field 'sources'")
    if not isinstance(data["sources"], list):
        raise ValueError(f"WebSearchResult 'sources' must be list, got {type(data['sources']).__name__}")
    
    # Validate each source
    for i, source in enumerate(data["sources"]):
        if not isinstance(source, dict):
            raise ValueError(f"WebSearchResult sources[{i}] must be dict, got {type(source).__name__}")
        if "url" not in source:
            raise ValueError(f"WebSearchResult sources[{i}] missing required field 'url'")
        if not isinstance(source.get("url"), str):
            raise ValueError(f"WebSearchResult sources[{i}]['url'] must be str")
        if "title" not in source:
            # Auto-populate title from URL domain if missing
            from urllib.parse import urlparse
            domain = urlparse(source["url"]).netloc.replace("www.", "")
            source["title"] = domain or "Quelle"
    
    # Validate 'metadata' field
    if "metadata" not in data:
        raise ValueError("WebSearchResult missing required field 'metadata'")
    if not isinstance(data["metadata"], dict):
        raise ValueError(f"WebSearchResult 'metadata' must be dict, got {type(data['metadata']).__name__}")
    if "provider" not in data["metadata"]:
        raise ValueError("WebSearchResult metadata missing required field 'provider'")
    
    return data  # type: ignore[return-value]
