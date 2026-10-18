# Spec: Auth & Family Workspace — Design

## Architecture Overview

```
┌─────────────────────────────────────┐
│           Next.js Frontend          │
│  /sign-in  /sign-up  /workspace     │
└────────────────┬────────────────────┘
                 │ HTTPS + JWT
┌────────────────▼────────────────────┐
│         FastAPI Backend             │
│  /api/v1/auth/*   /api/v1/workspaces│
│  AuthRouter       WorkspaceRouter   │
└──────┬──────────────────┬───────────┘
       │                  │
┌──────▼──────┐    ┌──────▼──────┐
│  PostgreSQL │    │    Redis     │
│  users      │    │  rate limits │
│  workspaces │    │  token cache │
│  invitations│    │  OTP codes   │
└─────────────┘    └─────────────┘
```

## Data Models

### `users` table
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
email           VARCHAR(255) UNIQUE NOT NULL
password_hash   TEXT NOT NULL  -- argon2id
role            VARCHAR(20) NOT NULL  -- student | parent | counsellor | admin
status          VARCHAR(30) NOT NULL DEFAULT 'pending_verification'
                -- pending_verification | active | locked | deleted
full_name       VARCHAR(255)
preferred_locale VARCHAR(5) DEFAULT 'en'
otp_enabled     BOOLEAN DEFAULT false
failed_login_count INT DEFAULT 0
locked_until    TIMESTAMPTZ
last_login_at   TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
deleted_at      TIMESTAMPTZ  -- soft delete
```

### `email_tokens` table
```sql
id          UUID PRIMARY KEY
user_id     UUID REFERENCES users(id)
token_hash  TEXT NOT NULL  -- SHA-256 of the raw token
purpose     VARCHAR(30) NOT NULL  -- email_verification | password_reset | workspace_invite
expires_at  TIMESTAMPTZ NOT NULL
used_at     TIMESTAMPTZ
created_at  TIMESTAMPTZ DEFAULT now()
```

### `refresh_tokens` table
```sql
id          UUID PRIMARY KEY
user_id     UUID REFERENCES users(id)
family_id   UUID NOT NULL  -- token rotation family; invalidate all on reuse
token_hash  TEXT NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
revoked_at  TIMESTAMPTZ
created_at  TIMESTAMPTZ DEFAULT now()
```

### `family_workspaces` table
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
name        VARCHAR(255) NOT NULL
owner_id    UUID REFERENCES users(id)
status      VARCHAR(20) DEFAULT 'active'
created_at  TIMESTAMPTZ DEFAULT now()
updated_at  TIMESTAMPTZ DEFAULT now()
deleted_at  TIMESTAMPTZ
```

### `workspace_members` table
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
workspace_id    UUID REFERENCES family_workspaces(id)
user_id         UUID REFERENCES users(id)
role            VARCHAR(20) NOT NULL  -- student | parent | counsellor
consent_given   BOOLEAN DEFAULT false
consent_given_at TIMESTAMPTZ
joined_at       TIMESTAMPTZ
removed_at      TIMESTAMPTZ
UNIQUE(workspace_id, user_id)
```

### `workspace_invitations` table
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
workspace_id    UUID REFERENCES family_workspaces(id)
invited_by      UUID REFERENCES users(id)
invited_email   VARCHAR(255) NOT NULL
invited_role    VARCHAR(20) DEFAULT 'parent'
token_hash      TEXT NOT NULL
status          VARCHAR(20) DEFAULT 'pending'  -- pending | accepted | expired | revoked
expires_at      TIMESTAMPTZ NOT NULL
accepted_at     TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT now()
```

### `user_profiles` table
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID UNIQUE REFERENCES users(id)
workspace_id    UUID REFERENCES family_workspaces(id)
profile_type    VARCHAR(20)  -- student | parent
-- Student fields (encrypted where noted)
exam_type       VARCHAR(20)  -- AP_EAPCET | TS_EAPCET | JEE_MAINS | JEE_ADV
rank_encrypted  TEXT  -- AES-256-GCM encrypted
category        VARCHAR(20)  -- OC | BC_A | BC_B | BC_C | BC_D | BC_E | SC | ST | EWS
gender          VARCHAR(10)
home_district   VARCHAR(100)
home_state      VARCHAR(100)
-- Parent fields
budget_min      INTEGER  -- INR per year
budget_max      INTEGER
location_pref   JSONB  -- {"districts": [...], "flexible": true}
career_priorities JSONB  -- {"stability": 4, "salary": 5, "abroad": 2}
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

