"""Additive Streaming-Protokoll für LLM-Provider und Orchestrator (Phase 2 Turbo-Flow)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class StreamEvent:
    """Ein diskretes Streaming-Ereignis (Opus: type, content, metadata)."""

    type: str
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        """Serialisiert das Event als eine SSE-Data-Zeile (inkl. abschließender Leerzeilen)."""
        payload: Dict[str, Any] = {"type": self.type}
        if self.content is not None:
            payload["content"] = self.content
        if self.metadata:
            payload["metadata"] = self.metadata
        line = json.dumps(payload, ensure_ascii=False, default=str)
        return f"data: {line}\n\n"
