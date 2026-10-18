"""
SQLAlchemy ORM models. Import all models here so Alembic can discover them.
"""
from app.models.audit import AuditLog
from app.models.auth import EmailToken, RefreshToken, User
from app.models.alignment import AlignmentSnapshot, MediationSession, PreferenceSubmission
from app.models.college import (
    College,
    CollegeProgram,
    CutoffRecord,
    FeeStructure,
    ImportJob,
    PlacementStat,
    Scholarship,
)
from app.models.preference import PreferenceDimension, PreferenceResponse, PreferenceWeight
from app.models.aptitude import AptitudeResult, QuizQuestion, QuizResponse, QuizSession
from app.models.chat import ChatMessage, ChatSession, DocumentChunk, KnowledgeDocument
from app.models.ml import MlModelVersion
from app.models.career import StudentCareerGoal
from app.models.shortlist import (
    AdmissionTask,
    CounsellingEvent,
    DecisionLogEntry,
    DocumentChecklistItem,
    Notification,
    ShortlistItem,
    ShortlistVote,
    WorkspaceChecklistStatus,
)
from app.models.workspace import FamilyWorkspace, UserProfile, WorkspaceInvitation, WorkspaceMember

__all__ = [
    "AuditLog",
    "User",
    "EmailToken",
    "RefreshToken",
    "PreferenceSubmission",
    "AlignmentSnapshot",
    "MediationSession",
    "FamilyWorkspace",
    "WorkspaceMember",
    "WorkspaceInvitation",
    "UserProfile",
    "College",
    "CollegeProgram",
    "CutoffRecord",
    "FeeStructure",
    "PlacementStat",
    "Scholarship",
    "ImportJob",
    "QuizQuestion",
    "QuizSession",
    "QuizResponse",
    "AptitudeResult",
    "PreferenceResponse",
    "PreferenceDimension",
    "PreferenceWeight",
    "KnowledgeDocument",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "MlModelVersion",
    "ShortlistItem",
    "ShortlistVote",
    "DecisionLogEntry",
    "CounsellingEvent",
    "DocumentChecklistItem",
    "WorkspaceChecklistStatus",
    "Notification",
    "AdmissionTask",
    "StudentCareerGoal",
]
