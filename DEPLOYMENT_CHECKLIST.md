# Pre-Deployment & Deployment Checklist

## ✅ Pre-Deployment Phase (Before Merging)

### Code Review
- [ ] Backend changes reviewed in `backend/routes/stocks.py`
- [ ] Backend changes reviewed in `backend/routes/analysis.py`
- [ ] Frontend changes reviewed in `frontend/src/pages/AllStocksAnalysis.js`
- [ ] Code follows project style guide
- [ ] No console.logs or debug code left
- [ ] No commented-out code blocks
- [ ] Error handling is comprehensive
- [ ] Comments explain non-obvious logic

### Testing (Local)
- [ ] Syntax check passes: `python -m py_compile backend/routes/stocks.py backend/routes/analysis.py`
- [ ] Import check passes: `python -c "from routes.stocks import analyze_all_stocks"`
- [ ] Test suite runs: `python test_duplicate_fix.py`
- [ ] All 6 tests pass (see test_duplicate_fix.py)
- [ ] No import errors
- [ ] No runtime exceptions
- [ ] No deprecation warnings

### Documentation Review
- [ ] FIX_SUMMARY.md reviewed
- [ ] DUPLICATE_JOB_FIX_SUMMARY.md reviewed
- [ ] DUPLICATE_JOB_FIX.md reviewed (technical)
- [ ] DEPLOYMENT_DUPLICATE_FIX.md reviewed
- [ ] VALIDATION_STEPS.md reviewed
- [ ] DUPLICATE_JOB_FIX_INDEX.md reviewed
- [ ] All code examples are correct
- [ ] All curl commands are tested
- [ ] Documentation is clear and complete

### Approval Gates
- [ ] ✅ Code reviewed and approved
- [ ] ✅ Product owner approved
- [ ] ✅ QA lead approved
- [ ] ✅ DevOps approved
- [ ] ✅ Architecture reviewed (no breaking changes)

### Git Preparation
- [ ] Code committed with clear message
- [ ] All changes staged: `git status` shows clean index
- [ ] No uncommitted changes: `git diff` is empty
- [ ] Branch is up to date with main
- [ ] No merge conflicts

---

## 🚀 Deployment Phase (Executing the Deploy)

### Pre-Deploy Verification
- [ ] Backend server is NOT running locally (to avoid conflicts)
- [ ] Database backups taken (if applicable)
- [ ] Monitoring dashboard is open and ready
- [ ] Team is on standby
- [ ] Runbook is available and read

### Execute Deployment

#### Step 1: Push to Main
```bash
git push origin main
# Expected: "remote: [success] Build triggered on Railway"
# or similar
```
- [ ] Git push succeeded
- [ ] No merge conflicts
- [ ] GitHub shows commit on main branch

#### Step 2: Monitor Railway Build (Backend)
```bash
# Check Railway dashboard
# or: railway logs
```
- [ ] Build started automatically
- [ ] Build logs show no errors
- [ ] Build completed successfully
- [ ] Deployment to production started
- [ ] Application restarted
- [ ] Logs show "Application started"

#### Step 3: Monitor Vercel Build (Frontend)
```bash
# Check Vercel dashboard
# or check git commit status
```
- [ ] Build started automatically
- [ ] Build completed successfully
- [ ] Deployment to production started
- [ ] Site is accessible

#### Step 4: Quick Smoke Test
```bash
# Verify backend is responding
curl -s https://thetool-production.up.railway.app/health | jq .
```
- [ ] Backend responds to health check
- [ ] Status code is 200
- [ ] Response is valid JSON

---

## 🧪 Post-Deployment Validation (First Hour)

### Test 1: Basic Functionality
```bash
# Test 1a: First request (should return 201)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["20MICRONS.NS"]}'
# Expected: 201, job_id present, thread_started: true
```
- [ ] Status code is 201 (not 409)
- [ ] job_id is present and valid UUID
- [ ] thread_started is true
- [ ] Response time < 500ms
- [ ] No error messages

