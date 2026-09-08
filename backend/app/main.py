"""
FastAPI Application Entry Point
Main application factory and configuration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class UnhandledExceptionMiddleware:
    """Turns an unhandled exception into a normal 500 JSON response.

    Starlette's own catch-all (``ServerErrorMiddleware``) is always the
    outermost layer, wrapping every other middleware including
    ``CORSMiddleware`` — so its bare 500 response never passes back through
    CORS's response-header injection, and a real backend bug on a
    cross-origin request looks like a blocked CORS request in the browser,
    hiding the actual error. Registering ``@app.exception_handler(Exception)``
    does not help either: Starlette special-cases a handler for the base
    ``Exception`` (or status 500) by attaching it to that same outer
    ``ServerErrorMiddleware`` rather than the inner ``ExceptionMiddleware``.
    A plain ASGI middleware placed *inside* ``CORSMiddleware`` (added to the
    app before it) is what's needed: it catches the exception itself and
    sends the response through the same ``send`` CORSMiddleware already
    wrapped, so CORS headers apply like any other response.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception:
            logger.exception(
                "Unhandled exception for %s %s", scope.get("method"), scope.get("path")
            )
            response = JSONResponse(status_code=500, content={"detail": "Internal server error."})
            await response(scope, receive, send)


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
    description = "AI-powered collaborative coding platform API"
    is_dev = settings.ENV == "development"
    app = FastAPI(
        title="CodeForge AI API",
        description=description,
        version="0.1.0",
        docs_url=("/api/docs" if is_dev else None),
        redoc_url=("/api/redoc" if is_dev else None),
        openapi_url=("/api/openapi.json" if is_dev else None),
        lifespan=lifespan,
    )

    # Added before CORSMiddleware so it ends up *inside* it (Starlette wraps
    # middleware in reverse add-order): its 500 responses still get CORS
    # headers. See UnhandledExceptionMiddleware's docstring for why the more
    # obvious `@app.exception_handler(Exception)` does not achieve this.
    app.add_middleware(UnhandledExceptionMiddleware)

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Compression Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

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
        return {"message": "CodeForge AI API", "version": settings.VERSION}

    # Include API routers
    from app.api.v1 import router as v1_router

    app.include_router(v1_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development",
    )
