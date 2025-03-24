import logging
from sqlalchemy.orm import Session

from .session import engine, Base
from ..repositories.user import user_repository
from ..models.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Initialize the database with tables and basic data.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Created database tables")

    # Check if we need to create the initial admin user
    admin_email = "admin@example.com"
    db_user = user_repository.get_by_email(db, email=admin_email)
    
    if not db_user:
        # Create initial admin user
        user_in = UserCreate(
            email=admin_email,
            password="password",  # In production, use a secure password
            name="Admin",
        )
        user_repository.create(db, obj_in=user_in)
        logger.info(f"Created admin user: {admin_email}")
    else:
        logger.info(f"Admin user already exists: {admin_email}")


def create_initial_data(db: Session) -> None:
    """
    Create initial data in the database.
    This should be idempotent - safe to run multiple times.
    """
    logger.info("Creating initial data")
    init_db(db)
    logger.info("Initial data created")


if __name__ == "__main__":
    from ..database.session import SessionLocal
    
    db = SessionLocal()
    try:
        create_initial_data(db)
    finally:
        db.close()