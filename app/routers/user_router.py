"""only http here.actual checks are in schemas and services."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import LoginResponse, RegisterResponse, UserCreate, UserLogin, UserResponse
from app.services import user_service

router = APIRouter(tags=["Users"])


@router.post("/users/register", response_model=RegisterResponse, status_code=201, summary="Register")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = user_service.register_user(db, payload)
    return RegisterResponse(message="User registered successfully", user=UserResponse.model_validate(user))


@router.post("/users/login", response_model=LoginResponse, summary="Login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    return user_service.login_user(db, payload)
