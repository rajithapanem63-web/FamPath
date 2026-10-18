"""Quick diagnostic: trace the profile PUT 500 error."""
import asyncio
import uuid

async def test():
    from app.core.database import get_db, engine
    from app.schemas.workspace_schema import StudentProfileRequest
    from app.services.workspace_service import update_profile
    from app.core.config import get_settings
    from sqlalchemy import text

    settings = get_settings()

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, email FROM users WHERE email='famtest_143124@fampath.dev'")
        )
        row = result.fetchone()
        if row:
            print("User found:", row[0], row[1])
            user_id = uuid.UUID(str(row[0]))
        else:
            print("User not found")
            return

    data = StudentProfileRequest(
        exam_type="AP_EAPCET", rank=5000, category="OC", gender="male"
    )
    async for db in get_db():
        try:
            prof = await update_profile(user_id, None, data, settings, db)
            await db.commit()
            print("Profile updated OK:", prof.id)
        except Exception as e:
            import traceback
            print("ERROR:", e)
            traceback.print_exc()

asyncio.run(test())
