from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: UUID
    document_id: UUID
    status: str
    progress: int
    message: str | None = None
    error_type: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
