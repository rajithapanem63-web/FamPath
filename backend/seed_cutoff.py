#!/usr/bin/env python3
"""
Seed the local SQLite database with college programs and cutoff records.
Run from the backend/ directory: python seed_cutoff.py
"""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import UTC, datetime
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FAMPATH_DB_URL", "sqlite+aiosqlite:///./fampath_dev.db")
os.environ.setdefault("FAMPATH_SECRET_KEY", "dev-secret-key-change-in-production")
os.environ.setdefault("FAMPATH_ENCRYPTION_KEY", "0" * 64)
os.environ.setdefault("FAMPATH_APP_ENV", "development")
os.environ.setdefault("FAMPATH_LLM_PROVIDER", "mock")

SEED_DATA = [
    ("JNTUH001","JNTUH College of Engineering, Hyderabad","Telangana","Hyderabad","government","CSE","Computer Science Engineering",5200),
    ("JNTUH001","JNTUH College of Engineering, Hyderabad","Telangana","Hyderabad","government","ECE","Electronics & Communication Engineering",9800),
    ("JNTUH001","JNTUH College of Engineering, Hyderabad","Telangana","Hyderabad","government","EEE","Electrical & Electronics Engineering",15000),
    ("JNTUH001","JNTUH College of Engineering, Hyderabad","Telangana","Hyderabad","government","MECH","Mechanical Engineering",22000),
    ("JNTUH001","JNTUH College of Engineering, Hyderabad","Telangana","Hyderabad","government","CIVIL","Civil Engineering",35000),
    ("CBIT001","CBIT Hyderabad","Telangana","Hyderabad","private_aided","CSE","Computer Science Engineering",12000),
    ("CBIT001","CBIT Hyderabad","Telangana","Hyderabad","private_aided","ECE","Electronics & Communication Engineering",22000),
    ("CBIT001","CBIT Hyderabad","Telangana","Hyderabad","private_aided","EEE","Electrical & Electronics Engineering",32000),
    ("CBIT001","CBIT Hyderabad","Telangana","Hyderabad","private_aided","MECH","Mechanical Engineering",45000),
    ("VASAVI001","Vasavi College of Engineering","Telangana","Hyderabad","private_aided","CSE","Computer Science Engineering",18000),
    ("VASAVI001","Vasavi College of Engineering","Telangana","Hyderabad","private_aided","ECE","Electronics & Communication Engineering",28000),
    ("VASAVI001","Vasavi College of Engineering","Telangana","Hyderabad","private_aided","IT","Information Technology",20000),
    ("VASAVI001","Vasavi College of Engineering","Telangana","Hyderabad","private_aided","MECH","Mechanical Engineering",50000),
    ("VNR001","VNR VJIET Hyderabad","Telangana","Hyderabad","private_unaided","CSE","Computer Science Engineering",25000),
    ("VNR001","VNR VJIET Hyderabad","Telangana","Hyderabad","private_unaided","ECE","Electronics & Communication Engineering",38000),
    ("VNR001","VNR VJIET Hyderabad","Telangana","Hyderabad","private_unaided","IT","Information Technology",30000),
    ("VNR001","VNR VJIET Hyderabad","Telangana","Hyderabad","private_unaided","AIML","AI & Machine Learning",28000),
    ("MVSR001","MVSR Engineering College","Telangana","Hyderabad","private_unaided","CSE","Computer Science Engineering",32000),
    ("MVSR001","MVSR Engineering College","Telangana","Hyderabad","private_unaided","ECE","Electronics & Communication Engineering",48000),
    ("MVSR001","MVSR Engineering College","Telangana","Hyderabad","private_unaided","MECH","Mechanical Engineering",65000),
    ("MGIT001","Mahatma Gandhi Institute of Technology","Telangana","Hyderabad","private_unaided","CSE","Computer Science Engineering",35000),
    ("MGIT001","Mahatma Gandhi Institute of Technology","Telangana","Hyderabad","private_unaided","ECE","Electronics & Communication Engineering",55000),
    ("MGIT001","Mahatma Gandhi Institute of Technology","Telangana","Hyderabad","private_unaided","IT","Information Technology",40000),
    ("JNTUA001","JNTUA College of Engineering, Anantapur","Andhra Pradesh","Anantapur","government","CSE","Computer Science Engineering",8000),
    ("JNTUA001","JNTUA College of Engineering, Anantapur","Andhra Pradesh","Anantapur","government","ECE","Electronics & Communication Engineering",14000),
    ("JNTUA001","JNTUA College of Engineering, Anantapur","Andhra Pradesh","Anantapur","government","EEE","Electrical & Electronics Engineering",20000),
    ("JNTUA001","JNTUA College of Engineering, Anantapur","Andhra Pradesh","Anantapur","government","MECH","Mechanical Engineering",30000),
    ("JNTUA001","JNTUA College of Engineering, Anantapur","Andhra Pradesh","Anantapur","government","CIVIL","Civil Engineering",45000),
    ("SVEC001","Sri Venkateswara Engineering College","Andhra Pradesh","Chittoor","private_aided","CSE","Computer Science Engineering",15000),
    ("SVEC001","Sri Venkateswara Engineering College","Andhra Pradesh","Chittoor","private_aided","ECE","Electronics & Communication Engineering",25000),
    ("SVEC001","Sri Venkateswara Engineering College","Andhra Pradesh","Chittoor","private_aided","EEE","Electrical & Electronics Engineering",38000),
    ("SVEC001","Sri Venkateswara Engineering College","Andhra Pradesh","Chittoor","private_aided","IT","Information Technology",18000),
    ("GITAM001","GITAM University, Visakhapatnam","Andhra Pradesh","Visakhapatnam","deemed","CSE","Computer Science Engineering",22000),
    ("GITAM001","GITAM University, Visakhapatnam","Andhra Pradesh","Visakhapatnam","deemed","ECE","Electronics & Communication Engineering",35000),
    ("GITAM001","GITAM University, Visakhapatnam","Andhra Pradesh","Visakhapatnam","deemed","AIML","AI & Machine Learning",28000),
    ("MVGR001","MVGR College of Engineering","Andhra Pradesh","Vizianagaram","private_unaided","CSE","Computer Science Engineering",40000),
    ("MVGR001","MVGR College of Engineering","Andhra Pradesh","Vizianagaram","private_unaided","ECE","Electronics & Communication Engineering",60000),
    ("MVGR001","MVGR College of Engineering","Andhra Pradesh","Vizianagaram","private_unaided","MECH","Mechanical Engineering",80000),
    ("RGUKT001","RGUKT Basar (IIIT Basar)","Telangana","Nirmal","government","CSE","Computer Science Engineering",3500),
    ("RGUKT001","RGUKT Basar (IIIT Basar)","Telangana","Nirmal","government","ECE","Electronics & Communication Engineering",7000),
    ("IIIT_H001","IIIT Hyderabad","Telangana","Hyderabad","deemed","CSE","Computer Science Engineering",800),
    ("IIIT_H001","IIIT Hyderabad","Telangana","Hyderabad","deemed","ECE","Electronics & Communication Engineering",2500),
    ("BITS_H001","BITS Pilani Hyderabad Campus","Telangana","Hyderabad","deemed","CSE","Computer Science Engineering",1500),
    ("BITS_H001","BITS Pilani Hyderabad Campus","Telangana","Hyderabad","deemed","ECE","Electronics & Communication Engineering",4000),
    ("BITS_H001","BITS Pilani Hyderabad Campus","Telangana","Hyderabad","deemed","MECH","Mechanical Engineering",8000),
]

