import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Institute LMS Backend"
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    auto_create_tables: bool = Field(default=True)

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/lms_db"
    )

    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    default_super_admin_email: str = Field(default="admin@gmail.com")
    default_super_admin_password: str = Field(default="Admin123")
    default_super_admin_first_name: str = Field(default="Super")
    default_super_admin_last_name: str = Field(default="Admin")
    default_super_admin_mob_no: str = Field(default="9999999999")

    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["https://lms-institute-psi.vercel.app"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    cors_expose_headers: Annotated[list[str], NoDecode] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "cors_origins",
        "cors_allow_methods",
        "cors_allow_headers",
        "cors_expose_headers",
        mode="before",
    )
    @classmethod
    def parse_list_env(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value

        raw = value.strip()
        if not raw:
            return []

        if raw.startswith("["):
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("Expected a JSON array.")
            return [str(item).strip() for item in parsed if str(item).strip()]

        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
