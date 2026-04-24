from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Batch, BatchDetail, BatchTeacher, UserBatch


def create_batch(db: Session, batch: Batch) -> Batch:
    db.add(batch)
    db.flush()
    return batch


def create_batch_detail(db: Session, detail: BatchDetail) -> BatchDetail:
    db.add(detail)
    db.flush()
    return detail


def create_user_batch(db: Session, user_batch: UserBatch) -> UserBatch:
    db.add(user_batch)
    db.flush()
    return user_batch


def create_batch_teacher(db: Session, batch_teacher: BatchTeacher) -> BatchTeacher:
    db.add(batch_teacher)
    db.flush()
    return batch_teacher


def get_batch(db: Session, batch_id: str, institute_id: str) -> Batch | None:
    stmt = (
        select(Batch)
        .options(selectinload(Batch.detail))
        .where(Batch.batch_id == batch_id, Batch.institute_id == institute_id)
    )
    return db.scalar(stmt)


def list_batches(db: Session, institute_id: str) -> list[Batch]:
    stmt = (
        select(Batch)
        .options(selectinload(Batch.detail))
        .where(Batch.institute_id == institute_id)
        .order_by(Batch.batch_name)
    )
    return list(db.scalars(stmt).all())


def list_batch_teachers_for_user(db: Session, user_id: str, institute_id: str) -> list[BatchTeacher]:
    stmt = select(BatchTeacher).where(
        BatchTeacher.user_id == user_id, BatchTeacher.institute_id == institute_id
    )
    return list(db.scalars(stmt).all())


def list_user_batches_for_user(db: Session, user_id: str, institute_id: str) -> list[UserBatch]:
    stmt = select(UserBatch).where(UserBatch.user_id == user_id, UserBatch.institute_id == institute_id)
    return list(db.scalars(stmt).all())


def list_user_batches_for_batch(db: Session, batch_id: str, institute_id: str) -> list[UserBatch]:
    stmt = select(UserBatch).where(UserBatch.batch_id == batch_id, UserBatch.institute_id == institute_id)
    return list(db.scalars(stmt).all())


def list_batch_teachers_for_batch(db: Session, batch_id: str, institute_id: str) -> list[BatchTeacher]:
    stmt = select(BatchTeacher).where(
        BatchTeacher.batch_id == batch_id, BatchTeacher.institute_id == institute_id
    )
    return list(db.scalars(stmt).all())
