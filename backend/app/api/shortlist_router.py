"""Shortlist, votes, decision log, timeline, and checklist router."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.shortlist import (
    AdmissionTask,
    CounsellingEvent,
    DecisionLogEntry,
    DocumentChecklistItem,
    ShortlistItem,
    ShortlistVote,
    WorkspaceChecklistStatus,
)
from app.services.workspace_service import get_workspace_for_user

router = APIRouter(prefix="/shortlist", tags=["Shortlist & Decision Log"])
timeline_router = APIRouter(prefix="/timeline", tags=["Timeline & Checklist"])
checklist_router = APIRouter(prefix="/checklist", tags=["Timeline & Checklist"])

MAX_SHORTLIST_SIZE = 20


class AddToShortlistRequest(BaseModel):
    college_id: uuid.UUID
    program_id: uuid.UUID
    cost_snapshot: dict | None = None
    prediction_snapshot: dict | None = None


class VoteRequest(BaseModel):
    vote: int = Field(ge=-1, le=1)
    comment: str | None = Field(None, max_length=1000)


class ShortlistItemResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    program_id: uuid.UUID
    added_by: uuid.UUID
    is_final_choice: bool
    cost_snapshot: dict | None
    prediction_snapshot: dict | None
    votes: list[dict]
    created_at: datetime


@router.get("/{workspace_id}", response_model=list[ShortlistItemResponse])
async def get_shortlist(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[ShortlistItemResponse]:
    await get_workspace_for_user(workspace_id, token.user_id, db)
    result = await db.execute(
        select(ShortlistItem).where(
            ShortlistItem.workspace_id == workspace_id,
            ShortlistItem.removed_at.is_(None),
        ).order_by(ShortlistItem.created_at)
    )
    items = result.scalars().all()

    responses = []
    for item in items:
        votes_result = await db.execute(
            select(ShortlistVote).where(ShortlistVote.shortlist_item_id == item.id)
        )
        votes = [{"user_id": str(v.user_id), "vote": v.vote, "comment": v.comment}
                 for v in votes_result.scalars().all()]
        responses.append(ShortlistItemResponse(
            id=item.id,
            college_id=item.college_id,
            program_id=item.program_id,
            added_by=item.added_by,
            is_final_choice=item.is_final_choice,
            cost_snapshot=item.cost_snapshot,
            prediction_snapshot=item.prediction_snapshot,
            votes=votes,
            created_at=item.created_at,
        ))
    return responses


@router.post("/{workspace_id}", response_model=ShortlistItemResponse, status_code=201)
async def add_to_shortlist(
    workspace_id: uuid.UUID,
    data: AddToShortlistRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> ShortlistItemResponse:
    await get_workspace_for_user(workspace_id, token.user_id, db)

    # Check limit
    count_result = await db.execute(
        select(ShortlistItem).where(
            ShortlistItem.workspace_id == workspace_id,
            ShortlistItem.removed_at.is_(None),
        )
    )
    if len(count_result.scalars().all()) >= MAX_SHORTLIST_SIZE:
        raise HTTPException(status_code=400, detail={"error_code": "SHORTLIST_LIMIT_REACHED"})

    now = datetime.now(UTC)
    item = ShortlistItem(
        workspace_id=workspace_id,
        college_id=data.college_id,
        program_id=data.program_id,
        added_by=token.user_id,
        cost_snapshot=data.cost_snapshot,
        prediction_snapshot=data.prediction_snapshot,
        created_at=now,
    )
    db.add(item)

    # Decision log
    log = DecisionLogEntry(
        workspace_id=workspace_id,
        user_id=token.user_id,
        action="added",
        resource_id=None,
        created_at=now,
    )
    db.add(log)
    await db.flush()

    return ShortlistItemResponse(
        id=item.id,
        college_id=item.college_id,
        program_id=item.program_id,
        added_by=item.added_by,
        is_final_choice=item.is_final_choice,
        cost_snapshot=item.cost_snapshot,
        prediction_snapshot=item.prediction_snapshot,
        votes=[],
        created_at=item.created_at,
    )


@router.delete("/{workspace_id}/{item_id}", response_model=dict)
async def remove_from_shortlist(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    await get_workspace_for_user(workspace_id, token.user_id, db)
    result = await db.execute(
        select(ShortlistItem).where(
            ShortlistItem.id == item_id,
            ShortlistItem.workspace_id == workspace_id,
            ShortlistItem.removed_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail={"error_code": "ITEM_NOT_FOUND"})
    item.removed_at = datetime.now(UTC)
    return {"message": "Removed from shortlist"}


@router.post("/{workspace_id}/{item_id}/vote", response_model=dict)
async def vote_on_shortlist(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    data: VoteRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    await get_workspace_for_user(workspace_id, token.user_id, db)
    now = datetime.now(UTC)

    existing = await db.execute(
        select(ShortlistVote).where(
            ShortlistVote.shortlist_item_id == item_id,
            ShortlistVote.user_id == token.user_id,
        )
    )
    vote = existing.scalar_one_or_none()
    if vote:
        vote.vote = data.vote
        vote.comment = data.comment
        vote.updated_at = now
    else:
        vote = ShortlistVote(
            shortlist_item_id=item_id,
            user_id=token.user_id,
            vote=data.vote,
            comment=data.comment,
            created_at=now,
            updated_at=now,
        )
        db.add(vote)

    return {"message": "Vote recorded"}


@router.put("/{workspace_id}/{item_id}/final", response_model=dict)
async def mark_final(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    await get_workspace_for_user(workspace_id, token.user_id, db)

    # Unmark any existing final choices
    existing_finals = await db.execute(
        select(ShortlistItem).where(
            ShortlistItem.workspace_id == workspace_id,
            ShortlistItem.is_final_choice == True,
        )
    )
    for f in existing_finals.scalars().all():
        f.is_final_choice = False

    result = await db.execute(
        select(ShortlistItem).where(
            ShortlistItem.id == item_id,
            ShortlistItem.workspace_id == workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail={"error_code": "ITEM_NOT_FOUND"})
    item.is_final_choice = True
    return {"message": "Final decision marked"}


@router.get("/{workspace_id}/log", response_model=list[dict])
async def get_decision_log(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[dict]:
    await get_workspace_for_user(workspace_id, token.user_id, db)
    result = await db.execute(
        select(DecisionLogEntry)
        .where(DecisionLogEntry.workspace_id == workspace_id)
        .order_by(DecisionLogEntry.created_at.desc())
        .limit(100)
    )
    return [
        {"id": str(e.id), "user_id": str(e.user_id), "action": e.action, "created_at": e.created_at.isoformat()}
        for e in result.scalars().all()
    ]


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    source_citation: str | None = None


# Timeline
@timeline_router.get("/{workspace_id}", response_model=list[dict])
async def get_timeline(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[dict]:
    """Returns official counselling dates and user tasks merged chronologically."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    # Get student profile exam type
    from app.models.workspace import UserProfile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.workspace_id == workspace_id)
    )
    profile = profile_result.scalar_one_or_none()
    exam_type = profile.exam_type if profile else None

    # 1. Fetch Official Counselling Events
    query = select(CounsellingEvent)
    if exam_type:
        query = query.where(CounsellingEvent.exam_type == exam_type)
    query = query.order_by(CounsellingEvent.event_date)
    result = await db.execute(query)
    official_events = result.scalars().all()

    # 2. Fetch User Tasks
    tasks_result = await db.execute(
        select(AdmissionTask)
        .where(AdmissionTask.workspace_id == workspace_id)
        .order_by(AdmissionTask.due_date)
    )
    user_tasks = tasks_result.scalars().all()

    timeline_items: list[dict] = []

    for e in official_events:
        timeline_items.append({
            "id": str(e.id),
            "event_name": e.event_name,
            "exam_type": e.exam_type,
            "event_date": e.event_date.isoformat() if e.event_date else None,
            "round_number": e.round_number,
            "is_completed": False,
            "source_type": "official",
            "source_citation": e.source or "State Counselling Authority Notification",
            "notes": e.notes,
            "can_delete": False,
        })

    for t in user_tasks:
        timeline_items.append({
            "id": str(t.id),
            "event_name": t.title,
            "exam_type": None,
            "event_date": t.due_date.isoformat() if t.due_date else None,
            "round_number": None,
            "is_completed": t.is_completed,
            "source_type": t.source_type,
            "source_citation": t.source_citation or "User-entered task",
            "notes": t.description,
            "can_delete": True,
        })

    # Sort merged list by event_date (None values at the end)
    timeline_items.sort(key=lambda x: x["event_date"] or "9999-99-99")
    return timeline_items


