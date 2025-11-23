# Quick Reference: URL & Configuration Guide

## One-Minute Overview

TheTool now has **centralized constants** that automatically provide the correct URLs for each environment.

### What to Know

| Scenario | What to Do | Result |
|----------|-----------|--------|
| **Local Development** | Just run `python app.py` | Uses `http://localhost:5000` |
| **Production on Railway** | Set `FLASK_ENV=production` | Uses `https://thetool-production.up.railway.app` |
| **Override Any URL** | Set `BACKEND_URL=...` env var | Uses your custom URL |

---

## Environment URLs

### Development (Default)

```
Backend:  http://localhost:5000
Frontend: http://localhost:3000
Redis:    redis://localhost:6379/0
Database: SQLite ./data/trading_app.db
```

### Staging

```
Backend:  https://thetool-staging.up.railway.app
Frontend: https://thetool-staging.vercel.app
Redis:    redis://staging-redis.railway.app:6379/0
Database: PostgreSQL (Railway)
```

### Production

```
Backend:  https://thetool-production.up.railway.app
Frontend: https://the-tool-theta.vercel.app
Redis:    redis://production-redis.railway.app:6379/0
Database: PostgreSQL (Railway)
```

---

## Key URLs to Know

### Analysis Endpoints
```
POST   /api/analysis/analyze
GET    /api/analysis/status/{job_id}
GET    /api/analysis/history/{ticker}
GET    /api/analysis/report/{ticker}
POST   /api/analysis/cancel/{job_id}
GET    /api/analysis/jobs
```

### Stock Endpoints
```
GET    /api/stocks/nse
GET    /api/stocks/nse-stocks
GET    /api/stocks/all-stocks
GET    /api/stocks/all-stocks/{symbol}/history
POST   /api/stocks/analyze-all-stocks
GET    /api/stocks/all-stocks/progress
```

### Watchlist Endpoints
```
GET    /api/watchlist
POST   /api/watchlist
DELETE /api/watchlist
```

### System Endpoints
```
GET    /health
GET    /config
GET    /
```

---

## How URLs Are Determined

```
┌─────────────────────────┐
│ Step 1: Check env var   │
│ BACKEND_URL set?        │
│ REDIS_URL set?          │
└──────────┬──────────────┘
           │ No
           ▼
┌─────────────────────────┐
│ Step 2: Check FLASK_ENV │
│ production?             │
│ staging?                │
│ development?            │
└──────────┬──────────────┘
           │ Not set
           ▼
┌─────────────────────────┐
│ Step 3: Use defaults    │
│ (DEVELOPMENT env)       │
└─────────────────────────┘
```

---

## Switching Environments

### Local → Production

**Before:**
- Edit 15+ files
- Search/replace `localhost:5000` → `production-url`
- Risk missing some files

**After:**
```bash
# Just set one variable!
FLASK_ENV=production

# Done. All URLs automatic.
```

---

## Using in Code

### ❌ Old Way (Don't Do)
```python
response = requests.get('http://localhost:5000/health')
response = requests.get('http://localhost:5000/api/analysis/analyze', ...)
```

### ✅ New Way (Do This)
```python
from constants import get_api_base_url, API_URLS

base_url = get_api_base_url()
response = requests.get(f'{base_url}{API_URLS.HEALTH_CHECK}')
response = requests.post(f'{base_url}{API_URLS.ANALYZE}', ...)
```

---

## CORS Configuration

### Allowed Origins by Environment

| Environment | Allowed From |
|---|---|
| **Dev** | `http://localhost:3000` `http://192.168.57.1:3000` |
| **Staging** | `https://thetool-staging.vercel.app` `https://thetool-staging.up.railway.app` |
| **Production** | `https://the-tool-theta.vercel.app` `https://thetool-production.up.railway.app` |

### Override CORS
Add to `.env`:
```bash
CORS_ORIGINS=https://your-frontend.com,https://another-frontend.com
```

---

## Railway Deployment: Step-by-Step

### 1. Backend Service

Go to Railway Console → Variables:

```bash
FLASK_ENV=production
MASTER_API_KEY=<your-secure-key>
CORS_ORIGINS=https://the-tool-theta.vercel.app,https://thetool-production.up.railway.app
DATABASE_URL=<from PostgreSQL service>
REDIS_URL=<from Redis service>
```

### 2. Frontend Service (Vercel)

Go to Vercel Dashboard → Settings → Environment Variables:

```bash
REACT_APP_ENV=production
REACT_APP_API_BASE_URL=https://thetool-production.up.railway.app
REACT_APP_API_KEY=<your-api-key>
```

### 3. Test

```bash
# Backend health check
curl https://thetool-production.up.railway.app/health

# Should return: {"status": "ok"}
```

