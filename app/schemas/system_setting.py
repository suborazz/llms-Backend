from pydantic import BaseModel

from app.schemas.common import ORMBase


class SystemSettingRead(ORMBase):
    id: str
    default_institute_id: str | None
    allow_multi_tenant: bool
