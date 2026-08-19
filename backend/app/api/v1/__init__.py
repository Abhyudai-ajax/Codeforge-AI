from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.github import router as github_router
from app.api.v1.health import router as health_router
from app.api.v1.problems import router as problems_router
from app.api.v1.projects import router as projects_router
from app.api.v1.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(admin_router)
router.include_router(projects_router)
router.include_router(ai_router)
router.include_router(problems_router)
router.include_router(github_router)

