from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.execution import ExecutionCreate, ExecutionResponse, ExecutionResultResponse
from app.services.execution_service import ExecutionService

router = APIRouter(prefix="/executions", tags=["Isolated Code Execution"])


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_execution(
    payload: ExecutionCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    return ExecutionResponse.model_validate(await ExecutionService(db).enqueue(user, payload))


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    return ExecutionResponse.model_validate(
        await ExecutionService(db).get_for_user(execution_id, user)
    )


@router.get("/{execution_id}/result", response_model=ExecutionResultResponse)
async def get_execution_result(
    execution_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResultResponse:
    return ExecutionResultResponse.model_validate(
        await ExecutionService(db).get_for_user(execution_id, user)
    )


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    return ExecutionResponse.model_validate(await ExecutionService(db).cancel(execution_id, user))
