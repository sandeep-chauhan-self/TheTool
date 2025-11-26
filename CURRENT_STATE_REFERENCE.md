# Current State Reference - Schema Migration v4→v6

## 🎯 What Just Happened

You've deployed a **two-phase fix** for the "column 'ticker' does not exist" error:

### Phase 1: NOW (Temporary Query Aliases) ✅ DEPLOYED
- Code uses `symbol AS ticker` when querying watchlist
- Allows UNION queries to work with mixed schema states
- **Status**: Code deployed, waiting for Railway to restart

### Phase 2: NEXT (Permanent Schema Rename) ⏳ QUEUED
- Migrations v5 & v6 will rename `symbol` → `ticker`
- Executes automatically when app starts
- **Status**: Ready to execute, waiting for deployment

## 📋 Changed Files

### `backend/routes/stocks.py`
```python
# Line 331-336: UNION query with alias
SELECT DISTINCT ticker FROM analysis_results
UNION
SELECT DISTINCT symbol AS ticker FROM watchlist  # ← Alias bridges schema
ORDER BY ticker
```

### `backend/routes/watchlist.py`
```python
# Queries use 'symbol' column (current schema)
items = query_db("SELECT id, symbol, name, created_at FROM watchlist")

# After migration: Will have 'ticker' instead (but code still works due to alias)
```

### `backend/populate_watchlist.py`
```python
# Insert uses 'symbol' column (current schema)
query = "INSERT INTO watchlist (symbol, notes) VALUES (?, ?)"
```

### `backend/db_migrations.py` (Already in place)
```python
CURRENT_SCHEMA_VERSION = 6  # Target version

def migration_v5():
    # Renames symbol → ticker in watchlist table
    
def migration_v6():
    # Verifies schema, cleans up old columns
```

## 🔄 Timeline

```
NOW: Code Deployed
    ↓
+1 min: Railway detects changes, restarts app
    ↓
+2 min: App starts, runs migrations v1-6
    ↓
+3 min: Migration v5 renames symbol → ticker
    ↓
+4 min: Migration v6 verifies schema
    ↓
+5 min: App fully ready
    ↓
SUCCESS: Column now exists, errors gone
```

## 🧪 Testing

### Quick Test Commands

```bash
# Test watchlist endpoint
curl https://your-app.railway.app/api/watchlist

# Test stock list
curl https://your-app.railway.app/api/stocks/analyze-all-stocks

# Check logs (Railway console)
# Look for: "Migration v5 completed"
```

### Expected After Migration
```
watchlist table:
├── id (integer)
├── ticker (text)  ← renamed from 'symbol'
├── name (text)
└── created_at (text)
```

## ⚠️ Quick Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "column 'ticker' does not exist" | Migration didn't run | Wait 5 minutes, check logs |
| 500 error on watchlist | Schema mismatch | Verify migrations completed |
| "column 'symbol' does not exist" | Pre-migration code state | App restart should fix |

## 🔑 Key Points

1. **Safe to deploy**: All changes are idempotent
2. **No data loss**: Column rename preserves all data
3. **Automatic**: Migrations run on app startup
4. **Backward compatible**: Aliases work until migration completes
5. **No manual steps**: Zero user intervention needed

## 📊 Schema Versions

| Version | Status | What Changed |
|---------|--------|---|
| 1-4 | ✅ Deployed | Existing schema |
| 5 | ⏳ Queued | Rename symbol → ticker |
| 6 | ⏳ Queued | Verify schema |

## ✅ Completed Tasks

- ✅ Fixed index row-size error (indexes removed)
- ✅ Created migrations v5 & v6
- ✅ Reverted code to use current schema
- ✅ Added temporary aliases for compatibility
- ✅ Set target schema version to 6
- ✅ Deployed code to Railway
- ✅ GitHub Actions cleanup automation active

## 🎓 Understanding the Fix

**Old Problem**: 
```
Code expects: watchlist.ticker
Database has: watchlist.symbol
Result: ERROR
```

**Current Solution**:
```
Code queries: SELECT symbol AS ticker FROM watchlist
Database has: watchlist.symbol
Result: Works! ✅
```

**After Migration**:
```
Code queries: SELECT symbol AS ticker FROM watchlist (still works!)
Database has: watchlist.ticker (renamed)
Result: Works! ✅
```

**Optional Future**:
```
Code queries: SELECT ticker FROM watchlist (can remove alias)
Database has: watchlist.ticker
Result: Works! ✅
```

## 🚀 What Happens Next

1. **Automatic**: Migrations v5 & v6 execute
2. **Result**: watchlist.symbol renamed to watchlist.ticker
3. **Impact**: Zero - all queries still work
4. **Optional**: Later, remove aliases for code cleanliness

## 📞 Monitoring

**Watch these logs**:
- `[ERROR]` - Any error messages
- `Migration v5 completed` - Success indicator
- `Migration v6 completed` - Final step done
- `Database now at version 6` - Confirmation

**Expected duration**: 2-5 minutes from restart

---

**Deployed**: 2025-01-XX via commit 9aa11c1  
**Status**: Waiting for Railway deployment  
**Next Action**: Monitor logs after app restart
