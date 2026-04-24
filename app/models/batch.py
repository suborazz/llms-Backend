from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("institute_id", "batch_name", name="uq_batch_name_institute"),
    )

    batch_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.course_id"), nullable=False)
    subcourse_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subcourses.subcourse_id"), nullable=False
    )
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    detail = relationship("BatchDetail", back_populates="batch", uselist=False, cascade="all, delete-orphan")
