# ✅ Progress Endpoint Fixed: "no such column: id" Error

**Date**: November 23, 2025
**Issue**: GET `/api/stocks/all-stocks/progress` returning 500 error
**Root Cause**: Query selecting non-existent `id` column from `analysis_jobs` table
**Status**: FIXED ✅

---

## The Error

### HTTP Response
```
Status: 500 Internal Server Error
URL: https://thetool-production.up.railway.app/api/stocks/all-stocks/progress

{
    "error": {
        "code": "PROGRESS_ERROR",
        "message": "Failed to get progress",
        "details": {
            "error": "no such column: id"
        }
    }
}
```

---

## Root Cause Analysis

### Database Schema
The `analysis_jobs` table structure:
```sql
CREATE TABLE analysis_jobs (
    job_id TEXT PRIMARY KEY,        -- ✅ Primary key
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    errors TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
)
```

**Key Point**: There is NO `id` column. The primary key is `job_id`.

### Buggy Code (Before)
```python
cursor.execute("""
    SELECT id, job_id, status, total, completed, successful, errors
           ↑↑ NON-EXISTENT COLUMN ❌
    FROM analysis_jobs
    WHERE status IN ('queued', 'processing')
""")

# Then accessing:
row[0]  # id (doesn't exist)
row[1]  # job_id
row[2]  # status
row[3]  # total
row[4]  # completed
row[5]  # successful
row[6]  # errors
```

### Additional Bug: Wrong Progress Calculation
```python
progress_pct = int((row[4] / row[4]) * 100)
                   ↑ completed / completed = always 100%
```

Should be:
```python
progress_pct = int((row[3] / row[2]) * 100)
                   ↑ completed / total (correct)
```

---

## The Fix

### Corrected Query
```python
cursor.execute("""
    SELECT job_id, status, total, completed, successful, errors
           ↑↑ Correct columns ✓
    FROM analysis_jobs
    WHERE status IN ('queued', 'processing')
    ORDER BY created_at DESC
    LIMIT 20
""")

# Now accessing:
row[0]  # job_id ✓
row[1]  # status ✓
row[2]  # total ✓
row[3]  # completed ✓
row[4]  # successful ✓
row[5]  # errors ✓
```

### Fixed Response Object
```python
jobs.append({
    "job_id": row[0],              # ✅ Correct
    "status": row[1],
    "total": row[2],
    "completed": row[3],
    "successful": row[4],
    "errors_count": len(errors_list),
    "progress_percent": progress_pct
})
```

### Fixed Progress Calculation
```python
progress_pct = 0
if row[3] > 0 and row[2] > 0:
    progress_pct = int((row[3] / row[2]) * 100)  # ✅ completed/total
```

### Added Logging
```python
logger.info(f"[PROGRESS] Retrieved {len(jobs)} active jobs")
```

---

## Changes Made

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| SELECT clause | `id, job_id, status, ...` | `job_id, status, ...` | ✅ Fixed |
| Column references | row[0]=id, row[1]=job_id | row[0]=job_id, row[1]=status | ✅ Fixed |
| Progress calculation | completed/completed | completed/total | ✅ Fixed |
| Response field | "id": row[0] | Removed (not needed) | ✅ Fixed |
| Logging | None | Added [PROGRESS] logging | ✅ Enhanced |

---

## Expected Response After Fix

### Success Response
```json
{
  "jobs": [
    {
      "job_id": "a1b2c3d4-e5f6-7890-abcd",
      "status": "processing",
      "total": 100,
      "completed": 45,
      "successful": 43,
      "errors_count": 2,
      "progress_percent": 45
    },
    {
      "job_id": "x1y2z3a4-b5c6-7890-defg",
      "status": "queued",
      "total": 50,
      "completed": 0,
      "successful": 0,
      "errors_count": 0,
      "progress_percent": 0
    }
  ],
  "active_count": 2
}
```

### Error Cases Handled
- No active jobs: Returns `{"jobs": [], "active_count": 0}`
- Malformed errors JSON: Falls back to empty list
- Database error: Returns 500 with clear error message

---

## Testing

### Test Case 1: No Active Jobs
```
Expected: {jobs: [], active_count: 0}
Status: ✅ Works
```

### Test Case 2: Active Jobs
```
Expected: {jobs: [...], active_count: n}
Status: ✅ Works (after fix)
```

### Test Case 3: Progress Calculation
```
Before: 45/45 * 100 = 100%  ❌ Wrong
After:  45/100 * 100 = 45%  ✅ Correct
```

---

## Files Modified

- `backend/routes/stocks.py` - Fixed query and progress calculation

---

## Deployment

- ✅ Committed: Commit 4e9abff
- ✅ Pushed to main branch
- ✅ Railway auto-deploying

---

## Related Issues

This fix prevents similar errors. Lesson learned:
- **Always verify column names** against actual database schema
- **Check data type alignment** - ensure row index matches SELECT column order
- **Test mathematical operations** - progress should be completed/total, not completed/completed

---

**Status**: ✅ COMPLETE AND DEPLOYED
