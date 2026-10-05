"""one audit row as the admin list returns it."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    action: str
    resource: str
    resource_id: int | None
    detail: str
    created_at: datetime
