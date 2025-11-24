# Deep Check Report - All Scenarios

## 1. Database Schema Consistency ✓

### Tables Verified:
- ✓ `analysis_jobs` - Has `tickers_json` column (added in migration_v3)
- ✓ `analysis_results` - All required columns present
- ✓ `watchlist` - All required columns present

### Indexes:
- ✓ `idx_job_tickers` on `analysis_jobs(tickers_json, status)` - Created
- ✓ All analysis_results indexes present
- ✓ All analysis_jobs indexes present

### Critical Fields:
- ✓ `job_id` is PRIMARY KEY in analysis_jobs
- ✓ `tickers_json` is TEXT field (can be NULL)
- ✓ Status field tracks: 'queued', 'processing', 'completed', 'failed', 'cancelled'

---

## 2. Potential Issues & Fixes Required

### Issue 1: Missing SQLite Migration for tickers_json
**File**: `backend/db_migrations.py`
**Status**: ⚠️ NEEDS FIX
**Problem**: migration_v3 only handles PostgreSQL. SQLite users won't get tickers_json column.
**Impact**: Local development with SQLite will fail
**Fix**: Add SQLite support to migration_v3

### Issue 2: Transaction Rollback on PostgreSQL Error
**File**: `backend/routes/stocks.py` line 407
**Status**: ⚠️ NEEDS INVESTIGATION
**Problem**: When `_get_active_job_for_symbols()` fails on final retry (line 407), the transaction may be in aborted state
**Error Message**: "current transaction is aborted, commands ignored until end of transaction block"
**Fix**: Reset transaction state after error

### Issue 3: Missing NULL Check in _get_active_job_for_symbols
**File**: `backend/routes/stocks.py` line 273
**Status**: ⚠️ POTENTIAL ISSUE
**Problem**: Code checks `if not tickers_json` but doesn't handle malformed JSON gracefully
**Fix**: Add try-catch around json.loads()

### Issue 4: Error Handling in analyze route
**File**: `backend/routes/analysis.py` line 43
**Status**: ⚠️ NEEDS VERIFICATION
**Problem**: Query uses `tickers_json = ?` without normalizing input
**Fix**: Ensure tickers are normalized before comparing

### Issue 5: Connection Cleanup on Errors
**File**: `backend/database.py` - get_db_session()
**Status**: ⚠️ POTENTIAL LEAK
**Problem**: If exception occurs in session, connection cleanup might be incomplete
**Fix**: Ensure finally block always closes

---

## 3. API Endpoint Scenarios

### Scenario 1: Normal Job Creation
- ✓ Request comes in with symbols
- ✓ Checks for active jobs
- ✓ Creates new job with UUID
- ✓ Returns 201 with job details

### Scenario 2: Concurrent Requests (Same Symbols)
- ✓ Request A checks → no job found
- ✓ Request B checks → no job found
- ✓ Request A creates job → succeeds
- ✓ Request B retries → finds job created by Request A → returns 200
- ✓ **Fixed by race condition handler**

### Scenario 3: Database Connection Error
- ⚠️ **ISSUE**: get_db_session() might leave connection open
- ⚠️ **ISSUE**: Transaction might be in aborted state
- ✓ **Partially Handled**: With try/except/finally

### Scenario 4: Empty Symbols Array
- ✓ Queries all stocks from database
- ✓ Returns 400 if no stocks found
- ✓ Analyzes all found stocks

### Scenario 5: NULL tickers_json in Database
- ⚠️ **ISSUE**: Code at line 269 checks `if not tickers_json` but some older jobs might have NULL
- ✓ **Handled**: Skips and continues

---

## 4. Migration Issues

### Current Version: 3
**Applied Migrations**:
- ✓ v1: Schema initialization
- ✓ v2: Constraints and columns
- ✓ v3: PostgreSQL-specific features + NEW tickers_json column

### Issue: SQLite Not Covered
**Problem**: migration_v3 skips for non-PostgreSQL databases
```python
if config.DATABASE_TYPE != 'postgres':
    logger.info("Migration v3 skipping for non-PostgreSQL database")
    return apply_migration(conn, 3, "PostgreSQL constraints (skipped)", "")
```
**Impact**: SQLite local dev won't have tickers_json column → Queries will fail
**Fix**: Add SQLite version of migration_v3

---

## 5. Transaction & Connection Pool Issues

### PostgreSQL Connection Issues
1. No connection pooling in production
2. get_db_connection() creates new connection each time
3. Potential for "too many connections" errors under load

### SQLite Lock Contention
1. ✓ WAL mode enabled
2. ✓ PRAGMA busy_timeout=5000 set
3. ✓ timeout=5.0 in sqlite3.connect()

### Issue: Missing Connection Limits
**Problem**: No maximum connection limit
**Impact**: Railway could receive "too many connections" error
**Fix**: Add connection pool limits

---

## 6. Code Quality Issues Found

### Issue 1: Bare Except Clauses - Already Fixed ✓
**Status**: RESOLVED

### Issue 2: Missing Imports
**File**: `backend/routes/stocks.py` line 376
**Issue**: `import time` is inside the loop
**Status**: ⚠️ Style Issue (works but inefficient)
**Fix**: Move to top of file

### Issue 3: Incomplete Error Details
**File**: `backend/routes/stocks.py` line 404
**Error Message**: "Failed to create analysis job after retries"
**Status**: ✓ ACCEPTABLE - Generic message to prevent info leak

---

## Summary of Fixes Needed

### 🔴 CRITICAL (Must Fix):
1. Add SQLite support to migration_v3 for tickers_json column

### 🟡 IMPORTANT (Should Fix):
2. Reset transaction state after connection errors in PostgreSQL
3. Add connection pool limits for PostgreSQL
4. Improve error context in transaction abort scenarios

### 🟢 MINOR (Nice to Have):
5. Move `import time` outside retry loop
6. Add more detailed logging for debugging

---

## Testing Scenarios Checklist

- [ ] Test 1: Normal job creation (single user)
- [ ] Test 2: Concurrent job creation (same symbols)
- [ ] Test 3: Concurrent job creation (different symbols)
- [ ] Test 4: Job with empty symbols array
- [ ] Test 5: Database connection timeout/error
- [ ] Test 6: SQLite with tickers_json queries
- [ ] Test 7: PostgreSQL with aborted transaction recovery
- [ ] Test 8: Job status polling after creation
- [ ] Test 9: Multiple requests to analyze-all-stocks
- [ ] Test 10: Database migration idempotency
