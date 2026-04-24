from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Content(Base):
    __tablename__ = "contents"

    content_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    institute_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutes.institute_id"), nullable=False, index=True
    )
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("modules.module_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    module = relationship("Module", back_populates="contents")
    profile = relationship("ContentProfile", back_populates="content", uselist=False, cascade="all, delete-orphan")

    @property
    def category(self) -> str:
        return self.profile.category if self.profile is not None else self.type

    @property
    def body_text(self) -> str | None:
        return self.profile.body_text if self.profile is not None else None

    @property
    def instructions(self) -> str | None:
        return self.profile.instructions if self.profile is not None else None

    @property
    def downloadable(self) -> bool:
        return self.profile.downloadable if self.profile is not None else False

    @property
    def response_type(self) -> str | None:
        return self.profile.response_type if self.profile is not None else None
