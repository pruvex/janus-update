import logging

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from backend.data import crud, database, schemas
from backend.data.models import User
from backend.dependencies import get_current_user
from backend.utils.config_loader import load_config_data

logger = logging.getLogger("janus_backend")

router = APIRouter()


@router.get("/users/me", response_model=schemas.UserMeResponse)
async def read_users_me(
    db: Session = Depends(database.get_db),
    current_user: str = Security(get_current_user, scopes=["me"]),
):
    """Validate JWT and return the primary user's proactive-suggestion tier."""
    mode = crud.get_default_user_suggestion_mode(db)
    cfg = load_config_data()
    return {
        "status": "authenticated",
        "user": current_user,
        "suggestion_mode": mode,
        "last_used_provider": cfg.get("last_used_provider"),
        "last_used_model": cfg.get("last_used_model"),
    }


@router.patch("/users/me", response_model=schemas.UserMeResponse)
async def patch_users_me(
    body: schemas.UserSuggestionModeUpdate,
    db: Session = Depends(database.get_db),
    current_user: str = Security(get_current_user, scopes=["settings:write"]),
):
    """Persist ``suggestion_mode`` for the primary user row (creates a row if none exist)."""
    row = db.query(User).order_by(User.id.asc()).first()
    if row is None:
        row = User(
            username="local_user",
            hashed_password="-",
            is_active=True,
            suggestion_mode=int(body.suggestion_mode),
        )
        db.add(row)
    else:
        row.suggestion_mode = int(body.suggestion_mode)
    db.commit()
    db.refresh(row)
    mode = int(row.suggestion_mode)
    logger.info(f"[SETTINGS] User updated suggestion_mode to: {mode}")
    cfg = load_config_data()
    return {
        "status": "authenticated",
        "user": current_user,
        "suggestion_mode": mode,
        "last_used_provider": cfg.get("last_used_provider"),
        "last_used_model": cfg.get("last_used_model"),
    }
