from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_application_health

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check_v1() -> HealthResponse:
    """API v1 health check endpoint"""
    return get_application_health()
