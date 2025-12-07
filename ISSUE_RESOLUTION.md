# Issue Resolution Guide

## Issue 1: CORS Error on Development Frontend

**Error:**
```
Access to XMLHttpRequest at 'https://thetool-production.up.railway.app/api/stocks/all' 
from origin 'https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app' 
has been blocked by CORS policy
```

### Root Cause
The production backend (`thetool-production.up.railway.app`) doesn't have the development frontend URL in its CORS whitelist because:
1. The backend code was updated locally with the CORS fix
2. The production backend on Railway hasn't been redeployed yet

### Solutions

#### Option A: Redeploy Production Backend (RECOMMENDED)
1. Go to Railway dashboard
2. Select TheTool production backend
3. Click "Deploy" to redeploy with the latest code (which now includes CORS fix)
4. Wait for deployment to complete (~2 minutes)

#### Option B: Use Environment Variables (IMMEDIATE)
On Railway production backend environment, add:
```
CORS_ORIGINS=https://the-tool-theta.vercel.app,https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app,https://thetool-production.up.railway.app
```

#### Option C: Redirect to Development Backend (FOR TESTING)
Temporarily set on Vercel development frontend:
```
REACT_APP_API_BASE_URL=https://thetool-development.up.railway.app
```

### What Was Fixed
- Updated `backend/config.py` to add development frontend to production CORS whitelist
- Added verbose logging in `frontend/src/api/api.js` to debug routing

---

## Issue 2: Database Duplicate Key Constraint Error

**Error:**
```
ERROR: could not create unique index "idx_analysis_ticker_date_strategy"
DETAIL: Key (ticker, (created_at::date), strategy_id)=(ELGIRUBCO.NS, 2025-11-30, 1) is duplicated.
```

### Root Cause
The `analysis_results` table has duplicate records for the same ticker/date/strategy combination. The migration v8 tries to create a unique constraint but fails because duplicates exist.

### Solution: Run Cleanup Script

1. **Ensure DATABASE_URL is set:**
   ```bash
   echo $env:DATABASE_URL  # Check if set
   ```

2. **Run the cleanup script:**
   ```bash
   cd backend
   python cleanup_duplicates.py
   ```

3. **What it does:**
   - Finds all duplicate (ticker, date, strategy_id) groups
   - Keeps the most recent record (highest ID)
   - Deletes older duplicates
   - Verifies the cleanup

4. **Expected output:**
   ```
   🔍 Analyzing duplicate records...
   📊 Found X groups with duplicates:
      • ELGIRUBCO.NS (2025-11-30) Strategy 1: 2 records
      ...
   🧹 Removing duplicates (keeping most recent per group)...
   ✓ Deleted Y duplicate records
   ✓ Duplicate cleanup verified - database is clean!
   ```

### After Cleanup
The database migration v8 will now succeed on next application startup, creating the unique constraint.

---

## Verification Checklist

- [ ] CORS error resolved (check browser console)
- [ ] API requests succeed from development frontend
- [ ] Database duplicates cleaned up
- [ ] No "duplicate key" errors in logs
- [ ] Can analyze stocks with all strategies (1-5)
- [ ] Strategy 5 shows correct stop loss (3%) and target (4%)

---

## Quick Reference: Environment URLs

| Environment | Frontend | Backend | Status |
|-------------|----------|---------|--------|
| **Local** | `http://localhost:3001` | `http://localhost:5000` | ✓ Working |
| **Development** | `https://the-tool-git-development-*.vercel.app` | `https://thetool-development.up.railway.app` | ✓ Working |
| **Production** | `https://the-tool-theta.vercel.app` | `https://thetool-production.up.railway.app` | ⏳ After redeploy |

