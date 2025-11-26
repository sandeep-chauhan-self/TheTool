# Post-Deployment Verification Checklist

## ✅ Pre-Deployment Complete

### Code Changes
- ✅ `backend/routes/stocks.py` - Uses `symbol AS ticker` alias in UNION
- ✅ `backend/routes/watchlist.py` - Queries/inserts using `symbol` column
- ✅ `backend/populate_watchlist.py` - Inserts using `symbol` column
- ✅ `backend/db_migrations.py` - Contains migrations v5 & v6, version = 6
- ✅ All syntax errors cleared
- ✅ Code committed: `9aa11c1`
- ✅ Code pushed to Railway

## ⏳ During/After Deployment

### 1. Monitor Railway Deployment Logs (First 5 minutes)
Watch for these messages:

**Expected Log Entries**:
```
[INFO] Starting Flask app...
[INFO] Database version: 6
[INFO] Running migrations...
[INFO] Current database version: 4 (or 5)
[INFO] Executing migration_v5()...
[INFO] Migration v5 completed
[INFO] Executing migration_v6()...
[INFO] Migration v6 completed
[INFO] Database now at version 6
[INFO] App started successfully
```

**Warning Signs**:
```
[ERROR] Database version mismatch: 6 != 6
[ERROR] Migration v5 failed: ...
[ERROR] column "ticker" does not exist
[ERROR] column "symbol" does not exist
```

### 2. Test Endpoints (After app is healthy)

#### A. Check Watchlist
```bash
curl https://your-railway-app/api/watchlist
```

Expected:
- ✅ Returns list of watchlist items
- ✅ Each item has `id`, `symbol` (not `ticker`), `name`, `created_at`
- ✅ Status 200

#### B. Check Stock Analysis List
```bash
curl https://your-railway-app/api/stocks/analyze-all-stocks
```

Expected:
- ✅ Returns list of all stocks
- ✅ Each stock has `ticker`, `symbol` fields
- ✅ Status 200

#### C. Check Cleanup Job
Monitor logs for cleanup task:
```
[INFO] Cleanup started...
[INFO] Deleted ... old jobs
[INFO] Cleanup completed
```

Expected:
- ✅ No "column 'ticker' does not exist" errors
- ✅ No "column 'symbol' does not exist" errors
- ✅ Cleanup completes successfully

### 3. Database Verification (If You Have Access)

After migrations complete, check database:

#### PostgreSQL
```sql
-- Check column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name='watchlist';

-- Should show: ticker (NOT symbol)
```

#### SQLite
```sql
-- Check schema
PRAGMA table_info(watchlist);

-- Should show: ticker column exists
```

## ⚠️ Troubleshooting

### Issue: "column 'ticker' does not exist"

**Root Cause**: Migration v5 didn't run

**Solution**:
1. Check logs for migration v5 error
2. Verify `CURRENT_SCHEMA_VERSION = 6` in code
3. Check database: `SELECT version FROM db_version`
4. If stuck at 4-5: Contact support or run migration manually

### Issue: "column 'symbol' does not exist"

**Root Cause**: Code is trying to use renamed column too early

**Solution**:
1. Wait for migration v5 to complete
2. Check logs for "Migration v5 completed"
3. Restart app
4. Retry endpoint

### Issue: 500 Error on `/api/watchlist`

**Root Cause**: Query syntax error or schema mismatch

**Solution**:
1. Check logs for exact error
2. Verify migrations completed
3. Check database schema: `SELECT * FROM watchlist LIMIT 1`
4. Verify response has correct column names

## 📊 Success Metrics

### After 5 Minutes
- ✅ App is running
- ✅ No startup errors
- ✅ Migrations logged as completed

### After 1 Hour
- ✅ Watchlist endpoints working
- ✅ Stock analysis lists populated
- ✅ No "column doesn't exist" errors in logs

### After 24 Hours
- ✅ Cleanup job completed successfully
- ✅ No recurring column errors
- ✅ All endpoints stable

## 📝 Notes

- **Migrations are idempotent**: Safe to run multiple times
- **No data loss**: Column rename preserves all data
- **Backward compatible**: Alias approach works during transition
- **No manual intervention needed**: Automatic on app startup

## 🎯 Final Status

| Component | Status | Notes |
|-----------|--------|-------|
| Code changes | ✅ Deployed | Aliases + migrations in place |
| Migrations v5 & v6 | ✅ Ready | Will execute on startup |
| Watchlist schema | ⏳ Pending | symbol → ticker rename on next deploy |
| Cleanup automation | ✅ Active | GitHub Actions running daily |
| Index issue | ✅ Resolved | Indexes removed from production |

---

**Deployment Date**: 2025-01-XX  
**Expected Migration Time**: 1-5 minutes after app restart  
**Estimated Full Resolution**: 1 hour  

Once verified, you can optionally clean up the temporary aliases and update code to use `ticker` directly everywhere.
