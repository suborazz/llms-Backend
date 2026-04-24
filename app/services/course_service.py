import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import batches as batch_crud
from app.crud import courses as course_crud
from app.crud import roles as roles_crud
from app.crud import system_settings as settings_crud
from app.dependencies.tenant import TenantContext
from app.models import Content, ContentProfile, Course, Module, SubCourse, User
from app.schemas.course import (
    ContentCreate,
    CourseCreate,
    CourseUpdate,
    ModuleCreate,
    ModuleRead,
    SubCourseCreate,
    SubCourseUpdate,
)


def _institute_id(payload_institute: str | None, tenant: TenantContext) -> str:
    if payload_institute and tenant.allow_multi_tenant:
        return payload_institute
    return tenant.institute_id


def _include_inactive_for_user(db: Session, current_user: User) -> bool:
    return "super_admin" in set(roles_crud.get_role_names_for_user(db, current_user.user_id))


def _role_names(db: Session, current_user: User) -> set[str]:
    return set(roles_crud.get_role_names_for_user(db, current_user.user_id))


def _teacher_scope(
    db: Session, current_user: User, institute_id: str
) -> tuple[set[str], set[tuple[str, str]]]:
    assignments = batch_crud.list_batch_teachers_for_user(db, current_user.user_id, institute_id)
    batches = {
        batch.batch_id: batch
        for batch in batch_crud.list_batches(db, institute_id)
        if batch.batch_id in {assignment.batch_id for assignment in assignments}
    }
    course_ids = {batch.course_id for batch in batches.values()}
    course_pairs = {(batch.course_id, batch.subcourse_id) for batch in batches.values()}
    return course_ids, course_pairs


def _validate_teacher_scope(
    db: Session, current_user: User, institute_id: str, course_id: str, subcourse_id: str
) -> None:
    role_names = _role_names(db, current_user)
    if "teacher" not in role_names or "super_admin" in role_names or "institute_admin" in role_names:
        return
    _, course_pairs = _teacher_scope(db, current_user, institute_id)
    if (course_id, subcourse_id) not in course_pairs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can only manage course data for their assigned batches.",
        )


def create_course(
    db: Session, payload: CourseCreate, tenant: TenantContext, current_user: User
) -> Course:
    institute_id = _institute_id(payload.institute_id, tenant)
    if "teacher" in _role_names(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot create top-level courses.",
        )
    course = Course(
        course_id=payload.course_id or str(uuid.uuid4()),
        institute_id=institute_id,
        course_name=payload.course_name,
        active=payload.active,
    )
    try:
        course_crud.create_course(db, course)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course already exists for this institute.",
        ) from exc
    db.refresh(course)
    return course


def create_subcourse(
    db: Session, payload: SubCourseCreate, tenant: TenantContext, current_user: User
) -> SubCourse:
    institute_id = _institute_id(payload.institute_id, tenant)
    if "teacher" in _role_names(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot create top-level subcourses.",
        )
    course = course_crud.get_course(db, payload.course_id, institute_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    subcourse = SubCourse(
        subcourse_id=payload.subcourse_id or str(uuid.uuid4()),
        course_id=payload.course_id,
        institute_id=institute_id,
        subcourse_name=payload.subcourse_name,
        active=payload.active,
    )
    try:
        course_crud.create_subcourse(db, subcourse)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subcourse already exists for this course.",
        ) from exc
    db.refresh(subcourse)
    return subcourse


def create_module(
    db: Session, payload: ModuleCreate, tenant: TenantContext, current_user: User
) -> Module:
    institute_id = _institute_id(payload.institute_id, tenant)
    subcourse = course_crud.get_subcourse(db, payload.subcourse_id, institute_id)
    if subcourse is None or subcourse.course_id != payload.course_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcourse not found.")
    _validate_teacher_scope(
        db, current_user, institute_id, payload.course_id, payload.subcourse_id
    )
    module = Module(
        module_id=payload.module_id or str(uuid.uuid4()),
        course_id=payload.course_id,
        subcourse_id=payload.subcourse_id,
        institute_id=institute_id,
        module_name=payload.module_name,
        active=payload.active,
    )
    try:
        course_crud.create_module(db, module)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Module already exists for this subcourse.",
        ) from exc
    db.refresh(module)
    return module


def create_content(
    db: Session, payload: ContentCreate, tenant: TenantContext, current_user: User
) -> Content:
    institute_id = _institute_id(payload.institute_id, tenant)
    module = db.get(Module, payload.module_id)
    if module is None or module.institute_id != institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")
    _validate_teacher_scope(
        db, current_user, institute_id, module.course_id, module.subcourse_id
    )
    content = Content(
        content_id=payload.content_id or str(uuid.uuid4()),
        institute_id=institute_id,
        module_id=payload.module_id,
        title=payload.title,
        type=payload.type,
        url=payload.url,
        duration=payload.duration,
    )
    try:
        course_crud.create_content(db, content)
        course_crud.create_content_profile(
            db,
            ContentProfile(
                content_id=content.content_id,
                category=payload.category,
                body_text=payload.body_text,
                instructions=payload.instructions,
                downloadable=payload.downloadable,
                response_type=payload.response_type,
            ),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Content could not be created with the provided identifiers.",
        ) from exc
    db.refresh(content)
    return content


