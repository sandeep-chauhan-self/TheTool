# Development → Main Branch Merge Safety Guide

> **Purpose**: Lists all changes in `development` branch with merge safety assessment to prevent breaking production on Railway.

**Generated**: December 2, 2025  
**Source Branch**: `development`  
**Target Branch**: `main` (Production)

---

## Quick Summary

| Category | Safe to Merge | Requires Caution | DO NOT Merge |
|----------|:-------------:|:----------------:|:------------:|
| Feature Enhancements | ✅ 15 | ⚠️ 2 | - |
| Database Changes | ✅ 3 | ⚠️ 1 | ❌ 1 |
| Environment/URL Config | - | - | ❌ 5 |
| Documentation Files | - | - | ❌ 4 |

---

## ❌ DO NOT MERGE - Environment-Specific Changes

These files contain development-specific URLs, settings, or debug configurations that will break production.

### 1. Frontend API Configuration

| File | Change | Reason to Exclude |
|------|--------|-------------------|
| `frontend/src/api/api.js` | Added auto-detection of Vercel preview URLs, changed default environment fallback | **Lines 20-37**: Development hostname detection (`the-tool-git-development`) and fallback changed from `local` to `production` - will confuse production routing |

**Problematic Code Block:**
```javascript
// ❌ Development-specific: Auto-detect from Vercel preview URL
if (hostname.includes('the-tool-git-development')) {
  env = 'development';
}
// ❌ Changed default: 'local' → 'production'
const url = backendUrls[env] || backendUrls.production;
```

**Action Required**: Cherry-pick only the `analyzeStocks()` and `analyzeAllStocks()` function signature changes (config parameter support), NOT the `getApiBaseUrl()` modifications.

---

### 2. Backend Database Configuration

| File | Change | Reason to Exclude |
|------|--------|-------------------|
| `backend/config.py` | Removed SQLite support, made PostgreSQL mandatory | **Production already uses PostgreSQL** - but error messages and validation are development-focused |
| `backend/database.py` | Removed ALL SQLite code, hardcoded PostgreSQL-only | **Critical**: Removes dual-database support that main branch maintains |

**Problematic Changes in `config.py`:**
```python
# ❌ Development-specific: Added Vercel preview URL to CORS
'https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app',

# ❌ Changed error messages assume local PostgreSQL setup
messages.append("  Local: DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_app")
```

**Problematic Changes in `database.py`:**
```python
# ❌ Removed entire _init_sqlite_db() function
# ❌ Removed DATABASE_TYPE conditional logic
# ❌ Removed sqlite3 import and all SQLite-specific code
```

**Action Required**: 
- Keep main's dual SQLite/PostgreSQL support
- Cherry-pick only the schema additions (position_size, risk_reward_ratio, analysis_config columns)
- Cherry-pick only the tickers_json column addition to analysis_jobs

---

### 3. Documentation Files (Development-Only)

| File | Reason to Exclude |
|------|-------------------|
| `VERCEL_ENV_VARS.txt` | Contains development deployment instructions and preview URLs |
| `RAILWAY_DEV_ENV_VARS.txt` | Development Railway service configuration |
| `RAILWAY_PROD_ENV_VARS.txt` | Already exists in production differently configured |
| `DATABASE_FIX_SUMMARY.md` | Development debugging documentation |
| `SQL_PLACEHOLDER_FIX.md` | Development debugging documentation |
| `DEPLOYMENT_CHECKLIST.txt` | May conflict with production checklist |

---

## ⚠️ MERGE WITH CAUTION - Requires Manual Review

### 1. SQL Placeholder Style Changes

| File | Change | Concern |
|------|--------|---------|
| `backend/routes/watchlist.py` | Changed `?` → `%s` in some queries | **Inconsistent**: Some queries use `%s` directly instead of `?` with auto-conversion |
| `backend/infrastructure/thread_tasks.py` | Changed `%s` → `?` placeholders | **Correct direction** but verify consistency |

**Details:**
```python
# watchlist.py - ⚠️ Uses %s directly (PostgreSQL-specific)
"SELECT id FROM watchlist WHERE LOWER(ticker) = LOWER(%s)"  # Line 124
"INSERT INTO watchlist (ticker, name) VALUES (%s, %s)"      # Lines 141-142

# thread_tasks.py - ✅ Correctly uses ? with auto-conversion
"UPDATE analysis_jobs SET status = 'processing', started_at = ? WHERE job_id = ?"
```

