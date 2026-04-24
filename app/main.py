from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.services.bootstrap_service import bootstrap_defaults

settings = get_settings()
logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap_defaults(db)
    except Exception:
        db.rollback()
        logger.exception("Application startup failed while bootstrapping defaults.")
        raise
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
logger.info(f"CORS SETTINGS - Origins: {settings.cors_origins}")
logger.info(f"CORS SETTINGS - Methods: {settings.cors_allow_methods}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all for debugging
    allow_credentials=False, # Must be False if using "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
