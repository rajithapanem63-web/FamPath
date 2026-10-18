"""Create a demo user for testing the quiz."""
import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.auth import User


async def create_demo_user():
    """Create a demo user with email verification already done."""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == "demo@fampath.com")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Demo user already exists!")
            print("\nSign in with:")
            print("  Email: demo@fampath.com")
            print("  Password: Demo1234")
            return
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email="demo@fampath.com",
            password_hash=hash_password("Demo1234"),
            full_name="Demo Student",
            role="student",
            status="active",  # Skip pending verification
            preferred_locale="en",
            created_at=datetime.now(UTC),
        )
        db.add(user)
        await db.commit()
        
        print("✅ Demo user created successfully!")
        print("\n📝 Sign in with:")
        print("  Email: demo@fampath.com")
        print("  Password: Demo1234")
        print("\n🎯 Then go to: http://localhost:3001/en/aptitude")
        print("   Click 'Start Quiz 🚀' and enjoy!")


if __name__ == "__main__":
    print("Creating demo user...")
    asyncio.run(create_demo_user())
