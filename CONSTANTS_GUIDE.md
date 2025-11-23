# TheTool Centralized Configuration & Constants Guide

**Version:** 1.0  
**Date:** 2025-11-23  
**FOLLOW:** TheTool.prompt.md Sections 2.1, 2.6, 10  

---

## Executive Summary

This document explains the **centralized constants module** (`backend/constants.py`) that eliminates hardcoded URLs and configuration values throughout the TheTool codebase.

**Problem Solved:**
- Previously: Hardcoded `http://localhost:5000` URLs scattered across 15+ files
- Result: Switching environments required manual edits to every file
- Risk: Production deployments using localhost URLs; staging URLs in production

**Solution:**
- Single source of truth for all URLs, environment configs, API endpoints
- Environment-aware defaults (development → localhost; production → Railway URLs)
- Easy switching via `FLASK_ENV` variable or explicit env vars

---

## Quick Start

### For Backend Development

```python
from constants import get_api_base_url, API_URLS

# Get current environment's API base URL
base_url = get_api_base_url()  # → http://localhost:5000 (dev) or https://... (prod)

# Build endpoint URLs
status_url = f"{base_url}{API_URLS.get_status(job_id)}"
history_url = f"{base_url}{API_URLS.get_history(ticker)}"
```

### For Testing

```python
from constants import get_api_base_url, API_URLS

BASE_URL = get_api_base_url()

response = requests.post(
    f'{BASE_URL}{API_URLS.ANALYZE}',
    json={'tickers': ['INFY.NS'], 'capital': 100000}
)
```

### For Frontend (.env files)

```bash
# .env.development
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_API_KEY=development-key

# .env.production
REACT_APP_API_BASE_URL=https://thetool-production.up.railway.app
REACT_APP_API_KEY=your-production-key
```

---

## Environment Configurations

### Development (Local)

```python
ENVIRONMENTS.DEVELOPMENT = {
    "backend_url": "http://localhost:5000",
    "frontend_url": "http://localhost:3000",
    "redis_url": "redis://localhost:6379/0",
    "is_secure": False,
}
```

**Activation:** Default or `FLASK_ENV=development`

### Staging

```python
ENVIRONMENTS.STAGING = {
    "backend_url": "https://thetool-staging.up.railway.app",
    "frontend_url": "https://thetool-staging.vercel.app",
    "redis_url": "redis://staging-redis.railway.app:6379/0",
    "is_secure": True,
}
```

**Activation:** `FLASK_ENV=staging`

### Production

```python
ENVIRONMENTS.PRODUCTION = {
    "backend_url": "https://thetool-production.up.railway.app",
    "frontend_url": "https://the-tool-theta.vercel.app",
    "redis_url": "redis://production-redis.railway.app:6379/0",
    "is_secure": True,
}
```

**Activation:** `FLASK_ENV=production`

---

## API Endpoints Reference

All endpoints are centralized in the `API_URLS` class. Use these instead of hardcoding strings.

### Root Endpoints

```python
API_URLS.HEALTH_CHECK      # "/health"
API_URLS.CONFIG            # "/config"
API_URLS.INFO              # "/"
```

### Analysis Endpoints

```python
API_URLS.ANALYZE           # "/api/analysis/analyze"
API_URLS.ANALYSIS_STATUS   # "/api/analysis/status"
API_URLS.ANALYSIS_REPORT   # "/api/analysis/report"
API_URLS.ANALYSIS_HISTORY  # "/api/analysis/history"
API_URLS.ANALYSIS_CANCEL   # "/api/analysis/cancel"
API_URLS.ANALYSIS_JOBS     # "/api/analysis/jobs"

# Dynamic endpoints (with placeholders)
API_URLS.get_status(job_id)         # "/api/analysis/status/{job_id}"
API_URLS.get_report(ticker)         # "/api/analysis/report/{ticker}"
API_URLS.get_history(ticker)        # "/api/analysis/history/{ticker}"
API_URLS.get_cancel(job_id)         # "/api/analysis/cancel/{job_id}"
```

### Stock Endpoints

```python
API_URLS.STOCKS_NSE                 # "/api/stocks/nse"
API_URLS.STOCKS_ALL                 # "/api/stocks/all-stocks"
API_URLS.STOCKS_INITIALIZE_ALL      # "/api/stocks/initialize-all-stocks"
API_URLS.STOCKS_ANALYZE_ALL         # "/api/stocks/analyze-all-stocks"
API_URLS.STOCKS_PROGRESS            # "/api/stocks/all-stocks/progress"

# Dynamic
API_URLS.get_stock_history(symbol)  # "/api/stocks/all-stocks/{symbol}/history"
```

