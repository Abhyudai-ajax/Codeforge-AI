"""
SQLAlchemy model package.

Import all ORM models here so Alembic can discover them
during autogeneration and other modules can import them
from a single location.
"""

from app.models.problem import Problem, ProblemDifficulty, Submission, SubmissionStatus
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.user import User, UserRole

__all__ = [
    "User",
    "UserRole",
    "Project",
    "ProjectVisibility",
    "Problem",
    "ProblemDifficulty",
    "Submission",
    "SubmissionStatus",
    "ProjectFile",
]

