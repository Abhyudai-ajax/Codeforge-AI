"""Language catalog the code editor uses to build its language switcher."""

from fastapi import APIRouter

from app.core import languages
from app.schemas.language import LanguageResponse

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get(
    "",
    response_model=list[LanguageResponse],
    summary="List supported languages",
    description=(
        "Returns every language the editor can highlight and the sandbox can execute, "
        "including the Monaco syntax mode and a ready-to-use starter scaffold."
    ),
)
async def list_languages() -> list[LanguageResponse]:
    return [
        LanguageResponse(
            id=entry.id,
            label=entry.label,
            monaco_id=entry.monaco_id,
            file_extension=entry.file_extension,
            compiled=entry.compiled,
            is_default=entry.id == languages.DEFAULT_LANGUAGE,
            starter_code=languages.starter_code(entry.id, ["Read stdin and print the answer."]),
        )
        for entry in languages.LANGUAGES.values()
    ]
