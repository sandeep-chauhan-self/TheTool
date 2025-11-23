# Database Schema Analysis: 3-Table Architecture

## Current Tables

### Table 1: `watchlist`
```sql
id INTEGER PRIMARY KEY
symbol TEXT UNIQUE NOT NULL
name TEXT
user_id INTEGER DEFAULT 1
created_at TIMESTAMP
```
**Purpose:** Store user's watchlist of stocks

**Data per row:** ~50-100 bytes

---

### Table 2: `analysis_results`
```sql
id INTEGER PRIMARY KEY
ticker TEXT NOT NULL
symbol TEXT
name TEXT
yahoo_symbol TEXT
score REAL
verdict TEXT
entry REAL
stop_loss REAL
target REAL
entry_method TEXT
data_source TEXT
is_demo_data BOOLEAN
raw_data TEXT (JSON, can be large)
status TEXT
error_message TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
analysis_source TEXT
```
**Purpose:** Store analysis results from both watchlist and bulk analysis

**Data per row:** ~500-5000 bytes (depending on raw_data size)

---

### Table 3: `analysis_jobs`
```sql
job_id TEXT PRIMARY KEY
status TEXT
progress INTEGER
total INTEGER
completed INTEGER
successful INTEGER
errors TEXT (JSON array)
created_at TIMESTAMP
updated_at TIMESTAMP
started_at TIMESTAMP
completed_at TIMESTAMP
```
**Purpose:** Track async job progress

**Data per row:** ~200-500 bytes

---

## Critical Analysis: CAN 3 TABLES HANDLE ALL DATA?

### ✅ YES, Technically Possible - But With Caveats

**Pros of 3-table design:**
- Simple, minimal
- Easy to query
- Normalization is reasonable
- Works for current scale

**Cons of 3-table design:**
- Multiple design issues hidden
- Data integrity problems
- Query complexity increases with features
- Scaling bottlenecks

---

## 🔴 CRITICAL FAILURE POINTS

### **FAILURE POINT 1: Duplicate Job IDs in analysis_jobs**
**Severity:** 🔴 CRITICAL

**Problem:**
```sql
-- job_id is PRIMARY KEY
job_id TEXT PRIMARY KEY  -- ✗ Unique constraint on TEXT
```

**Why it fails:**
- User clicks "Analyze" twice within 1 second
- Two processes generate same UUID (virtually impossible) OR same job_id passed twice
- INSERT fails with PRIMARY KEY violation
- Returns 409 error ❌

**Current fix attempt:**
```python
# In analyze_all_stocks():
created = JobStateTransactions.create_job_atomic(job_id, ...)
if not created:
    return 409  # ✗ Wrong! Treats any error as duplicate
```

**Real issue:**
- Each POST generates `uuid.uuid4()` → Different UUID each time
- So 409 shouldn't happen UNLESS there's a race condition
- **BUT:** If DB lock occurs, error is misinterpreted as duplicate
- Thread may have started even though 409 was returned

**Solution needed:**
```python
# Create unique composite key
# job_id = hash(symbols + timestamp + user_id)
# Allows re-checking without new UUID
```

---

### **FAILURE POINT 2: analysis_results Lacks Unique Constraint**
**Severity:** 🟠 HIGH

**Problem:**
```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL,  -- ✗ No unique constraint
    symbol TEXT,           -- ✗ No unique constraint
    analysis_source TEXT,  -- ✗ No unique constraint
    created_at TIMESTAMP,  -- ✗ No unique constraint
    ...
)
```

**Why it fails:**
```python
# In analyze_stocks_batch():
cursor.execute('''
    INSERT INTO analysis_results 
    (ticker, symbol, score, verdict, ...)
    VALUES (?, ?, ?, ?, ...)
''')
# No ON CONFLICT/DUPLICATE handling
# Same stock analyzed twice = duplicate row ❌
```

**Data corruption scenario:**
```
Job 1: Analyze TCS.NS at 2025-11-23 15:00:00
Job 2: Analyze TCS.NS at 2025-11-23 15:05:00
Job 3: Analyze TCS.NS at 2025-11-23 15:10:00

Result: 3 rows for same ticker
Frontend query: SELECT * FROM analysis_results WHERE symbol='TCS'
Returns: 3 rows, confused result display ❌
```

