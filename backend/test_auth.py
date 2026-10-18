"""Test auth endpoints directly."""
import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        
        # Test registration
        print("Testing registration...")
        r = await client.post("/api/v1/auth/register", json={
            "email": "quicktest@test.com",
            "password": "Test1234",
            "full_name": "Quick Test",
            "role": "student",
            "preferred_locale": "en"
        })
        print(f"Register status: {r.status_code}")
        print(f"Register response: {r.json()}")
        
        print("\nTesting login...")
        r2 = await client.post("/api/v1/auth/login", json={
            "email": "student@test.com",
            "password": "Test1234"
        })
        print(f"Login status: {r2.status_code}")
        print(f"Login response keys: {list(r2.json().keys())}")

if __name__ == "__main__":
    asyncio.run(test())
