# FamPath – Security Policy & Standards

## Threat Model Summary

FamPath handles sensitive personal data for minors and families (rank/marks, income, caste category, career aspirations). The threat model prioritises:

1. **Data breach** – unauthorised access to family profile data
2. **Privilege escalation** – student accessing another family's data, or gaining counsellor/admin privileges
3. **LLM abuse** – prompt injection, jailbreaks, extraction of other users' data via the chatbot
4. **Account takeover** – credential stuffing, brute force, token theft
5. **Data integrity** – tampering with cutoff/fee data that affects real decisions

---

## Authentication & Session Management

- Passwords hashed with **argon2id** (via Passlib); minimum work factor per OWASP recommendations.
- JWT access tokens: 15-minute expiry, signed with RS256.
- Refresh tokens: 7-day expiry, stored in `httpOnly; Secure; SameSite=Strict` cookie, rotated on every use.
- Refresh token family invalidation on detected reuse (theft detection).
- Email verification is **mandatory** before any profile data can be written.
- Password-reset tokens: HMAC-signed, single-use, 24-hour expiry.
- OTP login (optional): 6-digit TOTP or SMS code, 5-minute window, max 5 attempts then locked for 30 minutes.
- Rate limiting on `/api/v1/auth/*`: **10 requests / 15 min per IP** (Redis sliding window).
- Account lockout after 10 failed logins within 1 hour; unlock via email.

---

## Authorisation (RBAC)

| Role | Permissions |
|------|------------|
| `student` | Own profile, own workspace, invite family members, view shared shortlist |
| `parent` | Own profile, joined workspace (read/write shared data), view recommendations |
| `counsellor` | Read-only view of assigned client workspaces; write notes |
| `admin` | Full data management; cannot access individual user profiles except for support tickets |

- Every FastAPI endpoint uses `Depends(require_role([...]))` — no permission checks inside service layers.
- Workspace-level access control: every data query filters by `workspace_id` owned by or shared with the authenticated user.
- Horizontal privilege escalation checks: verified in integration tests for every endpoint.

---

## Input Validation & Output Encoding

- All inputs validated via **Pydantic v2** models before reaching any service or DB layer.
- String fields: max length enforced, HTML stripped with `bleach` (allowlist approach).
- SQL: **no raw SQL strings** — all queries via SQLAlchemy ORM or parameterised text().
- File uploads (CSV import): validated for MIME type, max size (10 MB), parsed in a sandboxed subprocess.
- API responses: FastAPI auto-serialises via Pydantic; no `jsonify(user_dict)` patterns.
- Frontend: all dynamic content rendered via React (auto-escaped); `dangerouslySetInnerHTML` is banned via ESLint rule.

---

## LLM / RAG Safeguards

- **Prompt injection defence**: user-provided text is inserted into a clearly delimited section of the prompt (`<user_input>…</user_input>`); system instructions are in a separate, non-overridable system turn.
- **PII minimisation**: rank, income, caste fields are replaced with anonymised tokens before being sent to the LLM API unless the user explicitly enables "personalised answers" in settings.
- **Consent gate**: a consent checkbox is shown before the first RAG chatbot use, explaining what data is sent externally.
- **Response validation**: every LLM response is parsed for `citations` field; responses without citations raise `CitationMissingError` and are not shown to users.
- **Refusal enforcement**: system prompt instructs the model to respond with a structured `{"refusal": true, "reason": "…"}` JSON when the question is outside its knowledge base.
- **Output length cap**: responses truncated at 1 500 tokens to prevent runaway generation.
- **No sensitive data in logs**: LLM request/response payloads are logged only in DEBUG mode, with PII redacted.

---

## Data Protection

### Sensitive Fields (encrypted at application layer, AES-256-GCM)

- `user_profiles.income_range`
- `user_profiles.caste_category`
- `exam_results.rank`, `exam_results.marks`

Encryption key managed via environment variable `FAMPATH_ENCRYPTION_KEY`; key rotation procedure documented in runbook.

### Data Residency

- All data stored in the configured PostgreSQL instance; no third-party analytics SDKs that exfiltrate raw user data.
- LLM API calls use anonymised tokens; full PII never leaves the platform unless user consents.

### Consent & Privacy

- Consent is collected at account creation and before each sensitive feature (RAG chatbot, sharing with counsellor).
- Users can: download their data (`GET /api/v1/me/export`), delete their account and all associated data (`DELETE /api/v1/me`).
- Soft-delete holds data for 30 days (DPDP Act grace period), then permanent deletion via scheduled Celery task.
- Privacy Policy and Terms of Service pages are required before MVP launch; plain-language summaries in all three languages.

---

## Transport & Infrastructure Security

- **TLS 1.2+ enforced** on all endpoints; HTTP redirects to HTTPS.
- **Secure headers** (via middleware):
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy` (strict; no `unsafe-inline` in production)
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=()`
- **CORS**: allowlist of known origins only; credentials mode requires exact origin match.
- **CSRF**: SameSite cookies + custom `X-Requested-With` header check on state-mutating routes.
- Secrets: never in code or `.env` files committed to git; `.env` in `.gitignore`; CI uses GitHub Actions secrets.
- Docker images: non-root user, read-only filesystem where possible, no debug tools in production image.

---

## Dependency Security

- `pip-audit` and `npm audit --audit-level=critical` run in every CI build; critical CVEs block merge.
- All dependencies pinned to exact versions.
- `Dependabot` or equivalent configured for automated PRs on security updates.
- No packages with < 1 000 weekly downloads or abandoned (last commit > 2 years) without documented exception.

---

## Audit Logging

Audit events written to `audit_logs` table and optionally streamed to log aggregator:

| Event | Fields logged |
|-------|--------------|
| Login / logout | `user_id`, `ip`, `user_agent`, `timestamp`, `success` |
| Failed login | same + `reason` |
| Profile update | `user_id`, `fields_changed` (no values), `timestamp` |
| Sensitive data access | `user_id`, `resource_type`, `resource_id`, `timestamp` |
| Admin data import | `admin_id`, `file_hash`, `record_count`, `timestamp` |
| Account deletion | `user_id`, `timestamp`, `initiated_by` |
| Counsellor workspace access | `counsellor_id`, `workspace_id`, `timestamp` |

Audit logs are **append-only**; no UPDATE or DELETE on `audit_logs`.

---

## Security Testing Requirements

- OWASP ZAP scan (baseline) in CI on every staging deploy.
- Manual penetration test checklist covering OWASP Top 10 before production launch.
- All auth-related endpoints have specific negative-path tests (wrong role, expired token, missing token).
- Fuzzing on CSV import endpoint with malformed files.
- `SECURITY.md` at repo root documents responsible disclosure process.

---

## Incident Response

- Runbook at `docs/runbooks/incident.md` covers: detection, containment, eradication, recovery, post-mortem.
- On suspected breach: rotate secrets, invalidate all refresh tokens (global `jti` blocklist), notify affected users.
- SLA for critical security issues: acknowledged within 24 h, patched within 72 h.
