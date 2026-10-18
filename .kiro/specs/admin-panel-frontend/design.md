# Design: Admin Panel Frontend

## Route Structure

```
/admin (protected by admin role)
├── /dashboard - Analytics, data freshness
├── /colleges - College CRUD + CSV import
├── /cutoffs - Cutoff record management
├── /fees - Fee structure management
├── /scholarships - Scholarship CRUD
├── /questions - Quiz question bank
└── /import - Generic CSV import interface
```

## Components

- `AdminLayout.tsx` - Sidebar navigation
- `DataTable.tsx` - Reusable data table with filters, sort, pagination
- `CSVUploader.tsx` - Drag-and-drop CSV upload
- `DataFreshnessIndicator.tsx` - Shows last update date

## Security

- Admin-only routes (middleware check)
- All mutations require confirmation
- Audit logging on all changes

---

**Status:** Ready for tasks.md
