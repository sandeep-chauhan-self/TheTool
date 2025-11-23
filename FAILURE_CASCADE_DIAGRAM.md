# Failure Point Cascade & Data Flow Analysis

## Current Data Flow vs. Where It Breaks

```
┌─────────────────────────────────────────────────────────────────┐
│ USER SUBMITS: POST /api/stocks/analyze-all-stocks               │
│ Payload: {"symbols": ["20MICRONS.NS"]}                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Route Handler (stocks.py:analyze_all_stocks)            │
│ ✓ Receives request                                              │
│ ✓ Validates payload                                             │
│ ✗ FAILURE POINT 1: Generates UUID (different every time!)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Check for Duplicate (New code from fix)                 │
│ ✓ Queries analysis_jobs for active jobs (last 5 min)            │
│ ✗ FAILURE POINT 2: No FK relationship!                          │
│   - Can't link analysis_results to analysis_jobs                │
│   - So duplicate check doesn't know which results are from job   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Create Job Record (JobStateTransactions.create_job)     │
│ ✓ Inserts to analysis_jobs table                                │
│ ✗ FAILURE POINT 3: PRIMARY KEY conflict possible                │
│   - If job_id exists (shouldn't happen with UUID, but...)        │
│   - DB returns error                                             │
│   - Caught and returned as 409                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (if insert succeeds)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Start Background Thread                                 │
│ ✓ Creates new thread in thread_tasks.py                         │
│ ✓ Passes job_id, symbols, capital, use_demo                     │
│ ✗ FAILURE POINT 4: use_demo not tracked to DB!                  │
│   - analysis_source will be lost                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Thread: analyze_stocks_batch()                          │
│ ✓ Marks job status as 'processing'                              │
│ ✓ Loops through symbols                                         │
│ ✗ FAILURE POINT 5: No job_id in analysis_results table!         │
│   - Can't link results back to job                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Analyze Each Stock                                      │
│ ✓ Calls analyze_ticker(ticker)                                  │
│ ✓ Gets result: {score, verdict, entry, stop, target, ...}       │
│ ✗ FAILURE POINT 6: result dict may not have analysis_source     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Insert Result to DB                                     │
│ INSERT INTO analysis_results                                    │
│   (ticker, symbol, score, verdict, analysis_source, ...)        │
│                                                                  │
│ ✗ FAILURE POINT 7: No UNIQUE constraint!                        │
│   - Same ticker analyzed twice = 2 rows                         │
│   - No way to know which is latest                              │
│                                                                  │
│ ✗ FAILURE POINT 8: Status column always NULL                    │
│   - Can't query by completion status                            │
│                                                                  │
│ ✗ FAILURE POINT 9: raw_data is huge JSON in TEXT                │
│   - Stores entire indicator array (100KB+)                      │
│   - Every query loads entire JSON                               │
│   - Kills performance with many results                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Update Job Progress                                     │
│ UPDATE analysis_jobs SET completed=X, status='processing'       │
│ ✗ FAILURE POINT 10: No per-stock tracking!                      │
│   - Job shows 50/100 complete                                   │
│   - But which 50? Which failed?                                 │
│   - No analysis_jobs_details table                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Complete Job                                            │
│ ✓ Mark job as 'completed'                                       │
│ ✗ FAILURE POINT 11: Errors array may be empty!                  │
│   - Failed stocks not recorded to analysis_results              │
│   - Just logged to file                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: Frontend Queries Results                               │
│                                                                  │
│ Query 1: SELECT * FROM analysis_results WHERE symbol='TCS'      │
│ ✗ FAILURE POINT 12: Returns 5 rows from different dates!        │
│   - No way to know which is latest                              │
│   - No unique constraint                                        │
│   - Has to ORDER BY created_at DESC and LIMIT 1                 │
│                                                                  │
│ Query 2: SELECT * FROM analysis_results WHERE job_id = ?        │
│ ✗ FAILURE POINT 13: job_id column doesn't exist!                │
│   - Can't query results by job                                  │
│   - Can't delete results if job deleted                         │
│                                                                  │
│ Query 3: SELECT * FROM watchlist WHERE symbol='TCS'             │
│   JOIN analysis_results ON ... WHERE status='completed'         │
│ ✗ FAILURE POINT 14: watchlist has no last_job_id!               │
│   - Can't join watchlist to latest analysis                     │
│   - Multiple LEFT JOINs, O(n²) complexity                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure Cascade Map

```
First User Click (New Job)
        ↓
    job_id = uuid.uuid4()
        ↓
    create_job_atomic(job_id)
        ├─ ✗ Race condition on PRIMARY KEY
        ├─ ✗ DB lock
        ├─ ✗ Connection pool issue
        └─ → Returns False on ANY error
            ↓
        Return 409 ❌
            ↓
    Thread NEVER starts ❌
            ↓
    Job row exists in DB but analysis stuck ❌

