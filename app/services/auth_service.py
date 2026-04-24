import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.crud import auth as auth_crud
from app.crud import courses as course_crud
from app.crud import enrollment as enrollment_crud
from app.crud import roles as roles_crud
from app.crud import system_settings as settings_crud
from app.crud import users as user_crud
from app.models import Auth, User, UserRole, UserSelectedCourse
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def register_user(db: Session, payload: RegisterRequest) -> User:
    if user_crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    settings = settings_crud.get_system_settings(db)
    if settings is None or not settings.default_institute_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System settings/default institute not configured.",
        )

    institute_id = settings.default_institute_id
    course = course_crud.get_course(db, payload.course_id, institute_id)
    subcourse = course_crud.get_subcourse(db, payload.subcourse_id, institute_id)
    if course is None or subcourse is None or subcourse.course_id != course.course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course/subcourse selection for default institute.",
        )

    user = User(
        user_id=str(uuid.uuid4()),
        institute_id=institute_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        mob_no=payload.mob_no,
        is_approved=False,
        active=True,
    )
    try:
        user_crud.create_user(db, user)
        user_crud.create_auth(
            db, Auth(user_id=user.user_id, password_hash=get_password_hash(payload.password))
        )

        student_role = roles_crud.get_role_by_name(db, "student")
        if student_role is None:
            student_role = roles_crud.create_role(db, "student")
        user_crud.assign_user_role(
            db, UserRole(user_id=user.user_id, role_id=student_role.role_id)
        )

        enrollment_crud.create_user_selected_course(
            db,
            UserSelectedCourse(
                user_id=user.user_id, course_id=payload.course_id, subcourse_id=payload.subcourse_id
            ),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration could not be completed because the record already exists.",
        ) from exc
    db.refresh(user)
    return user


def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = user_crud.get_user_by_email(db, payload.email)
    if user is None or user.auth is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    if not verify_password(payload.password, user.auth.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    if not user.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is pending approval.")

    auth_crud.update_last_login(db, user.auth)
    db.commit()
    role_names = roles_crud.get_role_names_for_user(db, user.user_id)
    token = create_access_token(user.user_id, institute_id=user.institute_id, roles=role_names)
    return TokenResponse(access_token=token)
