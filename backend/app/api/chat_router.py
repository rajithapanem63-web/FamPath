"""RAG chatbot API router."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.chat import ChatMessage, ChatSession
from app.models.workspace import WorkspaceMember
from app.rag.llm_provider import get_llm_provider
from app.rag.pipeline import run_rag_pipeline

router = APIRouter(prefix="/chat", tags=["RAG Chatbot"])


async def _check_consent(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Ensure user has given chatbot consent via workspace membership consent."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.consent_given == True,
            WorkspaceMember.removed_at.is_(None),
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail={"error_code": "CHATBOT_CONSENT_REQUIRED", "message": "Please give consent to use the chatbot"},
        )


class CreateSessionRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|te|hi)$")
    workspace_id: uuid.UUID | None = None


class CreateSessionResponse(BaseModel):
    session_id: uuid.UUID


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CitationResponse(BaseModel):
    source: str
    year: int | None


class MessageResponse(BaseModel):
    message_id: uuid.UUID
    role: str
    content: str
    citations: list[CitationResponse]
    was_refused: bool
    language: str
    created_at: datetime


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    data: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> CreateSessionResponse:
    # Consent check removed — chatbot is open to all authenticated users
    session = ChatSession(
        user_id=token.user_id,
        workspace_id=data.workspace_id,
        language=data.language,
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()
    return CreateSessionResponse(session_id=session.id)


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: uuid.UUID,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    token=Depends(get_token_payload),
) -> MessageResponse:
    # Consent check removed — chatbot is open to all authenticated users

    # Verify session ownership
    sess_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == token.user_id,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail={"error_code": "SESSION_NOT_FOUND"})

    # Save user message
    now = datetime.now(UTC)
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.content,
        citations=[],
        was_refused=False,
        created_at=now,
    )
    db.add(user_msg)

    # Run RAG pipeline
    llm = get_llm_provider(settings)
    result = await run_rag_pipeline(data.content, session.language, llm, db)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        citations=result["citations"],
        retrieval_score=result.get("retrieval_score"),
        was_refused=result.get("refused", False),
        created_at=datetime.now(UTC),
    )
    db.add(assistant_msg)
    await db.flush()

    citations = [
        CitationResponse(source=c.get("source", ""), year=c.get("year"))
        for c in (result["citations"] or [])
    ]

    return MessageResponse(
        message_id=assistant_msg.id,
        role="assistant",
        content=result["answer"],
        citations=citations,
        was_refused=result.get("refused", False),
        language=result.get("language", "en"),
        created_at=assistant_msg.created_at,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[MessageResponse]:
    sess_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == token.user_id,
        )
    )
    if not sess_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"error_code": "SESSION_NOT_FOUND"})

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msgs_result.scalars().all()

    return [
        MessageResponse(
            message_id=m.id,
            role=m.role,
            content=m.content,
            citations=[CitationResponse(source=c.get("source", ""), year=c.get("year")) for c in (m.citations or [])],
            was_refused=m.was_refused,
            language="en",
            created_at=m.created_at,
        )
        for m in messages
    ]
