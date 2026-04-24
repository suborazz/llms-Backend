import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import courses as course_crud
from app.crud import enrollment as enrollment_crud
from app.crud import roles as roles_crud
from app.crud import users as users_crud
from app.core.security import get_password_hash, verify_password
from app.dependencies.tenant import TenantContext
from app.models import Auth, User, UserCourse, UserModule, UserRole
from app.schemas.user import ProfileUpdateRequest, UserCreateRequest, UserRead, UserUpdateRequest


def _serialize_user(db: Session, user: User) -> UserRead:
    role_names = [user_role.role.role_name for user_role in user.roles if user_role.role is not None]
    if not role_names:
        role_names = roles_crud.get_role_names_for_user(db, user.user_id)

    return UserRead(
        user_id=user.user_id,
        institute_id=user.institute_id,
        institute_name=user.institute.name if user.institute else None,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mob_no=user.mob_no,
        is_approved=user.is_approved,
        active=user.active,
        role_names=sorted(role_names),
        created_at=user.created_at,
    )


def list_users(db: Session, tenant: TenantContext, current_user: User) -> list[UserRead]:
    return list_users_for_institute(db, tenant.institute_id, current_user)


def list_users_for_institute(
    db: Session, institute_id: str, current_user: User
) -> list[UserRead]:
    current_roles = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "super_admin" in current_roles:
        users = users_crud.get_all_users(db)
    else:
        users = users_crud.get_users_by_institute(db, institute_id, include_inactive=False)

    if "super_admin" in current_roles:
        users = [user for user in users if user.institute_id == institute_id]
    return [_serialize_user(db, user) for user in users]


def create_user(
    db: Session, payload: UserCreateRequest, tenant: TenantContext, current_user: User
) -> UserRead:
    if users_crud.get_user_by_email(db, str(payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    current_roles = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    institute_id = payload.institute_id if ("super_admin" in current_roles and payload.institute_id) else tenant.institute_id

    user = User(
        user_id=str(uuid.uuid4()),
        institute_id=institute_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        mob_no=payload.mob_no,
        is_approved=payload.is_approved,
        active=payload.active,
    )
    try:
        users_crud.create_user(db, user)
        users_crud.create_auth(
            db,
            Auth(
                user_id=user.user_id,
                password_hash=get_password_hash(payload.password),
            ),
        )

        normalized_roles = {role_name.strip() for role_name in payload.role_names if role_name.strip()}
        if not normalized_roles:
            normalized_roles = {"student"}

        for role_name in normalized_roles:
            role = roles_crud.get_role_by_name(db, role_name)
            if role is None:
                role = roles_crud.create_role(db, role_name=role_name)
            users_crud.assign_user_role(
                db,
                UserRole(
                    id=str(uuid.uuid4()),
                    user_id=user.user_id,
                    role_id=role.role_id,
                ),
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User creation conflicts with existing data.",
        ) from exc

    user = users_crud.get_user_by_id(db, user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed.")
    return _serialize_user(db, user)


def approve_user(db: Session, user_id: str, approve: bool, tenant: TenantContext) -> UserRead:
    user = users_crud.get_user_by_id(db, user_id)
    if user is None or user.institute_id != tenant.institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    users_crud.set_user_approval(db, user, approve)
    if approve:
        selected_courses = enrollment_crud.list_user_selected_courses(db, user.user_id)
        existing_enrollment_pairs = {
            (item.course_id, item.subcourse_id)
            for item in enrollment_crud.list_user_courses(db, user.user_id, user.institute_id)
        }
        for selected in selected_courses:
            if (selected.course_id, selected.subcourse_id) not in existing_enrollment_pairs:
                enrollment_crud.create_user_course(
                    db,
                    UserCourse(
                        institute_id=user.institute_id,
                        user_id=user.user_id,
                        course_id=selected.course_id,
                        subcourse_id=selected.subcourse_id,
                    ),
                )
            modules = course_crud.list_modules_by_subcourse(
                db, selected.subcourse_id, user.institute_id
            )
            existing_module_ids = {
                item.module_id
                for item in enrollment_crud.list_user_modules(
                    db, user.user_id, user.institute_id
                )
            }
            for module in modules:
                if module.module_id not in existing_module_ids:
                    enrollment_crud.create_user_module(
                        db,
                        UserModule(
                            institute_id=user.institute_id,
                            user_id=user.user_id,
                            module_id=module.module_id,
                            active=True,
                        ),
                    )
        enrollment_crud.delete_user_selected_courses(db, user.user_id)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User approval could not be completed because enrollment data conflicts.",
        ) from exc
    db.refresh(user)
    return _serialize_user(db, user)


def assign_user_institute(db: Session, user_id: str, institute_id: str) -> UserRead:
    user = users_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.institute_id = institute_id
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User institute assignment conflicts with existing data.",
        ) from exc
    db.refresh(user)
    return _serialize_user(db, user)


def assign_user_roles(db: Session, user_id: str, role_names: list[str], tenant: TenantContext) -> list[str]:
    user = users_crud.get_user_by_id(db, user_id)
    if user is None or (user.institute_id != tenant.institute_id and tenant.allow_multi_tenant):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    current_roles = set(roles_crud.get_role_names_for_user(db, user_id))
    for role_name in role_names:
        role = roles_crud.get_role_by_name(db, role_name)
        if role is None:
            role = roles_crud.create_role(db, role_name=role_name)
        if role_name not in current_roles:
            users_crud.assign_user_role(
                db,
                UserRole(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    role_id=role.role_id,
                ),
            )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more roles are already assigned to this user.",
        ) from exc
    return roles_crud.get_role_names_for_user(db, user_id)


def update_user(
    db: Session, user_id: str, payload: UserUpdateRequest, tenant: TenantContext, current_user: User
) -> UserRead:
    user = users_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    current_roles = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "super_admin" not in current_roles and user.institute_id != tenant.institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.email = str(payload.email)
    user.mob_no = payload.mob_no
    user.is_approved = payload.is_approved
    user.active = payload.active
    if payload.role_names is not None:
        target_roles = {role_name.strip() for role_name in payload.role_names if role_name.strip()}
        existing_assignments = {assignment.role.role_name: assignment for assignment in user.roles if assignment.role}

        for assignment in list(user.roles):
            if assignment.role and assignment.role.role_name not in target_roles:
                db.delete(assignment)

        for role_name in target_roles:
            if role_name not in existing_assignments:
                role = roles_crud.get_role_by_name(db, role_name)
                if role is None:
                    role = roles_crud.create_role(db, role_name=role_name)
                users_crud.assign_user_role(
                    db,
                    UserRole(
                        id=str(uuid.uuid4()),
                        user_id=user.user_id,
                        role_id=role.role_id,
                    ),
                )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User update conflicts with existing data.",
        ) from exc

    user = users_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update.")
    return _serialize_user(db, user)


def delete_user(db: Session, user_id: str, tenant: TenantContext, current_user: User) -> None:
    user = users_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    current_roles = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "super_admin" not in current_roles and user.institute_id != tenant.institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    try:
        users_crud.deactivate_user(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User cannot be deactivated because related data still exists.",
        ) from exc


def update_profile(db: Session, current_user: User, payload: ProfileUpdateRequest) -> UserRead:
    if current_user.auth is None or not verify_password(
        payload.current_password, current_user.auth.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")

    current_user.email = str(payload.email)
    if payload.new_password:
        current_user.auth.password_hash = get_password_hash(payload.new_password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile update conflicts with existing data.",
        ) from exc

    db.refresh(current_user)
    return _serialize_user(db, current_user)
