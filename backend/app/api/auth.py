from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token, generate_csrf_token
)
from app.core.auth import (
    get_current_user, set_auth_cookies, clear_auth_cookies, log_audit
)
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.audit_log import AuditAction

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: dict
    csrf_token: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    organization_id: int
    discipline: Optional[str] = None
    preferred_language: str = "en"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    organization_id: int
    discipline: Optional[str]
    preferred_language: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    csrf_token = generate_csrf_token()
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value, "org_id": user.organization_id})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    set_auth_cookies(response, access_token, refresh_token, csrf_token)
    
    log_audit(
        db=db,
        user_id=user.id,
        organization_id=user.organization_id,
        project_id=None,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )
    
    return LoginResponse(
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "organization_id": user.organization_id,
            "discipline": user.discipline,
            "preferred_language": user.preferred_language,
        },
        csrf_token=csrf_token,
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db),
):
    refresh_token = refresh_data.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    csrf_token = generate_csrf_token()
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value, "org_id": user.organization_id})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    set_auth_cookies(response, new_access_token, new_refresh_token, csrf_token)
    
    return {"csrf_token": csrf_token}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log_audit(
        db=db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        project_id=None,
        action=AuditAction.LOGOUT,
        entity_type="user",
        entity_id=current_user.id,
        request=request,
    )
    
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.SYSTEM_ADMIN and current_user.role != UserRole.CONTRACTOR_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create users")
    
    if current_user.role == UserRole.CONTRACTOR_ADMIN and user_data.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Can only create users in your organization")
    
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    org = db.query(Organization).filter(Organization.id == user_data.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        organization_id=user_data.organization_id,
        discipline=user_data.discipline,
        preferred_language=user_data.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_audit(
        db=db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        project_id=None,
        action=AuditAction.CREATE,
        entity_type="user",
        entity_id=user.id,
        new_values={"email": user.email, "role": user.role.value, "organization_id": user.organization_id},
        request=request,
    )
    
    return user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        users = db.query(User).all()
    else:
        users = db.query(User).filter(User.organization_id == current_user.organization_id).all()
    return users


@router.post("/csrf-token")
async def get_csrf_token(response: Response):
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return {"csrf_token": csrf_token}