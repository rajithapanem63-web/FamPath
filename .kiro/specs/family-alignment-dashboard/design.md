# Design: Family Alignment Dashboard

**Spec ID:** family-alignment-dashboard  
**Status:** Draft  
**Version:** 1.0

---

## Architecture

**Service Layer:** `AlignmentService` calculates alignment scores from preference data  
**No new tables:** Uses existing `preference_responses`  
**API:** 2 endpoints (GET dashboard, GET PDF export)

---

## Alignment Calculation Algorithm

```python
def calculate_dimension_alignment(responses_a, responses_b):
    # Weight alignment (50%)
    weight_diff = abs(responses_a.weight - responses_b.weight)
    weight_score = 100 - ((weight_diff / 6) * 100)
    
    # Option overlap (50%)
    options_a = set(responses_a.selected_options)
    options_b = set(responses_b.selected_options)
    overlap = len(options_a & options_b)
    total_unique = len(options_a | options_b)
    option_score = (overlap / total_unique * 100) if total_unique > 0 else 0
    
    return (weight_score + option_score) / 2

def calculate_overall_alignment(all_dimension_scores):
    return sum(all_dimension_scores) / len(all_dimension_scores)
```

---

## API Design

**GET /api/v1/alignment/dashboard?workspace_id={uuid}**
- Returns: AlignmentDashboard JSON (see requirements.md)
- Requires: Auth, workspace membership
- Caching: 5 minutes

**GET /api/v1/alignment/export?workspace_id={uuid}&format=pdf**
- Returns: PDF file
- Uses: WeasyPrint or ReportLab
- Max size: 5 pages

---

## Frontend Components

- `AlignmentOverview.tsx` - Overall score card
- `DimensionComparison.tsx` - Diverging bar chart per dimension
- `ConflictPanel.tsx` - Top 3 conflicts
- `AgreementPanel.tsx` - High-alignment areas
- `AlignmentChart.tsx` - Recharts wrapper

---

## Testing Strategy

**Unit Tests:**
- `test_calculate_weight_alignment()`
- `test_calculate_option_overlap()`
- `test_overall_alignment_average()`

**Integration Tests:**
- `test_dashboard_endpoint_returns_valid_json()`
- `test_pdf_export_generates_file()`

**E2E Tests:**
- Student and parent complete preferences → Dashboard shows alignment

---

**Status:** Ready for tasks.md