**Action Required**: Standardize ALL queries to use `?` placeholder with `_convert_query_params()` before merging.

---

### 2. Watchlist Column Name Change

| File | Change | Concern |
|------|--------|---------|
| `backend/routes/watchlist.py` | Changed column reference `symbol` → `ticker` | **Schema dependency**: Verify main branch schema uses `ticker` column |

**Action Required**: Verify `watchlist` table schema in main branch has `ticker` column, not `symbol`.

---

## ✅ SAFE TO MERGE - Feature Enhancements

### 1. Analysis Configuration System (NEW FEATURE)

| File | Change | Safe? |
|------|--------|:-----:|
| `frontend/src/components/AnalysisConfigModal.js` | **NEW FILE** - Configuration popup for analysis | ✅ |
| `frontend/src/utils/tradingViewUtils.js` | **NEW FILE** - TradingView link utility | ✅ |
| `backend/utils/timezone_util.py` | **NEW FILE** - IST timezone utilities | ✅ |

**Feature Summary**: Adds user-configurable analysis parameters:
- Capital/Investment amount
- Risk management (risk %, position size limit, R:R ratio)
- Data period selection (100d, 200d, 1y, 2y)
- Demo data toggle
- Category weights for scoring
- Individual indicator toggles

---

### 2. Analysis Config Parameter Flow

| File | Change | Safe? |
|------|--------|:-----:|
| `frontend/src/api/api.js` | `analyzeStocks()` and `analyzeAllStocks()` accept config object | ✅ |
| `frontend/src/pages/Dashboard.js` | Added config modal before analysis | ✅ |
| `frontend/src/pages/AllStocksAnalysis.js` | Added config modal before analysis | ✅ |
| `backend/routes/analysis.py` | Accept analysis_config in request body | ✅ |
| `backend/routes/stocks.py` | Accept analysis_config in request body | ✅ |
| `backend/infrastructure/thread_tasks.py` | Pass config to analyze_ticker() | ✅ |
| `backend/utils/compute_score.py` | Accept analysis_config parameter | ✅ |
| `backend/utils/analysis_orchestrator.py` | Process config for risk/position calculations | ✅ |

---

### 3. Database Schema Additions (ADDITIVE ONLY)

| File | Change | Safe? |
|------|--------|:-----:|
| `backend/database.py` | Added columns to `analysis_results` table | ✅ |

**New Columns (PostgreSQL):**
```sql
-- analysis_results table
position_size INTEGER DEFAULT 0
risk_reward_ratio REAL DEFAULT 0
analysis_config TEXT

-- analysis_jobs table
tickers_json TEXT
```

**Safe because**: Uses `ADD COLUMN IF NOT EXISTS` - additive, non-breaking.

---

### 4. IST Timezone Standardization

| File | Change | Safe? |
|------|--------|:-----:|
| `backend/utils/timezone_util.py` | **NEW** - Provides `get_ist_now()`, `get_ist_timestamp()` | ✅ |
| `backend/routes/analysis.py` | Uses IST timestamps | ✅ |
| `backend/routes/stocks.py` | Uses IST timestamps | ✅ |
| `backend/infrastructure/thread_tasks.py` | Uses IST timestamps | ✅ |

---

### 5. Enhanced Analysis Results

| File | Change | Safe? |
|------|--------|:-----:|
| `backend/routes/analysis.py` | Returns `position_size`, `risk_reward_ratio` in responses | ✅ |
| `backend/infrastructure/thread_tasks.py` | Stores `position_size`, `risk_reward_ratio`, `analysis_config` | ✅ |

---

### 6. Trade Parameter Calculations

| File | Change | Safe? |
|------|--------|:-----:|
| `backend/utils/analysis_orchestrator.py` | Configurable stop loss % and target based on risk settings | ✅ |

**New Logic:**
- Stop loss calculated from `risk_percent` config (2x risk = stop %)
- Target calculated from `risk_reward_ratio` config
- Position size considers both risk % and position limit %

---

### 7. NSE Stock List for Bulk Analysis

| File | Change | Safe? |
|------|--------|:-----:|
| `backend/routes/stocks.py` | Empty symbols array loads from `nse_stocks_complete.csv` | ✅ |

**Before**: Empty array queried existing database records  
**After**: Empty array loads all stocks from CSV file

---

### 8. UI Enhancements

