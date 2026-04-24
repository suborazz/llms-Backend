from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("institute_id", "course_name", name="uq_course_name_institute"),
    )

    course_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    institute = relationship("Institute", back_populates="courses")
    subcourses = relationship("SubCourse", back_populates="course", cascade="all, delete-orphan")
