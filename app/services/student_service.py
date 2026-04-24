from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import batches as batch_crud
from app.crud import courses as course_crud
from app.crud import enrollment as enrollment_crud
from app.dependencies.tenant import TenantContext
from app.models import Content, Course, Module, StudentSubmission, SubCourse, User


def get_enrolled_courses(db: Session, current_user: User, tenant: TenantContext) -> list[dict]:
    enrollments = enrollment_crud.list_user_courses(db, current_user.user_id, tenant.institute_id)
    result: list[dict] = []
    for item in enrollments:
        course = db.scalar(
            select(Course).where(
                Course.course_id == item.course_id,
                Course.institute_id == tenant.institute_id,
                Course.active.is_(True),
            )
        )
        subcourse = db.scalar(
            select(SubCourse).where(
                SubCourse.subcourse_id == item.subcourse_id,
                SubCourse.institute_id == tenant.institute_id,
                SubCourse.active.is_(True),
            )
        )
        if course and subcourse:
            result.append(
                {
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "subcourse_id": subcourse.subcourse_id,
                    "subcourse_name": subcourse.subcourse_name,
                }
            )
    return result


def get_my_modules_with_content(db: Session, current_user: User, tenant: TenantContext) -> list[dict]:
    user_modules = enrollment_crud.list_user_modules(db, current_user.user_id, tenant.institute_id)
    output: list[dict] = []
    for user_module in user_modules:
        module = db.scalar(
            select(Module).where(
                Module.module_id == user_module.module_id,
                Module.institute_id == tenant.institute_id,
                Module.active.is_(True),
            )
        )
        if module is None:
            continue
        contents = db.scalars(
            select(Content).where(
                Content.module_id == module.module_id,
                Content.institute_id == tenant.institute_id,
            )
        ).all()
        output.append(
            {
                "module_id": module.module_id,
                "module_name": module.module_name,
                "content": [
                    {
                        "content_id": content.content_id,
                        "title": content.title,
                        "type": content.type,
                        "category": content.category,
                        "body_text": content.body_text,
                        "instructions": content.instructions,
                        "downloadable": content.downloadable,
                        "response_type": content.response_type,
                        "url": content.url,
                        "duration": content.duration,
                    }
                    for content in contents
                ],
            }
        )
    return output


def get_student_batches(db: Session, current_user: User, tenant: TenantContext) -> list[dict]:
    assignments = batch_crud.list_user_batches_for_user(db, current_user.user_id, tenant.institute_id)
    result: list[dict] = []
    for assignment in assignments:
        if not assignment.active:
            continue
        batch = batch_crud.get_batch(db, assignment.batch_id, tenant.institute_id)
        if batch is None or not batch.active:
            continue
        course = course_crud.get_course(db, batch.course_id, tenant.institute_id, include_inactive=False)
        subcourse = course_crud.get_subcourse(
            db, batch.subcourse_id, tenant.institute_id, include_inactive=False
        )
        result.append(
            {
                "batch_id": batch.batch_id,
                "batch_name": batch.batch_name,
                "course_id": batch.course_id,
                "course_name": course.course_name if course else batch.course_id,
                "subcourse_id": batch.subcourse_id,
                "subcourse_name": subcourse.subcourse_name if subcourse else batch.subcourse_id,
                "description": batch.detail.description if batch.detail else None,
                "room_name": batch.detail.room_name if batch.detail else None,
                "schedule_notes": batch.detail.schedule_notes if batch.detail else None,
                "start_date": batch.detail.start_date if batch.detail else None,
                "end_date": batch.detail.end_date if batch.detail else None,
            }
        )
    return result


