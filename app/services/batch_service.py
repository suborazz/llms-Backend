import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import batches as batch_crud
from app.crud import courses as course_crud
from app.crud import roles as roles_crud
from app.crud.users import get_user_by_id
from app.dependencies.tenant import TenantContext
from app.models import Batch, BatchDetail, BatchTeacher, Course, SubCourse, User, UserBatch
from app.schemas.batch import AssignTeacherRequest, BatchCreate, BatchUpdate
from app.schemas.enrollment import AssignBatchRequest


def create_batch(db: Session, payload: BatchCreate, tenant: TenantContext) -> Batch:
    institute_id = payload.institute_id if (tenant.allow_multi_tenant and payload.institute_id) else tenant.institute_id
    course = course_crud.get_course(db, payload.course_id, institute_id)
    subcourse = course_crud.get_subcourse(db, payload.subcourse_id, institute_id)
    if course is None or subcourse is None or subcourse.course_id != payload.course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course or subcourse not found for this institute.",
        )

    batch = Batch(
        batch_id=payload.batch_id or str(uuid.uuid4()),
        institute_id=institute_id,
        course_id=payload.course_id,
        subcourse_id=payload.subcourse_id,
        batch_name=payload.batch_name,
        active=payload.active,
    )
    try:
        batch_crud.create_batch(db, batch)
        batch_crud.create_batch_detail(
            db,
            BatchDetail(
                batch_id=batch.batch_id,
                description=payload.description,
                room_name=payload.room_name,
                schedule_notes=payload.schedule_notes,
                start_date=payload.start_date,
                end_date=payload.end_date,
            ),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch already exists for this institute.",
        ) from exc
    db.refresh(batch)
    return batch


def update_batch(db: Session, batch_id: str, payload: BatchUpdate, tenant: TenantContext) -> Batch:
    institute_id = payload.institute_id if (tenant.allow_multi_tenant and payload.institute_id) else tenant.institute_id
    batch = batch_crud.get_batch(db, batch_id, institute_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")

    course = course_crud.get_course(db, payload.course_id, institute_id)
    subcourse = course_crud.get_subcourse(db, payload.subcourse_id, institute_id)
    if course is None or subcourse is None or subcourse.course_id != payload.course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course or subcourse not found for this institute.",
        )

    batch.course_id = payload.course_id
    batch.subcourse_id = payload.subcourse_id
    batch.batch_name = payload.batch_name
    batch.active = payload.active
    if batch.detail is None:
        batch.detail = BatchDetail(batch_id=batch.batch_id)
    batch.detail.description = payload.description
    batch.detail.room_name = payload.room_name
    batch.detail.schedule_notes = payload.schedule_notes
    batch.detail.start_date = payload.start_date
    batch.detail.end_date = payload.end_date
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch update conflicts with existing data.",
        ) from exc
    db.refresh(batch)
    return batch


def assign_user_to_batch(db: Session, payload: AssignBatchRequest, tenant: TenantContext) -> UserBatch:
    institute_id = payload.institute_id if (tenant.allow_multi_tenant and payload.institute_id) else tenant.institute_id
    batch = batch_crud.get_batch(db, payload.batch_id, institute_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
    user = get_user_by_id(db, payload.user_id)
    if user is None or user.institute_id != institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user_batch = UserBatch(
        institute_id=institute_id, user_id=payload.user_id, batch_id=payload.batch_id, active=True
    )
    try:
        batch_crud.create_user_batch(db, user_batch)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already assigned to batch."
        ) from exc
    db.refresh(user_batch)
    return user_batch


def assign_teacher_to_batch(
    db: Session, payload: AssignTeacherRequest, tenant: TenantContext
) -> BatchTeacher:
    institute_id = payload.institute_id if (tenant.allow_multi_tenant and payload.institute_id) else tenant.institute_id
    batch = batch_crud.get_batch(db, payload.batch_id, institute_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
    teacher = get_user_by_id(db, payload.user_id)
    if teacher is None or teacher.institute_id != institute_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found.")

    teacher = BatchTeacher(
        institute_id=institute_id, batch_id=payload.batch_id, user_id=payload.user_id
    )
    try:
        batch_crud.create_batch_teacher(db, teacher)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Teacher already assigned to batch."
        ) from exc
    db.refresh(teacher)
    return teacher


