"""Utilities for rendering prompt templates."""

from __future__ import annotations


def render_prompt(template: str, content: str, context: str | None) -> str:
    """Fill the prompt template while safely handling optional context."""
    safe_context = context.strip() if context else "No additional context provided."
    return template.format(content=content.strip(), context=safe_context)
