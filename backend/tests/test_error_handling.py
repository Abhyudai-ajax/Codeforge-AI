"""An unhandled exception must still look like a normal HTTP response to the browser.

CORSMiddleware only injects Access-Control-Allow-* headers on responses that
pass back through its own wrapped ``send``. Starlette's built-in catch-all
(``ServerErrorMiddleware``) is always the outermost layer — its bare 500
response never does that — so a real backend bug on a cross-origin request
looked like a *blocked CORS request* in the browser console, hiding the
actual error entirely. ``UnhandledExceptionMiddleware`` in ``app.main`` fixes
this by sitting inside ``CORSMiddleware`` instead; this test is what proves it.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

ORIGIN = "http://localhost:3000"


@pytest.mark.asyncio
async def test_unhandled_exception_returns_500_with_cors_headers():
    def _boom(*args, **kwargs):
        raise RuntimeError("simulated unexpected failure")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with patch("app.api.v1.health.get_application_health", side_effect=_boom):
            response = await client.get("/api/v1/health", headers={"Origin": ORIGIN})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert response.headers.get("access-control-allow-origin") == ORIGIN


@pytest.mark.asyncio
async def test_unhandled_exception_does_not_leak_internals():
    def _boom(*args, **kwargs):
        raise RuntimeError("a secret stack-trace-worthy detail")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with patch("app.api.v1.health.get_application_health", side_effect=_boom):
            response = await client.get("/api/v1/health", headers={"Origin": ORIGIN})

    assert "secret" not in response.text
