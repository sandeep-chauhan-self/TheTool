🚀 VERIFICATION CHECKLIST - Run This to Confirm Everything Works

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Step 1: Verify App is Running

```powershell
railway status
```

Expected output:
```
Project: empathetic-alignment
Environment: production
Service: TheTool
```

## Step 2: Check Recent Logs for Migration

```powershell
railway logs --service TheTool -n 30 | Select-Object -Last 15
```

Look for these lines (in order):
```
PostgreSQL database schema initialized successfully
[OK] Database initialized on startup (POSTGRES)
[OK] Database migrations completed    ← Migration v3 ran here
Application created - Environment: production
Database: postgres
```

If you see "[OK] Database migrations completed" → ✅ MIGRATION SUCCESSFUL

## Step 3: Test Job Creation

Get your app URL first:
```powershell
$appUrl = "https://thetool-production.up.railway.app"
```

Create a test job:
```powershell
$response = Invoke-WebRequest -Uri "$appUrl/api/stocks/analyze-all-stocks" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"symbols": ["INFY.NS"]}' `
  -SkipHttpErrorCheck

$jobData = $response.Content | ConvertFrom-Json
$jobData
```

Expected response:
```json
{
  "thread_started": true,
  "job_id": "12345678-1234-1234-1234-123456789012",
  "message": "Analysis started in background"
}
```

## Step 4: Check Job Status (CRITICAL TEST)

Wait 5 seconds, then:
```powershell
$progressUrl = "$appUrl/api/all-stocks/progress"
$progress = Invoke-WebRequest -Uri $progressUrl | ConvertFrom-Json
$progress
```

Expected response:
```json
{
  "status": "processing",      ← ✅ Should be "processing" NOT "queued"
  "progress_percent": 45,       ← ✅ Should be > 0, NOT stuck at 0
  "completed": 0,
  "total": 1
}
```

✅ SUCCESS if:
- status = "processing" (not "queued")
- progress_percent > 0 (not 0)
- Progress changes on subsequent checks

❌ FAILURE if:
- status = "queued"
- progress_percent = 0
- Status never changes

## Step 5: Monitor for Errors

```powershell
# Check for database lock errors
railway logs --service TheTool | Select-String "database is locked"

# Should return: (no matches) ✅

# Check for any errors
railway logs --service TheTool | Select-String "ERROR|FAILED" | Select-Object -First 5
```

Expected: No recent errors (old cached errors are OK)

## Step 6: Verify Database Structures

If you have PostgreSQL client installed:
```bash
psql $DATABASE_URL -c "SELECT MAX(version) FROM db_version;"
```

Expected: 3

Or use Railway's PostgreSQL UI:
```
1. Go to Railway dashboard
2. Select "empathetic-alignment" project
3. Select "Postgres" service
4. Look for database console/UI
5. Run query: SELECT MAX(version) FROM db_version;
6. Expected result: 3
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Complete Verification Script

Save as `verify_deployment.ps1` and run:

```powershell
#!/usr/bin/env pwsh

Write-Host "🔍 Verifying Database Migration Deployment" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Step 1: Check service status
Write-Host "`n[1] Checking Railway service status..." -ForegroundColor Yellow
$status = railway status
if ($status -match "TheTool") {
    Write-Host "  ✅ Service: TheTool" -ForegroundColor Green
} else {
    Write-Host "  ❌ Service not found" -ForegroundColor Red
    exit 1
}

# Step 2: Check logs for migration
Write-Host "`n[2] Checking logs for migration v3..." -ForegroundColor Yellow
$logs = railway logs --service TheTool -n 50
if ($logs -match "Database migrations completed") {
    Write-Host "  ✅ Migration v3 completed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Migration may not have run yet" -ForegroundColor Yellow
}

# Step 3: Test API
Write-Host "`n[3] Testing API endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://thetool-production.up.railway.app/api/all-stocks/progress" `
        -Method GET `
        -SkipHttpErrorCheck
    
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ API responding" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "    Status: $($data.status)" -ForegroundColor Green
        Write-Host "    Progress: $($data.progress_percent)%" -ForegroundColor Green
    } else {
        Write-Host "  ❌ API error: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ API unreachable: $_" -ForegroundColor Red
}

# Step 4: Check for errors
Write-Host "`n[4] Checking for errors in logs..." -ForegroundColor Yellow
$errors = railway logs --service TheTool -n 100 | Select-String "ERROR|FAILED"
if ($errors.Count -eq 0) {
    Write-Host "  ✅ No recent errors" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Found $($errors.Count) error lines" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Verification Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
```

## Troubleshooting

**If migration didn't run:**
- Check: `railway logs | grep "migration"`
- If no output, app may not have redeployed yet
- Wait 5 minutes and check again
- If still no migration, manually run: `railway run python backend/migrations_add_constraints.py`

**If jobs still stuck at "queued":**
- Check: `railway logs | grep "ERROR"`
- Look for "database is locked" errors
- Check thread_tasks.py retry logic is working
- Create new test job after fixing and retry

**If database connection fails:**
- Check DATABASE_URL is set: `railway env`
- Should show: `DATABASE_URL=postgresql://...`
- If missing, Railway may be misconfigured

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Success Criteria

✅ ALL of these must be true:

1. ✅ App deployed to Railway (Status shows TheTool)
2. ✅ Logs show "Database migrations completed"
3. ✅ API responds with 200 status
4. ✅ Job status changes to "processing" within 5 seconds
5. ✅ Progress goes from 0% to >0%
6. ✅ No "database is locked" errors
7. ✅ Migration version shows 3 in database

If all ✅, the deployment is complete and working!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
