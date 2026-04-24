import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserBatch(Base):
    __tablename__ = "user_batches"
    __table_args__ = (UniqueConstraint("user_id", "batch_id", name="uq_user_batch"),)

    user_batch_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("batches.batch_id"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
