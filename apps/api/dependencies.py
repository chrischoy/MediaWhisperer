import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.user import User
from pydantic import BaseModel

from config import settings

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
    print("\n=== Authentication Debug ===")
    print(f"DEV_MODE: {DEV_MODE}")
    print(f"Request headers: {request.headers.items()}")
    print(f"Authorization header: {token}")

    if DEV_MODE:
        print("DEV_MODE enabled, returning dev user")
        return User(id=DEV_USER_ID, email="dev@example.com", name="Dev User")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing 'sub' claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In a real app, you would fetch the user from the database here
    # For now, we'll use the mock user
    mock_users = {1: {"id": 1, "email": "dev@example.com", "name": "Dev User"}}
    user = mock_users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(**user)
