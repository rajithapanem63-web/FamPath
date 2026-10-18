"""Deadline reminder Celery Beat tasks."""
from __future__ import annotations

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.reminder_tasks.send_deadline_reminders")
def send_deadline_reminders() -> None:
    """Daily task: check upcoming counselling deadlines and send notifications."""
    import asyncio

    async def _run() -> None:
        from datetime import UTC, datetime, timedelta
        from sqlalchemy import select, and_
        from app.core.database import AsyncSessionLocal
        from app.models.shortlist import CounsellingEvent, Notification
        from app.models.workspace import WorkspaceMember, UserProfile

        async with AsyncSessionLocal() as db:
            today = datetime.now(UTC).date()
            upcoming = today + timedelta(days=7)

            events_result = await db.execute(
                select(CounsellingEvent).where(
                    and_(
                        CounsellingEvent.event_date >= today,
                        CounsellingEvent.event_date <= upcoming,
                    )
                )
            )
            events = events_result.scalars().all()

            for event in events:
                # Find users with matching exam type
                profiles_result = await db.execute(
                    select(UserProfile).where(UserProfile.exam_type == event.exam_type)
                )
                for profile in profiles_result.scalars().all():
                    notif = Notification(
                        user_id=profile.user_id,
                        workspace_id=profile.workspace_id,
                        type="deadline_reminder",
                        title=f"Upcoming: {event.event_name}",
                        message=f"{event.event_name} is scheduled on {event.event_date}.",
                        created_at=datetime.now(UTC),
                    )
                    db.add(notif)

            await db.commit()
            logger.info("deadline_reminders_sent", events=len(events))

    asyncio.run(_run())
