from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentProfile(Base):
    __tablename__ = "content_profiles"

    content_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contents.content_id"), primary_key=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="reading")
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    downloadable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    response_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    content = relationship("Content", back_populates="profile")

