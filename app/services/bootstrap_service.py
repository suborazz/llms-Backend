import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.crud import institutes as institute_crud
from app.crud import roles as role_crud
from app.crud import system_settings as settings_crud
from app.crud import users as users_crud
from app.models import Auth, User, UserRole
from app.models import Institute


DEFAULT_ROLES = ["super_admin", "institute_admin", "teacher", "student"]
DEFAULT_INSTITUTE_EMAIL = "default@institute.com"
settings = get_settings()


def bootstrap_defaults(db: Session) -> None:
    settings = settings_crud.get_system_settings(db)
    if settings is None:
        default_institute = Institute(
            institute_id=str(uuid.uuid4()),
            name="Default Institute",
            email=DEFAULT_INSTITUTE_EMAIL,
            mob_no="0000000000",
            country="N/A",
            state="N/A",
            place="N/A",
            pincode="000000",
            active=True,
        )
        institute_crud.create_institute(db, default_institute)
        settings_crud.create_system_settings(
            db, default_institute_id=default_institute.institute_id, allow_multi_tenant=True
        )
    elif settings.default_institute_id:
        default_institute = institute_crud.get_institute_by_id(db, settings.default_institute_id)
        if default_institute is not None and default_institute.email.endswith(".local"):
            default_institute.email = DEFAULT_INSTITUTE_EMAIL

    for role_name in DEFAULT_ROLES:
        if role_crud.get_role_by_name(db, role_name) is None:
            role_crud.create_role(db, role_name=role_name, active=True)

    _ensure_default_super_admin(db)

    db.commit()


def _ensure_default_super_admin(db: Session) -> None:
    app_settings = settings_crud.get_system_settings(db)
    if app_settings is None or not app_settings.default_institute_id:
        return

    admin = users_crud.get_user_by_email(db, settings.default_super_admin_email)
    if admin is None:
        admin = User(
            user_id=str(uuid.uuid4()),
            institute_id=app_settings.default_institute_id,
            first_name=settings.default_super_admin_first_name,
            last_name=settings.default_super_admin_last_name,
            email=settings.default_super_admin_email,
            mob_no=settings.default_super_admin_mob_no,
            is_approved=True,
            active=True,
        )
        users_crud.create_user(db, admin)
        users_crud.create_auth(
            db,
            Auth(
                user_id=admin.user_id,
                password_hash=get_password_hash(settings.default_super_admin_password),
            ),
        )
    else:
        admin.is_approved = True
        admin.active = True
        admin.institute_id = app_settings.default_institute_id
        if admin.auth is None:
            users_crud.create_auth(
                db,
                Auth(
                    user_id=admin.user_id,
                    password_hash=get_password_hash(settings.default_super_admin_password),
                ),
            )
        else:
            # Keep seeded admin credentials aligned with configured defaults for predictable login.
            admin.auth.password_hash = get_password_hash(settings.default_super_admin_password)

    super_admin_role = role_crud.get_role_by_name(db, "super_admin")
    if super_admin_role is None:
        super_admin_role = role_crud.create_role(db, role_name="super_admin", active=True)

    role_names = set(role_crud.get_role_names_for_user(db, admin.user_id))
    if "super_admin" not in role_names:
        users_crud.assign_user_role(
            db,
            UserRole(
                id=str(uuid.uuid4()),
                user_id=admin.user_id,
                role_id=super_admin_role.role_id,
            ),
        )
