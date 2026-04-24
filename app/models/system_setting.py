import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    default_institute_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=True
    )
    allow_multi_tenant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    default_institute = relationship("Institute")
