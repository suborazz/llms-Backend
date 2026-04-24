from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMBase


class UserRead(ORMBase):
    user_id: str
    institute_id: str
    institute_name: str | None = None
    first_name: str
    last_name: str
    email: str
    mob_no: str
    is_approved: bool
    active: bool
    role_names: list[str] = []
    created_at: datetime


class UserApproveRequest(BaseModel):
    approve: bool = True


class AssignInstituteRequest(BaseModel):
    institute_id: str


class AssignRolesRequest(BaseModel):
    role_names: list[str]


class UserUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mob_no: str
    is_approved: bool = False
    active: bool = True
    institute_id: str | None = None
    role_names: list[str] | None = None


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mob_no: str
    password: str
    is_approved: bool = False
    active: bool = True
    institute_id: str | None = None
    role_names: list[str] = ["student"]


class ProfileUpdateRequest(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str | None = None
