import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    submission_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    content_id: Mapped[str] = mapped_column(String(36), ForeignKey("contents.content_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    response_type: Mapped[str] = mapped_column(String(40), nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