### Watchlist Endpoints

```python
API_URLS.WATCHLIST                  # "/api/watchlist"
```

---

## CORS Configuration

### Default Allowed Origins by Environment

**Development:**
```python
CORS_CONFIG.DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",
    "http://192.168.57.1:3000",
    "http://localhost:5000",
]
```

**Production:**
```python
CORS_CONFIG.PRODUCTION_ORIGINS = [
    "https://the-tool-theta.vercel.app",       # Frontend
    "https://thetool-production.up.railway.app",  # Backend
]
```

### Override CORS Origins

Add to `.env`:
```bash
CORS_ORIGINS=https://my-frontend.com,https://my-other-frontend.com
```

Access in code:
```python
from constants import CORS_CONFIG

origins = CORS_CONFIG.get_allowed_origins()
```

---

## Redis Configuration

### Get Current Redis URL

```python
from constants import REDIS_CONFIG, get_redis_url

# Get full Redis URL (Railway format or local)
url = get_redis_url()  # "redis://localhost:6379/0" or "redis://..."

# Individual components
host = REDIS_CONFIG.get_host()  # "localhost"
port = REDIS_CONFIG.get_port()  # 6379
```

### Override Redis URL

Add to `.env`:
```bash
REDIS_URL=redis://your-redis-server:6379/0
```

Or use individual components:
```bash
REDIS_HOST=your-redis-server
REDIS_PORT=6379
REDIS_DB=0
```

---

## Database Configuration

```python
from constants import DATABASE_CONFIG

db_url = DATABASE_CONFIG.get_database_url()
# "sqlite:///./data/trading_app.db" (local)
# "postgresql+psycopg://..." (Railway)
```

### Use PostgreSQL on Railway

Add to `.env`:
```bash
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
```

---

## How Files Were Updated

### ✅ Backend Configuration

**`backend/constants.py`** (NEW)
- Central hub for all constants
- 500+ lines of well-documented configuration
- Supports development, staging, production environments

**`backend/config.py`** (UPDATED)
- Now imports and uses CORS_CONFIG, REDIS_CONFIG
- Delegates URL resolution to centralized module
- Much cleaner, no duplication

**`backend/.env.example`** (UPDATED)
- Comprehensive template with all supported variables
- Inline documentation for each setting
- Shows dev vs prod examples

### ✅ Frontend Configuration

**`frontend/.env.example`** (UPDATED)
- Environment-specific examples
- Clear comments for development, staging, production
- Documents REACT_APP_* variables

### ✅ Test Files Updated

All backend test files now use centralized constants:

- `backend/test_fix.py` → Uses `get_api_base_url()` and `API_URLS`
- `backend/test_backend_api.py` → Uses centralized constants
- `backend/test_unified_integration.py` → Uses centralized constants
- `backend/verify_integration.py` → Uses centralized constants
- `backend/check_results.py` → Uses centralized constants

**Before:**
```python
response = requests.post('http://localhost:5000/analyze', ...)
```

**After:**
```python
response = requests.post(f'{get_api_base_url()}{API_URLS.ANALYZE}', ...)
```

---

## Environment Variable Precedence

Priority (highest to lowest):

1. **Explicit override env vars** (e.g., `BACKEND_URL`, `CORS_ORIGINS`, `REDIS_URL`)
2. **Environment-based defaults** (DEVELOPMENT, STAGING, PRODUCTION)
3. **Fallback constants** (localhost, default ports)

Example resolution chain:

```python
# For get_api_base_url():
1. Is BACKEND_URL set? Use it
2. Is FLASK_ENV=production? Use PRODUCTION.backend_url
3. Is FLASK_ENV=staging? Use STAGING.backend_url
4. Else use DEVELOPMENT.backend_url
```

---

## Production Deployment Checklist

When deploying to production (Railway):

### Backend (.env on Railway)

```bash
FLASK_ENV=production
MASTER_API_KEY=your-secure-key
CORS_ORIGINS=https://the-tool-theta.vercel.app,https://thetool-production.up.railway.app
DATABASE_URL=postgresql+psycopg://... (from Railway)
REDIS_URL=redis://... (from Railway)
```

### Frontend (.env on Vercel)

```bash
REACT_APP_ENV=production
REACT_APP_API_BASE_URL=https://thetool-production.up.railway.app
REACT_APP_API_KEY=your-production-key
```