@timeline_router.post("/{workspace_id}/tasks", response_model=dict, status_code=201)
async def create_user_task(
    workspace_id: uuid.UUID,
    data: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Create a personal or family admission task."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    task = AdmissionTask(
        workspace_id=workspace_id,
        created_by=token.user_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        source_type="user_entered",
        source_citation=data.source_citation or "Added by Student/Family",
        is_completed=False,
    )
    db.add(task)
    await db.commit()
    return {"id": str(task.id), "title": task.title, "message": "Task created"}


@timeline_router.put("/{workspace_id}/tasks/{task_id}", response_model=dict)
async def toggle_user_task(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Toggle completed status of an admission task."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    result = await db.execute(
        select(AdmissionTask).where(
            AdmissionTask.id == task_id,
            AdmissionTask.workspace_id == workspace_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"error_code": "TASK_NOT_FOUND"})

    task.is_completed = not task.is_completed
    if task.is_completed:
        task.completed_at = datetime.now(UTC)
        task.completed_by = token.user_id
    else:
        task.completed_at = None
        task.completed_by = None

    await db.commit()
    return {"id": str(task.id), "is_completed": task.is_completed}


@timeline_router.delete("/{workspace_id}/tasks/{task_id}", response_model=dict)
async def delete_user_task(
    workspace_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Delete a user-entered admission task."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    result = await db.execute(
        select(AdmissionTask).where(
            AdmissionTask.id == task_id,
            AdmissionTask.workspace_id == workspace_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"error_code": "TASK_NOT_FOUND"})

    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}


