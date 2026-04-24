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
from app.schemas.course import (
    ContentCreate,
    ContentRead,
    CourseCreate,
    CourseRead,
    CourseUpdate,
    ModuleCreate,
    ModuleRead,
    SubCourseCreate,
    SubCourseRead,
    SubCourseUpdate,
)
from app.schemas.common import MessageResponse
from app.services.course_service import (
    create_content,
    create_course,
    create_module,
    create_subcourse,
    delete_course,
    delete_subcourse,
    list_courses,
    list_courses_for_institute,
    list_modules,
    list_modules_for_institute,
    list_subcourses,
    list_subcourses_for_institute,
    list_public_courses,
    list_public_subcourses,
    update_course,
    update_subcourse,
)

router = APIRouter(tags=["Courses"])


@router.post(
    "/courses",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def add_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> CourseRead:
    return create_course(db, payload, tenant, current_user)


@router.get("/courses", response_model=list[CourseRead], dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher", "student"))])
def get_courses(
    institute_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> list[CourseRead]:
    if institute_id:
        return list_courses_for_institute(db, institute_id, current_user)
    return list_courses(db, tenant, current_user)


@router.get(
    "/subcourses",
    response_model=list[SubCourseRead],
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher", "student"))],
)
def get_subcourses(
    institute_id: str | None = None,
    course_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> list[SubCourseRead]:
    if institute_id:
        return list_subcourses_for_institute(db, institute_id, current_user, course_id=course_id)
    return list_subcourses(db, tenant, current_user, course_id=course_id)


@router.get(
    "/modules",
    response_model=list[ModuleRead],
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher", "student"))],
)
def get_modules(
    institute_id: str | None = None,
    course_id: str | None = None,
    subcourse_id: str | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> list[ModuleRead]:
    if institute_id:
        return list_modules_for_institute(
            db, institute_id, current_user, course_id=course_id, subcourse_id=subcourse_id
        )
    return list_modules(db, tenant, current_user, course_id=course_id, subcourse_id=subcourse_id)


@router.get("/public/courses", response_model=list[CourseRead])
def get_public_courses(db: Session = Depends(get_db)) -> list[CourseRead]:
    return list_public_courses(db)


@router.get("/public/subcourses", response_model=list[SubCourseRead])
def get_public_subcourses(
    course_id: str | None = None, db: Session = Depends(get_db)
) -> list[SubCourseRead]:
    return list_public_subcourses(db, course_id=course_id)


@router.post(
    "/subcourses",
    response_model=SubCourseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def add_subcourse(
    payload: SubCourseCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> SubCourseRead:
    return create_subcourse(db, payload, tenant, current_user)


@router.post(
    "/modules",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher"))],
)
def add_module(
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> ModuleRead:
    return create_module(db, payload, tenant, current_user)


@router.post(
    "/content",
    response_model=ContentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("super_admin", "institute_admin", "teacher"))],
)
def add_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
    current_user: User = Depends(get_current_user),
) -> ContentRead:
    return create_content(db, payload, tenant, current_user)


@router.put(
    "/courses/{course_id}",
    response_model=CourseRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def edit_course(
    course_id: str,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> CourseRead:
    return update_course(db, course_id, payload, tenant)


@router.delete(
    "/courses/{course_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def remove_course(
    course_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> MessageResponse:
    delete_course(db, course_id, tenant)
    return MessageResponse(message="Course deleted successfully.")


@router.put(
    "/subcourses/{subcourse_id}",
    response_model=SubCourseRead,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def edit_subcourse(
    subcourse_id: str,
    payload: SubCourseUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> SubCourseRead:
    return update_subcourse(db, subcourse_id, payload, tenant)


@router.delete(
    "/subcourses/{subcourse_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles("super_admin", "institute_admin"))],
)
def remove_subcourse(
    subcourse_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(resolve_tenant_context),
) -> MessageResponse:
    delete_subcourse(db, subcourse_id, tenant)
    return MessageResponse(message="Subcourse deleted successfully.")