**Missing indexes/constraints:**
```sql
-- Should have:
CREATE UNIQUE INDEX IF NOT EXISTS 
    idx_ticker_analysis_date 
    ON analysis_results(ticker, DATE(created_at));

-- Or:
CREATE UNIQUE INDEX IF NOT EXISTS 
    idx_symbol_job_id 
    ON analysis_results(symbol, job_id);
```

---

### **FAILURE POINT 3: No Foreign Keys**
**Severity:** 🟠 HIGH

**Problem:**
```sql
-- analysis_results has NO reference to watchlist
ticker TEXT NOT NULL  -- ✓ Can be any value
symbol TEXT           -- ✓ Can be any value

-- analysis_results has NO reference to analysis_jobs
-- (no job_id column linking to analysis_jobs.job_id)
```

**Why it fails:**
```python
# If analysis_jobs row is deleted:
DELETE FROM analysis_jobs WHERE job_id = 'abc-123'

# analysis_results rows still exist with no parent ❌
# Orphaned data!
SELECT * FROM analysis_results WHERE ...
# Results from deleted jobs are still returned
```

**Data orphaning scenario:**
```
Job completes → Job row marked 'completed'
Week passes → Admin cleans up: DELETE FROM analysis_jobs WHERE created_at < NOW() - INTERVAL 7 DAYS
Results rows remain → 100K rows with no job reference
Query performance drops → No way to trace results back to job
```

---

### **FAILURE POINT 4: analysis_source Column Inconsistency**
**Severity:** 🟡 MEDIUM

**Problem:**
```python
# In analyze_stocks_batch():
cursor.execute('''
    INSERT INTO analysis_results 
    (..., analysis_source)
    VALUES (..., ?)
''', (
    ...,
    result.get('analysis_source', 'real'),  # ✗ From result dict
    ...
))

# But result dict might not have 'analysis_source'
# Falls back to 'real' always!
```

**Why it fails:**
```sql
-- Actual data in production:
SELECT DISTINCT analysis_source FROM analysis_results;
-- Returns:
-- real
-- real  
-- real  <-- Losing track of job source!

-- Should be:
-- watchlist
-- bulk
-- demo
```

**Missing values scenario:**
```python
# In analyze_all_stocks:
start_analysis_job(job_id, symbols, None, capital, use_demo=False)

# In analyze_stocks_batch:
# Should track use_demo parameter, but doesn't!
# analysis_source should be 'bulk', 'watchlist', or 'demo'
# But it's always 'real' ❌
```

---

### **FAILURE POINT 5: status Column Unused/Confusing**
**Severity:** 🟡 MEDIUM

**Problem:**
```sql
-- analysis_results has:
status TEXT  -- What does this mean? ✗

-- Three possible states, but unclear:
-- 'pending'    -- Analysis queued?
-- 'completed'  -- Analysis done?
-- 'failed'     -- Analysis failed?
```

**Why it fails:**
```python
# In code, never actually used:
cursor.execute('''
    INSERT INTO analysis_results 
    (..., status, ...)
    VALUES (..., ?, ...)
''', (
    ...,
    None,  # ✗ Always NULL!
    ...
))

# Later query assumes it has value:
SELECT * FROM analysis_results WHERE status = 'completed'
# Returns: 0 rows (all are NULL)
```

**Data confusion scenario:**
```sql
-- Frontend wants to show:
-- "Results: 5 completed, 2 pending, 1 failed"

-- But query:
SELECT status, COUNT(*) FROM analysis_results GROUP BY status;
-- Returns:
-- NULL | 8

-- Can't distinguish completed vs failed ❌
```

---

### **FAILURE POINT 6: raw_data Column Type Problem**
**Severity:** 🟡 MEDIUM

**Problem:**
```sql
raw_data TEXT  -- Storing JSON in TEXT column
```

**Why it fails:**
```python
# In thread_tasks.py:
raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)

cursor.execute('''
    INSERT INTO analysis_results (..., raw_data, ...)
    VALUES (..., ?, ...)
''', (..., raw_data, ...))

# Storing massive JSON strings in TEXT column
# Can be 100KB+ per row!

# Later retrieval:
SELECT * FROM analysis_results WHERE symbol = 'TCS'
# Loads entire 100KB JSON into memory per row
# With 1000 results: 100MB in memory ❌
```

**Performance degradation:**
```sql
-- After 10K results:
SELECT COUNT(*) FROM analysis_results;
-- Result: 10,000
-- Total raw_data size: ~1GB

-- Simple query:
SELECT ticker, verdict, score FROM analysis_results;
-- Must scan entire 1GB to extract 3 columns ❌
-- Query time: >10 seconds

-- Solution: Separate table for raw_data
```

