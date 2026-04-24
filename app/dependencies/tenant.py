from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.system_settings import get_system_settings
from app.dependencies.auth import get_current_user_optional
from app.models import User


@dataclass
class TenantContext:
    institute_id: str
    allow_multi_tenant: bool


def resolve_tenant_context(
    db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)
) -> TenantContext:
    settings = get_system_settings(db)
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System settings not initialized.",
        )

    if not settings.allow_multi_tenant:
        if not settings.default_institute_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="default_institute_id is required in single-tenant mode.",
            )
        return TenantContext(
            institute_id=settings.default_institute_id, allow_multi_tenant=settings.allow_multi_tenant
        )

    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    return TenantContext(institute_id=current_user.institute_id, allow_multi_tenant=settings.allow_multi_tenant)
