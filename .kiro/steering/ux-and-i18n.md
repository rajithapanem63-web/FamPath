# FamPath – UX Principles, Accessibility & Internationalisation

## UX Design Principles

### 1. Family-First, Not Student-First

Every screen asks: *"Does this work for a parent who has never used a college portal before?"* Interfaces must be approachable, jargon-light, and usable without prior knowledge of the counselling process.

### 2. Trust Through Transparency

- Every prediction, score, or recommendation shows **why** — at minimum: data source, data year, key factors.
- Data estimates always carry: *"This is an estimate based on historical data, not a guarantee."*
- Chatbot responses always show the source document they drew from.
- Confidence levels are shown visually (traffic-light or probability bars), not hidden.

### 3. Progressive Disclosure

- Show the most important information first; details are one tap/click away.
- Long questionnaires are broken into short steps with a progress indicator.
- Advanced options (custom weights, detailed ML breakdown) are accessible but not forced.

### 4. Mobile-First, Low-Bandwidth Friendly

- All layouts designed at 375 px first; desktop is an enhancement.
- Critical flows (questionnaire, prediction lookup) must work on a 2G connection.
- Images are lazy-loaded; charts degrade gracefully to text tables on slow connections.
- PWA: the app is installable, key pages are cached for offline viewing.

### 5. Emotional Safety

- The platform deals with high-stakes decisions; language must be calm, encouraging, and non-judgmental.
- Conflict Mediator AI uses neutral language — never takes sides or assigns blame.
- Avoid red/danger colours for prediction results; use descriptive labels (Safe / Target / Dream), not failure framing.

---

## Component & Interaction Standards

### Forms

- All form fields have visible labels (no placeholder-only labelling).
- Inline validation messages appear after blur, not on every keystroke.
- Error messages are specific: *"Rank must be a number between 1 and 200 000"* not *"Invalid input"*.
- Multi-step forms show step count and allow back navigation without losing data.
- Submit buttons are disabled during loading; show spinner + "Submitting…" state.

### Data Visualisation

- Every chart has a plain-text alternative (table or summary sentence) for screen readers.
- Colour is never the only differentiator; patterns or labels are added.
- Family Alignment Dashboard uses diverging bar charts with clear family-member labels, not just colours.
- Cost calculator shows both a chart and a numeric breakdown table.

### Navigation

- Breadcrumb on all pages deeper than two levels.
- Active state clearly visible in sidebar/tab navigation.
- Skip-to-main-content link as first focusable element on every page.

### Notifications

- In-app toasts for transient actions (saved, copied); banners for persistent states (email not verified).
- Deadline reminders shown in the timeline view and as dismissible in-app banners, not just email.

---

## Accessibility Standards

**Target:** WCAG 2.1 Level AA

### Mandatory Checks (automated via axe in every component test)

| Rule | Requirement |
|------|------------|
| Colour contrast | ≥ 4.5:1 for normal text, ≥ 3:1 for large text |
| Focus management | Visible focus ring on all interactive elements; no `outline: none` without alternative |
| Keyboard navigation | All interactions reachable and operable via keyboard |
| Screen reader compatibility | All images have `alt`; icons have `aria-label`; form fields have associated labels |
| ARIA | Use native HTML semantics first; ARIA only when HTML is insufficient |
| Heading hierarchy | Logical heading order (`h1` → `h2` → `h3`); one `h1` per page |
| Skip links | Skip-to-main-content on every page |
| Error announcements | Form errors announced via `aria-live="polite"` |
| Video / audio | Captions and transcripts for any media (N/A for MVP, noted for Phase 2) |

### shadcn/ui Accessibility Notes

- shadcn components use Radix UI primitives which are keyboard and screen-reader accessible by default.
- Custom overrides must not remove `aria-*` attributes from Radix components.
- Always pass a visible label or `aria-label` when using icon-only buttons from shadcn.

### Lighthouse Targets (measured on key pages before each release)

| Category | Target |
|---------|--------|
| Performance | ≥ 90 |
| Accessibility | ≥ 90 |
| Best Practices | ≥ 90 |
| SEO | ≥ 80 |

---

## Internationalisation (i18n)

### Supported Locales

| Code | Language | Notes |
|------|---------|-------|
| `en` | English | Default / fallback |
| `te` | Telugu | Primary regional language |
| `hi` | Hindi | Secondary; common among migrant families |

### Implementation (next-intl)

- Locale is in the URL: `/{locale}/...` (e.g., `/te/workspace/dashboard`).
- Locale is persisted in a cookie (`FAMPATH_LOCALE`) and respected on return visits.
- Language switcher is visible on every page (top-right or in user menu).
- Server Components use `getTranslations()`; Client Components use `useTranslations()`.

### Message File Structure (`frontend/src/i18n/messages/`)

```json
// en.json (example structure)
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "loading": "Loading…"
  },
  "auth": {
    "signIn": { "title": "Sign in to FamPath", "emailLabel": "Email address" }
  },
  "prediction": {
    "resultCard": {
      "safeLabel": "Safe",
      "targetLabel": "Target",
      "dreamLabel": "Dream",
      "disclaimer": "This is an estimate based on historical data, not a guarantee."
    }
  }
}
```

### i18n Rules

1. **No hard-coded strings** in any component; every visible string comes from the message file.
2. All three locale files must have identical key sets — enforced by CI hook (`scripts/check_i18n_keys.py`).
3. Missing translations fall back to English; missing English key is a **build error**.
4. Use ICU message format for plurals and variables: `"You have {count, plural, one {# college} other {# colleges}} shortlisted."`.
5. Dates and numbers use `Intl.DateTimeFormat` / `Intl.NumberFormat` with the active locale — never manual formatting.
6. Currency: Indian Rupee (`INR`); formatted as `₹1,23,456` (Indian numbering system via `Intl.NumberFormat('en-IN', {style:'currency', currency:'INR'})`).
7. Right-to-left (RTL) is not required for MVP (none of the three languages are RTL).

### Content Translation Workflow

- English is the source of truth; Telugu and Hindi translations are maintained by human translators.
- Translation keys added by developers first in English; placeholder `[TODO: translate]` in other locales triggers a CI warning (not error) until translated.
- Sensitive strings (legal text, disclaimers) must be reviewed by a domain expert before shipping.

### Backend i18n

- API error messages use error codes (e.g., `"error_code": "RANK_OUT_OF_RANGE"`); the frontend translates them.
- Email templates are rendered per-locale using Jinja2 with locale-specific template files.
- PDF reports are generated in the user's preferred locale.

---

## Onboarding & Empty States

- Every empty state (no shortlist, no questionnaire filled) shows a clear call-to-action and a brief explanation of what the section does.
- First-time users see a 3-step onboarding modal: *What is FamPath → How family workspace works → Start now*.
- Tooltips and info icons explain jargon (EAPCET, cutoff, RIASEC) inline without requiring navigation away.

---

## Responsive Breakpoints (Tailwind)

| Breakpoint | Width | Target Device |
|-----------|-------|--------------|
| `sm` | 640 px | Large phone / small tablet |
| `md` | 768 px | Tablet |
| `lg` | 1024 px | Laptop |
| `xl` | 1280 px | Desktop |

- Default (no prefix): mobile (< 640 px).
- Layouts are single-column on mobile; two-column on `md`; three-column max on `lg`.
- Touch targets are minimum 44 × 44 px.
- No horizontal scroll on any mobile viewport.
