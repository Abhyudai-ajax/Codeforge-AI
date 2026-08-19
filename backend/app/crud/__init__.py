"""
CRUD repository package.

Exports all repository classes used by the service layer.
"""

from app.crud.project import ProjectCRUD
from app.crud.user import UserCRUD

__all__ = (
    "UserCRUD",
    "ProjectCRUD",
)
