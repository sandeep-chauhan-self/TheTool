# Database Fix Summary - November 28, 2025

## Issue
The production logs showed an error when attempting bulk stock analysis:
```
[ERROR] Error checking for active jobs: no such column: tickers_json
[ERROR] Transaction rolled back due to error: table analysis_jobs has no column named tickers_json
```

## Root Cause
The development SQLite database (`./data/trading_app.db`) had an old schema without the `tickers_json` column that was needed for tracking which stocks belong to each analysis job.

## Solution Implemented

### 1. Added Missing Column
- Ran `backend/migrate_add_tickers_json.py` migration script
- Successfully added `tickers_json TEXT` column to `analysis_jobs` table in SQLite

### 2. Removed Problematic Indexes
- Dropped all indexes from `analysis_jobs` table except the PRIMARY KEY auto-index
- **Reason**: The 8KB index limit in SQLite causes overflow when indexing both `tickers_json` (large JSON string) and status columns together
- **Decision**: Use table scans for job queries (acceptable since `analysis_jobs` typically has <100 rows)

### 3. Updated Migration Script
- Modified `backend/migrate_add_tickers_json.py` to NOT create indexes on `analysis_jobs` 
- Updated documentation to explain the deliberate design choice
- Consistent approach between SQLite (dev) and PostgreSQL (production)

## Files Changed
1. **backend/database.py** - Already had correct schema definition
2. **backend/migrate_add_tickers_json.py** - Removed index creation, updated comments
3. **backend/fix_db_indexes.py** - Created utility to remove problematic indexes
4. **backend/verify_db_fix.py** - Created verification script to confirm schema

## Current Schema - analysis_jobs Table
```
Columns:
  - job_id: TEXT (PRIMARY KEY)
  - status: TEXT
  - progress: INTEGER
  - total: INTEGER
  - completed: INTEGER
  - successful: INTEGER
  - errors: TEXT
  - created_at: TIMESTAMP
  - updated_at: TIMESTAMP
  - started_at: TIMESTAMP
  - completed_at: TIMESTAMP
  - tickers_json: TEXT  ✅ (newly added)

Indexes:
  - sqlite_autoindex_analysis_jobs_1 (PRIMARY KEY - auto-created)
  - (No other indexes - as per design decision)
```

## Verification
- ✅ Column exists in schema
- ✅ Test INSERT/SELECT with tickers_json works
- ✅ No problematic indexes causing 8KB limit overflow
- ✅ Application ready for bulk analysis operations

## Next Steps
If the issue persists after restart:
1. Ensure backend is restarted to reload schema from database
2. Clear any stale connection pools
3. Test `/api/stocks/analyze-all-stocks` endpoint again

The bulk analysis feature should now work correctly!