```bash
# Test 1b: Duplicate request (should return 200)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["20MICRONS.NS"]}'
# Expected: 200, is_duplicate: true, same job_id
```
- [ ] Status code is 200 (not 409)
- [ ] is_duplicate is true
- [ ] job_id matches first request
- [ ] status shows "processing" or "queued"
- [ ] Response time < 100ms

```bash
# Test 1c: Force parameter (should return 201 with new job)
curl -X POST https://thetool-production.up.railway.app/api/stocks/analyze-all-stocks \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["20MICRONS.NS"], "force": true}'
# Expected: 201, new job_id (different from previous)
```
- [ ] Status code is 201
- [ ] job_id is different from first test
- [ ] thread_started is true

### Test 2: Check Logs
```bash
# Backend logs
railway logs --follow

# Look for:
# ✓ "Creating new analysis job {job_id} for N symbols"
# ✓ "Found active job {job_id} with status processing"
# ✓ "Duplicate detected. Returning existing job {job_id}"
# ✓ "Started background thread for job {job_id}"
```
- [ ] See "Creating new analysis job" messages
- [ ] See "Duplicate detected" messages
- [ ] See "Started background thread" messages
- [ ] No error messages related to job creation
- [ ] No stack traces

### Test 3: Frontend UI Test
1. Go to https://the-tool-theta.vercel.app/
2. Navigate to "All Stocks Analysis"
3. Click "Analyze All Stocks" button
   - [ ] No error modal appears
   - [ ] Browser console has no errors
   - [ ] Alert shows: "Analysis started. Job ID: [uuid]"
4. Immediately click again
   - [ ] Alert shows helpful duplicate message
   - [ ] No error modal appears
   - [ ] Shows progress: "X/Y"

### Test 4: Database Check
```bash
# Connect to production database
psql -h $RAILWAY_POSTGRES_HOST -U $RAILWAY_POSTGRES_USER -d $RAILWAY_POSTGRES_DB

# Query active jobs
SELECT job_id, status, total, completed, created_at 
FROM analysis_jobs 
WHERE status IN ('queued', 'processing') 
ORDER BY created_at DESC 
LIMIT 5;

# Expected: See recent jobs with status queued/processing
```
- [ ] Can connect to database
- [ ] analysis_jobs table exists
- [ ] Recent job entries visible
- [ ] Status shows queued/processing
- [ ] created_at timestamps are recent

### Test 5: Status Endpoint
```bash
# Check job status (use job_id from Test 1a)
JOB_ID="550e8400-e29b-41d4-a716-446655440000"
curl https://thetool-production.up.railway.app/api/analysis/status/$JOB_ID \
  -H "X-API-Key: your-key"
# Expected: 200, with job details and progress
```
- [ ] Status code is 200
- [ ] job_id matches request
- [ ] status field is present
- [ ] total/completed fields are numbers
- [ ] progress_percent is calculated

---

## 📊 Post-Deployment Monitoring (24-48 Hours)

### Metrics to Track

#### Error Rates
```bash
# Check 409 error rate (should be near 0)
grep -c '409 Conflict' backend/logs/*.log

# Expected: <1% of requests
# Red flag if: >2% or upward trend
```
- [ ] 409 errors are < 0.1%
- [ ] No upward trend in error rate

#### Success Rates
```bash
# Check successful job creation (should be >99%)
grep -c 'Creating new analysis job' backend/logs/*.log

# Expected: Nearly 100% of requests succeed
# Red flag if: <95%
```
- [ ] Job creation success rate >99%
- [ ] Stable over time

#### Performance
```bash
# Check response times (should be reasonable)
grep 'response_time' backend/logs/*.log | awk '{print $NF}' | sort -n | tail -20

# Expected:
# First request: 100-300ms
# Duplicate request: 20-100ms
# Red flag if: >1000ms
```
- [ ] Response times are reasonable
- [ ] No sudden spikes
- [ ] Duplicate requests are faster than first

