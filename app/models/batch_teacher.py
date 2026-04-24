import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BatchTeacher(Base):
    __tablename__ = "batch_teachers"
    __table_args__ = (UniqueConstraint("batch_id", "user_id", name="uq_batch_teacher"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.batch_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
