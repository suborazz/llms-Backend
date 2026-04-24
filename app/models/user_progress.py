import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_user_progress"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("modules.module_id"), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    progress_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
