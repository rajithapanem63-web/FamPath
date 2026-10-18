"""Check if demo user exists and can sign in."""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.auth import User
from app.core.security import verify_password

async def check_demo():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "demo@fampath.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Demo user does NOT exist!")
            print("\nRun: python create_demo_user.py")
            return
        
        print("✅ Demo user exists!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.full_name}")
        print(f"   Role: {user.role}")
        print(f"   Status: {user.status}")
        
        # Test password
        password_ok = verify_password("Demo1234", user.password_hash)
        print(f"   Password 'Demo1234': {'✅ CORRECT' if password_ok else '❌ WRONG'}")
        
        if user.status != "active":
            print(f"\n⚠️ User status is '{user.status}' not 'active'")
            print("   This might cause sign-in to fail")

if __name__ == "__main__":
    asyncio.run(check_demo())
