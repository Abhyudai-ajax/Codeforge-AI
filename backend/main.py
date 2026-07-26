"""
FastAPI Application Entry Point
Main application factory and configuration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware

from app.core.config import settings
from app.core.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    Startup and shutdown events
    """
    # Startup
    logger.info("Starting CodeForge AI Backend")
    logger.info(f"Environment: {settings.ENV}")
    yield
    # Shutdown
    logger.info("Shutting down CodeForge AI Backend")


def create_app() -> FastAPI:
    """
    Application factory
    Creates and configures the FastAPI application
    """
    app = FastAPI(
        title="CodeForge AI API",
        description="AI-powered collaborative coding platform API",
        version="0.1.0",
        docs_url="/api/docs" if settings.ENV == "development" else None,
        redoc_url="/api/redoc" if settings.ENV == "development" else None,
        openapi_url="/api/openapi.json" if settings.ENV == "development" else None,
        lifespan=lifespan,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Compression Middleware
    app.add_middleware(GZIPMiddleware, minimum_size=1000)

    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "environment": settings.ENV,
            "version": "0.1.0",
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "CodeForge AI API", "version": "0.1.0"}

    # TODO: Include routers
    # from app.api.v1 import router as v1_router
    # app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development",
    )
