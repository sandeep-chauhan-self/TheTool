# JOB_DUPLICATE Issue - Root Cause & Fix

## Problem Summary
User was getting 500 "JOB_CREATION_FAILED" errors when submitting analysis jobs.

Error logs showed:
```
[ERROR] column "tickers_json" does not exist in relation "analysis_jobs"
```

## Root Cause Analysis

### What Happened:
1. Migration `migration_v3` was deployed and ran on production database → Set version to 3
2. Later, I added `tickers_json` column code to `migration_v3` function
3. BUT: The production database was ALREADY at version 3
4. When migration runs, it only executes migrations where `current_version < X`
5. Since current_version was already 3, `migration_v3` was skipped
6. The `tickers_json` column was never created on the production database!

### Why This Happened:
- Incorrect migration strategy: Added code to existing migration_v3 after it was already deployed
- The versioning system prevents re-running migrations
- Production database got stuck in intermediate state

## Solution Implemented

### File: `backend/db_migrations.py`

Added a **standalone emergency check** in `run_migrations()` that:

```python
# CRITICAL: Ensure tickers_json column exists (added after v3 was already deployed)
# This runs REGARDLESS of version to fix existing databases
```

The fix:
1. **Runs on EVERY startup** (not dependent on version checks)
2. **Checks if tickers_json column exists** in analysis_jobs table
3. **Creates it if missing** (both PostgreSQL and SQLite)
4. **Creates the index** on (tickers_json, status)
5. **Handles both database types** with appropriate queries

### Key Code:
```python
if config.DATABASE_TYPE == 'postgres':
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='analysis_jobs' AND column_name='tickers_json'
    """)
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
        logger.info("✓ tickers_json column added")
```

## Deployment Timeline

1. **09:08:31** - New version with emergency check deployed to Railway
2. **09:08:33** - Migrations completed
3. **Next request** - Will use the fixed schema

## What Changed

- ✅ `migration_v3` now includes universal tickers_json handling
- ✅ Added emergency standalone check in `run_migrations()`
- ✅ Production database will automatically get the column on next startup
- ✅ Both SQLite (local dev) and PostgreSQL (production) supported
- ✅ No need to manually patch production database

## Testing

The fix will be verified when:
1. User makes next API request to `/api/stocks/analyze-all-stocks`
2. Column exists → Query succeeds
3. Job creation proceeds normally
4. No more 500 errors

## Prevention for Future

When adding columns to existing migrations:
- ✅ **DO**: Increment CURRENT_SCHEMA_VERSION and create new migration_v4, migration_v5, etc.
- ✅ **DO**: Create migration function that only runs for new version
- ❌ **DON'T**: Add code to already-deployed migration versions
- ✅ **DO**: For emergency fixes: Add standalone idempotent checks in run_migrations()

---

**Status**: ✅ DEPLOYED  
**Expected Result**: 500 errors should be gone  
**Verification**: Watch for successful analyze-all-stocks requests in logs