def get_student_course_workspace(
    db: Session,
    current_user: User,
    tenant: TenantContext,
    course_id: str,
    category: str | None = None,
) -> dict:
    batches = [
        batch
        for batch in get_student_batches(db, current_user, tenant)
        if batch["course_id"] == course_id
    ]
    if not batches:
        return {"course_id": course_id, "batches": [], "modules": [], "content_categories": []}

    allowed_subcourse_ids = {batch["subcourse_id"] for batch in batches}
    modules = [
        module
        for module in course_crud.list_modules(
            db, tenant.institute_id, course_id=course_id, include_inactive=False
        )
        if module.subcourse_id in allowed_subcourse_ids
    ]
    module_ids = [module.module_id for module in modules]
    contents = course_crud.list_user_module_content(db, module_ids, tenant.institute_id)
    submissions = db.scalars(
        select(StudentSubmission).where(
            StudentSubmission.user_id == current_user.user_id,
            StudentSubmission.institute_id == tenant.institute_id,
            StudentSubmission.content_id.in_([content.content_id for content in contents]) if contents else False,
        )
    ).all() if contents else []
    submissions_by_content = {submission.content_id: submission for submission in submissions}

    available_categories = sorted({content.category for content in contents})
    filtered_contents = [
        content for content in contents if not category or content.category == category
    ]
    content_by_module: dict[str, list[dict]] = {}
    for content in filtered_contents:
        submission = submissions_by_content.get(content.content_id)
        content_by_module.setdefault(content.module_id, []).append(
            {
                "content_id": content.content_id,
                "title": content.title,
                "type": content.type,
                "category": content.category,
                "body_text": content.body_text,
                "instructions": content.instructions,
                "downloadable": content.downloadable,
                "response_type": content.response_type,
                "url": content.url,
                "duration": content.duration,
                "submission": (
                    {
                        "submission_id": submission.submission_id,
                        "response_type": submission.response_type,
                        "response_text": submission.response_text,
                        "response_url": submission.response_url,
                        "submitted_at": submission.submitted_at.isoformat(),
                    }
                    if submission is not None
                    else None
                ),
            }
        )

    return {
        "course_id": course_id,
        "course_name": batches[0]["course_name"],
        "batches": batches,
        "content_categories": available_categories,
        "selected_category": category,
        "modules": [
            {
                "module_id": module.module_id,
                "module_name": module.module_name,
                "subcourse_id": module.subcourse_id,
                "subcourse_name": next(
                    (
                        batch["subcourse_name"]
                        for batch in batches
                        if batch["subcourse_id"] == module.subcourse_id
                    ),
                    module.subcourse_id,
                ),
                "content": content_by_module.get(module.module_id, []),
            }
            for module in modules
            if content_by_module.get(module.module_id)
        ],
    }


def submit_student_content(
    db: Session,
    current_user: User,
    tenant: TenantContext,
    content_id: str,
    response_type: str,
    response_text: str | None,
    response_url: str | None,
) -> dict:
    content = db.scalar(
        select(Content).where(
            Content.content_id == content_id,
            Content.institute_id == tenant.institute_id,
        )
    )
    if content is None:
        raise ValueError("Content not found.")

    workspace = get_student_course_workspace(db, current_user, tenant, content.module.course_id)
    allowed_content_ids = {
        item["content_id"]
        for module in workspace["modules"]
        for item in module["content"]
    }
    if content_id not in allowed_content_ids:
        raise ValueError("Content access denied.")

    submission = db.scalar(
        select(StudentSubmission).where(
            StudentSubmission.user_id == current_user.user_id,
            StudentSubmission.institute_id == tenant.institute_id,
            StudentSubmission.content_id == content_id,
        )
    )
    if submission is None:
        submission = StudentSubmission(
            institute_id=tenant.institute_id,
            content_id=content_id,
            user_id=current_user.user_id,
            response_type=response_type,
            response_text=response_text,
            response_url=response_url,
        )
        db.add(submission)
    else:
        submission.response_type = response_type
        submission.response_text = response_text
        submission.response_url = response_url
    db.commit()
    db.refresh(submission)
    return {
        "submission_id": submission.submission_id,
        "response_type": submission.response_type,
        "response_text": submission.response_text,
        "response_url": submission.response_url,
        "submitted_at": submission.submitted_at.isoformat(),
    }
