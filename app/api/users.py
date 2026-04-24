from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import (
    TenantContext,
    get_current_user,
    get_db,
    require_roles,
    resolve_tenant_context,
)
from app.models import User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    AssignInstituteRequest,
    AssignRolesRequest,
    ProfileUpdateRequest,
    UserCreateRequest,
    UserApproveRequest,
    UserRead,
    UserUpdateRequest,
)
from app.services.user_service import (
    approve_user,
    assign_user_institute,
    assign_user_roles,
    create_user,
    delete_user,
    list_users,
    list_users_for_institute,
    update_profile,
    update_user,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_roles("super_admin", "institute_admin"))])
def get_users(
    institute_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> list[UserRead]:
    if institute_id:
        return list_users_for_institute(db, institute_id, current_user)
    return list_users(db, tenant, current_user)


@router.post(
    "",
    response_model=UserRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def add_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return create_user(db, payload, tenant, current_user)


@router.put(
    "/{user_id}/approve",
    response_model=UserRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def approve(
    user_id: str,
    payload: UserApproveRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> UserRead:
    return approve_user(db, user_id, payload.approve, tenant)


@router.put(
    "/{user_id}/assign-institute",
    response_model=UserRead,
    dependencies=[Depends(require_roles("super_admin"))],
)
def assign_institute(
    user_id: str, payload: AssignInstituteRequest, db: Session = Depends(get_db)
) -> UserRead:
    return assign_user_institute(db, user_id, payload.institute_id)


@router.post(
    "/{user_id}/roles",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def assign_roles(
    user_id: str,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> MessageResponse:
    roles = assign_user_roles(db, user_id, payload.role_names, tenant)
    return MessageResponse(message=f"Roles assigned: {', '.join(roles)}")


@router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def update_user_info(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return update_user(db, user_id, payload, tenant, current_user)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def remove_user(
    user_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    delete_user(db, user_id, tenant, current_user)
    return MessageResponse(message="User deleted successfully.")


@router.put("/me/profile", response_model=UserRead)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return update_profile(db, current_user, payload)
