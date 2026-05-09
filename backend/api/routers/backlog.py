from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from backend.services.backlog.parser import DEFAULT_BACKLOG_PATH, parse_backlog_file
from backend.services.backlog.schemas import BacklogItemsResponse

router = APIRouter(prefix="/backlog", tags=["Backlog"])


@router.get("/items", response_model=BacklogItemsResponse)
def list_backlog_items() -> BacklogItemsResponse:
    backlog_path = Path(DEFAULT_BACKLOG_PATH)
    if not backlog_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backlog file not found: {backlog_path}",
        )
    try:
        return parse_backlog_file(backlog_path)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read backlog file: {exc}",
        ) from exc