---

## Testing Locally

### Test Development URLs
```bash
cd backend
python test_fix.py
# Uses http://localhost:5000
```

### Test Production URLs (Simulation)
```bash
cd backend
FLASK_ENV=production python test_fix.py
# Would use https://thetool-production.up.railway.app (except no server)
# But shows it's using correct URL
```

### Verify Configuration
```bash
cd backend
python -c "from constants import print_config_summary; print_config_summary()"
```

---

## Configuration Files

### Backend

**`backend/.env` (local development)**
```bash
FLASK_ENV=development
MASTER_API_KEY=dev-key
LOG_LEVEL=DEBUG
REDIS_ENABLED=False
```

**`backend/.env.example` (template)**
```bash
# See all available options here
# Copy and customize for your environment
```

### Frontend

**`frontend/.env.development`**
```bash
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_API_KEY=development-key
```

**`frontend/.env.production`**
```bash
REACT_APP_API_BASE_URL=https://thetool-production.up.railway.app
REACT_APP_API_KEY=<production-key>
```

---

## Troubleshooting

### CORS 403 Error

**Problem:** Frontend can't call backend API

**Solution:**
```bash
# Check what origins are allowed
python -c "from constants import CORS_CONFIG; print(CORS_CONFIG.get_allowed_origins())"

# If your frontend URL isn't there, add to .env:
CORS_ORIGINS=https://your-frontend.com,https://the-tool-theta.vercel.app,...
```

### Wrong URLs in Logs

**Problem:** Logs show `http://localhost:5000` in production

**Solution:**
```bash
# Check FLASK_ENV
echo $FLASK_ENV

# Should be: production
# If not, set it:
FLASK_ENV=production
```

### Redis Connection Failed

**Problem:** Redis errors in logs

**Solution:**
```bash
# Option 1: Use Railway Redis
REDIS_URL=redis://your-railway-redis:6379/0

# Option 2: Disable Redis
REDIS_ENABLED=False
```

---

## All Available Constants

### Functions
```python
get_api_base_url()      # Current environment's backend URL
get_frontend_url()      # Current environment's frontend URL
get_redis_url()         # Current environment's Redis URL
print_config_summary()  # Print current config to console
validate_urls()         # Check if URLs are valid
```

### Classes
```python
ENVIRONMENTS            # Dev/Staging/Prod configs
API_URLS               # All 30+ endpoint paths
CORS_CONFIG            # Allowed origins per environment
REDIS_CONFIG           # Redis settings
DATABASE_CONFIG        # Database URL resolution
```

### Environment Variables Checked
```
FLASK_ENV              # primary: dev/staging/production
BACKEND_URL            # override backend URL
FRONTEND_URL           # override frontend URL
REDIS_URL              # override Redis URL
DATABASE_URL           # override database URL
CORS_ORIGINS           # override CORS origins
```

---

## Files to Know

| File | Purpose |
|------|---------|
| `backend/constants.py` | Central constants hub (550 lines) |
| `backend/config.py` | Flask configuration (uses constants) |
| `CONSTANTS_GUIDE.md` | Detailed reference documentation |
| `PRODUCTION_READY_DEPLOYMENT.md` | Deployment guide |
| `PRODUCTION_HARDENING_SUMMARY.md` | Full summary report |

---

## One-Page Commands

### For Developers

```bash
# See current configuration
cd backend
python -c "from constants import print_config_summary; print_config_summary()"

# Run test with production URLs (simulation)
FLASK_ENV=production python test_fix.py

# Check CORS config
python -c "from constants import CORS_CONFIG; print(CORS_CONFIG.get_allowed_origins())"
```

### For DevOps/Railway

```bash
# Set backend to production
FLASK_ENV=production

# Verify URLs are correct
curl https://thetool-production.up.railway.app/health

# Check logs for correct environment
# Should show: "Environment: production"
```

---

## Migration Checklist

- [ ] Update `backend/constants.py` with your URLs (if custom)
- [ ] Set `FLASK_ENV=production` on Railway
- [ ] Set `CORS_ORIGINS` to include your frontend URL
- [ ] Test backend health: `curl https://your-backend/health`
- [ ] Test frontend loads without CORS errors
- [ ] Verify API calls work
- [ ] Monitor logs for URL correctness

---

## Summary

| What | Before | After |
|-----|--------|-------|
| **Hardcoded URLs** | 15+ files | 0 files |
| **Environment switching** | Manual edits | One env var |
| **Production readiness** | Risk of localhost | Guaranteed correct URLs |
| **Code quality** | Scattered config | Single source of truth |
| **Maintainability** | Difficult | Easy |

✅ **Result:** TheTool is now production-ready!
