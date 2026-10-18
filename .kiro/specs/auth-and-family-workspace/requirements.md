# Spec: Auth & Family Workspace — Requirements

## Overview
Secure, role-based authentication and a shared family workspace so students, parents, and counsellors can collaborate on a single decision record.

## User Stories

### Authentication
- US-AUTH-01: As a new user, I can register with email and password so that I have an account.
- US-AUTH-02: As a registered user, I must verify my email before accessing any data.
- US-AUTH-03: As a user, I can sign in with email and password to access my account.
- US-AUTH-04: As a user, I can reset my password via a time-limited email link.
- US-AUTH-05: As a user, I can opt in to OTP-based login as an alternative to password.
- US-AUTH-06: As a user, I can sign out and my session tokens are invalidated.
- US-AUTH-07: As a user, my session automatically refreshes so I am not logged out unexpectedly.

### Family Workspace
- US-WS-01: As a student, I can create a Family Workspace after verifying my email.
- US-WS-02: As a student, I can invite family members (parents/guardians) by email.
- US-WS-03: As an invitee, I receive an email invitation and can accept it to join the workspace.
- US-WS-04: As a workspace member, I can see all other members and their roles.
- US-WS-05: As a student (workspace owner), I can remove a member from the workspace.
- US-WS-06: As any member, I must consent to data sharing before contributing to the workspace.
- US-WS-07: As a counsellor, I can be added to a workspace by the student with read-only access.
- US-WS-08: As an admin, I can view all workspaces for support purposes.

### Profiles
- US-PROF-01: As a student, I can fill in my academic profile (exam, rank, category, gender, region).
- US-PROF-02: As a parent, I can fill in my expectations profile (budget, location preference, career priorities).
- US-PROF-03: As any user, I can update my profile at any time.
- US-PROF-04: As any user, I can view a consent summary and withdraw consent, which disables shared data.

## Acceptance Criteria (EARS Format)

### Registration & Verification
- WHEN a user submits a valid email and password (≥ 8 chars, 1 uppercase, 1 number), THEN an account is created with status `pending_verification` and a verification email is sent within 10 seconds.
- WHEN a user submits an already-registered email, THEN the system returns HTTP 409 with error code `EMAIL_ALREADY_REGISTERED`.
- WHEN a user clicks the verification link within 24 hours, THEN their account status changes to `active` and they are redirected to onboarding.
- WHERE a verification link has expired (> 24 hours), the system returns error code `VERIFICATION_LINK_EXPIRED` and offers to resend.
- WHILE a user's email is unverified, the system MUST reject all data-write requests with HTTP 403 and error code `EMAIL_NOT_VERIFIED`.

### Login & Session
- WHEN a user provides correct credentials, THEN an access token (15 min) and refresh token (7 days) are returned; the refresh token is set in an `httpOnly; Secure; SameSite=Strict` cookie.
- WHEN a user provides incorrect credentials 10 times within 1 hour, THEN the account is locked and an unlock email is sent.
- WHEN the access token expires, the frontend SHOULD automatically call `/auth/refresh`; IF the refresh token is valid, a new pair is issued.
- WHEN a refresh token is used more than once, THEN the entire token family is invalidated (theft detection).

### Family Workspace
- WHEN a verified student creates a workspace, THEN a workspace record is created with the student as `owner` and status `active`.
- WHEN the owner sends an invitation to a valid email, THEN an invitation record is created and an email is sent within 10 seconds.
- WHEN an invitee accepts within 7 days, THEN they are added as a `parent` member and can access shared workspace data.
- WHERE an invitation has expired (> 7 days), the system returns error code `INVITATION_EXPIRED`.
- WHEN a member joins, THEN they MUST see and accept the consent screen before any of their profile data is stored.
- WHEN the owner removes a member, THEN the member loses workspace access immediately and their contributed data is retained (audit trail).

### RBAC
- WHERE a `student` attempts to access another student's workspace, the system MUST return HTTP 403.
- WHERE a `parent` attempts to access admin endpoints, the system MUST return HTTP 403.
- WHERE a `counsellor` attempts to write workspace data (non-note), the system MUST return HTTP 403.
