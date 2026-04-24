from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import TenantContext, get_current_user, get_db, resolve_tenant_context
from app.models import User
from app.schemas.progress import MarkModuleCompleteRequest, UserProgressRead
from app.services.progress_service import list_my_progress, mark_module_completion

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post(
    "/mark-complete",
    response_model=UserProgressRead,
    status_code=status.HTTP_201_CREATED,
)
def mark_complete(
    payload: MarkModuleCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> UserProgressRead:
    return mark_module_completion(db, current_user, payload, tenant)


@router.get("/me", response_model=list[UserProgressRead])
def my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> list[UserProgressRead]:
    return list_my_progress(db, current_user, tenant)
