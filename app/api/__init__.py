from fastapi import APIRouter

from app.api import auth, batches, courses, enrollment, institutes, progress, students, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(institutes.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(enrollment.router)
api_router.include_router(batches.router)
api_router.include_router(progress.router)
api_router.include_router(students.router)

__all__ = ["api_router"]