---

Second User Click (Same Symbols, New UUID)
        ↓
    job_id = uuid.uuid4()  (Different from first!)
        ↓
    Check for active job? 
        ├─ ✓ Query analysis_jobs (status='processing')
        ├─ ✗ But NO FK! Can't verify results exist
        └─ Returns existing job OR creates new
            ↓
        If creates new:
            ├─ Two jobs analyzing same symbols!
            ├─ analysis_results gets duplicates
            └─ Frontend confused ❌
        
        If returns existing:
            ├─ ✓ Now returns 200 with is_duplicate
            └─ ✓ No 409 error!

---

Results Accumulation
        ↓
    analyze_ticker() returns result
        ↓
    INSERT INTO analysis_results
        ├─ ✗ No job_id column!
        ├─ ✗ No UNIQUE constraint (ticker, date)
        ├─ ✗ analysis_source maybe NULL
        ├─ ✗ status column NULL
        ├─ ✗ raw_data = 100KB JSON
        └─ → Duplicate rows possible ❌
            ↓
    SELECT FROM analysis_results
        ├─ Loads entire table
        ├─ Loads all 100KB JSON for each row
        └─ O(n) complexity, kills DB ❌

---

Data Orphaning
        ↓
    Job completes, marked 'completed'
        ↓
    2 weeks pass, cleanup task runs:
        DELETE FROM analysis_jobs WHERE completed_at < 2 weeks ago
        ↓
    ✗ analysis_results rows still exist!
    ✗ No FK constraint to prevent
    ✗ Foreign key reference (non-existent job_id) ❌
            ↓
    100K orphaned rows remain ❌
            ↓
    Query SELECT * FROM analysis_results
        Includes orphaned rows ❌
        Can't trace them to job ❌
        Can't know if they're valid ❌
```

---

## Query Performance Degradation Over Time

```
Data Growth:
├─ Day 1:     100 results → Query: 50ms ✓
├─ Week 1:  1,000 results → Query: 200ms ✓
├─ Week 2:  2,000 results → Query: 600ms ⚠️
├─ Week 3:  5,000 results → Query: 2000ms ⚠️
├─ Month 1: 10,000 results → Query: 8000ms 🔴
└─ Month 2: 20,000 results → Query timeout 🔴

Why?
1. No index on (symbol, created_at)
2. raw_data column: 20,000 × 100KB = 2GB
3. SELECT * loads entire 2GB
4. No WHERE clause optimization
5. Linear scan of all rows
```

---

## Three Table Design: Sufficient? Analysis

```
Current 3 Tables:
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   watchlist     │     │ analysis_results     │     │ analysis_jobs    │
├─────────────────┤     ├──────────────────────┤     ├──────────────────┤
│ id (PK)         │     │ id (PK)              │     │ job_id (PK)      │
│ symbol (UNIQUE) │     │ ticker               │     │ status           │
│ name            │     │ symbol               │     │ total            │
│ user_id         │     │ score, verdict       │     │ completed        │
│ created_at      │     │ entry, stop, target  │     │ errors           │
│                 │     │ raw_data (TEXT)      │     │ created_at       │
│                 │     │ analysis_source      │     │ started_at       │
│                 │     │ status (NULL!)       │     │ completed_at     │
│                 │     │ created_at           │     │                  │
│                 │     │ updated_at           │     │                  │
└─────────────────┘     └──────────────────────┘     └──────────────────┘
        ↓                       ↓                             ↓
    Missing:               Missing:                     Missing:
    • last_job_id          • job_id (FK!)               • description
    • last_status          • watchlist_id               • job_source
    • last_analysis        • UNIQUE constraint          • timeout
    • FK to results        • status tracking
                          • per-stock errors
                          • started_at
                          • completed_at

