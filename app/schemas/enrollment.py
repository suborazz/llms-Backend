from pydantic import BaseModel

from app.schemas.common import ORMBase


class EnrollUserRequest(BaseModel):
    user_id: str
    course_id: str
    subcourse_id: str
    institute_id: str | None = None


class UserCourseRead(ORMBase):
    id: str
    institute_id: str
    user_id: str
    course_id: str
    subcourse_id: str


class AssignBatchRequest(BaseModel):
    user_id: str
    batch_id: str
    institute_id: str | None = None


class UserBatchRead(ORMBase):
    user_batch_id: str
    institute_id: str
    user_id: str
    batch_id: str
    active: bool
