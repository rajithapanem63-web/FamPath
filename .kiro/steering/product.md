# FamPath – Product Vision, Users & Scope

## Vision

FamPath is an AI-enabled, family-first decision-support platform for engineering college and branch selection in India. It transforms a historically scattered, stressful, and inequitable process into a transparent, data-backed, multilingual experience that the whole family navigates together.

The platform does not merely predict a rank cutoff — it surfaces reasoning, resolves conflicts between family members, calculates true costs, and produces a shareable decision record that students and parents can feel confident about.

## Problem Statement

- Information about colleges, cutoffs, fees, placements, and counselling rules is scattered across dozens of portals.
- First-generation learners lack knowledgeable guidance networks.
- Students and parents often disagree on branch/location/budget priorities with no structured way to reconcile differences.
- Existing tools are rank → college list lookups with no explainability, no family collaboration, and no cost or career context.

## Target Users

| Role | Description | Key Needs |
|------|-------------|-----------|
| Student | Post-10+2, AP/TS EAPCET or JEE candidate | Branch fit, peer comparisons, career context, unbiased advice |
| Parent / Guardian | Primary financial decision-maker | Cost, ROI, safety, reputation, placement data |
| Counsellor | School or independent career counsellor | Client workspace view, report access, notes |
| Admin | Platform operator | Data management, content moderation, analytics |

## Initial Geographic Scope

- **Primary:** Andhra Pradesh (AP EAPCET) and Telangana (TS EAPCET)
- **Secondary:** National JEE / JoSAA pool
- **Data model:** Designed to extend to other state CETs (MHT-CET, KCET, WBJEE, etc.) without schema migrations

## MVP Feature Set

1. Accounts and Family Workspace (student creates space, invites parents; role-based profiles)
2. Preference Questionnaires (weighted preferences per family member)
3. Family Alignment Dashboard (agreement/conflict visualisation)
4. Conflict Mediator AI (neutral reasoning + compromise suggestions)
5. College & Branch Predictor (rank → Safe/Target/Dream bands with probability + explanation)
6. Aptitude & Interest Profiler (RIASEC-style quiz → Branch Fit Score)
7. Cost & ROI Calculator (4-year cost, scholarships, EMI, payback vs placement)
8. Explainable Recommendations (every card shows data source, year, reasoning)
9. Multilingual RAG Chatbot (Telugu, Hindi, English; cites sources; refuses on uncertainty)
10. Shortlist & Family Decision Log (shared list, comments, voting, history)
11. Final Decision Report (downloadable PDF)
12. Counselling Timeline & Document Checklist (deadlines, category-wise docs)
13. Admin Panel (college/cutoff/fee data management, CSV import, freshness indicator)

## Phase 2 Features (post-MVP, behind feature flags)

Counselling Round Simulator, Plan B/C Generator, Peer-Pressure & Bias Detector, College Claim Verifier, Scam Alerts, Safety & Living Cost Index, Senior Mentor Matching, Counsellor Booking, Scenario Stress Test, WhatsApp/Voice Mode, Anonymised Insights Dashboard.

## Data Integrity Rules

- No real-world cutoff/fee/placement numbers may be invented or hard-coded.
- All ingested data records must carry: `source`, `year`, `import_date`, `verification_status`.
- Synthetic seed data is clearly labelled (prefix `SEED_` in source field) for development use only.
- Every prediction UI element carries the disclaimer: *"Estimate, not a guarantee."*
- No scraping without explicit source permission; prefer official or openly licensed datasets.

## Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Family workspaces created | 1 000 in first semester |
| Shortlists with ≥ 2 family members contributing | 60 % |
| PDF report downloads | 40 % of active workspaces |
| Chatbot grounded-answer rate | ≥ 85 % |
| User satisfaction (CSAT) | ≥ 4 / 5 |

## Out of Scope (MVP)

- Live seat-allotment tracking during counselling rounds
- Real payments or loan origination (links to external providers only)
- Native mobile apps (PWA covers mobile in MVP)
- Any state outside AP/TS/National JEE
