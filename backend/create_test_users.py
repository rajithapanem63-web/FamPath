"""Create multiple test users for easy access."""
import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.auth import User


TEST_USERS = [
    {
        "email": "student@test.com",
        "password": "Test1234",
        "name": "Test Student",
        "role": "student",
    },
    {
        "email": "parent@test.com",
        "password": "Test1234",
        "name": "Test Parent",
        "role": "parent",
    },
    {
        "email": "demo@fampath.com",
        "password": "Demo1234",
        "name": "Demo User",
        "role": "student",
    },
]


async def create_users():
    """Create all test users."""
    async with AsyncSessionLocal() as db:
        created = []
        existing = []
        
        for user_data in TEST_USERS:
            # Check if exists
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            if result.scalar_one_or_none():
                existing.append(user_data["email"])
                continue
            
            # Create user
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["name"],
                role=user_data["role"],
                status="active",
                preferred_locale="en",
                created_at=datetime.now(UTC),
            )
            db.add(user)
            created.append(user_data["email"])
        
        await db.commit()
        
        print("=" * 60)
        print("✅ TEST USERS READY")
        print("=" * 60)
        
        if created:
            print(f"\n✨ Created {len(created)} new accounts:")
            for email in created:
                print(f"   • {email}")
        
        if existing:
            print(f"\n📋 Already existed ({len(existing)}):")
            for email in existing:
                print(f"   • {email}")
        
        print("\n" + "=" * 60)
        print("🔐 USE THESE CREDENTIALS TO SIGN IN:")
        print("=" * 60)
        for user_data in TEST_USERS:
            print(f"\nEmail:    {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print(f"Role:     {user_data['role']}")
        
        print("\n" + "=" * 60)
        print("🌐 SIGN IN AT:")
        print("=" * 60)
        print("http://localhost:3001/en/sign-in")
        print("http://10.78.234.12:3001/en/sign-in")
        print("\n✅ All accounts are ready to use!")


if __name__ == "__main__":
    asyncio.run(create_users())
