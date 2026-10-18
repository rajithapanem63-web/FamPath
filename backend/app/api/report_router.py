"""PDF report generation router."""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.services.workspace_service import get_workspace_for_user
from app.workers.report_tasks import generate_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{workspace_id}/pdf", response_class=FileResponse)
async def download_report(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> FileResponse:
    """Generate and download a PDF decision report for the workspace."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    # Run synchronously in Celery (blocking for simplicity; in prod use async result)
    result = generate_report(str(workspace_id), str(token.user_id))
    file_path = result.get("file_path")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail={"error_code": "REPORT_GENERATION_FAILED"})

    # Determine content type
    is_pdf = file_path.endswith(".pdf")
    media_type = "application/pdf" if is_pdf else "text/html"
    filename = f"fampath_report_{str(workspace_id)[:8]}.{'pdf' if is_pdf else 'html'}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        background=None,  # File will be deleted after response in production
    )