def list_batches(db: Session, tenant: TenantContext, current_user: User) -> list[Batch]:
    return list_batches_for_institute(db, tenant.institute_id, current_user)


def list_batches_for_institute(db: Session, institute_id: str, current_user: User) -> list[Batch]:
    role_names = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "teacher" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        teacher_assignments = batch_crud.list_batch_teachers_for_user(
            db, current_user.user_id, institute_id
        )
        batch_ids = {assignment.batch_id for assignment in teacher_assignments}
        return [
            batch
            for batch in batch_crud.list_batches(db, institute_id)
            if batch.batch_id in batch_ids and batch.active
        ]
    if "student" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        student_assignments = batch_crud.list_user_batches_for_user(
            db, current_user.user_id, institute_id
        )
        batch_ids = {assignment.batch_id for assignment in student_assignments if assignment.active}
        return [
            batch
            for batch in batch_crud.list_batches(db, institute_id)
            if batch.batch_id in batch_ids and batch.active
        ]

    batches = batch_crud.list_batches(db, institute_id)
    if "super_admin" in role_names:
        return batches
    return [batch for batch in batches if batch.active]


def get_batch_detail(
    db: Session,
    batch_id: str,
    tenant: TenantContext,
    current_user: User,
    institute_id: str | None = None,
) -> dict:
    target_institute_id = institute_id if (tenant.allow_multi_tenant and institute_id) else tenant.institute_id
    batch = batch_crud.get_batch(db, batch_id, target_institute_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")

    role_names = set(roles_crud.get_role_names_for_user(db, current_user.user_id))
    if "teacher" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        allowed_batch_ids = {
            assignment.batch_id
            for assignment in batch_crud.list_batch_teachers_for_user(
                db, current_user.user_id, target_institute_id
            )
        }
        if batch_id not in allowed_batch_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Batch access denied.")
    if "student" in role_names and "super_admin" not in role_names and "institute_admin" not in role_names:
        allowed_batch_ids = {
            assignment.batch_id
            for assignment in batch_crud.list_user_batches_for_user(
                db, current_user.user_id, target_institute_id
            )
            if assignment.active
        }
        if batch_id not in allowed_batch_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Batch access denied.")

    course = course_crud.get_course(db, batch.course_id, target_institute_id)
    subcourse = course_crud.get_subcourse(db, batch.subcourse_id, target_institute_id)

    teacher_rows = batch_crud.list_batch_teachers_for_batch(db, batch.batch_id, target_institute_id)
    student_rows = batch_crud.list_user_batches_for_batch(db, batch.batch_id, target_institute_id)

    teachers = []
    for row in teacher_rows:
        teacher = get_user_by_id(db, row.user_id)
        if teacher is not None and teacher.active:
            teachers.append(
                {
                    "user_id": teacher.user_id,
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                    "email": teacher.email,
                    "mob_no": teacher.mob_no,
                    "institute_id": teacher.institute_id,
                    "role_names": roles_crud.get_role_names_for_user(db, teacher.user_id),
                    "active": teacher.active,
                    "is_approved": teacher.is_approved,
                }
            )

    students = []
    for row in student_rows:
        student = get_user_by_id(db, row.user_id)
        if student is not None and student.active:
            students.append(
                {
                    "user_id": student.user_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "mob_no": student.mob_no,
                    "institute_id": student.institute_id,
                    "role_names": roles_crud.get_role_names_for_user(db, student.user_id),
                    "active": student.active,
                    "is_approved": student.is_approved,
                }
            )

    return {
        "batch_id": batch.batch_id,
        "batch_name": batch.batch_name,
        "active": batch.active,
        "description": batch.detail.description if batch.detail else None,
        "room_name": batch.detail.room_name if batch.detail else None,
        "schedule_notes": batch.detail.schedule_notes if batch.detail else None,
        "start_date": batch.detail.start_date if batch.detail else None,
        "end_date": batch.detail.end_date if batch.detail else None,
        "course": {
            "course_id": course.course_id if course else batch.course_id,
            "course_name": course.course_name if course else batch.course_id,
        },
        "subcourse": {
            "subcourse_id": subcourse.subcourse_id if subcourse else batch.subcourse_id,
            "subcourse_name": subcourse.subcourse_name if subcourse else batch.subcourse_id,
        },
        "teachers": teachers,
        "students": students,
    }