### `audit_logs` table
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID REFERENCES users(id)
action      VARCHAR(100) NOT NULL
resource_type VARCHAR(50)
resource_id UUID
ip_address  INET
user_agent  TEXT
metadata    JSONB  -- non-PII context
created_at  TIMESTAMPTZ DEFAULT now()
```

## API Contracts

### Auth Endpoints

```
POST /api/v1/auth/register
  Body: { email, password, full_name, role, preferred_locale }
  200: { message: "Verification email sent" }
  409: { error_code: "EMAIL_ALREADY_REGISTERED" }

POST /api/v1/auth/verify-email
  Body: { token }
  200: { message: "Email verified" }
  400: { error_code: "VERIFICATION_LINK_EXPIRED" | "INVALID_TOKEN" }

POST /api/v1/auth/login
  Body: { email, password }
  200: { access_token, token_type: "bearer", user: UserResponse }
  Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict
  401: { error_code: "INVALID_CREDENTIALS" }
  423: { error_code: "ACCOUNT_LOCKED", unlock_at }

POST /api/v1/auth/refresh
  Cookie: refresh_token
  200: { access_token }
  401: { error_code: "INVALID_REFRESH_TOKEN" }

POST /api/v1/auth/logout
  Cookie: refresh_token
  200: { message: "Logged out" }

POST /api/v1/auth/forgot-password
  Body: { email }
  200: { message: "Reset email sent if account exists" }  -- always 200 (no enum)

POST /api/v1/auth/reset-password
  Body: { token, new_password }
  200: { message: "Password reset" }
  400: { error_code: "INVALID_RESET_TOKEN" }

GET /api/v1/auth/me
  Auth: Bearer
  200: UserResponse
```

### Workspace Endpoints

```
POST /api/v1/workspaces
  Auth: Bearer (student)
  Body: { name }
  201: WorkspaceResponse

GET /api/v1/workspaces/{workspace_id}
  Auth: Bearer (member)
  200: WorkspaceDetailResponse

POST /api/v1/workspaces/{workspace_id}/invitations
  Auth: Bearer (owner)
  Body: { email, role }
  201: { invitation_id, expires_at }

POST /api/v1/workspaces/accept-invitation
  Body: { token }
  Auth: Bearer (or creates account)
  200: WorkspaceResponse

DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}
  Auth: Bearer (owner)
  200: { message: "Member removed" }

GET /api/v1/workspaces/{workspace_id}/members
  Auth: Bearer (member)
  200: [WorkspaceMemberResponse]

POST /api/v1/workspaces/{workspace_id}/consent
  Auth: Bearer (member)
  Body: { consented: true }
  200: { consent_given_at }
```

### Profile Endpoints

```
PUT /api/v1/profile
  Auth: Bearer
  Body: StudentProfileRequest | ParentProfileRequest
  200: ProfileResponse

GET /api/v1/profile
  Auth: Bearer
  200: ProfileResponse
```

## Security Design

- All `/api/v1/auth/*` endpoints rate-limited: 10 req/15 min per IP via Redis.
- `rank` and sensitive profile fields encrypted with AES-256-GCM before storage; decrypted only for the authenticated owner.
- Passwords never logged; token hashes (SHA-256) stored, not raw tokens.
- `require_role` dependency injected in every protected endpoint.
- Workspace access guard: `get_workspace_or_403` validates `workspace_id` against authenticated user's memberships.

## Sequence: Login + Token Refresh

```
Client          FastAPI         PostgreSQL      Redis
  |                |                |              |
  |--POST /login-->|                |              |
  |                |--SELECT user-->|              |
  |                |<--user row-----|              |
  |                |--verify argon2 hash           |
  |                |--check rate limit------------>|
  |                |<--allowed--------------------|
  |                |--INSERT refresh_token-------->|
  |<--access_token-|                               |
  |  Set-Cookie    |                               |
  ...
  |--POST /refresh (cookie)-->|                    |
  |                |--SELECT refresh_token-------->|  (Redis cache check first)
  |                |--rotate token: INSERT new, revoke old
  |<--new access_token--------|                    |
```

## Error Handling

All errors follow:
```json
{ "error_code": "SNAKE_CASE_CODE", "message": "Human-readable (English)", "details": {} }
```
Frontend translates `error_code` to the user's locale.

## Test Strategy

- Unit: `test_auth_service.py` — token generation, hash verification, lockout logic.
- Integration: `test_auth_endpoints.py` — full HTTP cycle with test DB.
- Integration: `test_workspace_endpoints.py` — invite → accept → consent → remove flow.
- E2E (Playwright): `signup.spec.ts`, `family-invite.spec.ts`.
- Negative paths: expired token, wrong role, duplicate email, reused refresh token.
