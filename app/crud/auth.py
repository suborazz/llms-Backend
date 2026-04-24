from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Auth


def update_last_login(db: Session, auth: Auth) -> Auth:
    auth.last_login = datetime.now(UTC)
    db.flush()
    return auth
