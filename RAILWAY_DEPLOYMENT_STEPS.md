🚀 RAILWAY DEPLOYMENT - Step by Step

You are logged in as: scst1011@gmail.com
Project: empathetic-alignment
Environment: production
Service: TheTool

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 1: Push Code to GitHub (5 minutes)

From: C:\Users\scst1\2025\TheTool

```powershell
# Add all changes
git add -A

# Commit with message
git commit -m "Fix: Jobs stuck in queued state + PostgreSQL migration + database schema hardening"

# Push to main branch
git push origin main
```

Expected output:
```
[main 12345ab] Fix: Jobs stuck in queued state...
 3 files changed, 250 insertions(+)
 create mode 100644 backend/migrations_add_constraints_postgres.py
 Updating 12345ab..67890cd
 Fast-forward
  backend/migrations_add_constraints.py | 50 ++++++++++
  ...
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 2: Watch Railway Auto-Deploy (3-5 minutes)

Railway automatically deploys when you push to main. Watch progress:

```powershell
# Option A: Watch in Railway CLI
railway status

# Option B: View logs live
railway logs
```

Wait for message like:
```
✓ Deployment successful
App running at: https://thetool-production-XXXX.railway.app
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 3: Run Database Migration (2 minutes)

Once app is running on Railway:

```powershell
# Run migration on Railway's PostgreSQL
railway run python backend/migrations_add_constraints.py
```

Expected output:
```
============================================================
Database Migration: Add Constraints & Indices
Database Type: postgres
============================================================

[PostgreSQL] Adding constraints and indices...
[1/10] Adding UNIQUE INDEX on analysis_results...
  ✓ Index created
[2/10] Adding INDEX on analysis_results(symbol)...
  ✓ Index created
...
[10/10] Adding composite indices...
  ✓ Composite index created

✅ PostgreSQL migration completed successfully!
```

If you see errors about columns already existing - that's OK! It means:
```
⚠ Columns may already exist: column "job_id" of relation "analysis_results" already exists
```

This is normal on re-runs. All indices and columns were successfully created.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 4: Verify Job Execution Works (3 minutes)

Get your Railway app URL from logs, then test:

```powershell
# Get your app URL
$url = railway logs | grep "App running at" | tail -1

# Test creating a job
$response = Invoke-WebRequest -Uri "$url/api/stocks/analyze-all-stocks" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"symbols": ["TCS.NS"]}'

$response.Content | ConvertFrom-Json
```

Expected response:
```json
{
  "thread_started": true,
  "job_id": "12345678-1234-1234-1234-123456789012",
  "message": "Analysis started in background"
}
```

Then check job progress:

```powershell
$progressUrl = "$url/api/all-stocks/progress"
$progress = Invoke-WebRequest -Uri $progressUrl | ConvertFrom-Json
$progress
```

Expected response (should change from "queued" to "processing"):
```json
{
  "status": "processing",      ← Should be "processing" NOT "queued"
  "progress_percent": 45,       ← Should be > 0, not stuck at 0
  "completed": 0,
  "total": 1
}
```

✅ If status shows "processing" and progress > 0: JOB IS WORKING!
❌ If status shows "queued" and progress = 0: Still stuck (check logs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 5: Monitor Logs for Issues (Live monitoring)

```powershell
# Watch live logs
railway logs -f

# Look for:
✓ No "database is locked" errors
✓ Job status transitions: queued → processing → completed
✓ Progress updates: 0% → 25% → 50% → 75% → 100%
```

If you see errors, check:
- DATABASE_URL is set (Railway auto-sets this)
- psycopg2 is installed (in requirements.txt)
- PostgreSQL server is running (Railway manages this)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Complete Timeline

| Step | Action | Time | Status |
|------|--------|------|--------|
| 1 | Push to GitHub | 1 min | Do this first ⬇️ |
| 2 | Railway auto-deploys | 3-5 min | Wait for ✓ |
| 3 | Run migration | 2 min | Do this after ✓ |
| 4 | Test job | 3 min | Verify it works |
| 5 | Monitor logs | 24h+ | Watch for issues |

**Total Time: ~15 minutes to deployment**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Troubleshooting

**If migration fails with "psycopg2 not found":**
```powershell
# psycopg2 needs to be in requirements.txt
# Add to backend/requirements.txt if missing:
# psycopg2-binary>=2.9.0
```

**If job still stuck at "queued":**
```powershell
# Check app logs
railway logs

# Look for errors in:
# - thread_tasks.py
# - database.py
# - Status update failures
```

**If you need to rollback:**
```powershell
# Revert last commit
git revert HEAD
git push origin main
# Railway auto-deploys the previous version
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✅ Success Criteria

Your deployment is successful when:

✅ Code pushed to GitHub
✅ Railway auto-deployed (check via `railway status`)
✅ Migration ran without critical errors
✅ New job transitions to "processing" within 5 seconds
✅ Progress updates from 0% to 100%
✅ Results appear in database
✅ No "database is locked" errors in logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: ✅ READY TO DEPLOY

You are already logged into Railway and linked to your project.
Follow the steps above to deploy the fixes to production.
