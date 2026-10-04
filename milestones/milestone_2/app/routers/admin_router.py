"""admin routes.permission is checked here,shop rules stay in the service."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user_schema import RoleUpdate, UserResponse
from app.services import user_service
from app.utils.deps import require_permission

router = APIRouter(tags=["Admin"])


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse, summary="Change a user's role")
def change_role(
    user_id: int,
    payload: RoleUpdate,
    current: User = Depends(require_permission("user:role")),
    db: Session = Depends(get_db),
):
    user = user_service.change_role(db, current, user_id, payload)
    return UserResponse.model_validate(user)
