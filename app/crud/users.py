from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Auth, User, UserRole


USER_RELATIONS = (
    selectinload(User.institute),
    selectinload(User.roles).selectinload(UserRole.role),
)


def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user


def create_auth(db: Session, auth: Auth) -> Auth:
    db.add(auth)
    db.flush()
    return auth


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).options(*USER_RELATIONS).where(User.user_id == user_id))


def get_all_users(db: Session) -> list[User]:
    stmt = select(User).options(*USER_RELATIONS).order_by(User.created_at.desc())
    return list(db.scalars(stmt).all())


def get_users_by_institute(
    db: Session, institute_id: str, include_inactive: bool = True
) -> list[User]:
    stmt = (
        select(User)
        .options(*USER_RELATIONS)
        .where(User.institute_id == institute_id)
        .order_by(User.created_at.desc())
    )
    if not include_inactive:
        stmt = stmt.where(User.active.is_(True))
    return list(db.scalars(stmt).all())


def set_user_approval(db: Session, user: User, approved: bool) -> User:
    user.is_approved = approved
    db.flush()
    return user


def assign_user_role(db: Session, user_role: UserRole) -> UserRole:
    db.add(user_role)
    db.flush()
    return user_role


def deactivate_user(db: Session, user: User) -> None:
    user.active = False
    user.is_approved = False
    db.flush()
