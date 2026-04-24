import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserCourse(Base):
    __tablename__ = "user_courses"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "subcourse_id", name="uq_user_course"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.course_id"), nullable=False)
    subcourse_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subcourses.subcourse_id"), nullable=False
    )
