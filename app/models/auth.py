from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Auth(Base):
    __tablename__ = "auth"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="auth")

    def mark_login(self) -> None:
        self.last_login = datetime.now(UTC)