# Checklist
@checklist_router.get("/{workspace_id}", response_model=list[dict])
async def get_checklist(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[dict]:
    await get_workspace_for_user(workspace_id, token.user_id, db)

    from app.models.workspace import UserProfile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.workspace_id == workspace_id)
    )
    profile = profile_result.scalar_one_or_none()
    exam_type = profile.exam_type if profile else None
    category = profile.category if profile else None

    query = select(DocumentChecklistItem)
    if exam_type:
        query = query.where(DocumentChecklistItem.exam_type == exam_type)
    if category:
        from sqlalchemy import or_
        query = query.where(
            or_(
                DocumentChecklistItem.category_filter.is_(None),
                DocumentChecklistItem.category_filter == category,
            )
        )

    items_result = await db.execute(query)
    items = items_result.scalars().all()

    # Get completion status
    status_result = await db.execute(
        select(WorkspaceChecklistStatus).where(
            WorkspaceChecklistStatus.workspace_id == workspace_id
        )
    )
    statuses = {str(s.checklist_item_id): s for s in status_result.scalars().all()}

    return [
        {
            "id": str(i.id),
            "document_name": i.document_name,
            "is_mandatory": i.is_mandatory,
            "is_completed": statuses.get(str(i.id), {}).is_completed if str(i.id) in statuses else False,
        }
        for i in items
    ]


@checklist_router.put("/{workspace_id}/{item_id}", response_model=dict)
async def mark_checklist_item(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    await get_workspace_for_user(workspace_id, token.user_id, db)
    now = datetime.now(UTC)

    existing = await db.execute(
        select(WorkspaceChecklistStatus).where(
            WorkspaceChecklistStatus.workspace_id == workspace_id,
            WorkspaceChecklistStatus.checklist_item_id == item_id,
        )
    )
    status = existing.scalar_one_or_none()
    if status:
        status.is_completed = not status.is_completed
        if status.is_completed:
            status.completed_by = token.user_id
            status.completed_at = now
    else:
        status = WorkspaceChecklistStatus(
            workspace_id=workspace_id,
            checklist_item_id=item_id,
            is_completed=True,
            completed_by=token.user_id,
            completed_at=now,
        )
        db.add(status)

    return {"is_completed": status.is_completed}