---

### **FAILURE POINT 7: error_message Field Not Used**
**Severity:** 🟡 MEDIUM

**Problem:**
```sql
error_message TEXT  -- When is this populated?
```

**Why it fails:**
```python
# In analyze_stocks_batch:
try:
    result = analyze_ticker(ticker, ...)
    
    cursor.execute('''
        INSERT INTO analysis_results 
        (..., status, error_message, ...)
    ''', (..., 'completed', None, ...))  # ✗ Always None!
    
except Exception as e:
    # Exception happens, but where do we log it?
    logger.error(f"Failed to analyze {ticker}: {e}")
    
    # We DON'T insert error row to database!
    # The exception is lost ❌
```

**Lost errors scenario:**
```python
# Job completes with 5/100 successes
# What happened to other 95?
# Check analysis_jobs.errors:
SELECT errors FROM analysis_jobs WHERE job_id = 'abc-123'
# Returns: []  (empty!)

# The errors were logged to file but not to DB ❌
# Can't query error patterns in database
```

---

### **FAILURE POINT 8: watchlist Has No Job Tracking**
**Severity:** 🟡 MEDIUM

**Problem:**
```sql
-- watchlist table has:
id, symbol, name, user_id, created_at
-- But NO reference to last_analysis_job_id
-- No last_analyzed_at
-- No analysis_status
```

**Why it fails:**
```python
# In frontend, user wants:
# "Show me my watchlist and status of analysis for each stock"

# Query needed:
SELECT w.symbol, w.name, j.status, j.completed, j.total
FROM watchlist w
LEFT JOIN analysis_jobs j ON j.??? = w.???
# ✗ Can't join! No FK relationship!

# Has to query analysis_results instead:
SELECT DISTINCT w.symbol, ar.verdict
FROM watchlist w
LEFT JOIN analysis_results ar ON ar.symbol = w.symbol
ORDER BY ar.created_at DESC
# ✗ Gets latest result, not job status!
```

---

### **FAILURE POINT 9: Composite Key Issues**
**Severity:** 🟠 HIGH

**Problem:**
```python
# How to uniquely identify an analysis result?
# Option 1: (ticker, created_at)? - NO, can have multiple same day
# Option 2: (ticker, job_id)? - NO, job_id not in analysis_results!
# Option 3: (symbol, analysis_source, created_at)? - Weak, time-based
# Option 4: Just use id? - OK but no semantic meaning ✓
```

**Why it fails:**
```python
# Update logic is broken:
cursor.execute('''
    UPDATE analysis_results 
    SET verdict = ?, score = ?
    WHERE ticker = ?
''')
# ✗ Updates ALL rows with that ticker!
# If TCS analyzed 100 times, all get same verdict ❌
```

---

### **FAILURE POINT 10: No Temporal Data Tracking**
**Severity:** 🟡 MEDIUM

**Problem:**
```sql
-- analysis_results has:
created_at TIMESTAMP
updated_at TIMESTAMP

-- But NO way to track:
-- - When analysis started?
-- - How long did it take?
-- - Was it retried?
-- - Multiple versions of same analysis?
```

**Why it fails:**
```python
# Frontend wants:
# "Analysis of TCS took 5 minutes"

# But no data in DB to calculate:
SELECT 
  (completed_at - started_at) as duration
FROM analysis_jobs
# ✗ What about analysis_results?
# No started_at, no completed_at ❌

# Can only say:
# "Analysis result created at X, updated at Y"
# But that's for job, not individual result
```

---

## Missing Tables (Needed for Scale)

### **Should Exist: `analysis_jobs_details`**
Track per-stock progress:
```sql
CREATE TABLE analysis_jobs_details (
    id INTEGER PRIMARY KEY,
    job_id TEXT NOT NULL,  -- FK to analysis_jobs
    ticker TEXT NOT NULL,
    status TEXT NOT NULL,  -- queued, processing, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_id INTEGER,     -- FK to analysis_results
    FOREIGN KEY(job_id) REFERENCES analysis_jobs(job_id),
    FOREIGN KEY(result_id) REFERENCES analysis_results(id)
);
```

**Solves:**
- Track per-stock progress in bulk job
- Know which stock failed in which job
- Retry specific stocks
- Better error tracking

