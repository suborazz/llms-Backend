from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Content, ContentProfile, Course, Module, SubCourse


def create_course(db: Session, course: Course) -> Course:
    db.add(course)
    db.flush()
    return course


def create_subcourse(db: Session, subcourse: SubCourse) -> SubCourse:
    db.add(subcourse)
    db.flush()
    return subcourse


def create_module(db: Session, module: Module) -> Module:
    db.add(module)
    db.flush()
    return module


def create_content(db: Session, content: Content) -> Content:
    db.add(content)
    db.flush()
    return content


def create_content_profile(db: Session, profile: ContentProfile) -> ContentProfile:
    db.add(profile)
    db.flush()
    return profile


def get_course(
    db: Session, course_id: str, institute_id: str, include_inactive: bool = True
) -> Course | None:
    stmt = select(Course).where(Course.course_id == course_id, Course.institute_id == institute_id)
    if not include_inactive:
        stmt = stmt.where(Course.active.is_(True))
    return db.scalar(stmt)


def get_subcourse(
    db: Session, subcourse_id: str, institute_id: str, include_inactive: bool = True
) -> SubCourse | None:
    stmt = select(SubCourse).where(
        SubCourse.subcourse_id == subcourse_id, SubCourse.institute_id == institute_id
    )
    if not include_inactive:
        stmt = stmt.where(SubCourse.active.is_(True))
    return db.scalar(stmt)


def get_module(
    db: Session, module_id: str, institute_id: str, include_inactive: bool = True
) -> Module | None:
    stmt = select(Module).where(Module.module_id == module_id, Module.institute_id == institute_id)
    if not include_inactive:
        stmt = stmt.where(Module.active.is_(True))
    return db.scalar(stmt)


def list_courses(db: Session, institute_id: str, include_inactive: bool = True) -> list[Course]:
    stmt = select(Course).where(Course.institute_id == institute_id).order_by(Course.course_name)
    if not include_inactive:
        stmt = stmt.where(Course.active.is_(True))
    return list(db.scalars(stmt).all())


def list_subcourses(
    db: Session, institute_id: str, course_id: str | None = None, include_inactive: bool = True
) -> list[SubCourse]:
    stmt = select(SubCourse).where(SubCourse.institute_id == institute_id)
    if course_id:
        stmt = stmt.where(SubCourse.course_id == course_id)
    if not include_inactive:
        stmt = stmt.where(SubCourse.active.is_(True))
    stmt = stmt.order_by(SubCourse.subcourse_name)
    return list(db.scalars(stmt).all())


def list_modules(
    db: Session,
    institute_id: str,
    course_id: str | None = None,
    subcourse_id: str | None = None,
    include_inactive: bool = True,
) -> list[Module]:
    stmt = select(Module).where(Module.institute_id == institute_id)
    if course_id:
        stmt = stmt.where(Module.course_id == course_id)
    if subcourse_id:
        stmt = stmt.where(Module.subcourse_id == subcourse_id)
    if not include_inactive:
        stmt = stmt.where(Module.active.is_(True))
    stmt = stmt.order_by(Module.module_name)
    return list(db.scalars(stmt).all())


def list_user_module_content(db: Session, module_ids: list[str], institute_id: str) -> list[Content]:
    if not module_ids:
        return []
    stmt = select(Content).where(Content.institute_id == institute_id, Content.module_id.in_(module_ids))
    return list(db.scalars(stmt).all())


def list_modules_by_subcourse(db: Session, subcourse_id: str, institute_id: str) -> list[Module]:
    stmt = select(Module).where(
        Module.subcourse_id == subcourse_id,
        Module.institute_id == institute_id,
        Module.active.is_(True),
    )
    return list(db.scalars(stmt).all())


def deactivate_course(db: Session, course: Course) -> None:
    course.active = False
    db.flush()


def deactivate_subcourse(db: Session, subcourse: SubCourse) -> None:
    subcourse.active = False
    db.flush()
