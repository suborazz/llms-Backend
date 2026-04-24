from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BatchDetail(Base):
    __tablename__ = "batch_details"

    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.batch_id"), primary_key=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    schedule_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(40), nullable=True)

    batch = relationship("Batch", back_populates="detail")

