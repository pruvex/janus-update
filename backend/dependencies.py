from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta

# JWT Settings (in production, use environment variables and proper secrets management)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This is a simple user store for demo purposes
# In a real application, you would query a database here
VALID_USERS = {
    "local_user": {
        "username": "local_user",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 'secret'
        "disabled": False,
    }
}

# JWT Bearer for token authentication
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    security_scopes: SecurityScopes, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Dependency to get the current user from a JWT token and validate required scopes.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
        # Check scopes
        # This connects the validation to the scopes defined in main.py (e.g. ["settings:write"])
        token_scopes = payload.get("scopes", [])
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )

        # In a real app, you would validate the user against a database here
        user = VALID_USERS.get(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": authenticate_value},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
    except (jwt.JWTError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )

def check_api_keys_in_keyring() -> bool:
    """
    Check if the required API keys are present in the keyring.
    This is a placeholder - implement according to your keyring setup.
    """
    # Import keyring here to avoid circular imports
    import keyring
    
    # Check for OpenAI key as an example
    try:
        openai_key = keyring.get_password("Janus-Projekt", "openai")
        return openai_key is not None and len(openai_key) > 0
    except Exception as e:
        print(f"Error checking keyring: {e}")
        return False