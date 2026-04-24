import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSelectedCourse(Base):
    __tablename__ = "user_selected_courses"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "subcourse_id", name="uq_user_selected_course"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.course_id"), nullable=False)
    subcourse_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subcourses.subcourse_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
