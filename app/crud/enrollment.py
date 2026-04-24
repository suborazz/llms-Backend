from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import UserCourse, UserModule, UserSelectedCourse


def create_user_selected_course(db: Session, selected: UserSelectedCourse) -> UserSelectedCourse:
    db.add(selected)
    db.flush()
    return selected


def list_user_selected_courses(db: Session, user_id: str) -> list[UserSelectedCourse]:
    return list(db.scalars(select(UserSelectedCourse).where(UserSelectedCourse.user_id == user_id)).all())


def delete_user_selected_courses(db: Session, user_id: str) -> None:
    db.execute(delete(UserSelectedCourse).where(UserSelectedCourse.user_id == user_id))


def create_user_course(db: Session, enrollment: UserCourse) -> UserCourse:
    db.add(enrollment)
    db.flush()
    return enrollment


def list_user_courses(db: Session, user_id: str, institute_id: str) -> list[UserCourse]:
    stmt = select(UserCourse).where(
        UserCourse.user_id == user_id, UserCourse.institute_id == institute_id
    )
    return list(db.scalars(stmt).all())


def create_user_module(db: Session, user_module: UserModule) -> UserModule:
    db.add(user_module)
    db.flush()
    return user_module


def list_user_modules(db: Session, user_id: str, institute_id: str) -> list[UserModule]:
    stmt = select(UserModule).where(
        UserModule.user_id == user_id, UserModule.institute_id == institute_id
    )
    return list(db.scalars(stmt).all())