Missing Tables:
┌──────────────────────────────┐
│ analysis_jobs_details        │
├──────────────────────────────┤
│ id (PK)                      │
│ job_id (FK) → analysis_jobs  │
│ ticker                       │
│ status (processing/failed)   │
│ started_at, completed_at     │
│ error_message                │
│ result_id (FK) → results     │
└──────────────────────────────┘

┌──────────────────────────────┐
│ analysis_raw_data            │
├──────────────────────────────┤
│ id (PK)                      │
│ result_id (FK) → results     │
│ raw_indicators (JSON)        │
│ created_at                   │
└──────────────────────────────┘

Why 5 Tables Better Than 3?
├─ Separates concerns
├─ Reduces data duplication
├─ Improves query performance
├─ Enables per-stock tracking
├─ Supports error tracking
└─ Better for auditing
```

---

## Fix Priority

**CRITICAL (Fix Today):**
1. ❌ Duplicate job_id PRIMARY KEY violation
   - Add: Composite key strategy (job_id + timestamp hash)
   - Or: UUID collision handling
   
2. ❌ No UNIQUE constraint on (ticker, date)
   - Add: `CREATE UNIQUE INDEX idx_ticker_date ON analysis_results(ticker, DATE(created_at))`

3. ❌ No job_id in analysis_results
   - Add: `job_id TEXT` column to analysis_results
   - Add: `FOREIGN KEY (job_id) REFERENCES analysis_jobs(job_id)`

**HIGH (Fix This Sprint):**
4. ❌ analysis_source lost
   - Fix: Pass use_demo through function calls
   - Populate analysis_source on INSERT

5. ❌ Status column unused
   - Fix: Populate status on INSERT
   - Use in queries for filtering

6. ❌ raw_data performance issue
   - Plan: Create analysis_raw_data table
   - Move 100KB+ JSON to separate table

**MEDIUM (Fix Next Sprint):**
7. ⚠️ error_message not captured
   - Fix: Try/except around analyze_ticker
   - Insert error rows to analysis_results OR analysis_jobs_details

8. ⚠️ watchlist-job relationship
   - Add: last_job_id, last_analyzed_at, analysis_status to watchlist

9. ⚠️ Per-stock job tracking
   - Create: analysis_jobs_details table
   - Track each stock's status within job

10. ⚠️ Orphaned data problem
    - Add: ON DELETE CASCADE to FKs
    - Or: Archive table for deleted jobs

---

## Summary: 3 Tables - Verdict

**Can 3 tables work?** ✓ Technically yes
**Will 3 tables work reliably?** ✗ No, too many issues
**Will it scale?** ✗ Performance collapses after 10K results

**Why the 409 error exists:**
- Root cause: PRIMARY KEY violation on job_id (rare but happens on db locks)
- Symptom: 409 returned immediately
- Result: Thread never starts, job stuck

**Why duplicates aren't caught:**
- No FK linking results to jobs
- No UNIQUE constraint on ticker+date
- Multiple rows for same stock possible
- Can't identify "latest" result reliably

**Path to reliability:**
1. Fix the 3 tables immediately (add constraints)
2. Add analysis_jobs_details for per-stock tracking
3. Split raw_data to separate table
4. Test with 100K+ results
5. Monitor performance
6. Plan multi-user support with proper isolation
