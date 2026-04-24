from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Institute


def create_institute(db: Session, institute: Institute) -> Institute:
    db.add(institute)
    db.flush()
    return institute


def get_all_institutes(db: Session, include_inactive: bool = True) -> list[Institute]:
    stmt = select(Institute)
    if not include_inactive:
        stmt = stmt.where(Institute.active.is_(True))
    stmt = stmt.order_by(Institute.name)
    return list(db.scalars(stmt).all())


def get_institute_by_id(
    db: Session, institute_id: str, include_inactive: bool = True
) -> Institute | None:
    stmt = select(Institute).where(Institute.institute_id == institute_id)
    if not include_inactive:
        stmt = stmt.where(Institute.active.is_(True))
    return db.scalar(stmt)


def deactivate_institute(db: Session, institute: Institute) -> None:
    institute.active = False
    db.flush()
