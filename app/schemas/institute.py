import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMBase


class InstituteBase(BaseModel):
    name: str
    email: EmailStr
    mob_no: str
    country: str
    state: str
    place: str
    pincode: str
    active: bool = True


class InstituteCreate(InstituteBase):
    institute_id: str | None = None
    admin_first_name: str = "Institute"
    admin_last_name: str = "Admin"
    admin_password: str = Field(min_length=8)


class InstituteUpdate(InstituteBase):
    admin_first_name: str | None = None
    admin_last_name: str | None = None
    admin_password: str | None = Field(default=None, min_length=8)


class InstituteRead(InstituteBase, ORMBase):
    institute_id: str
    email: str
    created_at: datetime
    updated_at: datetime


def institute_id_or_new(value: str | None) -> str:
    return value or str(uuid.uuid4())
