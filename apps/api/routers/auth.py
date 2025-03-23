from datetime import timedelta

from dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models.user import Token, User, UserCreate
from utils.security import create_access_token, get_password_hash, verify_password

from config import settings

router = APIRouter()

# Mock database for demonstration
# In a real app, replace this with actual database operations
mock_users = {
    "admin@example.com": {
        "id": 1,
        "email": "admin@example.com",
        "name": "Admin",
        "hashed_password": get_password_hash("password"),
    }
}


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    # Check if email already exists
    if user_data.email in mock_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    user_id = len(mock_users) + 1
    hashed_password = get_password_hash(user_data.password)

    # Store user in mock database
    mock_users[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
    }

    return {"id": user_id, "email": user_data.email, "name": user_data.name}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    # Check if user exists and password is correct
    user = mock_users.get(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"])}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user
