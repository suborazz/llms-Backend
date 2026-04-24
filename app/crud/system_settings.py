from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SystemSetting


def get_system_settings(db: Session) -> SystemSetting | None:
    return db.scalar(select(SystemSetting).limit(1))


def create_system_settings(
    db: Session, default_institute_id: str | None = None, allow_multi_tenant: bool = True
) -> SystemSetting:
    setting = SystemSetting(
        default_institute_id=default_institute_id, allow_multi_tenant=allow_multi_tenant
    )
    db.add(setting)
    db.flush()
    return setting
