"""week 3 login.same check as /users/login,this path is the auth one from the case study."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import LoginResponse, UserLogin
from app.services import user_service

router = APIRouter(tags=["Auth"])


@router.post("/auth/login", response_model=LoginResponse, summary="Login and receive a JWT")
def auth_login(payload: UserLogin, db: Session = Depends(get_db)):
    return user_service.login_user(db, payload)
