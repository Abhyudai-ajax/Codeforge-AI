from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.coding_rooms import router as coding_rooms_router
from app.api.v1.contests import router as contests_router
from app.api.v1.executions import router as executions_router
from app.api.v1.github import router as github_router
from app.api.v1.health import router as health_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.languages import router as languages_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.problems import router as problems_router
from app.api.v1.projects import router as projects_router
from app.api.v1.roadmaps import router as roadmaps_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(coding_rooms_router)
router.include_router(executions_router)
router.include_router(users_router)
router.include_router(admin_router)
router.include_router(projects_router)
router.include_router(ai_router)
router.include_router(languages_router)
router.include_router(leaderboard_router)
router.include_router(problems_router)
router.include_router(submissions_router)
router.include_router(contests_router)
router.include_router(github_router)
router.include_router(roadmaps_router)
router.include_router(interviews_router)
router.include_router(notifications_router)
