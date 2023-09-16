from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BaseDto(BaseModel):
    id: UUID
    created_at: datetime | None
    updated_at: datetime | None
