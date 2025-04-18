# apps/api/mock_user_database.py
from utils.logger import get_logger
from utils.security import get_password_hash

logger = get_logger(__name__)

# Structure: { user_id: {user_data}, ... }
MOCK_USERS_BY_ID = {
    1: {
        "id": 1,
        "email": "admin@example.com",
        "name": "Admin",
        "hashed_password": get_password_hash("password"),
    },
    2: {
        "id": 2,
        "email": "test@example.com",
        "name": "Test",
        "hashed_password": get_password_hash("password"),
    },
}

# Structure: { email: {user_data}, ... }
# We can generate this from MOCK_USERS_BY_ID for consistency
MOCK_USERS_BY_EMAIL = {user["email"]: user for user in MOCK_USERS_BY_ID.values()}


def add_mock_user(name, email, password):
    """Adds a new user to the mock database."""
    if email in MOCK_USERS_BY_EMAIL:
        logger.error(f"Email already registered: {email}")
        return None  # User already exists

    # Find the next available integer ID
    new_id = max(MOCK_USERS_BY_ID.keys()) + 1 if MOCK_USERS_BY_ID else 1
    hashed_password = get_password_hash(password)

    new_user_data = {
        "id": new_id,
        "email": email,
        "name": name,
        "hashed_password": hashed_password,
    }

    MOCK_USERS_BY_ID[new_id] = new_user_data
    MOCK_USERS_BY_EMAIL[email] = new_user_data
    return new_user_data
