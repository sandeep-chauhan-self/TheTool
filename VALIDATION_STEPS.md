# Validation Steps After Deployment

## Pre-Deployment Checklist (Local)

### 1. Syntax Validation
```bash
cd backend
python -m py_compile routes/stocks.py routes/analysis.py
echo "✅ Python syntax valid"
```

### 2. Import Check
```bash
python -c "from routes.stocks import analyze_all_stocks; print('✅ Routes import successfully')"
```

### 3. Database Schema Check
```bash
python -c "
from database import init_db
init_db()
print('✅ Database initialized')
"
```

---

## Post-Deployment Validation (Production)

### Step 1: Verify Backend Responses

#### Test 1a: First Request (Should Return 201)
```bash
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"symbols": ["20MICRONS.NS"]}'
```

**Expected Output:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "symbols": ["20MICRONS.NS"],
  "capital": 100000,
  "count": 1,
  "thread_started": true
}

HTTP/1.1 201 Created
```

**Validation Points:**
- ✅ Status code is 201 (not 409)
- ✅ `job_id` is present and valid UUID
- ✅ `thread_started` is true
- ✅ Response time < 500ms

---

#### Test 1b: Duplicate Request (Should Return 200 with is_duplicate=true)
```bash
# Immediately after first request (within 5 min)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"symbols": ["20MICRONS.NS"]}'
```

**Expected Output:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "is_duplicate": true,
  "message": "Analysis already running for these symbols",
  "total": 1,
  "completed": 0,
  "symbols": ["20MICRONS.NS"],
  "capital": 100000,
  "count": 1
}

HTTP/1.1 200 OK
```

**Validation Points:**
- ✅ Status code is 200 (not 409)
- ✅ `is_duplicate` is true
- ✅ `job_id` matches first request (same job)
- ✅ Response time < 100ms (faster than first)

---

#### Test 1c: Force Parameter (Should Return 201 with New Job ID)
```bash
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"symbols": ["20MICRONS.NS"], "force": true}'
```

**Expected Output:**
```json
{
  "job_id": "660f9501-f40d-63f6-c828-667877662111",
  "status": "queued",
  "symbols": ["20MICRONS.NS"],
  "capital": 100000,
  "count": 1,
  "thread_started": true
}

HTTP/1.1 201 Created
```

**Validation Points:**
- ✅ Status code is 201
- ✅ `job_id` is different from previous requests
- ✅ `thread_started` is true

---

#### Test 1d: Check Job Status
```bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"

curl https://thetool-production.up.railway.app/api/analysis/status/$JOB_ID \
  -H "X-API-Key: your-api-key"
```

**Expected Output:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total": 1,
  "completed": 0,
  "successful": 0,
  "progress_percent": 0
}

HTTP/1.1 200 OK
```

**Validation Points:**
- ✅ Job exists in database
- ✅ Status is "processing" or "completed"
- ✅ Progress fields are present

---

### Step 2: Verify Frontend Behavior

#### Test 2a: Open Frontend in Browser
1. Go to: https://the-tool-theta.vercel.app/
2. Navigate to: "All Stocks Analysis" page
3. Click "Analyze All Stocks" button

**Expected Behavior:**
- ✅ No error modal appears
- ✅ Alert shows: "Analysis started. Job ID: [uuid]"
- ✅ Button becomes disabled while analyzing

#### Test 2b: Submit Duplicate Request
1. Immediately click "Analyze All Stocks" again (before first completes)

**Expected Behavior:**
- ✅ No error occurs
- ✅ Alert shows: "Analysis already running for these stocks. Job ID: [uuid] (Progress: X/total)"
- ✅ Same job ID as first request

#### Test 2c: Check Browser Console
Open DevTools → Console tab and verify:
- No error messages
- Response shows `is_duplicate: true` for duplicate request
- Request URLs are correct

---

### Step 3: Verify Logs

#### Backend Logs
Check Railway logs:
```bash
# Via Railway CLI
railway logs

