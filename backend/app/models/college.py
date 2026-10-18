"""
College and related data models: College, CollegeProgram, CutoffRecord,
FeeStructure, PlacementStat, Scholarship, ImportJob.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class College(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "colleges"

    college_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[str | None] = mapped_column(String(255))
    name_hi: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(50), index=True)
    district: Mapped[str | None] = mapped_column(String(100), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    college_type: Mapped[str | None] = mapped_column(String(30), index=True)
    affiliation: Mapped[str | None] = mapped_column(String(255))
    naac_grade: Mapped[str | None] = mapped_column(String(5))
    nba_programs: Mapped[list | None] = mapped_column(JSONB)
    website: Mapped[str | None] = mapped_column(Text)
    established_year: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    import_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)

    programs: Mapped[list["CollegeProgram"]] = relationship(back_populates="college")

    def __repr__(self) -> str:
        return f"<College {self.college_code}: {self.name}>"


class CollegeProgram(UUIDPKMixin, Base):
    __tablename__ = "college_programs"

    college_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("colleges.id"), nullable=False, index=True
    )
    branch_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_name_te: Mapped[str | None] = mapped_column(String(255))
    branch_name_hi: Mapped[str | None] = mapped_column(String(255))
    intake_seats: Mapped[int | None] = mapped_column(Integer)
    duration_years: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    college: Mapped["College"] = relationship(back_populates="programs")


class CutoffRecord(UUIDPKMixin, Base):
    __tablename__ = "cutoff_records"
    __table_args__ = (
        UniqueConstraint(
            "college_id", "program_id", "counselling_year", "round", "category", "gender",
            "exam_type",
            name="uq_cutoff_record",
        ),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("colleges.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("college_programs.id"), nullable=False, index=True
    )
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    counselling_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    round: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(10), default="any", nullable=False)
    opening_rank: Mapped[int | None] = mapped_column(Integer)
    closing_rank: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    import_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FeeStructure(UUIDPKMixin, Base):
    __tablename__ = "fee_structures"

    college_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("colleges.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("college_programs.id"), nullable=False, index=True
    )
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tuition_fee: Mapped[float | None] = mapped_column(Numeric(12, 2))
    hostel_fee: Mapped[float | None] = mapped_column(Numeric(12, 2))
    transport_fee: Mapped[float | None] = mapped_column(Numeric(12, 2))
    other_fees: Mapped[float | None] = mapped_column(Numeric(12, 2))
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    import_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlacementStat(UUIDPKMixin, Base):
    __tablename__ = "placement_stats"

    college_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("colleges.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("college_programs.id"), nullable=False, index=True
    )
    placement_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    placed_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_package_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    median_package_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    highest_package_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    top_recruiters: Mapped[list | None] = mapped_column(JSONB)
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    import_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Scholarship(UUIDPKMixin, Base):
    __tablename__ = "scholarships"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_te: Mapped[str | None] = mapped_column(String(255))
    name_hi: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(255))
    eligible_categories: Mapped[list | None] = mapped_column(JSONB)
    income_ceiling: Mapped[float | None] = mapped_column(Numeric(12, 2))
    amount_per_year: Mapped[float | None] = mapped_column(Numeric(12, 2))
    covers_hostel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    application_url: Mapped[str | None] = mapped_column(Text)
    deadline_notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))
    source_year: Mapped[int | None] = mapped_column(Integer)
    import_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImportJob(UUIDPKMixin, Base):
    __tablename__ = "import_jobs"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    dataset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    total_rows: Mapped[int | None] = mapped_column(Integer)
    imported_rows: Mapped[int | None] = mapped_column(Integer)
    skipped_rows: Mapped[int | None] = mapped_column(Integer)
    error_rows: Mapped[int | None] = mapped_column(Integer)
    error_report: Mapped[list | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
