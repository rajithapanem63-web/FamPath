# Spec: Data Platform & Admin — Requirements

## Overview
A trusted data layer for colleges, cutoffs, fees, placements, and scholarships — with a full admin panel for ingestion, validation, and freshness management.

## User Stories

### Data Ingestion
- US-DATA-01: As an admin, I can upload a CSV/Excel file of college data so it is validated and imported.
- US-DATA-02: As an admin, I can upload historical cutoff records (rank/category/branch/year) via CSV.
- US-DATA-03: As an admin, I can upload fee structures and placement statistics per college/branch/year.
- US-DATA-04: As an admin, I can upload scholarship schemes linked to category and income criteria.
- US-DATA-05: As an admin, I see import validation errors (schema mismatches, missing required fields, out-of-range values) before records are committed.
- US-DATA-06: As an admin, I can view a data-freshness dashboard showing when each dataset was last updated.
- US-DATA-07: As an admin, I can add/edit/deactivate individual college records through a web form.

### Question Bank
- US-QB-01: As an admin, I can add, edit, and deactivate aptitude/interest quiz questions with translations.
- US-QB-02: As an admin, I can preview how a question appears to a student.

### Data Quality
- US-DATA-08: As an admin, I can mark any data record as "verified" or "unverified"; the UI shows both states to users.
- US-DATA-09: Every imported record stores: source name, source year, import date, imported_by, verification_status.

## Acceptance Criteria

### CSV Import
- WHEN an admin uploads a college CSV matching the schema, THEN all valid rows are imported, a summary shows inserted/skipped/error counts, and each record has `verification_status = unverified`.
- WHEN a row fails schema validation (wrong type, missing required field), THEN that row is skipped, an error report row is created, and valid rows are still imported.
- WHEN an admin uploads a file > 10 MB, THEN the system returns HTTP 413 and no records are imported.
- WHERE duplicate detection finds an identical (college_code, year) pair, the existing record is updated and a `DUPLICATE_UPDATED` flag is set.

### Freshness & Verification
- WHEN the admin dashboard is loaded, THEN each dataset shows its last import date and count of unverified records.
- WHEN data is older than 365 days, THEN a "stale data" warning is shown on the dataset card.

### Admin RBAC
- WHERE a non-admin attempts to access `/api/v1/admin/*`, the system MUST return HTTP 403.

### Question Bank
- WHEN an admin saves a question with translations for all three locales, THEN the question is active and returned in the quiz API.
- WHERE a question is missing a translation for any active locale, THEN saving is blocked with error `MISSING_TRANSLATION`.
