"""Check if quiz questions exist in the database."""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.aptitude import QuizQuestion

async def check_questions():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(QuizQuestion))
        questions = result.scalars().all()
        print(f"Found {len(questions)} quiz questions in database")
        
        if questions:
            print("\nFirst 3 questions:")
            for i, q in enumerate(questions[:3], 1):
                print(f"{i}. {q.question_text[:70]}...")
                print(f"   RIASEC: {q.riasec_dimension}, Active: {q.is_active}")
        else:
            print("\n⚠️ No quiz questions found! You need to seed the database.")
            print("Run: python scripts/seed_aptitude_questions.py")

if __name__ == "__main__":
    asyncio.run(check_questions())
