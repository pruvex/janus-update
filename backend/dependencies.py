from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta
import secrets

from backend.utils.config_loader import load_config_data


async def api_key_auth(internal_api_key: str = Header(..., alias="X-Janus-Internal-Key")):
    """
    Dependency to authenticate requests via an internal API key in the header.
    """
    if not internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal API Key missing",
        )
    
    config = load_config_data()
    correct_api_key = config.get("api_key")

    if not correct_api_key:
        # This case should ideally not happen if bootstrap is correct
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key not configured on the server."
        )

    if not secrets.compare_digest(internal_api_key, correct_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Internal API Key",
        )

# JWT Settings (in production, use environment variables and proper secrets management)
def _get_or_generate_jwt_secret() -> str:
    """
    Get JWT secret from environment, config.json, or generate a new one.
    Persists generated secrets to config.json for future runs.
    """
    # First, check environment variable
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret:
        logger = __import__('logging').getLogger("janus_backend")
        logger.info("JWT_SECRET_KEY loaded from environment variable.")
        return env_secret
    
    # Second, check config.json
    try:
        config = load_config_data()
        config_secret = config.get("jwt_secret_key")
        if config_secret:
            logger = __import__('logging').getLogger("janus_backend")
            logger.info("JWT_SECRET_KEY loaded from config.json.")
            return config_secret
    except Exception as e:
        logger = __import__('logging').getLogger("janus_backend")
        logger.warning(f"Failed to load config for JWT secret: {e}")
    
    # Third, generate a new secret
    generated_secret = secrets.token_hex(32)
    logger = __import__('logging').getLogger("janus_backend")
    logger.warning(
        "JWT_SECRET_KEY not set in environment or config.json. "
        "Generated ephemeral key. Tokens will not survive restarts. "
        "Set JWT_SECRET_KEY environment variable or add 'jwt_secret_key' to config.json for production."
    )
    
    # Try to persist to config.json
    try:
        config = load_config_data()
        config["jwt_secret_key"] = generated_secret
        from backend.utils.config_loader import save_config_data
        save_config_data(config)
        logger.info("Generated JWT_SECRET_KEY persisted to config.json.")
    except Exception as e:
        logger.warning(f"Failed to persist generated JWT secret to config.json: {e}")
    
    return generated_secret

SECRET_KEY = _get_or_generate_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 💎 FIX-AUTH-068: Erhöht auf 24h (1440 Minuten)

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
    from backend.services.ollama_manager import ollama_manager
    
    # Check cloud keys
    try:
        openai_key = keyring.get_password("Janus-Projekt", "openai")
        gemini_key = keyring.get_password("Janus-Projekt", "gemini")
        has_cloud_key = bool(openai_key) or bool(gemini_key)
        has_local_provider = bool(ollama_manager.check_ollama().get("running"))
        return has_cloud_key or has_local_provider
    except Exception as e:
        print(f"Error checking keyring: {e}")
        return False