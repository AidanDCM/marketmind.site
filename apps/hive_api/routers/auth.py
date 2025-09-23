from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from sqlalchemy.orm import Session

from packages.database.models.user import User as DBUser
from packages.shared.config import get_settings
from packages.shared.db import get_db

# Rate limiting setup
try:
    import os

    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    storage_uri = os.getenv("REDIS_URL") or "memory://"
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["100/minute"]  # Global default limit
    )
    
    # Custom rate limit handler for better error messages
    def auth_rate_limit_handler(request, exc):  # noqa: ARG001
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
            headers={"Retry-After": str(exc.retry_after)}
        )
        
except ImportError:  # pragma: no cover
    limiter = None
    auth_rate_limit_handler = None

router = APIRouter(prefix="/auth", tags=["auth"])

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
settings = get_settings()


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserInDB(UserBase):
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    meta: Optional[Dict[str, Any]] = None

    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_username(db: Session, username: str) -> Optional[DBUser]:
    return db.query(DBUser).filter(DBUser.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[DBUser]:
    return db.query(DBUser).filter(DBUser.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[DBUser]:
    # First try to find by username
    user = get_user_by_username(db, username)

    # If not found by username, try by email
    if not user and "@" in username:
        user = get_user_by_email(db, username)

    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# API Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # Check if username is already taken
    if get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
        )

    # Check if email is already registered
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(password)
    db_user = DBUser(
        username=username,
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,  # required for SlowAPI rate limiting
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Minimal role mapping for RBAC: superuser -> admin; otherwise editor
    role = "admin" if getattr(user, "is_superuser", False) else "editor"
    access_token = create_access_token(
        data={"sub": user.username, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Apply rate limiting decorator if available - must be after route definition
if limiter is not None:
    login_for_access_token = limiter.limit("5/minute")(login_for_access_token)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Check if token is in the blacklist
        # This would require a token blacklist implementation
        # if is_token_blacklisted(token):
        #     raise credentials_exception

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception from e

    user = get_user_by_username(db, username=token_data.username)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    return current_user