#### Database Health
```bash
# Check query performance
SELECT COUNT(*) as job_count FROM analysis_jobs WHERE status IN ('queued', 'processing');

# Expected: Usually 0-5 active jobs (they complete quickly)
# Red flag if: >100 stuck jobs
```
- [ ] Jobs are completing normally
- [ ] No stuck jobs
- [ ] Database is responsive

### Alert Thresholds
Set up alerts for:
- [ ] 409 error rate > 1% 
- [ ] Job creation success rate < 95%
- [ ] Response time > 1000ms
- [ ] Backend downtime
- [ ] Database connection errors

---

## 🔍 Verification Checklist (Sign-Off)

### Before Marking as Complete

#### Functionality
- [ ] ✅ First request returns 201 (not 409)
- [ ] ✅ Duplicate request returns 200 with is_duplicate
- [ ] ✅ Force parameter creates new job
- [ ] ✅ Job status endpoint works
- [ ] ✅ Analyze endpoint works similarly

#### Frontend
- [ ] ✅ No error messages on first request
- [ ] ✅ Helpful message on duplicate request
- [ ] ✅ Job ID is displayed
- [ ] ✅ Progress is shown
- [ ] ✅ No console errors

#### Backend
- [ ] ✅ Logs show success patterns
- [ ] ✅ Thread start messages visible
- [ ] ✅ No error stack traces
- [ ] ✅ Database records created
- [ ] ✅ Job status is accurate

#### Performance
- [ ] ✅ Response times are reasonable
- [ ] ✅ No sudden spikes
- [ ] ✅ Database queries are fast
- [ ] ✅ No CPU/memory issues

#### Reliability
- [ ] ✅ 99%+ job creation success
- [ ] ✅ <0.1% 409 errors
- [ ] ✅ 100% thread start when created
- [ ] ✅ No hung/stuck jobs

#### Documentation
- [ ] ✅ All docs are accurate
- [ ] ✅ Code examples work
- [ ] ✅ Deployment steps are clear
- [ ] ✅ Troubleshooting guide is helpful

---

## ⚠️ If Issues Occur

### Issue: 409 Errors Still Appearing
1. [ ] Check if new code deployed: `curl ... | grep "is_duplicate"`
2. [ ] Check Railway logs for deployment errors
3. [ ] Verify main branch has new code
4. [ ] Manual redeploy if needed: Railway dashboard → Deploy button

### Issue: Jobs Not Starting (thread_started: false)
1. [ ] Check logs for "Failed to start thread"
2. [ ] Check system resources (CPU, memory)
3. [ ] Check Python version compatibility
4. [ ] Verify threading module is available

### Issue: Performance Degradation
1. [ ] Check database query times
2. [ ] Check system resource usage
3. [ ] Verify indices exist on analysis_jobs
4. [ ] Reduce TTL window from 5 to 2 minutes if needed

### Issue: Database Connection Errors
1. [ ] Verify PostgreSQL connection string
2. [ ] Check database is running and accessible
3. [ ] Verify user permissions
4. [ ] Check for connection pool exhaustion

### Issue: Rollback Needed
1. [ ] Execute: `git revert <commit-hash> && git push origin main`
2. [ ] Wait for Railway/Vercel auto-redeployment (5 min)
3. [ ] Verify old behavior restored
4. [ ] Post-incident review

---

## 📝 Sign-Off

### Deployment Successful ✅
- Date: _______________
- Deployed By: _______________
- QA Verified By: _______________
- Approved By: _______________

### Comments
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

### Next Steps
- [ ] Monitor for 24-48 hours
- [ ] Collect metrics and feedback
- [ ] Archive logs
- [ ] Document lessons learned
- [ ] Plan any follow-up work

---

**Checklist Version:** 1.0
**Last Updated:** November 23, 2025
**Status:** Ready for deployment
