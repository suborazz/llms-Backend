import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.role_name == role_name))


def create_role(db: Session, role_name: str, active: bool = True) -> Role:
    role = Role(role_id=str(uuid.uuid4()), role_name=role_name, active=active)
    db.add(role)
    db.flush()
    return role


def get_role_names_for_user(db: Session, user_id: str) -> list[str]:
    from app.models import UserRole

    stmt = (
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user_id)
    )
    return list(db.scalars(stmt).all())