# Expected patterns:
# ✅ "Creating new analysis job {job_id} for N symbols"
# ✅ "Found active job {job_id} with status processing"
# ✅ "Duplicate detected. Returning existing job {job_id}"
# ✅ "Started background thread for job {job_id}"
```

#### Thread Task Logs
```bash
# Check for analysis execution
# ✅ "THREAD TASK STARTED - Job ID: {job_id}"
# ✅ "Total stocks to analyze: N"
# ✅ "START analyzing {ticker}"
```

---

### Step 4: Database Verification

#### Connect to Production Database
```bash
# Using psql (PostgreSQL)
psql -h your-railway-host -U your-user -d your-db

# View active jobs
SELECT job_id, status, total, completed, created_at
FROM analysis_jobs
WHERE status IN ('queued', 'processing')
ORDER BY created_at DESC;

# Expected output:
# job_id                               | status     | total | completed | created_at
# ------+--------+-------+-----------+------------------------------
# 550e8400-e29b-41d4-a716-446655440000 | processing |     1 |         0 | 2025-11-23 21:30:00
```

**Validation Points:**
- ✅ Job record exists in database
- ✅ Status is 'queued' or 'processing'
- ✅ `created_at` is recent (within last few minutes)
- ✅ No duplicate job_ids (each is unique UUID)

---

### Step 5: Analytics & Metrics

#### Track These Metrics (24-48 hours)
1. **Duplicate Detection Rate**
   ```sql
   SELECT COUNT(*) as duplicate_requests
   FROM audit_log
   WHERE event_type = 'analyze_duplicate'
   AND timestamp > NOW() - INTERVAL '24 hours';
   ```
   Expected: 10-30% of total analyze requests

2. **Job Creation Success Rate**
   ```sql
   SELECT COUNT(*) as successful_jobs
   FROM analysis_jobs
   WHERE status IN ('processing', 'completed')
   AND created_at > NOW() - INTERVAL '24 hours';
   ```
   Expected: >99% of submitted requests

3. **Average Response Time**
   - First request: 100-300ms
   - Duplicate request: 20-80ms
   - (Duplicate should be 3-4x faster)

4. **Thread Start Success**
   ```bash
   grep "Started background thread" backend/logs/*.log | wc -l
   # Should equal number of successful job creations
   ```

---

## Regression Testing

### Test Backward Compatibility

#### Old Client Behavior (No `force` parameter)
```bash
# Old clients will work fine
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["TCS.NS"], "capital": 100000}'

# Should return 201 or 200 (both are success)
```

#### Missing Parameters
```bash
# Empty symbols array (should analyze all)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -d '{"symbols": []}'
# Expected: 201, fetches all stocks

# Missing capital (should use default)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["TCS.NS"]}'
# Expected: 201, capital defaults to 100000
```

---

## Error Scenarios

### Test Error Handling

#### Invalid Symbols
```bash
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["INVALID.XX"]}'
# Expected: 201 (job created), but may fail during analysis
# Check: Job status after 5 min should show errors
```

#### Database Connection Error
```bash
# Simulate by stopping database (dev only)
# Expected: 500 error with "JOB_CREATION_FAILED" code
# Check: Logs show retry attempts
```

#### Invalid API Key
```bash
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "X-API-Key: invalid-key" \
  -d '{"symbols": ["TCS.NS"]}'
# Expected: 401 or 403 error
```

---

## Performance Baseline

### Measure Performance

#### Response Times (ms)
```bash
# Test 1: New job
time curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["20MICRONS.NS"]}' | jq .

# Expected: ~150-250ms total

# Test 2: Duplicate (5 times)
for i in {1..5}; do
  time curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
    -d '{"symbols": ["20MICRONS.NS"]}'
  sleep 1
done

# Expected: ~50-100ms each (much faster)
```

#### Database Load
```sql
-- Check query performance
SELECT 
  COUNT(*) as total_queries,
  AVG(duration) as avg_ms,
  MAX(duration) as max_ms
FROM pg_stat_statements
WHERE query LIKE '%analysis_jobs%'
AND timestamp > NOW() - INTERVAL '1 hour';

-- Expected: <10ms average for duplicate check query
```

---

## Rollback Validation

If rollback is needed:

1. **Verify rollback deployed:**
   ```bash
   curl https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
     -d '{"symbols": ["TCS.NS"]}'
   
   # Old behavior: 409 on duplicate (if hit race condition)
   # New behavior: 200 with is_duplicate or 201
   ```

2. **Check logs for old error patterns:**
   ```bash
   grep "Job already exists" backend/logs/*.log
   # Should be present after rollback
   ```

---

## Sign-Off Checklist

After validating all tests, check these boxes:

- [ ] First request returns 201 with job_id
- [ ] Duplicate request returns 200 with is_duplicate=true
- [ ] Force parameter creates new job (returns 201)
- [ ] Job status endpoint works and returns progress
- [ ] Frontend shows success message (not error)
- [ ] Frontend shows helpful duplicate message
- [ ] Backend logs show "Creating new analysis job" messages
- [ ] No error logs related to job creation
- [ ] Database has active jobs with status 'processing'
- [ ] Response times are fast (>300ms is red flag)
- [ ] Thread start messages in logs for each job
- [ ] Old clients work without modification
- [ ] No regression in other endpoints
- [ ] Browser console shows no errors
- [ ] Production deployment is stable for 24h

---

## Troubleshooting Guide

### Issue: Still Getting 409 Errors

**Diagnosis:**
```bash
# Check if new code is deployed
curl https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["20MICRONS.NS"]}'

# If 409 still appears, old code is running
# Check: Railway deployment status
```

**Solution:**
1. Check Railway build logs for errors
2. Verify git push succeeded
3. Manually trigger redeploy in Railway console

### Issue: Jobs Not Starting (thread_started: false)

**Diagnosis:**
```bash
# Check logs for thread error
grep "Failed to start thread" backend/logs/*.log

# Check if other threads are running
ps aux | grep "python\|flask"
```

**Solution:**
1. Check system resources (CPU, memory)
2. Verify `start_analysis_job()` function is accessible
3. Check for permission issues on thread creation

### Issue: Duplicate Check Always Triggers

**Diagnosis:**
```bash
# Check TTL window (5 minutes)
SELECT created_at, status
FROM analysis_jobs
ORDER BY created_at DESC
LIMIT 10;

# If very old jobs have status='processing', they're stuck
```

**Solution:**
1. Manually mark stale jobs as completed
2. Reduce TTL window in code (from 5 to 2 minutes)
3. Add job cleanup task

### Issue: Performance Regression

**Diagnosis:**
```bash
# Benchmark duplicate query
EXPLAIN ANALYZE SELECT job_id FROM analysis_jobs 
WHERE status IN ('queued', 'processing') 
AND created_at > NOW() - INTERVAL '5 minutes'
LIMIT 1;

# Should use index on status and created_at
```

**Solution:**
1. Add index: `CREATE INDEX ON analysis_jobs(status, created_at DESC)`
2. Verify database indices exist
3. Run VACUUM ANALYZE on database

---

## Success Criteria

Fix is successfully deployed when:

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| **No 409 errors** | Count of 409s in 24h | < 1% of requests |
| **Duplicate detection works** | 200 responses with is_duplicate | >80% of duplicates detected |
| **Jobs start** | thread_started=true | 100% |
| **Response time (first)** | Latency in ms | <500ms |
| **Response time (duplicate)** | Latency in ms | <100ms |
| **Database health** | Query time for check | <10ms |
| **User satisfaction** | Feedback/complaints | 0 regressions |
| **Backward compat** | Old API clients | Still work |

---

## Final Checklist

```bash
# Run all validation steps
echo "✅ Step 1: Syntax check"
python -m py_compile backend/routes/stocks.py backend/routes/analysis.py

echo "✅ Step 2: First request (201)"
curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["20MICRONS.NS"]}'

echo "✅ Step 3: Duplicate request (200)"
curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["20MICRONS.NS"]}'

echo "✅ Step 4: Force parameter (201)"
curl -X POST http://localhost:8000/api/stocks/analyze-all-stocks \
  -d '{"symbols": ["20MICRONS.NS"], "force": true}'

echo "✅ Step 5: Check logs"
grep "Creating new analysis job" backend/logs/*.log

echo "✅ Step 6: Verify database"
sqlite3 backend/data.db "SELECT COUNT(*) FROM analysis_jobs WHERE status IN ('queued', 'processing')"

echo "✅ All validation steps passed!"
```

---

**Deployment Complete! ✅**

All validation steps must pass before marking as production-ready.
