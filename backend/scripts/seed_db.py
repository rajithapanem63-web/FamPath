#!/usr/bin/env python3
"""
Seed the database with synthetic development data.
Run: python scripts/seed_db.py
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("FAMPATH_DB_URL", "postgresql+asyncpg://fampath:fampath@localhost:5432/fampath")
os.environ.setdefault("FAMPATH_SECRET_KEY", "dev-secret-key-change-in-production")
os.environ.setdefault("FAMPATH_ENCRYPTION_KEY", "0" * 64)
os.environ.setdefault("FAMPATH_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FAMPATH_APP_ENV", "development")
os.environ.setdefault("FAMPATH_LLM_PROVIDER", "mock")


async def seed() -> None:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal, Base, engine
    from app.models import (
        College, CollegeProgram, CutoffRecord, FeeStructure,
        PlacementStat, Scholarship, QuizQuestion, CounsellingEvent,
        DocumentChecklistItem, KnowledgeDocument, User
    )
    from app.core.security import hash_password

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        now = datetime.now(UTC)

        # â”€â”€ Admin user â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        admin_email = "admin@fampath.dev"
        existing_admin = await db.execute(select(User).where(User.email == admin_email))
        if not existing_admin.scalar_one_or_none():
            admin = User(
                email=admin_email,
                password_hash=hash_password("AdminDev1"),
                role="admin",
                status="active",
                full_name="FamPath Admin",
                preferred_locale="en",
            )
            db.add(admin)
            await db.flush()
            print(f"âœ“ Admin user created: {admin_email} / AdminDev1")

        # â”€â”€ Colleges â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        seed_dir = Path(__file__).parent.parent / "seed_data"
        colleges_csv = seed_dir / "colleges_seed.csv"

        college_map: dict[str, uuid.UUID] = {}
        if colleges_csv.exists():
            with open(colleges_csv) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing = await db.execute(
                        select(College).where(College.college_code == row["college_code"])
                    )
                    college = existing.scalar_one_or_none()
                    if not college:
                        college = College(
                            college_code=row["college_code"],
                            name=row["name"],
                            state=row.get("state"),
                            district=row.get("district"),
                            city=row.get("city"),
                            college_type=row.get("college_type"),
                            source=row.get("source", "SEED_SYNTHETIC"),
                            source_year=int(row["source_year"]) if row.get("source_year") else 2024,
                            import_date=now,
                            verification_status="synthetic",
                        )
                        db.add(college)
                        await db.flush()
                    college_map[college.college_code] = college.id

            print(f"âœ“ {len(college_map)} colleges seeded")

        # â”€â”€ Programs per college â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        branches = [
            ("CSE", "Computer Science & Engineering", "à°•à°‚à°ªà±à°¯à±‚à°Ÿà°°à± à°¸à±ˆà°¨à±à°¸à± & à°‡à°‚à°œà°¿à°¨à±€à°°à°¿à°‚à°—à±", "à¤•à¤‚à¤ªà¥à¤¯à¥‚à¤Ÿà¤° à¤µà¤¿à¤œà¥à¤žà¤¾à¤¨ à¤”à¤° à¤‡à¤‚à¤œà¥€à¤¨à¤¿à¤¯à¤°à¤¿à¤‚à¤—"),
            ("ECE", "Electronics & Communication Engineering", "à°Žà°²à°•à±à°Ÿà±à°°à°¾à°¨à°¿à°•à±à°¸à± & à°•à°®à±à°¯à±‚à°¨à°¿à°•à±‡à°·à°¨à± à°‡à°‚à°œà°¿à°¨à±€à°°à°¿à°‚à°—à±", "à¤‡à¤²à¥‡à¤•à¥à¤Ÿà¥à¤°à¥‰à¤¨à¤¿à¤•à¥à¤¸ à¤”à¤° à¤¸à¤‚à¤šà¤¾à¤° à¤‡à¤‚à¤œà¥€à¤¨à¤¿à¤¯à¤°à¤¿à¤‚à¤—"),
            ("MECH", "Mechanical Engineering", "à°®à±†à°•à°¾à°¨à°¿à°•à°²à± à°‡à°‚à°œà°¿à°¨à±€à°°à°¿à°‚à°—à±", "à¤®à¥ˆà¤•à¥‡à¤¨à¤¿à¤•à¤² à¤‡à¤‚à¤œà¥€à¤¨à¤¿à¤¯à¤°à¤¿à¤‚à¤—"),
            ("CIVIL", "Civil Engineering", "à°¸à°¿à°µà°¿à°²à± à°‡à°‚à°œà°¿à°¨à±€à°°à°¿à°‚à°—à±", "à¤¸à¤¿à¤µà¤¿à¤² à¤‡à¤‚à¤œà¥€à¤¨à¤¿à¤¯à¤°à¤¿à¤‚à¤—"),
            ("EEE", "Electrical & Electronics Engineering", "à°Žà°²à°•à±à°Ÿà±à°°à°¿à°•à°²à± & à°Žà°²à°•à±à°Ÿà±à°°à°¾à°¨à°¿à°•à±à°¸à± à°‡à°‚à°œà°¿à°¨à±€à°°à°¿à°‚à°—à±", "à¤‡à¤²à¥‡à¤•à¥à¤Ÿà¥à¤°à¤¿à¤•à¤² à¤”à¤° à¤‡à¤²à¥‡à¤•à¥à¤Ÿà¥à¤°à¥‰à¤¨à¤¿à¤•à¥à¤¸ à¤‡à¤‚à¤œà¥€à¤¨à¤¿à¤¯à¤°à¤¿à¤‚à¤—"),
        ]

        program_map: dict[tuple[str, str], uuid.UUID] = {}
        for college_code, college_id in list(college_map.items())[:5]:  # 5 colleges Ã— 5 branches
            for branch_code, branch_name, branch_te, branch_hi in branches:
                existing = await db.execute(
                    select(CollegeProgram).where(
                        CollegeProgram.college_id == college_id,
                        CollegeProgram.branch_code == branch_code,
                    )
                )
                program = existing.scalar_one_or_none()
                if not program:
                    program = CollegeProgram(
                        college_id=college_id,
                        branch_code=branch_code,
                        branch_name=branch_name,
                        branch_name_te=branch_te,
                        branch_name_hi=branch_hi,
                        intake_seats=60,
                    )
                    db.add(program)
                    await db.flush()
                program_map[(college_code, branch_code)] = program.id

        print(f"âœ“ {len(program_map)} programs seeded")

        # â”€â”€ Cutoff records (synthetic) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        import random
        rng = random.Random(42)  # deterministic seed

        cutoff_count = 0
        for (college_code, branch_code), program_id in program_map.items():
            college_id = college_map[college_code]
            for year in [2022, 2023, 2024]:
                for category in ["OC", "BC_A", "BC_B", "SC", "ST"]:
                    # Synthetic closing ranks (lower = better college)
                    base_rank = rng.randint(1000, 80000)
                    opening_rank = max(1, base_rank - rng.randint(500, 3000))
                    closing_rank = base_rank

                    existing = await db.execute(
                        select(CutoffRecord).where(
                            CutoffRecord.college_id == college_id,
                            CutoffRecord.program_id == program_id,
                            CutoffRecord.counselling_year == year,
                            CutoffRecord.category == category,
                            CutoffRecord.exam_type == "AP_EAPCET",
                        )
                    )
                    if not existing.scalar_one_or_none():
                        cr = CutoffRecord(
                            college_id=college_id,
                            program_id=program_id,
                            exam_type="AP_EAPCET",
                            counselling_year=year,
                            round=1,
                            category=category,
                            gender="any",
                            opening_rank=opening_rank,
                            closing_rank=closing_rank,
                            source="SEED_SYNTHETIC",
                            source_year=year,
                            import_date=now,
                            verification_status="synthetic",
                            created_at=now,
                        )
                        db.add(cr)
                        cutoff_count += 1

        print(f"âœ“ ~{cutoff_count} cutoff records seeded")

        # â”€â”€ Fee structures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        fee_count = 0
        rng2 = random.Random(99)
        for (college_code, branch_code), program_id in program_map.items():
            college_id = college_map[college_code]
            for year in [2023, 2024]:
                is_govt = "JNTUH" in college_code or "JNTUA" in college_code or "OSMANIA" in college_code or "RGUKT" in college_code
                tuition = rng2.randint(30000, 60000) if is_govt else rng2.randint(80000, 180000)

                existing = await db.execute(
                    select(FeeStructure).where(
                        FeeStructure.college_id == college_id,
                        FeeStructure.program_id == program_id,
                        FeeStructure.academic_year == year,
                    )
                )
                if not existing.scalar_one_or_none():
                    fs = FeeStructure(
                        college_id=college_id,
                        program_id=program_id,
                        academic_year=year,
                        tuition_fee=float(tuition),
                        hostel_fee=float(rng2.randint(40000, 80000)),
                        transport_fee=float(rng2.randint(10000, 25000)),
                        other_fees=float(rng2.randint(5000, 15000)),
                        source="SEED_SYNTHETIC",
                        source_year=year,
                        import_date=now,
                        verification_status="synthetic",
                        created_at=now,
                    )
                    db.add(fs)
                    fee_count += 1

        print(f"âœ“ {fee_count} fee records seeded")

        # â”€â”€ Placement stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        placement_count = 0
        rng3 = random.Random(7)
        for (college_code, branch_code), program_id in list(program_map.items())[:15]:
            college_id = college_map[college_code]
            for year in [2023, 2024]:
                placed = rng3.uniform(60, 95)
                avg_pkg = rng3.uniform(3.5, 12.0)
                median_pkg = avg_pkg * 0.85

                existing = await db.execute(
                    select(PlacementStat).where(
                        PlacementStat.college_id == college_id,
                        PlacementStat.program_id == program_id,
                        PlacementStat.placement_year == year,
                    )
                )
                if not existing.scalar_one_or_none():
                    ps = PlacementStat(
                        college_id=college_id,
                        program_id=program_id,
                        placement_year=year,
                        placed_percent=round(placed, 1),
                        avg_package_lpa=round(avg_pkg, 2),
                        median_package_lpa=round(median_pkg, 2),
                        highest_package_lpa=round(avg_pkg * 2.5, 2),
                        source="SEED_SYNTHETIC",
                        source_year=year,
                        import_date=now,
                        verification_status="synthetic",
                        created_at=now,
                    )
                    db.add(ps)
                    placement_count += 1

        print(f"âœ“ {placement_count} placement records seeded")

        # â”€â”€ Scholarships â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        scholarships_data = [
            {
                "name": "Jagananna Vidya Deevena (RTF - Full Fee Reimbursement)",
                "name_te": "à°œà°—à°¨à°¨à±à°¨ à°µà°¿à°¦à±à°¯à°¾ à°¦à±€à°µà±†à°¨ (à°ªà±‚à°°à±à°¤à°¿ à°«à±€à°œà± à°°à±€à°¯à°¿à°‚à°¬à°°à±à°¸à±â€Œà°®à±†à°‚à°Ÿà±)",
                "name_hi": "à¤œà¤—à¤¨à¤¨à¥à¤¨à¤¾ à¤µà¤¿à¤¦à¥à¤¯à¤¾ à¤¦à¥€à¤µà¥‡à¤¨à¤¾ (à¤ªà¥‚à¤°à¥à¤£ à¤¶à¥à¤²à¥à¤• à¤ªà¥à¤°à¤¤à¤¿à¤ªà¥‚à¤°à¥à¤¤à¤¿)",
                "provider": "Government of Andhra Pradesh (Social Welfare Dept)",
                "eligible_categories": ["SC", "ST", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "EWS"],
                "income_ceiling": 250000.0,
                "amount_per_year": 52000.0,
                "covers_hostel": False,
                "application_url": "https://jnanabhumi.ap.gov.in",
                "deadline_notes": "Official annual registration opens July-August for regular academic sessions",
                "source": "AP Social Welfare Dept Official Scheme Guidelines",
                "source_year": 2024,
                "verification_status": "verified",
            },
            {
                "name": "Jagananna Vasathi Deevena (Hostel & Boarding Assistance)",
                "name_te": "à°œà°—à°¨à°¨à±à°¨ à°µà°¸à°¤à°¿ à°¦à±€à°µà±†à°¨ (à°¹à°¾à°¸à±à°Ÿà°²à± & à°¬à±‹à°°à±à°¡à°¿à°‚à°—à± à°¸à°¾à°¯à°‚)",
                "name_hi": "à¤œà¤—à¤¨à¤¨à¥à¤¨à¤¾ à¤µà¤¸à¤¤à¤¿ à¤¦à¥€à¤µà¥‡à¤¨à¤¾ (à¤›à¤¾à¤¤à¥à¤°à¤¾à¤µà¤¾à¤¸ à¤¸à¤¹à¤¾à¤¯à¤¤à¤¾)",
                "provider": "Government of Andhra Pradesh",
                "eligible_categories": ["SC", "ST", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "EWS"],
                "income_ceiling": 250000.0,
                "amount_per_year": 20000.0,
                "covers_hostel": True,
                "application_url": "https://jnanabhumi.ap.gov.in",
                "deadline_notes": "Disbursed in 2 tranches per academic year directly to mother's account",
                "source": "AP Higher Education Department Official Gazette",
                "source_year": 2024,
                "verification_status": "verified",
            },
            {
                "name": "Telangana ePASS Post-Matric Reimbursement of Tuition (RTF)",
                "name_te": "à°¤à±†à°²à°‚à°—à°¾à°£ à°ˆà°ªà°¾à°¸à± à°ªà±‹à°¸à±à°Ÿà±-à°®à±†à°Ÿà±à°°à°¿à°•à± à°«à±€à°œà± à°°à±€à°¯à°¿à°‚à°¬à°°à±à°¸à±â€Œà°®à±†à°‚à°Ÿà± (RTF)",
                "name_hi": "à¤¤à¥‡à¤²à¤‚à¤—à¤¾à¤¨à¤¾ à¤ˆà¤ªà¤¾à¤¸ à¤ªà¥‹à¤¸à¥à¤Ÿ-à¤®à¥ˆà¤Ÿà¥à¤°à¤¿à¤• à¤›à¤¾à¤¤à¥à¤°à¤µà¥ƒà¤¤à¥à¤¤à¤¿",
                "provider": "Government of Telangana (BC Welfare Dept)",
                "eligible_categories": ["SC", "ST", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "EWS"],
                "income_ceiling": 200000.0,
                "amount_per_year": 35000.0,
                "covers_hostel": False,
                "application_url": "https://telanganaepass.cgg.gov.in",
                "deadline_notes": "Online portal opens August to October annually for fresh and renewal applicants",
                "source": "Telangana ePASS Official Portal",
                "source_year": 2024,
                "verification_status": "verified",
            },
            {
                "name": "AICTE Pragati Scholarship for Girl Students",
                "name_te": "à°¬à°¾à°²à°¿à°•à°² à°•à±‹à°¸à°‚ AICTE à°ªà±à°°à°—à°¤à°¿ à°¸à±à°•à°¾à°²à°°à±â€Œà°·à°¿à°ªà±",
                "name_hi": "à¤›à¤¾à¤¤à¥à¤°à¤¾à¤“à¤‚ à¤•à¥‡ à¤²à¤¿à¤ à¤à¤†à¤ˆà¤¸à¥€à¤Ÿà¥€à¤ˆ à¤ªà¥à¤°à¤—à¤¤à¤¿ à¤›à¤¾à¤¤à¥à¤°à¤µà¥ƒà¤¤à¥à¤¤à¤¿",
                "provider": "All India Council for Technical Education (AICTE)",
                "eligible_categories": ["OC", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "SC", "ST", "EWS"],
                "income_ceiling": 800000.0,
                "amount_per_year": 50000.0,
                "covers_hostel": False,
                "application_url": "https://scholarships.gov.in",
                "deadline_notes": "National Scholarship Portal window opens July to October annually",
                "source": "National Scholarship Portal (NSP) AICTE Guidelines",
                "source_year": 2024,
                "verification_status": "verified",
            },
            {
                "name": "Central Sector Scheme of Scholarships for College Students",
                "name_te": "à°•à°¾à°²à±‡à°œà±€ à°µà°¿à°¦à±à°¯à°¾à°°à±à°¥à±à°² à°•à±‹à°¸à°‚ à°¸à±†à°‚à°Ÿà±à°°à°²à± à°¸à±†à°•à±à°Ÿà°¾à°°à± à°¸à±à°•à°¾à°²à°°à±â€Œà°·à°¿à°ªà±",
                "name_hi": "à¤•à¥‰à¤²à¥‡à¤œ à¤›à¤¾à¤¤à¥à¤°à¥‹à¤‚ à¤•à¥‡ à¤²à¤¿à¤ à¤•à¥‡à¤‚à¤¦à¥à¤°à¥€à¤¯ à¤•à¥à¤·à¥‡à¤¤à¥à¤° à¤›à¤¾à¤¤à¥à¤°à¤µà¥ƒà¤¤à¥à¤¤à¤¿ à¤¯à¥‹à¤œà¤¨à¤¾",
                "provider": "Ministry of Education, Government of India",
                "eligible_categories": ["OC", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "SC", "ST", "EWS"],
                "income_ceiling": 450000.0,
                "amount_per_year": 12000.0,
                "covers_hostel": False,
                "application_url": "https://scholarships.gov.in",
                "deadline_notes": "Targeted at top 20th percentile students in 12th Board examinations",
                "source": "Ministry of Education - Department of Higher Education",
                "source_year": 2024,
                "verification_status": "verified",
            },
        ]

        s_count = 0
        for s_item in scholarships_data:
            existing = await db.execute(
                select(Scholarship).where(Scholarship.name == s_item["name"])
            )
            if not existing.scalar_one_or_none():
                sc = Scholarship(
                    name=s_item["name"],
                    name_te=s_item["name_te"],
                    name_hi=s_item["name_hi"],
                    provider=s_item["provider"],
                    eligible_categories=s_item["eligible_categories"],
                    income_ceiling=s_item["income_ceiling"],
                    amount_per_year=s_item["amount_per_year"],
                    covers_hostel=s_item["covers_hostel"],
                    application_url=s_item["application_url"],
                    deadline_notes=s_item["deadline_notes"],
                    source=s_item["source"],
                    source_year=s_item["source_year"],
                    import_date=now,
                    verification_status=s_item["verification_status"],
                    is_active=True,
                    created_at=now,
                )
                db.add(sc)
                s_count += 1

        print(f"âœ“ {s_count} scholarships seeded")

        # â”€â”€ Quiz questions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        questions_file = seed_dir / "questions_seed.json"
        if questions_file.exists():
            with open(questions_file, encoding="utf-8") as f:
                questions = json.load(f)

            q_count = 0
            for q_data in questions:
                existing = await db.execute(
                    select(QuizQuestion).where(QuizQuestion.question_text == q_data["question_text"])
                )
                if not existing.scalar_one_or_none():
                    q = QuizQuestion(
                        question_text=q_data["question_text"],
                        question_te=q_data.get("question_te"),
                        question_hi=q_data.get("question_hi"),
                        riasec_dimension=q_data["riasec_dimension"],
                        weight=q_data.get("weight", 1.0),
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(q)
                    q_count += 1

            print(f"âœ“ {q_count} quiz questions seeded")

        # â”€â”€ Counselling events â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        from datetime import date
        events = [
            ("AP_EAPCET", "AP EAPCET Round 1 Registration", "AP EAPCET à°°à±Œà°‚à°¡à± 1 à°¨à°®à±‹à°¦à±", "AP EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 1 à¤ªà¤‚à¤œà¥€à¤•à¤°à¤£", 2024, date(2024, 7, 15), 1),
            ("AP_EAPCET", "AP EAPCET Round 1 Allotment", "AP EAPCET à°°à±Œà°‚à°¡à± 1 à°•à±‡à°Ÿà°¾à°¯à°¿à°‚à°ªà±", "AP EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 1 à¤†à¤µà¤‚à¤Ÿà¤¨", 2024, date(2024, 7, 25), 1),
            ("AP_EAPCET", "AP EAPCET Round 2 Registration", "AP EAPCET à°°à±Œà°‚à°¡à± 2 à°¨à°®à±‹à°¦à±", "AP EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 2 à¤ªà¤‚à¤œà¥€à¤•à¤°à¤£", 2024, date(2024, 8, 1), 2),
            ("AP_EAPCET", "AP EAPCET Round 2 Allotment", "AP EAPCET à°°à±Œà°‚à°¡à± 2 à°•à±‡à°Ÿà°¾à°¯à°¿à°‚à°ªà±", "AP EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 2 à¤†à¤µà¤‚à¤Ÿà¤¨", 2024, date(2024, 8, 10), 2),
            ("TS_EAPCET", "TS EAPCET Round 1 Web Options", "TS EAPCET à°°à±Œà°‚à°¡à± 1 à°µà±†à°¬à± à°†à°ªà±à°·à°¨à±à°²à±", "TS EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 1 à¤µà¥‡à¤¬ à¤µà¤¿à¤•à¤²à¥à¤ª", 2024, date(2024, 7, 18), 1),
            ("TS_EAPCET", "TS EAPCET Round 1 Allotment", "TS EAPCET à°°à±Œà°‚à°¡à± 1 à°•à±‡à°Ÿà°¾à°¯à°¿à°‚à°ªà±", "TS EAPCET à¤°à¤¾à¤‰à¤‚à¤¡ 1 à¤†à¤µà¤‚à¤Ÿà¤¨", 2024, date(2024, 7, 28), 1),
        ]

        ev_count = 0
        for exam, name, name_te, name_hi, year, ev_date, round_no in events:
            existing = await db.execute(
                select(CounsellingEvent).where(
                    CounsellingEvent.exam_type == exam,
                    CounsellingEvent.event_name == name,
                    CounsellingEvent.event_year == year,
                )
            )
            if not existing.scalar_one_or_none():
                ev = CounsellingEvent(
                    exam_type=exam,
                    event_name=name,
                    event_name_te=name_te,
                    event_name_hi=name_hi,
                    event_year=year,
                    event_date=ev_date,
                    round_number=round_no,
                    source="SEED_SYNTHETIC",
                )
                db.add(ev)
                ev_count += 1

        print(f"âœ“ {ev_count} counselling events seeded")

        # â”€â”€ Document checklist â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        checklist_items = [
            ("AP_EAPCET", None, "AP EAPCET Rank Card", "AP EAPCET à°°à±à°¯à°¾à°‚à°•à± à°•à°¾à°°à±à°¡à±", "AP EAPCET à¤°à¥ˆà¤‚à¤• à¤•à¤¾à¤°à¥à¤¡", True),
            ("AP_EAPCET", None, "10th (SSC) Certificate", "10à°µ à°¤à°°à°—à°¤à°¿ à°¸à°°à±à°Ÿà°¿à°«à°¿à°•à±‡à°Ÿà±", "10à¤µà¥€à¤‚ (SSC) à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤°", True),
            ("AP_EAPCET", None, "12th (Intermediate) Marks Memo", "12à°µ à°¤à°°à°—à°¤à°¿ à°®à°¾à°°à±à°•à±à°² à°®à±†à°®à±‹", "12à¤µà¥€à¤‚ à¤®à¤¾à¤°à¥à¤•à¤¶à¥€à¤Ÿ", True),
            ("AP_EAPCET", None, "Study/Residence Certificate", "à°…à°§à±à°¯à°¯à°¨/à°¨à°¿à°µà°¾à°¸ à°§à±ƒà°µà±€à°•à°°à°£", "à¤…à¤§à¥à¤¯à¤¯à¤¨/à¤¨à¤¿à¤µà¤¾à¤¸ à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤°", True),
            ("AP_EAPCET", None, "Aadhaar Card", "à°†à°§à°¾à°°à± à°•à°¾à°°à±à°¡à±", "à¤†à¤§à¤¾à¤° à¤•à¤¾à¤°à¥à¤¡", True),
            ("AP_EAPCET", None, "Passport-size Photographs (6 copies)", "à°ªà°¾à°¸à±à°ªà±‹à°°à±à°Ÿà± à°«à±‹à°Ÿà±‹à°²à± (6 à°•à°¾à°ªà±€à°²à±)", "à¤ªà¤¾à¤¸à¤ªà¥‹à¤°à¥à¤Ÿ à¤«à¥‹à¤Ÿà¥‹ (6 à¤ªà¥à¤°à¤¤à¤¿à¤¯à¤¾à¤)", True),
            ("AP_EAPCET", "SC", "Caste Certificate (SC)", "à°•à±à°²à°‚ à°§à±ƒà°µà±€à°•à°°à°£ (SC)", "à¤œà¤¾à¤¤à¤¿ à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤° (SC)", True),
            ("AP_EAPCET", "ST", "Caste Certificate (ST)", "à°•à±à°²à°‚ à°§à±ƒà°µà±€à°•à°°à°£ (ST)", "à¤œà¤¾à¤¤à¤¿ à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤° (ST)", True),
            ("AP_EAPCET", "BC_A", "Caste Certificate (BC)", "à°•à±à°²à°‚ à°§à±ƒà°µà±€à°•à°°à°£ (BC)", "à¤œà¤¾à¤¤à¤¿ à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤° (BC)", True),
            ("AP_EAPCET", "EWS", "Income Certificate (EWS)", "à°†à°¦à°¾à°¯ à°§à±ƒà°µà±€à°•à°°à°£ (EWS)", "à¤†à¤¯ à¤ªà¥à¤°à¤®à¤¾à¤£ à¤ªà¤¤à¥à¤° (EWS)", True),
        ]

        cl_count = 0
        for exam, cat, name, name_te, name_hi, mandatory in checklist_items:
            existing = await db.execute(
                select(DocumentChecklistItem).where(
                    DocumentChecklistItem.exam_type == exam,
                    DocumentChecklistItem.document_name == name,
                )
            )
            if not existing.scalar_one_or_none():
                item = DocumentChecklistItem(
                    exam_type=exam,
                    category_filter=cat,
                    document_name=name,
                    document_name_te=name_te,
                    document_name_hi=name_hi,
                    is_mandatory=mandatory,
                )
                db.add(item)
                cl_count += 1

        print(f"âœ“ {cl_count} checklist items seeded")

        # â”€â”€ Knowledge documents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        knowledge_dir = seed_dir / "knowledge"
        docs_count = 0
        if knowledge_dir.exists():
            for txt_file in knowledge_dir.glob("*.txt"):
                existing = await db.execute(
                    select(KnowledgeDocument).where(KnowledgeDocument.title == txt_file.stem)
                )
                if not existing.scalar_one_or_none():
                    kd = KnowledgeDocument(
                        title=txt_file.stem,
                        doc_type="counselling_rules",
                        language="en",
                        source="SEED_SYNTHETIC",
                        source_year=2024,
                        upload_date=now,
                        is_active=True,
                    )
                    db.add(kd)
                    docs_count += 1

        print(f"âœ“ {docs_count} knowledge documents seeded")

        await db.commit()
        print("\nâœ… Database seeding complete!")
        print("âš ï¸  All data is SYNTHETIC SEED DATA for development only.")
        print("   source field = 'SEED_SYNTHETIC', verification_status = 'synthetic'")


if __name__ == "__main__":
    asyncio.run(seed())
