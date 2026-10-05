"""week 3 login.same check as /users/login,this path is the auth one from the case study."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import LoginResponse, RefreshRequest, UserLogin, UserResponse
from app.services import user_service
from app.utils import get_current_user

router = APIRouter(tags=["Auth"])


@router.post("/auth/login", response_model=LoginResponse, summary="Login")
def auth_login(payload: UserLogin, db: Session = Depends(get_db)):
    return user_service.login_user(db, payload)


@router.post("/auth/token", response_model=LoginResponse, include_in_schema=False)
def auth_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return user_service.login_user(db, UserLogin(email=form.username, password=form.password))


@router.get("/auth/me", response_model=UserResponse, summary="Me")
def auth_me(current: User = Depends(get_current_user)):
    return UserResponse.model_validate(current)


@router.post("/auth/refresh", response_model=LoginResponse, summary="Refresh")
def auth_refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return user_service.refresh_session(db, payload)
