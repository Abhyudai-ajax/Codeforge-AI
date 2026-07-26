from app.core.config import settings
from app.schemas.health import HealthResponse


def get_application_health() -> HealthResponse:
    """Return health status data for the application."""
    return HealthResponse(
        status="healthy",
        environment=settings.ENV,
        version=settings.VERSION,
    )
