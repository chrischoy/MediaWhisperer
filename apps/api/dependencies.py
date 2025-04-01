from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.user import User

from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


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


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Print debug info about the request
    print("Request headers:", request.headers)
    auth_header = request.headers.get("authorization")
    print("Authorization header:", auth_header)

    try:
        # Try to decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print("Decoded token payload:", payload)

        user_id: str = payload.get("sub")

        if user_id is None:
            print("No 'sub' claim in token")
            raise credentials_exception

        # Here you would typically fetch the user from database
        # For now, we'll simulate with a placeholder
        # In a real implementation, replace with database lookup
        user = User(id=user_id, email="user@example.com", name="User")
        print(f"Created user with id: {user_id}")

        if user is None:
            print("User not found")
            raise credentials_exception

        return user

    except JWTError as e:
        print(f"JWT Error: {str(e)}")

        # Development fallback - if token looks like a mock token from frontend
        if token and token.startswith("mock-token-"):
            print("Using development fallback for mock token")
            # Extract user ID from request if available
            user_id = token.split("-")[-1]
            return User(
                id=user_id or "1", email="dev@example.com", name="Development User"
            )

        # Try to parse the token as base64-encoded JSON
        try:
            import base64
            import json

            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            decoded = base64.b64decode(token).decode("utf-8")
            token_data = json.loads(decoded)
            print("Successfully decoded mock token:", token_data)

            user_id = token_data.get("sub")
            if user_id:
                print(f"Using mock token with user_id: {user_id}")
                return User(id=user_id, email="mock@example.com", name="Mock User")
        except Exception as e:
            print(f"Failed to parse mock token: {str(e)}")

        raise credentials_exception
