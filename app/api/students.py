from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import TenantContext, get_current_user, get_db, resolve_tenant_context
from app.models import User
from app.schemas.student import StudentSubmissionRequest
from app.services.student_service import (
    get_enrolled_courses,
    get_my_modules_with_content,
    get_student_batches,
    get_student_course_workspace,
    submit_student_content,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/enrolled-courses")
def enrolled_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> list[dict]:
    return get_enrolled_courses(db, current_user, tenant)


@router.get("/modules-content")
def modules_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> list[dict]:
    return get_my_modules_with_content(db, current_user, tenant)


@router.get("/batches")
def my_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> list[dict]:
    return get_student_batches(db, current_user, tenant)


@router.get("/course-workspace/{course_id}")
def course_workspace(
    course_id: str,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> dict:
    return get_student_course_workspace(db, current_user, tenant, course_id, category)


@router.post("/content-submissions", status_code=status.HTTP_201_CREATED)
def submit_content_response(
    payload: StudentSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> dict:
    try:
        return submit_student_content(
            db,
            current_user,
            tenant,
            payload.content_id,
            payload.response_type,
            payload.response_text,
            payload.response_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
