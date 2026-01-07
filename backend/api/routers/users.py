from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user

router = APIRouter()

@router.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    """
    A protected endpoint to verify if the current user's token is valid.
    Requires the 'me' scope in the JWT token.
    """
    return {"status": "authenticated", "user": current_user}
