# SQL Placeholder Fix - November 28, 2025

## Issue
The bulk analysis job was failing with:
```
sqlite3.OperationalError: near "%": syntax error
```

## Root Cause
In `backend/infrastructure/thread_tasks.py`, two UPDATE queries were using PostgreSQL-style placeholders (`%s`) instead of SQLite-style (`?`):

1. **Line 281-286**: Final job completion status update
   ```python
   # BEFORE (WRONG):
   SET status = %s, completed_at = %s, errors = %s
   WHERE job_id = %s
   
   # AFTER (CORRECT):
   SET status = ?, completed_at = ?, errors = ?
   WHERE job_id = ?
   ```

2. **Line 308-313**: Error handling - job failed status update
   ```python
   # BEFORE (WRONG):
   SET status = 'failed', completed_at = %s, errors = %s
   WHERE job_id = %s
   
   # AFTER (CORRECT):
   SET status = ?, completed_at = ?, errors = ?
   WHERE job_id = ?
   ```

## Why This Matters
The `_convert_query_params()` function is designed to:
1. Accept queries with SQLite placeholders (`?`)
2. Convert them to PostgreSQL placeholders (`%s`) if needed
3. Leave them as-is for SQLite

When raw `%s` placeholders are used, SQLite doesn't know how to interpret them and throws a syntax error.

## Fix Applied
Updated both UPDATE queries to use `?` placeholders and rely on `_convert_query_params()` for automatic conversion:

```python
# Consistent pattern used throughout thread_tasks.py:
from database import _convert_query_params, DATABASE_TYPE

query = '''
    UPDATE analysis_jobs 
    SET status = ?, completed_at = ?, errors = ?
    WHERE job_id = ?
'''
query, params = _convert_query_params(query, (value1, value2, value3, job_id), DATABASE_TYPE)
cursor.execute(query, params)
```

## Files Modified
- `backend/infrastructure/thread_tasks.py` - Lines 281-286 and 308-313

## Impact
- ✅ Bulk analysis jobs can now complete without SQL errors
- ✅ Consistent placeholder style across entire codebase
- ✅ Works correctly with both SQLite (dev) and PostgreSQL (production)

## Testing
The fix allows the bulk analysis workflow to proceed through all steps:
1. Job creation ✅
2. Data fetching ✅
3. Analysis processing ✅
4. Results insertion ✅
5. Progress updates ✅
6. **Final job status update** ✅ (now fixed)
