# Critical Issue: Jobs Stuck in 'Queued' State

## Problem Summary

Jobs are being created successfully with status='queued' but **never transition to 'processing'**. They remain stuck at 0% progress indefinitely.

```json
{
    "job_id": "05205e62-6f29-4ce8-80ff-f81b282311a8",
    "status": "queued",  // ❌ NEVER CHANGES TO 'processing'
    "progress_percent": 0,
    "completed": 0,
    "total": 1
}
```

## Root Cause Analysis

### What's Happening:

1. **Thread IS being created** ✓
   - `start_analysis_job()` successfully creates a daemon thread
   - Returns `thread_started: true` in response ✓

2. **Thread enters `analyze_stocks_batch()` function** ✓
   - All the logging setup happens
   - Database context manager is entered ✓

3. **Thread attempts to UPDATE job status to 'processing'** ❌ **FAILS SILENTLY**
   - The UPDATE statement fails or doesn't execute
   - Job state remains 'queued'
   - Thread continues anyway (should crash but doesn't)
   - No error is logged

4. **Thread tries to loop through tickers** ✗ **BUT DATABASE READS ARE FAILING**
   - `analyze_ticker()` gets called
   - Results would be generated
   - INSERT into analysis_results would fail or not execute
   - Thread continues anyway
   - Job progress never updates

### Why It's Silent:

```python
# In thread_tasks.py, line ~67-71:
try:
    logger.info("=" * 60)
    logger.info(f"THREAD TASK STARTED - Job ID: {job_id}")
    # ...
    
    # ❌ This UPDATE fails:
    with get_db_session() as (conn, cursor):
        cursor.execute('''
            UPDATE analysis_jobs 
            SET status = 'processing', started_at = ?
            WHERE job_id = ?
        ''', (datetime.now().isoformat(), job_id))
    
    # ❌ But then there's NO try/except, just continues!
    
except Exception as e:
    logger.error(f"FATAL ERROR in job {job_id}: {e}", exc_info=True)
    # Only catches at top level, not inside the status update
```

### The Real Issue - Database Connection Problems:

**In background threads, the database connection has issues:**

1. **SQLite Thread Safety:**
   ```python
   # This is used in threads:
   def get_db_connection():
       return sqlite3.connect(DB_PATH, check_same_thread=False)
       #                                  ^^^^^^^^^^^^^^^
       # Allows connections from different threads
       # BUT this can cause: "database is locked" errors!
   ```

2. **PostgreSQL on Railway:**
   - Connection pool issues on Railway
   - Connection timeout before query completes
   - Transaction isolation problems

3. **Database Lock from Request Thread:**
   - Frontend request thread may hold a read/write lock
   - Background thread tries to UPDATE
   - Gets "database is locked" error
   - Fails silently

## Failure Points

### Failure Point #11: Thread-Unsafe Database Updates ❌ CRITICAL

**Location:** `backend/infrastructure/thread_tasks.py`, line ~67-73

```python
def analyze_stocks_batch(job_id: str, tickers: List[str], ...):
    try:
        logger.info("THREAD TASK STARTED - Job ID: {job_id}")
        
        # ❌ PROBLEM: This is outside try/except!
        with get_db_session() as (conn, cursor):
            cursor.execute('''
                UPDATE analysis_jobs 
                SET status = 'processing', started_at = ?
                WHERE job_id = ?
            ''', (datetime.now().isoformat(), job_id))
        
        # ✓ But this is inside try
        total = len(tickers)
        completed = 0
        
        # ...rest of code...
```

**Why It Fails:**
- If UPDATE fails, exception is caught by outer try/except
- But exception handler assumes only FATAL errors occur later
- Actually, if UPDATE fails = database is locked = subsequent queries will also fail
- Thread continues anyway in a locked state

**Result:**
- Job status never changes to 'processing'
- All subsequent database operations fail silently
- Thread completes without error log
- Job remains 'queued' forever

---

### Failure Point #12: No Per-Operation Error Checking ❌ HIGH

**Location:** `backend/infrastructure/thread_tasks.py`, line ~100-130

```python
# Process each stock
for idx, ticker in enumerate(tickers, 1):
    try:
        logger.info(f"START analyzing {ticker} ({idx}/{total})")
        
        # Analyze the stock
        result = analyze_ticker(ticker, ...)
        
        if result:
            raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
            
            # ❌ This INSERT fails silently
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    INSERT INTO analysis_results 
                    (ticker, symbol, ..., analysis_source)
                    VALUES (?, ?, ..., ?)
                ''', (...))
            
            # ✓ But logger.info is called anyway!
            logger.info(f"✓ {ticker} COMPLETED ...")
            successful += 1
            
    except Exception as e:
        error_msg = str(e)
        errors.append({'ticker': ticker, 'error': error_msg})
        logger.error(f"? {ticker} ERROR - {error_msg}", exc_info=True)
    
    completed += 1
    progress = int((completed / total) * 100)
    
    # ❌ This UPDATE also fails
    with get_db_session() as (conn, cursor):
        cursor.execute('''
            UPDATE analysis_jobs 
            SET progress = ?, completed = ?, successful = ?
            WHERE job_id = ?
        ''', (progress, completed, successful, job_id))
```

**Why It Fails:**
- INSERT into analysis_results fails due to database lock
- Exception is caught, error added to list ✓
- But then UPDATE progress ALSO fails
- Progress update never happens
- Loop continues anyway
- All subsequent inserts also fail

**Result:**
- No results are stored
- Progress never updates
- Job appears stuck at 0%

---

### Failure Point #13: SQLite "Database is Locked" Pattern ❌ CRITICAL

**Root Cause:**

```python
# Frontend request (main Flask thread):
# GET /api/all-stocks/progress
with get_db_session() as (conn, cursor):
    cursor.execute('''
        SELECT job_id, status, total, completed, successful
        FROM analysis_jobs
        WHERE status IN ('queued', 'processing')
    ''')  # Reads lock
    
    # Takes time to serialize response...

# Meanwhile, background thread (thread_tasks):
# UPDATE analysis_jobs SET status = 'processing', started_at = ?
with get_db_session() as (conn, cursor):
    cursor.execute(...)  # ❌ Tries to write while read lock exists!
    # Fails: "database is locked"
```

**Why This Happens:**
1. Flask processes GET /api/all-stocks/progress request
2. Query acquires READ lock on analysis_jobs table
3. JSON response is being serialized (lock still held)
4. Background thread tries to UPDATE (needs WRITE lock)
5. WRITE lock wait timeout or immediate failure
6. Thread exception not properly caught/logged

---

## The Fix

### Fix #11: Add Inner Try/Except for Status Update

**File:** `backend/infrastructure/thread_tasks.py`

```python
def analyze_stocks_batch(job_id: str, tickers: List[str], capital: float, 
                        indicators: Optional[List[str]] = None, 
                        use_demo_data: bool = True):
    """Background task to analyze multiple stocks"""
    try:
        logger.info("=" * 60)
        logger.info(f"THREAD TASK STARTED - Job ID: {job_id}")
        logger.info(f"Total stocks to analyze: {len(tickers)}")
        logger.info("=" * 60)
        
        # ✅ FIX: Add inner try/except for status update
        max_retries = 3
        status_updated = False
        for attempt in range(max_retries):
            try:
                with get_db_session() as (conn, cursor):
                    cursor.execute('''
                        UPDATE analysis_jobs 
                        SET status = 'processing', started_at = ?
                        WHERE job_id = ?
                    ''', (datetime.now().isoformat(), job_id))
                status_updated = True
                logger.info(f"Job {job_id} status updated to 'processing'")
                break
            except Exception as update_error:
                logger.warning(f"Failed to update status (attempt {attempt + 1}/3): {update_error}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    logger.error(f"FAILED to update job {job_id} to processing after {max_retries} attempts")
                    # Don't raise - continue anyway but log failure
        
        if not status_updated:
            logger.warning(f"Job {job_id}: Proceeding despite status update failure")
        
        total = len(tickers)
        completed = 0
        successful = 0
        errors = []
        
        # Create job state
        job_state.create_job(job_id, {'status': 'processing' if status_updated else 'queued', ...})
        
        # ... rest of function ...
```

---

### Fix #12: Wrap Each Database Operation in Try/Except

**File:** `backend/infrastructure/thread_tasks.py`

```python
# Process each stock
for idx, ticker in enumerate(tickers, 1):
    try:
        logger.info(f"START analyzing {ticker} ({idx}/{total})")
        
        # Analyze the stock
        result = analyze_ticker(ticker, ...)
        
        if result:
            raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
            
            # ✅ FIX: Add dedicated try/except for INSERT
            insert_success = False
            try:
                with get_db_session() as (conn, cursor):
                    cursor.execute('''
                        INSERT INTO analysis_results 
                        (ticker, symbol, ..., analysis_source)
                        VALUES (?, ?, ..., ?)
                    ''', (...))
                insert_success = True
            except Exception as insert_error:
                logger.error(f"Failed to insert result for {ticker}: {insert_error}")
                errors.append({'ticker': ticker, 'error': f"DB insert failed: {str(insert_error)}"})
            
            if insert_success:
                logger.info(f"✓ {ticker} COMPLETED - Score: {result.get('score')}")
                successful += 1
            else:
                logger.warning(f"✗ {ticker} analyzed but not stored in DB")
        else:
            error_msg = 'No result returned'
            errors.append({'ticker': ticker, 'error': error_msg})
            logger.error(f"✗ {ticker} FAILED - {error_msg}")
    
    except Exception as e:
        error_msg = str(e)
        errors.append({'ticker': ticker, 'error': error_msg})
        logger.error(f"? {ticker} ERROR - {error_msg}", exc_info=True)
    
    completed += 1
    progress = int((completed / total) * 100)
    
    # ✅ FIX: Retry progress update with backoff
    progress_updated = False
    for attempt in range(3):
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    UPDATE analysis_jobs 
                    SET progress = ?, completed = ?, successful = ?, errors = ?
                    WHERE job_id = ?
                ''', (progress, completed, successful, json.dumps(errors), job_id))
            progress_updated = True
            break
        except Exception as update_error:
            logger.warning(f"Failed to update progress for {job_id} (attempt {attempt + 1}/3): {update_error}")
            if attempt < 2:
                time.sleep(0.5)
    
    if not progress_updated:
        logger.error(f"Failed to update progress for {job_id} after 3 attempts")
    
    # Update job state in Redis/memory
    job_state.update_job(job_id, {
        'completed': completed,
        'successful': successful,
        'progress': progress,
        'errors': errors
    })
    
    if total == 1 or completed % 10 == 0 or completed == total:
        logger.info(f"Progress: {completed}/{total} ({progress}%) | Successful: {successful}")
```

---

### Fix #13: Handle SQLite Lock Timeout

**File:** `backend/database.py`

```python
import sqlite3

def get_db_connection():
    """Get a new database connection with timeout handling"""
    if DATABASE_TYPE == 'postgres':
        return psycopg2.connect(config.DATABASE_URL)
    else:
        # ✅ FIX: Add timeout for sqlite3
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5.0)
        #                                                    ^^^^^^^^
        # Wait up to 5 seconds for locks instead of failing immediately
        return conn

def get_db_session():
    """Get a thread-safe database session as context manager"""
    from contextlib import contextmanager

    @contextmanager
    def session():
        max_retries = 3
        conn = None
        
        for attempt in range(max_retries):
            try:
                conn = get_db_connection()
                if DATABASE_TYPE == 'sqlite':
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('PRAGMA journal_mode=WAL')
                    cursor.execute('PRAGMA synchronous=NORMAL')
                    # ✅ FIX: Add busy timeout
                    cursor.execute('PRAGMA busy_timeout=5000')  # 5 second timeout
                    cursor.close()
                try:
                    yield conn, conn.cursor()
                    conn.commit()
                except:
                    conn.rollback()
                    raise
                break  # Success
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked (attempt {attempt + 1}/3), retrying...")
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    if conn:
                        conn.close()
                else:
                    raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
    
    return session()
```

---

## Complete File Changes Summary

### File 1: `backend/infrastructure/thread_tasks.py`

**Changes:**
1. Add inner try/except for status='processing' update with retry logic
2. Add try/except for each INSERT operation
3. Add retry logic for progress UPDATE operations
4. Log all database failures with detail
5. Continue thread execution even if some DB operations fail (graceful degradation)

**Line Changes:**
- Line ~67-90: Add status update with retries
- Line ~120-130: Add INSERT try/except wrapper
- Line ~185-210: Add progress update with retries

### File 2: `backend/database.py`

**Changes:**
1. Add `timeout=5.0` to sqlite3.connect() calls
2. Add `PRAGMA busy_timeout=5000` to SQLite connection setup
3. Add retry loop in get_db_session() for lock handling
4. Log all lock timeout errors

**Line Changes:**
- Line ~106-107: Add timeout to sqlite3.connect()
- Line ~117-150: Add retry loop in session() context manager
- Line ~130-135: Add PRAGMA busy_timeout

---

## Impact

**Before Fix:**
- Jobs stuck at 'queued' forever
- 0% progress
- User sees "Analysis already running" even though nothing is happening
- No database updates occur
- Silent failures in thread

**After Fix:**
- Jobs transition to 'processing' with retry logic
- Progress updates even if locked (eventual consistency)
- Database inserts complete with error tracking
- Clear logging of all failures
- Thread continues and completes even with intermittent DB locks

## Testing

```bash
# Test 1: Create job and check status changes
curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["TCS.NS"]}'

# Get the job_id from response, then check progress every second:
curl http://localhost:8000/api/all-stocks/progress

# Expected: status changes from 'queued' to 'processing' to 'completed' within 10 seconds
```

---

## Deployment Checklist

- [ ] Update `backend/infrastructure/thread_tasks.py` with all three fixes
- [ ] Update `backend/database.py` with timeout and retry logic
- [ ] Test locally: Create job and verify progress updates
- [ ] Check logs for "Job {job_id} status updated to 'processing'"
- [ ] Verify no "database is locked" errors in logs
- [ ] Deploy to Railway
- [ ] Monitor: `/api/all-stocks/progress` should show jobs transitioning through states
- [ ] Verify results are stored: `SELECT COUNT(*) FROM analysis_results` should increase

---

## Why This Happens in Production (Railway)

1. **Railway PostgreSQL:** 
   - Connection pooling issues with daemon threads
   - Keep-alive timeouts
   - Transient "connection refused" errors

2. **SQLite (Local):**
   - WAL mode lock contention
   - Synchronous=NORMAL still has locking
   - Thread timeout on first UPDATE = all subsequent queries fail

3. **Both:**
   - Background thread doesn't have Flask context
   - No connection pool management
   - Exceptions not properly caught at thread level

**This fix handles all three scenarios with retry logic and graceful degradation.**
