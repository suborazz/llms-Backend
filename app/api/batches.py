from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import (
    TenantContext,
    get_current_user,
    get_db,
    require_roles,
    resolve_tenant_context,
)
from app.models import User
from app.schemas.batch import AssignTeacherRequest, BatchCreate, BatchRead, BatchTeacherRead, BatchUpdate
from app.services.batch_service import (
    assign_teacher_to_batch,
    create_batch,
    get_batch_detail,
    list_batches,
    list_batches_for_institute,
    update_batch,
)

router = APIRouter(tags=["Batches"])


@router.post(
    "/batches",
    response_model=BatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def add_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> BatchRead:
    return create_batch(db, payload, tenant)


@router.put(
    "/batches/{batch_id}",
    response_model=BatchRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def edit_batch(
    batch_id: str,
    payload: BatchUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> BatchRead:
    return update_batch(db, batch_id, payload, tenant)


@router.post(
    "/assign-teacher",
    response_model=BatchTeacherRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def assign_teacher(
    payload: AssignTeacherRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> BatchTeacherRead:
    return assign_teacher_to_batch(db, payload, tenant)


@router.get(
    "/batches",
    response_model=list[BatchRead],
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher", "student"))],
)
def get_batches(
    institute_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> list[BatchRead]:
    if institute_id:
        return list_batches_for_institute(db, institute_id, current_user)
    return list_batches(db, tenant, current_user)


@router.get(
    "/batches/{batch_id}/details",
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher", "student"))],
)
def batch_detail(
    batch_id: str,
    institute_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> dict:
    return get_batch_detail(db, batch_id, tenant, current_user, institute_id=institute_id)