---

### **Should Exist: `analysis_raw_data`**
Separate large data:
```sql
CREATE TABLE analysis_raw_data (
    id INTEGER PRIMARY KEY,
    analysis_result_id INTEGER NOT NULL,  -- FK to analysis_results
    raw_indicators JSON,
    raw_signals JSON,
    raw_metadata JSON,
    created_at TIMESTAMP,
    FOREIGN KEY(analysis_result_id) REFERENCES analysis_results(id)
);
```

**Solves:**
- Separate large JSON from query results
- Query doesn't load huge JSON
- Lazy-load raw data only when needed
- 10x faster queries

---

### **Should Exist: `user_preferences`**
For future multi-user:
```sql
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    watchlist_alerts BOOLEAN,
    email TEXT,
    last_login TIMESTAMP,
    analysis_history_days INTEGER,
    created_at TIMESTAMP
);
```

**Solves:**
- Prepare for multi-user support
- Settings per user
- User preferences independent

---

## Point of Failure Summary Table

| # | Failure Point | Severity | Root Cause | Impact | Fix |
|---|---|---|---|---|---|
| 1 | Duplicate job_id | 🔴 CRITICAL | UUID collision or race condition | 409 errors, lost jobs | Composite key + retry logic |
| 2 | No unique constraint | 🟠 HIGH | Allows duplicate results | Data duplication, confusion | ADD UNIQUE INDEX |
| 3 | No foreign keys | 🟠 HIGH | Orphaned data possible | Stale results, lost traceability | ADD FOREIGN KEY |
| 4 | analysis_source ignored | 🟡 MEDIUM | Parameter not passed through | Wrong categorization | Pass parameter through call stack |
| 5 | status column unused | 🟡 MEDIUM | Never populated | Can't track result status | Populate on insert/update |
| 6 | raw_data in TEXT | 🟡 MEDIUM | Performance issue | 1GB+ bloat, slow queries | Move to separate table |
| 7 | error_message unused | 🟡 MEDIUM | Exceptions not logged to DB | Can't query error patterns | Catch & insert errors |
| 8 | watchlist no status | 🟡 MEDIUM | Missing columns | Can't query watchlist + job status | Add FK, last_job_id, last_analyzed_at |
| 9 | Composite key issues | 🟠 HIGH | No clear PK strategy | Update/delete wrong rows | Define composite key + indices |
| 10 | No temporal tracking | 🟡 MEDIUM | Missing time columns | Can't measure performance | Add started_at, completed_at to results |

---

## Can 3 Tables Handle Everything?

### ✅ Functionally: YES
- Watchlist: User's stocks
- Analysis Results: Results + job reference
- Analysis Jobs: Job tracking

### ❌ Reliably: NO
**Because:**
- No constraints prevent bad data
- No FK integrity
- No unique indices
- No semantic tracking
- Query complexity grows
- Performance degrades fast

### 🔧 What's Needed to Make 3 Tables Work:

**Add to schema:**
1. UNIQUE INDEX on (ticker, DATE(created_at)) for analysis_results
2. FOREIGN KEY from analysis_results to analysis_jobs
3. FOREIGN KEY from analysis_results to watchlist
4. Composite key strategy (ticker + job_id or ticker + timestamp)
5. Separate analysis_raw_data table (don't store large JSON)
6. Add columns: last_job_id, last_analyzed_at to watchlist

**OR accept the current design with these caveats:**
- Expect 409 duplicate errors (as we're seeing now)
- Accept duplicate results in analysis_results
- Accept performance degradation after 10K+ results
- Accept orphaned rows when jobs deleted
- Accept inaccurate error tracking

---

## Recommended Path Forward

### Short-term (Immediate Fix):
Fix the 3 current tables with:
1. Add UNIQUE constraints
2. Add FOREIGN KEY constraints
3. Fix analysis_source tracking
4. Fix status column usage

### Medium-term (Next Sprint):
1. Split analysis_raw_data to separate table
2. Add analysis_jobs_details table for per-stock tracking
3. Add temporal columns (started_at, completed_at)
4. Add watchlist status columns

### Long-term (Scaling):
1. Add user_preferences table
2. Add audit log table
3. Add caching layer
4. Consider read replicas for analytics queries

---

**Current Status:** 3 tables CAN work, but are **fragile and prone to data integrity issues**. The 409 duplicate error you're seeing is a symptom of this fragility.
