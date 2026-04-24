from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("role_name", name="uq_role_name"),)

    role_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user_roles = relationship("UserRole", back_populates="role")
