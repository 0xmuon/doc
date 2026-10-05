from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """one row per admin or payment change.admins can read the list."""

    __tablename__ = "AuditLogs"

    id: Mapped[int] = mapped_column("AuditLogID", Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int | None] = mapped_column("ActorID", ForeignKey("Users.UserID"), index=True)
    action: Mapped[str] = mapped_column("Action", String(40), nullable=False)
    resource: Mapped[str] = mapped_column("Resource", String(40), nullable=False)
    resource_id: Mapped[int | None] = mapped_column("ResourceID", Integer)
    detail: Mapped[str] = mapped_column("Detail", Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
