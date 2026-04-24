from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.common import MessageResponse
from app.dependencies import get_current_user, get_db, require_roles
from app.models import User
from app.schemas.institute import InstituteCreate, InstituteRead, InstituteUpdate
from app.services.institute_service import (
    create_institute,
    delete_institute,
    list_institutes,
    update_institute,
)

router = APIRouter(prefix="/institutes", tags=["Institutes"])


@router.post(
    "", response_model=InstituteRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("super_admin"))]
)
def create(payload: InstituteCreate, db: Session = Depends(get_db)) -> InstituteRead:
    return create_institute(db, payload)


@router.get("", response_model=list[InstituteRead], dependencies=[Depends(require_roles("super_admin", "institute_admin"))])
def get_all(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[InstituteRead]:
    return list_institutes(db, current_user)


@router.put(
    "/{institute_id}",
    response_model=InstituteRead,
    dependencies=[Depends(require_roles("super_admin"))],
)
def update(
    institute_id: str, payload: InstituteUpdate, db: Session = Depends(get_db)
) -> InstituteRead:
    return update_institute(db, institute_id, payload)


@router.delete(
    "/{institute_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles("super_admin"))],
)
def delete(institute_id: str, db: Session = Depends(get_db)) -> MessageResponse:
    delete_institute(db, institute_id)
    return MessageResponse(message="Institute deleted successfully.")
