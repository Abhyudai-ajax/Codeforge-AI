"""
Admin API Routes.
GET   /admin/users              — List users with pagination (Admin only)
PATCH /admin/users/{user_id}/role — Update user role / active status (Admin only)
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_role
from app.schemas.user import UserListResponse, UserResponse, UserRoleUpdate
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List users (Admin only)",
    description="Fetch a paginated list of all users in CodeForge AI.",
    dependencies=[Depends(require_role("admin"))],
)
async def list_users_admin(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """List users for admin dashboard."""
    service = UserService(db)
    items, total = await service.list_users_admin(skip=skip, limit=limit)
    item_responses = [UserResponse.model_validate(u) for u in items]
    return UserListResponse(items=item_responses, total=total, skip=skip, limit=limit)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role or status (Admin only)",
    description="Promote/demote user role or activate/deactivate account.",
    dependencies=[Depends(require_role("admin"))],
)
async def update_user_role_admin(
    user_id: str,
    payload: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update role or status for target user."""
    service = UserService(db)
    updated = await service.update_user_role_admin(user_id, payload)
    return UserResponse.model_validate(updated)
