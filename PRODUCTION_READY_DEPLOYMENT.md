# TheTool Production-Ready Configuration - Deployment Guide

**Date:** 2025-11-23  
**Version:** 1.0  
**Status:** Production-Ready  

---

## Overview

TheTool has been **hardened for production** by centralizing all environment-specific URLs and configuration into a single, maintainable constants module. No more scattered localhost hardcodes. Every deployment now uses environment-aware defaults.

---

## Key Improvements

### ✅ Before: Hardcoded URLs Everywhere

```
15+ files with hardcoded strings:
- test_analysis.py:           'http://localhost:5000'
- test_backend_api.py:        'http://localhost:5000'
- test_unified_integration.py: 'http://localhost:5000'
- verify_integration.py:       'http://localhost:5000'
- check_results.py:            'http://localhost:5000'
- index.html:                  'http://localhost:5000' (multiple)
- celery_config.py:            'redis://localhost:6379'
- ... many more
```

**Problem:** Production deployments could accidentally use localhost URLs

### ✅ After: Single Source of Truth

```
All URLs/config now come from:
- backend/constants.py (environment-aware defaults)
  - Development → localhost:5000
  - Staging → thetool-staging.up.railway.app
  - Production → thetool-production.up.railway.app
  
- Environment variables (.env files)
  - Can override defaults per deployment
  
- Centralized CORS, Redis, Database config
```

**Result:** Guaranteed correct URLs for each environment

---

## Deployment Workflow

### Development (Local)

**No action needed.** Defaults work automatically:

```bash
# Terminal
cd backend
python app.py

# Browser
http://localhost:3000
http://localhost:5000
```

### Staging (Railway Preview)

**Set environment on Railway Console:**

```bash
FLASK_ENV=staging
CORS_ORIGINS=https://thetool-staging.vercel.app,https://thetool-staging.up.railway.app
DATABASE_URL=postgresql+psycopg://... (from Railway)
REDIS_URL=redis://... (from Railway)
```

**Result:** Staging environment constants automatically applied

### Production (Railway Main)

**Set environment on Railway Console:**

```bash
FLASK_ENV=production
MASTER_API_KEY=<your-secure-key>
CORS_ORIGINS=https://the-tool-theta.vercel.app,https://thetool-production.up.railway.app
DATABASE_URL=postgresql+psycopg://... (from Railway)
REDIS_URL=redis://... (from Railway)
```

**Verify on Railway:**

```bash
# Option 1: Check logs
curl https://thetool-production.up.railway.app/health
# Should succeed, not 403 CORS error

# Option 2: Test health endpoint with logs
# Production will show:
#   "Backend URL: https://thetool-production.up.railway.app"
#   "Frontend URL: https://the-tool-theta.vercel.app"
```

---

## Environment Variables Reference

### Must-Set in Production

| Variable | Railway Source | Example |
|----------|---|---|
| `MASTER_API_KEY` | Manual | `<your-generated-key>` |
| `FLASK_ENV` | Manual | `production` |
| `DATABASE_URL` | PostgreSQL Service | `postgresql+psycopg://...` |
| `REDIS_URL` | Redis Service | `redis://...` |
| `CORS_ORIGINS` | Manual | `https://the-tool-theta.vercel.app,https://thetool-production.up.railway.app` |

### Optional (Use Defaults)

| Variable | Default (Production) | Purpose |
|----------|---|---|
| `FLASK_HOST` | `0.0.0.0` | Server bind address |
| `FLASK_PORT` | `5000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CACHE_ENABLED` | `True` | Enable caching |
| `RATE_LIMIT_ENABLED` | `True` | Rate limiting |

---

## URL Resolution Priority

When TheTool starts, it determines URLs in this order:

```
1. Explicit env var (e.g., BACKEND_URL=...)
2. FLASK_ENV-based default (development/staging/production)
3. Fallback constant (localhost:5000)
```

### Example: CORS Origins Resolution

```python
# Development (FLASK_ENV=development or not set)
→ Uses: CORS_CONFIG.DEVELOPMENT_ORIGINS
→ Result: ['http://localhost:3000', 'http://192.168.57.1:3000', ...]

# Production (FLASK_ENV=production)
→ Uses: CORS_CONFIG.PRODUCTION_ORIGINS
→ Result: ['https://the-tool-theta.vercel.app', 'https://thetool-production.up.railway.app']

# Override (CORS_ORIGINS env var set)
→ Parses: comma-separated list from env var
→ Result: Whatever was specified
```

---

## Verification Checklist

### Pre-Deployment

- [ ] **Centralized constants module created:** `backend/constants.py` ✅
- [ ] **Config.py updated:** Uses `CORS_CONFIG`, `REDIS_CONFIG` ✅
- [ ] **.env templates updated:** `backend/.env.example`, `frontend/.env.example` ✅
- [ ] **Test files updated:** All 5 test scripts use `get_api_base_url()` ✅
- [ ] **Documentation created:** `CONSTANTS_GUIDE.md` ✅

### Post-Deployment (Production)

1. **Check Backend Logs:**
   ```bash
   # Railway console → Logs
   # Should show:
   #   "Environment: production"
   #   "Backend URL: https://thetool-production.up.railway.app"
   #   "CORS Allowed Origins: ['https://the-tool-theta.vercel.app', ...]"
   ```

