"""AI endpoint unit tests."""

from unittest.mock import AsyncMock, patch

import pytest
from app.ai.schemas import AITextRequest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "username": "aiuser",
    "email": "aiuser@example.com",
    "password": "StrongPass123!",
    "full_name": "AI User",
}

LOGIN_PAYLOAD = {
    "email": "aiuser@example.com",
    "password": "StrongPass123!",
}

AI_REQUEST = {
    "content": "def add(a, b):\n    return a + b",
    "additional_context": "Write tests for this helper.",
}


async def _get_auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_resp = await client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_ai_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/ai/review", json=AI_REQUEST)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_endpoints_return_response_for_authenticated_user(client: AsyncClient) -> None:
    headers = await _get_auth_headers(client)
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate_text", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = "This is AI output."

        endpoints = [
            "/api/v1/ai/review",
            "/api/v1/ai/debug",
            "/api/v1/ai/explain",
            "/api/v1/ai/tests",
            "/api/v1/ai/documentation",
            "/api/v1/ai/dsa-hint",
        ]

        for endpoint in endpoints:
            response = await client.post(endpoint, json=AI_REQUEST, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()["result"] == "This is AI output."

        assert mock_generate.call_count == len(endpoints)


@pytest.mark.asyncio
async def test_ai_service_uses_provider_to_generate_text() -> None:
    request = AITextRequest(**AI_REQUEST)

    mock_provider = AsyncMock()
    mock_provider.generate_text.return_value = "AI generated explanation."

    with patch("app.ai.services.ai_service.get_ai_provider", return_value=mock_provider):
        from app.ai.services.ai_service import AIService

        service = AIService()
        response = await service.explain_code(request)

        assert response.result == "AI generated explanation."
