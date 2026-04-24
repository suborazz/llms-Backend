from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import enrollment as enrollment_crud
from app.crud import progress as progress_crud
from app.dependencies.tenant import TenantContext
from app.models import User, UserProgress
from app.schemas.progress import MarkModuleCompleteRequest


def mark_module_completion(
    db: Session, current_user: User, payload: MarkModuleCompleteRequest, tenant: TenantContext
) -> UserProgress:
    user_module_ids = {
        item.module_id
        for item in enrollment_crud.list_user_modules(db, current_user.user_id, tenant.institute_id)
    }
    if payload.module_id not in user_module_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found for the current user.",
        )

    progress = progress_crud.upsert_progress(
        db,
        user_id=current_user.user_id,
        module_id=payload.module_id,
        institute_id=tenant.institute_id,
        completed=payload.completed,
        percent=payload.progress_percent,
    )
    db.commit()
    db.refresh(progress)
    return progress


def list_my_progress(db: Session, current_user: User, tenant: TenantContext) -> list[UserProgress]:
    return progress_crud.list_progress(db, current_user.user_id, tenant.institute_id)
