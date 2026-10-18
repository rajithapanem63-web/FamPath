# Spec: Auth & Family Workspace — Tasks

## Task List

### TASK-AUTH-01: Database models & migrations for users/tokens
- Create SQLAlchemy models: `User`, `EmailToken`, `RefreshToken`
- Write Alembic migration: `20240901_001_create_auth_tables`
- Add indexes: `ix_users_email`, `ix_email_tokens_token_hash`, `ix_refresh_tokens_user_id`
- Linked requirements: US-AUTH-01, US-AUTH-02

### TASK-AUTH-02: Password hashing & JWT utilities
- Implement `backend/app/core/security.py`: `hash_password`, `verify_password` (argon2id), `create_access_token`, `create_refresh_token`, `decode_token`
- Write unit tests: `test_security_utils.py`
- Linked requirements: US-AUTH-03

### TASK-AUTH-03: Register & email verification endpoints
- `POST /api/v1/auth/register` → create user, send verification email (Celery task)
- `POST /api/v1/auth/verify-email` → validate token, activate account
- Email template: `backend/app/workers/templates/verify_email.html` (en/te/hi)
- Tests: happy path, duplicate email, expired token
- Linked requirements: US-AUTH-01, US-AUTH-02

### TASK-AUTH-04: Login, logout, refresh endpoints
- `POST /api/v1/auth/login` → verify credentials, issue tokens, set httpOnly cookie
- `POST /api/v1/auth/refresh` → rotate refresh token
- `POST /api/v1/auth/logout` → revoke refresh token
- Rate limiting middleware (Redis)
- Account lockout logic (10 failures / 1 hour)
- Tests: happy path, wrong password, lockout, token reuse detection
- Linked requirements: US-AUTH-03, US-AUTH-06, US-AUTH-07

### TASK-AUTH-05: Password reset flow
- `POST /api/v1/auth/forgot-password` → send reset email
- `POST /api/v1/auth/reset-password` → validate token, update hash
- Tests: happy path, expired token, used token
- Linked requirements: US-AUTH-04

### TASK-AUTH-06: OTP login (optional)
- `POST /api/v1/auth/otp/enable` → generate TOTP secret, return QR URI
- `POST /api/v1/auth/otp/verify` → verify TOTP or SMS code
- Feature flag: `FEATURE_OTP_LOGIN`
- Tests: valid code, expired code, brute force block
- Linked requirements: US-AUTH-05

### TASK-AUTH-07: RBAC dependency & middleware
- `get_current_user` dependency: decode JWT, load user from DB
- `require_role([...])` dependency factory
- `get_workspace_member` dependency: validate workspace access
- Unit tests for all dependency error paths
- Linked requirements: US-WS-07, US-WS-08

### TASK-WS-01: Workspace & member database models
- SQLAlchemy models: `FamilyWorkspace`, `WorkspaceMember`, `WorkspaceInvitation`
- Alembic migration: `20240901_002_create_workspace_tables`
- Linked requirements: US-WS-01

### TASK-WS-02: Create workspace & invite endpoints
- `POST /api/v1/workspaces` → create workspace
- `POST /api/v1/workspaces/{id}/invitations` → send invitation email
- Invitation email template (en/te/hi)
- Tests: create, invite existing user, invite new email, re-invite
- Linked requirements: US-WS-01, US-WS-02

### TASK-WS-03: Accept invitation & consent flow
- `POST /api/v1/workspaces/accept-invitation` → accept invite, create account if needed
- `POST /api/v1/workspaces/{id}/consent` → record consent
- `GET /api/v1/workspaces/{id}/members` → list members
- Tests: accept valid, accept expired, accept already-member, consent required before data write
- Linked requirements: US-WS-03, US-WS-06

### TASK-WS-04: Remove member & counsellor access
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` → owner removes member
- Counsellor role read-only enforcement (tested in integration)
- Tests: owner removes, non-owner tries to remove (403), counsellor write attempt (403)
- Linked requirements: US-WS-05, US-WS-07

### TASK-PROF-01: User profile models & endpoints
- SQLAlchemy model: `UserProfile` with encrypted fields
- `PUT /api/v1/profile`, `GET /api/v1/profile`
- Field-level encryption for `rank`, `income_range`, `caste_category`
- Tests: create, update, encrypted fields round-trip
- Linked requirements: US-PROF-01, US-PROF-02, US-PROF-03

### TASK-AUDIT-01: Audit logging
- `audit_logs` model and Alembic migration
- `log_audit_event()` service function
- Hook audit logging into: login, logout, profile update, workspace join/leave, admin actions
- Tests: verify audit records created for key events
- Linked requirements: Security policy

### TASK-FE-AUTH-01: Frontend auth pages
- `/sign-in`, `/sign-up`, `/verify-email`, `/forgot-password`, `/reset-password` pages
- React Hook Form + Zod validation matching backend schemas
- JWT storage: access token in memory (Zustand), refresh token in httpOnly cookie
- Auto-refresh on 401 response (axios interceptor or React Query retry)
- i18n: all strings externalised in en/te/hi
- Linked requirements: US-AUTH-01 – US-AUTH-07

### TASK-FE-WS-01: Frontend workspace pages
- `/workspace/create` — create workspace form
- `/workspace/[id]` — dashboard showing members
- `/workspace/invite` — send invite form
- `/workspace/accept` — accept invitation page with consent screen
- Linked requirements: US-WS-01 – US-WS-06

### TASK-FE-PROF-01: Frontend profile pages
- Student profile form (exam, rank, category, gender, district)
- Parent profile form (budget, location, career priorities)
- Profile completion indicator
- Linked requirements: US-PROF-01 – US-PROF-04