EXAM_TYPES = {"Telangana": "TS_EAPCET", "Andhra Pradesh": "AP_EAPCET"}
CATEGORY_MULTIPLIERS = {"OC":1.0,"BC_A":1.4,"BC_B":1.5,"BC_C":1.6,"BC_D":1.7,"SC":2.5,"ST":3.5,"EWS":1.1}

async def seed():
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal, Base, engine
    import app.models  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.models.college import College, CollegeProgram, CutoffRecord
    async with AsyncSessionLocal() as db:
        now = datetime.now(UTC)
        college_map = {}
        program_map = {}
        for row in SEED_DATA:
            code,name,state,district,ctype,branch_code,branch_name,oc_rank = row
            if code not in college_map:
                existing = await db.execute(select(College).where(College.college_code == code))
                college = existing.scalar_one_or_none()
                if not college:
                    college = College(college_code=code,name=name,state=state,district=district,college_type=ctype,is_active=True,source="SEED_SYNTHETIC",source_year=2024)
                    db.add(college); await db.flush()
                    print(f"  + College: {name}")
                college_map[code] = college.id
            college_id = college_map[code]
            prog_key = (college_id, branch_code)
            if prog_key not in program_map:
                ep = await db.execute(select(CollegeProgram).where(CollegeProgram.college_id==college_id,CollegeProgram.branch_code==branch_code))
                prog = ep.scalar_one_or_none()
                if not prog:
                    prog = CollegeProgram(college_id=college_id,branch_code=branch_code,branch_name=branch_name,is_active=True)
                    db.add(prog); await db.flush()
                program_map[prog_key] = prog.id
            program_id = program_map[prog_key]
            exam_type = EXAM_TYPES.get(state,"AP_EAPCET")
            for category, multiplier in CATEGORY_MULTIPLIERS.items():
                closing_rank = min(int(oc_rank * multiplier), 200000)
                opening_rank = max(1, int(closing_rank * 0.7))
                ec = await db.execute(select(CutoffRecord).where(CutoffRecord.college_id==college_id,CutoffRecord.program_id==program_id,CutoffRecord.counselling_year==2024,CutoffRecord.category==category,CutoffRecord.exam_type==exam_type,CutoffRecord.gender=="any",CutoffRecord.round==1))
                if not ec.scalar_one_or_none():
                    db.add(CutoffRecord(college_id=college_id,program_id=program_id,exam_type=exam_type,counselling_year=2024,round=1,category=category,gender="any",opening_rank=opening_rank,closing_rank=closing_rank,source="SEED_SYNTHETIC",source_year=2024,created_at=now))
        await db.commit()
        print(f"\n[OK] Seeded {len(SEED_DATA)} programs x {len(CATEGORY_MULTIPLIERS)} categories = {len(SEED_DATA)*len(CATEGORY_MULTIPLIERS)} cutoff records")

if __name__ == "__main__":
    print("Seeding cutoff data into local SQLite DB...")
    asyncio.run(seed())
