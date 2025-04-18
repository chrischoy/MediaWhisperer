import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from mock_user_database import MOCK_USERS_BY_ID
from models.user import User
from utils.logger import get_logger

from config import settings

logger = get_logger(__name__)

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

# Enable development mode bypass for authentication
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
DEV_USER_ID = int(os.getenv("DEV_USER_ID", "1"))


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    logger.info(f"Creating access token for user {data.get('sub')}")
    logger.debug(f"First 10 chars of secret key: {settings.SECRET_KEY[:10]}")
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        # Try to decode as a development token if it starts with "mock-token-"
        if token and token.startswith("mock-token-"):
            try:
                # Extract user ID from the mock token
                user_id = int(token.split("-")[-1])
                return {"sub": str(user_id)}
            except (ValueError, IndexError):
                return None
        return None


async def get_current_user(
    request: Request, token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current authenticated user."""
    logger.debug("\n=== Authentication Debug ===")
    logger.debug(f"DEV_MODE: {DEV_MODE}")
    logger.debug(f"Request headers: {request.headers.items()}")
    logger.debug(f"Authorization header: {token}")

    if DEV_MODE:
        logger.debug("DEV_MODE enabled, returning dev user")
        return User(id=DEV_USER_ID, email="dev@example.com", name="Dev User")

    if not token:
        logger.info("No token provided, raising 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        logger.debug(f"Payload: {payload}")
        user_id_str: str = payload.get("sub")  # Read as string from token
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing 'sub' claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert sub claim to integer for lookup
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: 'sub' claim is not a valid user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Use the shared mock database (lookup by integer ID)
    user_data = MOCK_USERS_BY_ID.get(user_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user model, excluding sensitive info like hashed_password if necessary
    # The User model itself should handle what fields are exposed
    return User(**user_data)
