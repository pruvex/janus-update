"""Shared helpers for ToolResultV1 (Global Skill Contract V1)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from backend.data.schemas_tools import SuggestionMetadata, ToolErrorDetails, ToolResultV1


def execution_time_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def tool_v1_metadata(
    started_at: float,
    *,
    relevance_tags: Optional[List[str]] = None,
    suggest_follow_up: bool = True,
    primary_entity_name: Optional[str] = None,
    primary_entity_id: Optional[str] = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"execution_time_ms": execution_time_ms(started_at)}
    sm = SuggestionMetadata(
        relevance_tags=list(relevance_tags or []),
        suggest_follow_up=suggest_follow_up,
        primary_entity_name=primary_entity_name,
        primary_entity_id=primary_entity_id,
    )
    meta["suggestion"] = sm.model_dump(exclude_none=True)
    return meta


def tool_ok_v1(
    data: Dict[str, Any],
    *,
    message: Optional[str] = None,
    tags: List[str],
    started_at: float,
    suggest_follow_up: bool = True,
    primary_entity_id: Optional[str] = None,
) -> ToolResultV1:
    return ToolResultV1(
        status="ok",
        data=data,
        message=message,
        metadata=tool_v1_metadata(
            started_at,
            relevance_tags=tags,
            suggest_follow_up=suggest_follow_up,
            primary_entity_id=primary_entity_id,
        ),
    )


def tool_err_v1(
    code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    started_at: Optional[float] = None,
    suggest_follow_up: bool = False,
) -> ToolResultV1:
    meta = None
    if started_at is not None:
        meta = tool_v1_metadata(
            started_at,
            relevance_tags=tags or [],
            suggest_follow_up=suggest_follow_up,
        )
    return ToolResultV1(
        status="error",
        data={},
        message=message,
        error=ToolErrorDetails(code=code, message=message, details=details),
        metadata=meta,
    )