### Verification

```bash
# Test that constants are loaded correctly
cd backend
python -c "from constants import print_config_summary; print_config_summary()"
```

Expected output in production:
```
Environment: production
Backend URL: https://thetool-production.up.railway.app
Frontend URL: https://the-tool-theta.vercel.app
Redis URL: redis://...
CORS Allowed Origins:
  - https://the-tool-theta.vercel.app
  - https://thetool-production.up.railway.app
```

---

## Adding New Endpoints

When adding new API endpoints:

1. **Define constant in `backend/constants.py`:**
   ```python
   class API_URLS:
       NEW_FEATURE_BASE = "/api/new-feature"
       NEW_FEATURE_ENDPOINT = f"{NEW_FEATURE_BASE}/endpoint"
   ```

2. **Use in tests/code:**
   ```python
   from constants import API_URLS
   url = f"{BASE_URL}{API_URLS.NEW_FEATURE_ENDPOINT}"
   ```

3. **Never hardcode:**
   ```python
   # ❌ BAD
   url = f"{BASE_URL}/api/new-feature/endpoint"
   
   # ✅ GOOD
   url = f"{BASE_URL}{API_URLS.NEW_FEATURE_ENDPOINT}"
   ```

---

## Adding New Environments

To add a staging or custom environment:

1. **Add to `constants.py`:**
   ```python
   class ENVIRONMENTS:
       CUSTOM = {
           "name": "custom",
           "backend_url": "https://custom-backend.com",
           "frontend_url": "https://custom-frontend.com",
           "redis_url": "redis://custom-redis:6379/0",
           "is_secure": True,
       }
   ```

2. **Update `get_current()` method:**
   ```python
   @staticmethod
   def get_current() -> Dict[str, str]:
       env = os.getenv('FLASK_ENV', 'development').lower()
       
       if env == 'custom':
            return ENVIRONMENTS.CUSTOM
        # ... rest of logic
   ```

3. **Deploy with environment variable:**
   ```bash
   FLASK_ENV=custom python app.py
   ```

---

## Troubleshooting

### Issue: "Import 'constants' could not be resolved"

**Solution:** Make sure you're in a backend context that includes the backend directory in Python path.

```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from constants import get_api_base_url
```

### Issue: Wrong URL in production (localhost appearing in logs)

**Solution:** Check FLASK_ENV variable:

```bash
echo $FLASK_ENV
# Should output: production
```

If incorrect, set it:

```bash
# Railway console
set FLASK_ENV=production

# Local .env
FLASK_ENV=production
```

### Issue: CORS errors despite correct config

**Solution:** Verify origins in constants match your actual frontend URL:

```python
python -c "from constants import CORS_CONFIG; print(CORS_CONFIG.get_allowed_origins())"
```

Should show your frontend URL. If not, add to `.env`:

```bash
CORS_ORIGINS=https://your-actual-frontend.com
```

---

## Files Modified Summary

| File | Changes | Status |
|------|---------|--------|
| `backend/constants.py` | Created (new) | ✅ |
| `backend/config.py` | Added imports, delegated CORS/Redis to constants | ✅ |
| `backend/.env.example` | Expanded docs, added all config options | ✅ |
| `frontend/.env.example` | Added environment examples | ✅ |
| `backend/test_fix.py` | Use constants instead of hardcoded URLs | ✅ |
| `backend/test_backend_api.py` | Use constants instead of hardcoded URLs | ✅ |
| `backend/test_unified_integration.py` | Use constants instead of hardcoded URLs | ✅ |
| `backend/verify_integration.py` | Use constants instead of hardcoded URLs | ✅ |
| `backend/check_results.py` | Use constants instead of hardcoded URLs | ✅ |

---

## Next Steps

1. **Deploy updated code to all environments:**
   - Local development continues using defaults
   - Railway production uses FLASK_ENV=production + env vars

2. **Update CI/CD pipelines** to set `FLASK_ENV=production` in deployment steps

3. **Monitor logs** for any URL mismatches post-deployment

4. **Add similar constants module to frontend** (future enhancement):
   - Frontend JavaScript equivalent of `constants.py`
   - Centralized endpoint definitions for React components

---

## References

- **TheTool.prompt.md** Section 2.1: Application Factory & Configuration
- **TheTool.prompt.md** Section 2.6: Utilities & Abstractions
- **TheTool.prompt.md** Section 10: Deployment Workflow & Environment Management
- **Backend Code:** `backend/constants.py`
- **Config Reference:** `backend/config.py`
