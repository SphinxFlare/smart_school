# app/deps/common.py


from typing import Generator

from sqlalchemy.orm import Session

from db.session import SessionLocal


# ---------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session per request.

    Ensures:
    - session is created
    - session is closed after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()