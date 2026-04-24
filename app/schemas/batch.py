import uuid

from pydantic import BaseModel

from app.schemas.common import ORMBase


class BatchCreate(BaseModel):
    course_id: str
    subcourse_id: str
    batch_name: str
    description: str | None = None
    room_name: str | None = None
    schedule_notes: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    batch_id: str | None = None
    institute_id: str | None = None
    active: bool = True


class BatchUpdate(BaseModel):
    course_id: str
    subcourse_id: str
    batch_name: str
    description: str | None = None
    room_name: str | None = None
    schedule_notes: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    institute_id: str | None = None
    active: bool = True


class BatchDetailInfo(ORMBase):
    description: str | None = None
    room_name: str | None = None
    schedule_notes: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class BatchRead(ORMBase):
    batch_id: str
    institute_id: str
    course_id: str
    subcourse_id: str
    batch_name: str
    active: bool
    detail: BatchDetailInfo | None = None


class AssignTeacherRequest(BaseModel):
    batch_id: str
    user_id: str
    institute_id: str | None = None


class BatchTeacherRead(ORMBase):
    id: str
    institute_id: str
    batch_id: str
    user_id: str


def batch_id_or_new(value: str | None) -> str:
    return value or str(uuid.uuid4())