| File | Change | Safe? |
|------|--------|:-----:|
| `frontend/src/pages/Dashboard.js` | Added TradingViewLink component | ✅ |
| `frontend/src/pages/AllStocksAnalysis.js` | Added TradingViewLink component | ✅ |
| `frontend/src/pages/Results.js` | (Check diff - likely UI improvements) | ✅ |

---

## 📋 Recommended Merge Strategy

### Step 1: Pre-Merge Preparation

```bash
# Create a merge branch from main
git checkout main
git pull origin main
git checkout -b merge/development-to-main
```

### Step 2: Cherry-Pick Safe Changes

```bash
# Option A: Interactive rebase to select commits
git cherry-pick <commit-hash>  # For each safe feature commit

# Option B: Merge then revert problematic files
git merge development
git checkout main -- frontend/src/api/api.js  # Revert API URL changes
git checkout main -- backend/config.py         # Keep original config
git checkout main -- backend/database.py       # Keep dual DB support
```

### Step 3: Manual File Edits Required

1. **`frontend/src/api/api.js`**:
   - Keep main's `getApiBaseUrl()` function unchanged
   - Merge only the new function signatures for `analyzeStocks()` and `analyzeAllStocks()`

2. **`backend/database.py`**:
   - Keep main's dual SQLite/PostgreSQL support
   - Add only the new schema columns (position_size, risk_reward_ratio, analysis_config, tickers_json)

3. **`backend/config.py`**:
   - Keep main's configuration
   - Do NOT add development-specific CORS URL

4. **`backend/routes/watchlist.py`**:
   - Change all `%s` placeholders back to `?` with `_convert_query_params()`
   - Verify `ticker` vs `symbol` column name matches schema

### Step 4: Delete Development-Only Files

```bash
git rm VERCEL_ENV_VARS.txt
git rm RAILWAY_DEV_ENV_VARS.txt
git rm RAILWAY_PROD_ENV_VARS.txt
git rm DATABASE_FIX_SUMMARY.md
git rm SQL_PLACEHOLDER_FIX.md
```

### Step 5: Test Before Push

```bash
# Run backend tests
cd backend
python test_comprehensive_scenarios.py
python test_backend_api.py

# Verify production config
python -c "from config import config; config.print_config()"
```

---

## 📊 Change Summary Table

| Change Type | Files | Merge Action |
|-------------|-------|--------------|
| **New Components** | `AnalysisConfigModal.js`, `tradingViewUtils.js`, `timezone_util.py` | ✅ Copy directly |
| **API Function Signatures** | `api.js` (partial) | ⚠️ Cherry-pick functions only |
| **Route Handlers** | `analysis.py`, `stocks.py` | ✅ Merge with review |
| **Analysis Logic** | `analysis_orchestrator.py`, `compute_score.py` | ✅ Merge |
| **Thread Tasks** | `thread_tasks.py` | ✅ Merge (verify placeholders) |
| **Database Schema** | `database.py` (partial) | ⚠️ Add columns only, keep dual-DB |
| **Config** | `config.py` | ❌ Do not merge |
| **Watchlist Routes** | `watchlist.py` | ⚠️ Fix placeholders first |
| **Documentation** | Various `.txt`, `.md` | ❌ Do not merge |

---

## ⚡ Quick Reference: Files by Merge Safety

### ✅ Safe - Merge Directly
```
frontend/src/components/AnalysisConfigModal.js    (NEW)
frontend/src/utils/tradingViewUtils.js            (NEW)
backend/utils/timezone_util.py                    (NEW)
backend/utils/compute_score.py
backend/utils/analysis_orchestrator.py
frontend/src/pages/Dashboard.js
frontend/src/pages/AllStocksAnalysis.js
frontend/src/pages/Results.js
```

### ⚠️ Caution - Partial Merge Required
```
frontend/src/api/api.js                           (functions only, not getApiBaseUrl)
backend/database.py                               (schema additions only)
backend/routes/analysis.py                        (review IST imports)
backend/routes/stocks.py                          (review IST imports)
backend/routes/watchlist.py                       (fix placeholders)
backend/infrastructure/thread_tasks.py            (verify placeholders)
backend/utils/db_utils.py                         (minor changes)
```

### ❌ Do Not Merge
```
backend/config.py
VERCEL_ENV_VARS.txt
RAILWAY_DEV_ENV_VARS.txt
RAILWAY_PROD_ENV_VARS.txt
DATABASE_FIX_SUMMARY.md
SQL_PLACEHOLDER_FIX.md
DEPLOYMENT_CHECKLIST.txt
```

---

**Last Updated**: December 2, 2025
