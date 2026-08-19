"""Pydantic schemas for AI module request and response payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AITextRequest(BaseModel):
    """Base request schema for AI text operations."""

    content: str = Field(
        ..., min_length=1, max_length=30000, description="Source text or code to process."
    )
    additional_context: str | None = Field(
        default=None,
        max_length=8000,
        description="Optional extra context to guide the AI generation.",
    )


class AITextResponse(BaseModel):
    """Generic AI text response."""

    result: str = Field(..., description="Generated AI text output.")
