from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_user
from core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from models.user import User, UserRole
from schemas.user import UserCreate, UserOut, LoginRequest, TokenResponse, RefreshRequest, SocialLoginRequest
from utils.auth0 import get_auth0_user_info

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenResponse:
    payload = {"sub": str(user.id), "role": user.role.value}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.password or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == int(data["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/social-login", response_model=TokenResponse)
async def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    info = await get_auth0_user_info(payload.access_token)
    email = info.get("email")
    auth0_id = info.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from provider")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=info.get("name", email),
            email=email,
            password=None,
            role=UserRole.CUSTOMER,
            auth0_id=auth0_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    return _issue_tokens(user)