from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class MarkModuleCompleteRequest(BaseModel):
    module_id: str
    completed: bool = True
    progress_percent: float = Field(default=100.0, ge=0.0, le=100.0)


class UserProgressRead(ORMBase):
    id: str
    institute_id: str
    user_id: str
    module_id: str
    completed: bool
    progress_percent: float
    last_accessed: datetime
