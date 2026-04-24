import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.crud import institutes as institute_crud
from app.crud import roles as roles_crud
from app.crud import users as users_crud
from app.models import Auth, Institute, User, UserRole
from app.schemas.institute import InstituteCreate, InstituteUpdate


def _get_or_create_role_id(db: Session, role_name: str) -> str:
    role = roles_crud.get_role_by_name(db, role_name)
    if role is None:
        role = roles_crud.create_role(db, role_name)
    return role.role_id


def _get_primary_institute_admin(db: Session, institute_id: str) -> User | None:
    for user in users_crud.get_users_by_institute(db, institute_id, include_inactive=True):
        role_names = set(roles_crud.get_role_names_for_user(db, user.user_id))
        if "institute_admin" in role_names:
            return user
    return None


def create_institute(db: Session, payload: InstituteCreate) -> Institute:
    if users_crud.get_user_by_email(db, str(payload.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institute email is already used by another login account.",
        )

    institute = Institute(
        institute_id=payload.institute_id or str(uuid.uuid4()),
        name=payload.name,
        email=str(payload.email),
        mob_no=payload.mob_no,
        country=payload.country,
        state=payload.state,
        place=payload.place,
        pincode=payload.pincode,
        active=payload.active,
    )
    try:
        institute_crud.create_institute(db, institute)
        admin_user = User(
            user_id=str(uuid.uuid4()),
            institute_id=institute.institute_id,
            first_name=payload.admin_first_name,
            last_name=payload.admin_last_name,
            email=str(payload.email),
            mob_no=payload.mob_no,
            is_approved=True,
            active=payload.active,
        )
        users_crud.create_user(db, admin_user)
        users_crud.create_auth(
            db,
            Auth(
                user_id=admin_user.user_id,
                password_hash=get_password_hash(payload.admin_password),
            ),
        )
        users_crud.assign_user_role(
            db,
            UserRole(
                id=str(uuid.uuid4()),
                user_id=admin_user.user_id,
                role_id=_get_or_create_role_id(db, "institute_admin"),
            ),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institute already exists with this email or identifier.",
        ) from exc
    db.refresh(institute)
    return institute


def list_institutes(db: Session, current_user: User) -> list[Institute]:
    current_roles = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "super_admin" in current_roles:
        return institute_crud.get_all_institutes(db, include_inactive=True)
    return (
        [current_user.institute]
        if current_user.institute is not None and current_user.institute.active
        else []
    )


def update_institute(db: Session, institute_id: str, payload: InstituteUpdate) -> Institute:
    institute = institute_crud.get_institute_by_id(db, institute_id)
    if institute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institute not found.")

    existing_user = users_crud.get_user_by_email(db, str(payload.email))
    primary_admin = _get_primary_institute_admin(db, institute_id)
    if existing_user is not None and (primary_admin is None or existing_user.user_id != primary_admin.user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institute email is already used by another login account.",
        )

    institute.name = payload.name
    institute.email = str(payload.email)
    institute.mob_no = payload.mob_no
    institute.country = payload.country
    institute.state = payload.state
    institute.place = payload.place
    institute.pincode = payload.pincode
    institute.active = payload.active

    if primary_admin is None and payload.admin_password:
        primary_admin = User(
            user_id=str(uuid.uuid4()),
            institute_id=institute.institute_id,
            first_name=payload.admin_first_name or "Institute",
            last_name=payload.admin_last_name or "Admin",
            email=str(payload.email),
            mob_no=payload.mob_no,
            is_approved=payload.active,
            active=payload.active,
        )
        users_crud.create_user(db, primary_admin)
        users_crud.create_auth(
            db,
            Auth(
                user_id=primary_admin.user_id,
                password_hash=get_password_hash(payload.admin_password),
            ),
        )
        users_crud.assign_user_role(
            db,
            UserRole(
                id=str(uuid.uuid4()),
                user_id=primary_admin.user_id,
                role_id=_get_or_create_role_id(db, "institute_admin"),
            ),
        )

    if primary_admin is not None:
        primary_admin.email = str(payload.email)
        primary_admin.mob_no = payload.mob_no
        primary_admin.active = payload.active
        primary_admin.is_approved = payload.active
        if payload.admin_first_name:
            primary_admin.first_name = payload.admin_first_name
        if payload.admin_last_name:
            primary_admin.last_name = payload.admin_last_name
        if payload.admin_password and primary_admin.auth is not None:
            primary_admin.auth.password_hash = get_password_hash(payload.admin_password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institute update conflicts with existing data.",
        ) from exc
    db.refresh(institute)
    return institute


def delete_institute(db: Session, institute_id: str) -> None:
    institute = institute_crud.get_institute_by_id(db, institute_id)
    if institute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institute not found.")

    try:
        primary_admin = _get_primary_institute_admin(db, institute_id)
        if primary_admin is not None:
            users_crud.deactivate_user(db, primary_admin)
        institute_crud.deactivate_institute(db, institute)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Institute cannot be deactivated because it is still in use.",
        ) from exc
