from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (
        UniqueConstraint("subcourse_id", "module_name", name="uq_module_name_per_subcourse"),
    )

    module_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.course_id"), nullable=False)
    subcourse_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subcourses.subcourse_id"), nullable=False
    )
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    module_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    subcourse = relationship("SubCourse", back_populates="modules")
    contents = relationship("Content", back_populates="module", cascade="all, delete-orphan")
