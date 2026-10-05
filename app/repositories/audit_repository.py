"""audit rows.the caller commits,so a failed save rolls the log back with the change."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, actor_id: int | None, action: str, resource: str, resource_id: int | None, detail: str) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            detail=detail,
        )
    )


def list_recent(db: Session, limit: int = 100) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    return list(db.scalars(statement).all())
