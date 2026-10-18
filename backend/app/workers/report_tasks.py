"""PDF report generation Celery task."""
from __future__ import annotations

import os
import tempfile
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.report_tasks.generate_report")
def generate_report(workspace_id: str, user_id: str, locale: str = "en") -> dict:
    """
    Generate a PDF decision report for a workspace.
    Returns dict with {file_path, generated_at}.
    """
    import asyncio

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        return await _generate_pdf(workspace_id, user_id, locale)

    return asyncio.run(_run())


async def _generate_pdf(workspace_id: str, user_id: str, locale: str) -> dict:
    """Render HTML template and convert to PDF via WeasyPrint."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.workspace import FamilyWorkspace, UserProfile
    from app.models.shortlist import ShortlistItem
    from app.models.alignment import AlignmentSnapshot

    async with AsyncSessionLocal() as db:
        ws_result = await db.execute(
            select(FamilyWorkspace).where(FamilyWorkspace.id == uuid.UUID(workspace_id))
        )
        workspace = ws_result.scalar_one_or_none()

        profile_result = await db.execute(
            select(UserProfile).where(
                UserProfile.workspace_id == uuid.UUID(workspace_id)
            )
        )
        profile = profile_result.scalar_one_or_none()

        shortlist_result = await db.execute(
            select(ShortlistItem).where(
                ShortlistItem.workspace_id == uuid.UUID(workspace_id),
                ShortlistItem.removed_at.is_(None),
            ).limit(5)
        )
        shortlist = shortlist_result.scalars().all()

        snap_result = await db.execute(
            select(AlignmentSnapshot).where(
                AlignmentSnapshot.workspace_id == uuid.UUID(workspace_id)
            )
        )
        snap = snap_result.scalar_one_or_none()

    # Build template context
    context = {
        "workspace_name": workspace.name if workspace else "Family Workspace",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "profile": {
            "exam_type": profile.exam_type if profile else "N/A",
            "category": profile.category if profile else "N/A",
            "gender": profile.gender if profile else "N/A",
        },
        "shortlist_count": len(shortlist),
        "alignment_score": float(snap.alignment_score) if snap and snap.alignment_score else "N/A",
        "disclaimer": "This report is based on historical data and estimates. It is not a guarantee of admission.",
        "locale": locale,
    }

    # Render HTML
    env = Environment(
        loader=FileSystemLoader("app/workers/templates"),
        autoescape=select_autoescape(["html"]),
    )

    try:
        template = env.get_template(f"report_{locale}.html")
    except Exception:
        template = env.get_template("report_en.html")

    html_content = template.render(**context)

    # Generate PDF
    tmp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False, prefix=f"fampath_report_{workspace_id[:8]}_"
    )
    try:
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
            HTML(string=html_content).write_pdf(tmp_file.name)
        except ImportError:
            # WeasyPrint not available — write HTML as fallback for development
            tmp_file_html = tmp_file.name.replace(".pdf", ".html")
            with open(tmp_file_html, "w") as f:
                f.write(html_content)
            logger.warning("weasyprint_not_available_using_html_fallback")
            return {"file_path": tmp_file_html, "generated_at": context["generated_at"]}

        return {"file_path": tmp_file.name, "generated_at": context["generated_at"]}
    finally:
        tmp_file.close()
