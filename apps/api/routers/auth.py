from datetime import timedelta

from dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

# Import from the shared mock database
from mock_user_database import MOCK_USERS_BY_EMAIL, add_mock_user
from models.user import Token, User, UserCreate
from utils.logger import get_logger
from utils.security import create_access_token, verify_password

from config import settings

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    logger.info(f"Registering new user: {user_data.email}")
    # Use the shared add_mock_user function
    new_user = add_mock_user(user_data.name, user_data.email, user_data.password)

    if new_user is None:
        logger.error(f"Email already registered: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Return only non-sensitive data
    return {"id": new_user["id"], "email": new_user["email"], "name": new_user["name"]}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    # Check if user exists and password is correct using shared data
    user = MOCK_USERS_BY_EMAIL.get(form_data.username)  # Use shared dict

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
