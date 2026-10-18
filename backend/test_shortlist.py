"""Debug shortlist 500 error."""
import asyncio, uuid

async def test():
    from app.core.database import get_db, engine
    from sqlalchemy import text

    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT id FROM family_workspaces WHERE id='a8c18ccd-2e66-49a7-b741-11f3fba1774d'"))
        print("WS found:", r.fetchone())

    from app.models.shortlist import ShortlistItem
    async for db in get_db():
        try:
            item = ShortlistItem(
                workspace_id=uuid.UUID("a8c18ccd-2e66-49a7-b741-11f3fba1774d"),
                college_id=uuid.UUID("23fc1cd2-315e-40c2-a31f-08699b44bd38"),
                program_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                added_by_user_id=uuid.UUID("8935b81f-1e2a-4697-90b1-d1df418a9fa3"),
            )
            db.add(item)
            await db.flush()
            await db.commit()
            print("Shortlist item added:", item.id)
        except Exception as e:
            import traceback
            print("ERROR:", e)
            traceback.print_exc()

asyncio.run(test())
