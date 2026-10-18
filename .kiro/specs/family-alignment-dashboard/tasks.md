# Tasks: Family Alignment Dashboard

**Estimated:** 6-7 days

---

## Backend Tasks (3-4 days)

### TASK-FAD-BE-001: Create AlignmentService
- Implement alignment calculation algorithms
- Weight alignment, option overlap, overall score
- Tests: Unit tests for all calculations

### TASK-FAD-BE-002: Create Alignment Router
- GET /api/v1/alignment/dashboard
- GET /api/v1/alignment/export (PDF)
- Auth + workspace membership checks

### TASK-FAD-BE-003: PDF Export Service
- Generate PDF with alignment data
- Use WeasyPrint or ReportLab
- Include charts as images

### TASK-FAD-BE-004: Register Router
- Add to main.py
- Verify in /docs

---

## Frontend Tasks (3 days)

### TASK-FAD-FE-001: Create Alignment Page
- `/[locale]/(workspace)/alignment/page.tsx`
- Layout with 4 panels

### TASK-FAD-FE-002: AlignmentOverview Component
- Overall score display
- Progress bar
- Member status

### TASK-FAD-FE-003: DimensionComparison Component
- Diverging bar chart
- Member weights and options
- Recharts integration

### TASK-FAD-FE-004: ConflictPanel Component
- Top 3 conflicts
- Link to mediator (placeholder)

### TASK-FAD-FE-005: AgreementPanel Component
- High-alignment dimensions
- Success messaging

### TASK-FAD-FE-006: PDF Export Button
- Download trigger
- Loading state

---

**Total:** 10 tasks, 6-7 days
