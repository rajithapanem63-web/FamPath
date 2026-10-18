# Requirements: Admin Panel Frontend

**Spec ID:** admin-panel-frontend  
**Status:** Draft  
**Dependencies:** None (backend already exists)

---

## Overview

Build the missing admin UI for data management. Backend already has admin_router with endpoints; we need the frontend.

**In Scope:**
- College management (CRUD, CSV import)
- Cutoff record management
- Fee structure management
- Scholarship management
- Question bank (aptitude quiz)
- Data verification workflow
- Analytics dashboard

**Out of Scope:**
- User management (use existing tools)
- Platform settings

---

## User Stories

### US-AP-001: Import College Data via CSV
**As an** admin  
**I want to** upload a CSV of colleges  
**So that** the platform has up-to-date college information

**Acceptance:**
- Upload CSV file
- System validates schema
- Shows preview of 10 rows
- Confirms import
- Shows success/error summary

### US-AP-002: Manage Cutoff Records
**As an** admin  
**I want to** view and edit cutoff records  
**So that** predictions are accurate

**Acceptance:**
- List all cutoffs with filters (exam, year, college, branch)
- Edit individual records
- Bulk import via CSV
- Mark as "verified"

### US-AP-003: View Data Freshness
**As an** admin  
**I want to** see when data was last updated  
**So that** I know what needs refreshing

**Acceptance:**
- Dashboard shows: last import date per data type
- Red indicator if data > 1 year old

### US-AP-004: Analytics Dashboard
**As an** admin  
**I want to** see platform usage stats  
**So that** I understand user behavior

**Acceptance:**
- Total families, predictions, preferences filled
- Completion rates
- Most searched colleges

---

## Pages Required

1. `/admin/dashboard` - Overview, analytics
2. `/admin/colleges` - College management
3. `/admin/cutoffs` - Cutoff records
4. `/admin/fees` - Fee structures
5. `/admin/scholarships` - Scholarship management
6. `/admin/questions` - Aptitude quiz questions
7. `/admin/import` - CSV import interface

---

## API (Already Exists)

Backend has `admin_router.py` with these endpoints:
- GET /api/v1/admin/colleges
- POST /api/v1/admin/colleges
- POST /api/v1/admin/import/csv

We just need to connect frontend to them.

---

**Status:** Ready for design.md
