from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserProgress


def get_progress(db: Session, user_id: str, module_id: str, institute_id: str) -> UserProgress | None:
    stmt = select(UserProgress).where(
        UserProgress.user_id == user_id,
        UserProgress.module_id == module_id,
        UserProgress.institute_id == institute_id,
    )
    return db.scalar(stmt)


def upsert_progress(
    db: Session, *, user_id: str, module_id: str, institute_id: str, completed: bool, percent: float
) -> UserProgress:
    progress = get_progress(db, user_id, module_id, institute_id)
    if progress is None:
        progress = UserProgress(
            user_id=user_id,
            module_id=module_id,
            institute_id=institute_id,
            completed=completed,
            progress_percent=percent,
            last_accessed=datetime.now(UTC),
        )
        db.add(progress)
    else:
        progress.completed = completed
        progress.progress_percent = percent
        progress.last_accessed = datetime.now(UTC)
    db.flush()
    return progress


def list_progress(db: Session, user_id: str, institute_id: str) -> list[UserProgress]:
    stmt = select(UserProgress).where(
        UserProgress.user_id == user_id, UserProgress.institute_id == institute_id
    )
    return list(db.scalars(stmt).all())