def list_courses(db: Session, tenant: TenantContext, current_user: User) -> list[Course]:
    return list_courses_for_institute(db, tenant.institute_id, current_user)


def list_courses_for_institute(
    db: Session, institute_id: str, current_user: User
) -> list[Course]:
    role_names = _role_names(db, current_user)
    courses = course_crud.list_courses(
        db, institute_id, include_inactive=_include_inactive_for_user(db, current_user)
    )
    if "teacher" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        course_ids, _ = _teacher_scope(db, current_user, institute_id)
        return [course for course in courses if course.active and course.course_id in course_ids]
    return courses


def list_subcourses(
    db: Session, tenant: TenantContext, current_user: User, course_id: str | None = None
) -> list[SubCourse]:
    return list_subcourses_for_institute(db, tenant.institute_id, current_user, course_id)


def list_subcourses_for_institute(
    db: Session, institute_id: str, current_user: User, course_id: str | None = None
) -> list[SubCourse]:
    role_names = _role_names(db, current_user)
    subcourses = course_crud.list_subcourses(
        db,
        institute_id,
        course_id,
        include_inactive=_include_inactive_for_user(db, current_user),
    )
    if "teacher" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        _, course_pairs = _teacher_scope(db, current_user, institute_id)
        return [
            subcourse
            for subcourse in subcourses
            if subcourse.active and (subcourse.course_id, subcourse.subcourse_id) in course_pairs
        ]
    return subcourses


def list_modules(
    db: Session,
    tenant: TenantContext,
    current_user: User,
    course_id: str | None = None,
    subcourse_id: str | None = None,
) -> list[Module]:
    return list_modules_for_institute(
        db, tenant.institute_id, current_user, course_id=course_id, subcourse_id=subcourse_id
    )


def list_modules_for_institute(
    db: Session,
    institute_id: str,
    current_user: User,
    course_id: str | None = None,
    subcourse_id: str | None = None,
) -> list[Module]:
    role_names = _role_names(db, current_user)
    modules = course_crud.list_modules(
        db,
        institute_id,
        course_id,
        subcourse_id,
        include_inactive=_include_inactive_for_user(db, current_user),
    )
    if "teacher" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        _, course_pairs = _teacher_scope(db, current_user, institute_id)
        return [
            module
            for module in modules
            if module.active and (module.course_id, module.subcourse_id) in course_pairs
        ]
    return modules


def update_course(db: Session, course_id: str, payload: CourseUpdate, tenant: TenantContext) -> Course:
    institute_id = _institute_id(payload.institute_id, tenant)
    course = course_crud.get_course(db, course_id, institute_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    course.course_name = payload.course_name
    course.active = payload.active
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course update conflicts with existing data.",
        ) from exc
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: str, tenant: TenantContext) -> None:
    course = course_crud.get_course(db, course_id, tenant.institute_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    try:
        course_crud.deactivate_course(db, course)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course cannot be deactivated because it is still in use.",
        ) from exc


def update_subcourse(
    db: Session, subcourse_id: str, payload: SubCourseUpdate, tenant: TenantContext
) -> SubCourse:
    institute_id = _institute_id(payload.institute_id, tenant)
    subcourse = course_crud.get_subcourse(db, subcourse_id, institute_id)
    if subcourse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcourse not found.")

    course = course_crud.get_course(db, payload.course_id, institute_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    subcourse.course_id = payload.course_id
    subcourse.subcourse_name = payload.subcourse_name
    subcourse.active = payload.active
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subcourse update conflicts with existing data.",
        ) from exc
    db.refresh(subcourse)
    return subcourse


def delete_subcourse(db: Session, subcourse_id: str, tenant: TenantContext) -> None:
    subcourse = course_crud.get_subcourse(db, subcourse_id, tenant.institute_id)
    if subcourse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcourse not found.")
    try:
        course_crud.deactivate_subcourse(db, subcourse)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subcourse cannot be deactivated because it is still in use.",
        ) from exc


def list_public_courses(db: Session) -> list[Course]:
    settings = settings_crud.get_system_settings(db)
    if settings is None or not settings.default_institute_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System settings/default institute not configured.",
        )
    return course_crud.list_courses(db, settings.default_institute_id, include_inactive=False)


def list_public_subcourses(db: Session, course_id: str | None = None) -> list[SubCourse]:
    settings = settings_crud.get_system_settings(db)
    if settings is None or not settings.default_institute_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System settings/default institute not configured.",
        )
    return course_crud.list_subcourses(
        db, settings.default_institute_id, course_id, include_inactive=False
    )
