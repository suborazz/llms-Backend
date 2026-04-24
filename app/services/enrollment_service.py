from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import courses as course_crud
from app.crud import enrollment as enrollment_crud
from app.crud.users import get_user_by_id
from app.dependencies.tenant import TenantContext
from app.models import UserCourse, UserModule
from app.schemas.enrollment import EnrollUserRequest


def assign_user_to_course(db: Session, payload: EnrollUserRequest, tenant: TenantContext) -> UserCourse:
    institute_id = payload.institute_id if (tenant.allow_multi_tenant and payload.institute_id) else tenant.institute_id

    user = get_user_by_id(db, payload.user_id)
    if user is None or user.institute_id != institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    subcourse = course_crud.get_subcourse(db, payload.subcourse_id, institute_id)
    course = course_crud.get_course(db, payload.course_id, institute_id)
    if subcourse is None or course is None or subcourse.course_id != course.course_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course/subcourse not found.")

    enrollment = UserCourse(
        institute_id=institute_id,
        user_id=payload.user_id,
        course_id=payload.course_id,
        subcourse_id=payload.subcourse_id,
    )
    try:
        enrollment_crud.create_user_course(db, enrollment)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already enrolled for selected course."
        ) from exc

    modules = course_crud.list_modules_by_subcourse(db, payload.subcourse_id, institute_id)
    existing_module_ids = {
        item.module_id
        for item in enrollment_crud.list_user_modules(db, payload.user_id, institute_id)
    }
    for item in modules:
        if item.module_id not in existing_module_ids:
            enrollment_crud.create_user_module(
                db,
                UserModule(
                    institute_id=institute_id,
                    user_id=payload.user_id,
                    module_id=item.module_id,
                    active=True,
                ),
            )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enrollment modules could not be created for this user.",
        ) from exc
    db.refresh(enrollment)
    return enrollment