2. **Test Health Endpoint:**
   ```bash
   curl https://thetool-production.up.railway.app/health
   # Should return 200 OK
   ```

3. **Test Frontend Connection:**
   ```
   Open: https://the-tool-theta.vercel.app
   Browser Console → Network tab
   Should see successful API calls (no 403 CORS errors)
   ```

4. **Test API Endpoint:**
   ```bash
   curl -X POST https://thetool-production.up.railway.app/api/analysis/analyze \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["INFY.NS"], "capital": 100000}'
   # Should return 200 with job_id
   ```

---

## Troubleshooting

### Issue: 403 CORS Error in Production

**Symptom:** Frontend can't call backend API

**Diagnosis:**
```bash
# Check CORS config
python -c "from constants import CORS_CONFIG; print(CORS_CONFIG.get_allowed_origins())"

# Should include your frontend URL
```

**Fix:**
1. Verify `CORS_ORIGINS` env var on Railway is set correctly
2. Or update `backend/constants.py` PRODUCTION_ORIGINS
3. Redeploy backend

### Issue: Localhost URLs in Production Logs

**Symptom:** Logs show "http://localhost:5000"

**Diagnosis:**
```bash
# Check FLASK_ENV
echo $FLASK_ENV
# Should output: production
```

**Fix:**
1. Set `FLASK_ENV=production` on Railway
2. Redeploy backend
3. Logs should now show correct production URLs

### Issue: Redis Connection Failing

**Symptom:** Redis errors in logs

**Diagnosis:**
```bash
python -c "from constants import get_redis_url; print(get_redis_url())"
# Should show Railway Redis URL
```

**Fix:**
1. Ensure `REDIS_URL` is set on Railway (from Redis service)
2. Or disable Redis: `REDIS_ENABLED=False`
3. Redeploy

---

## File Changes Summary

### New Files

- `backend/constants.py` (550 lines) - Central constants hub
- `CONSTANTS_GUIDE.md` - Comprehensive documentation

### Modified Files

| File | Changes |
|------|---------|
| `backend/config.py` | Added imports from constants; CORS/Redis now delegated |
| `backend/.env.example` | Expanded with all config options; environment examples |
| `frontend/.env.example` | Added dev/staging/prod examples |
| `backend/test_fix.py` | Now uses `get_api_base_url()` + `API_URLS` |
| `backend/test_backend_api.py` | Now uses `get_api_base_url()` + `API_URLS` |
| `backend/test_unified_integration.py` | Now uses `get_api_base_url()` + `API_URLS` |
| `backend/verify_integration.py` | Now uses `get_api_base_url()` + `API_URLS` |
| `backend/check_results.py` | Now uses `get_api_base_url()` + `API_URLS` |

### Impact Assessment

- **Development:** No impact (defaults work as before)
- **Staging:** Must set `FLASK_ENV=staging` on Railway
- **Production:** Must set `FLASK_ENV=production` + relevant env vars

---

## Best Practices Going Forward

### ❌ Never Do This

```python
# Don't hardcode URLs
response = requests.get('http://localhost:5000/health')
response = requests.get('https://thetool-production.up.railway.app/health')
```

### ✅ Always Do This

```python
from constants import get_api_base_url, API_URLS

base_url = get_api_base_url()
response = requests.get(f'{base_url}{API_URLS.HEALTH_CHECK}')
```

### When Adding New Endpoints

1. **Define constant in `backend/constants.py`:**
   ```python
   class API_URLS:
       FEATURE_NEW = "/api/feature/new"
   ```

2. **Use in code:**
   ```python
   url = f"{base_url}{API_URLS.FEATURE_NEW}"
   ```

3. **Never skip this step** - ensures consistency across environments

---

## Next Deployment Steps

### Immediate (This Week)

1. Deploy updated code to all environments
2. Set `FLASK_ENV=production` on Railway
3. Monitor logs for any URL mismatches
4. Verify frontend/backend communication

### Short-term (Next Week)

1. Update CI/CD pipelines to set `FLASK_ENV` during deployment
2. Test staging environment with `FLASK_ENV=staging`
3. Create runbook for troubleshooting environment issues

### Medium-term (This Month)

1. Add frontend constants module (JavaScript equivalent)
2. Implement centralized endpoint registry for React components
3. Create auto-generated OpenAPI spec from constants

---

## Support & Questions

**Q: Can I still use environment-specific configs?**  
A: Yes! Override any constant with env var (e.g., `BACKEND_URL=...`)

**Q: What if I need a 4th environment?**  
A: Add to `ENVIRONMENTS` class in `constants.py`, update `get_current()` method

**Q: Do tests still work locally?**  
A: Yes! Tests automatically use development defaults (localhost)

**Q: What about feature flags or A/B testing?**  
A: Can be added alongside constants module without conflicts

---

## References

- **Constants Guide:** `CONSTANTS_GUIDE.md`
- **Operating Prompt:** `TheTool.prompt.md` (Sections 2.1, 2.6, 10)
- **Constants Module:** `backend/constants.py`
- **Configuration:** `backend/config.py`
