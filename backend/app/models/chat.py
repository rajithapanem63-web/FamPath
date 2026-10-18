"""RAG chatbot models: KnowledgeDocument, DocumentChunk, ChatSession, ChatMessage."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import JSON as JSONB  # SQLite-compat (replaces postgresql JSONB)
from sqlalchemy import Text as TSVECTOR  # SQLite-compat (replaces postgresql TSVECTOR)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import GUID, UUIDPKMixin  # SQLite-compat UUID

try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
    _VECTOR_AVAILABLE = True
except ImportError:
    _VECTOR_AVAILABLE = False


class KnowledgeDocument(UUIDPKMixin, Base):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    upload_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DocumentChunk(UUIDPKMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("knowledge_documents.id"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Embedding stored as JSON array if pgvector not available; Vector otherwise
    embedding_json: Mapped[list | None] = mapped_column(JSONB)
    bm25_tokens: Mapped[str | None] = mapped_column(TSVECTOR)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatSession(UUIDPKMixin, Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), index=True
    )
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatMessage(UUIDPKMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list | None] = mapped_column(JSONB)
    retrieval_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    was_refused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
