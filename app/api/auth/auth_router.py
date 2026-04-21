# app/api/auth/auth_router.py


from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext

from app.deps.common import get_db
from app.api.auth.auth_schema import LoginRequest, TokenResponse

from domains.identity.repositories.accounts.user_repository import UserRepository

# ---------------------------------------------------------------------
# Config (move to settings later)
# ---------------------------------------------------------------------

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------------------------------
# Login Endpoint
# ---------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    """

    user_repo = UserRepository()

    # 🔴 IMPORTANT: requires school_id
    # Since you're using schema-based multitenancy,
    # user lookup should work without explicit school_id
    user = user_repo.get_by_email(db, None, payload.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    # Create token
    token = create_access_token(
        data={
            "sub": str(user.id),
            "school_id": str(user.school_id)  # useful later
        }
    )

    return TokenResponse(access_token=token)