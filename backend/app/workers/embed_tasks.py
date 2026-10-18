"""Document embedding Celery tasks for the RAG chatbot."""
from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.embed_tasks.embed_document")
def embed_document(document_id: str) -> dict:
    """Chunk and embed a knowledge document into pgvector."""
    import asyncio

    async def _run() -> dict:
        from sqlalchemy import select
        from app.core.database import AsyncSessionLocal
        from app.models.chat import DocumentChunk, KnowledgeDocument
        from datetime import UTC, datetime

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == uuid.UUID(document_id))
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return {"status": "error", "message": "Document not found"}

            # Read document content from storage (stub — reads from metadata)
            content = doc.title  # In production, read from file storage
            chunks = _chunk_text(content, chunk_size=500, overlap=50)

            for i, chunk_text in enumerate(chunks):
                # Generate embedding (mock for development)
                embedding = [0.0] * 1536  # Real: call embedding API

                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding_json=embedding,
                    metadata_={"source": doc.source, "year": doc.source_year},
                    created_at=datetime.now(UTC),
                )
                db.add(chunk)

            await db.commit()
            logger.info("document_embedded", document_id=document_id, chunks=len(chunks))
            return {"status": "completed", "chunks": len(chunks)}

    return asyncio.run(_run())


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
