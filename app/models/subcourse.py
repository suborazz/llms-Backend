from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SubCourse(Base):
    __tablename__ = "subcourses"
    __table_args__ = (
        UniqueConstraint("course_id", "subcourse_name", name="uq_subcourse_name_per_course"),
    )

    subcourse_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.course_id"), nullable=False)
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    subcourse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    course = relationship("Course", back_populates="subcourses")
    modules = relationship("Module", back_populates="subcourse", cascade="all, delete-orphan")
