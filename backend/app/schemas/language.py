"""Editor-facing description of a supported language."""

from pydantic import BaseModel, Field


class LanguageResponse(BaseModel):
    id: str = Field(description="Canonical id used by run and submit requests.")
    label: str = Field(description="Human-readable name including the toolchain version.")
    monaco_id: str = Field(description="Syntax mode identifier for the Monaco editor.")
    file_extension: str
    compiled: bool = Field(description="Compiled languages can report compilation errors.")
    is_default: bool
    starter_code: str = Field(description="Generic scaffold for a blank editor tab.")
