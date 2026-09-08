"""
SQLAlchemy model package.

Import all ORM models here so Alembic can discover them
during autogeneration and other modules can import them
from a single location.
"""

from app.models.coding_room import CodingRoom, RoomMemberRole, RoomMembership
from app.models.contest import (
    Contest,
    ContestParticipant,
    ContestProblem,
    ContestRegistration,
    ContestSubmission,
)
from app.models.execution import ExecutionJob, ExecutionStatus
from app.models.interview import (
    InterviewAnswer,
    InterviewFeedback,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.notification import Notification, NotificationType
from app.models.problem import (
    Problem,
    ProblemDifficulty,
    ProblemTag,
    ProblemTagLink,
    Submission,
    SubmissionStatus,
    TestCase,
    UserProblemProgress,
)
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.roadmap import (
    Roadmap,
    RoadmapStage,
    RoadmapStageProblem,
    UserRoadmapSelection,
)
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
    "TestCase",
    "ProblemTag",
    "ProblemTagLink",
    "UserProblemProgress",
    "ProjectFile",
    "CodingRoom",
    "RoomMembership",
    "RoomMemberRole",
    "ExecutionJob",
    "ExecutionStatus",
    "Contest",
    "ContestProblem",
    "ContestRegistration",
    "ContestSubmission",
    "ContestParticipant",
    "Roadmap",
    "RoadmapStage",
    "RoadmapStageProblem",
    "UserRoadmapSelection",
    "InterviewSession",
    "InterviewQuestion",
    "InterviewAnswer",
    "InterviewFeedback",
    "InterviewType",
    "InterviewStatus",
    "Notification",
    "NotificationType",
]
