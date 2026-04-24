from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mob_no: str
    password: str = Field(min_length=8)
    course_id: str
    subcourse_id: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
