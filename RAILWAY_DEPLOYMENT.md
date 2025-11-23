# Railway Deployment Guide for TheTool Backend

## Quick Start (5 minutes)

### 1. Connect GitHub Repository
- Go to [railway.app](https://railway.app)
- Click "New Project" → "Deploy from GitHub"
- Select your TheTool repository
- Authorize Railway to access GitHub

### 2. Configure Environment Variables
In Railway Dashboard, set the following:

```bash
# Core
FLASK_ENV=production
PORT=8000
MASTER_API_KEY=<generate-strong-key>

# Database
DATABASE_URL=<auto-set-by-Railway-Postgres-add-on>

# Optional: Redis for distributed state
REDIS_URL=<auto-set-by-Railway-Redis-add-on>

# CORS
CORS_ORIGINS=https://your-frontend.domain.com,https://another-domain.com

# Logging
LOG_LEVEL=INFO
```

### 3. Add Database (PostgreSQL)
- In Railway Project → "Add Service"
- Select "PostgreSQL"
- Railway auto-generates DATABASE_URL
- Database will be automatically created and migrated

### 4. Deploy
- Push code to GitHub
- Railway auto-deploys on push
- Watch deploy logs in Railway dashboard

---

## Architecture

### Process Model
```
Railway Instance
├── Web Service (gunicorn)
│   ├── Workers: 2-4 (auto-scaled based on load)
│   ├── Timeout: 120s
│   └── Port: 0.0.0.0:$PORT
│
└── Optional Services
    ├── PostgreSQL (managed)
    ├── Redis (for distributed state)
    └── Cron Jobs (for periodic cleanup)
```

### Data Flow
```
Client → Railway Load Balancer → Gunicorn Workers (multi-process)
                                       ↓
                            PostgreSQL (managed, persistent)
                                       ↓
                            Redis (optional, for job state)
```

### Key Features
- **Ephemeral Filesystem**: No persistent local files. Use Postgres for state.
- **Auto-scaling**: Railway scales based on CPU/memory
- **Automatic HTTPS**: All traffic encrypted
- **Health Checks**: Railway pings `/health` endpoint
- **Logs**: Streamed to Railway dashboard (stdout/stderr)

---

## Configuration Details

### Environment Variables

#### Required
```bash
FLASK_ENV=production
MASTER_API_KEY=your-api-key
DATABASE_URL=postgresql://...  # Auto-set by Railway
```

#### Optional
```bash
PORT=8000                    # Railway sets automatically
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
REDIS_URL=redis://...       # If using Redis add-on
RATE_LIMIT_ENABLED=true
CACHE_ENABLED=true
```

### Database Setup
Railway PostgreSQL add-on automatically:
1. Creates managed Postgres instance
2. Provides DATABASE_URL
3. Runs migrations on first deploy (via db_migrations.py)
4. Scales storage automatically

### Gunicorn Configuration
Railway uses `gunicorn.conf.py`:
- **Workers**: Auto-scaled (2-4 based on CPU cores)
- **Timeout**: 120 seconds (for heavy analysis jobs)
- **Max Requests**: 1000 per worker (prevents memory leaks)
- **Bind**: 0.0.0.0:$PORT (Railway sets PORT)

---

## Deployment Checklist

### Pre-Deployment
- [ ] Update `requirements-prod.txt` with all dependencies
- [ ] Verify `wsgi.py` exists and imports correctly
- [ ] Test locally: `python wsgi.py`
- [ ] Verify `gunicorn.conf.py` is present
- [ ] Check `.env` file is in `.gitignore`

### Environment Setup
- [ ] Create Railway project
- [ ] Add PostgreSQL add-on
- [ ] (Optional) Add Redis add-on for distributed state
- [ ] Set all required environment variables
- [ ] Verify DATABASE_URL auto-generated

### First Deploy
- [ ] Trigger deploy from GitHub
- [ ] Watch logs for:
  - `[OK] Database migrations completed`
  - `Gunicorn starting with X workers`
  - `/health` endpoint returns 200
- [ ] Test API: `curl https://<your-railway-app>/health`

### Post-Deployment
- [ ] Test `/analyze` endpoint with test data
- [ ] Monitor logs for errors
- [ ] Set up alerting (Railway dashboard)
- [ ] Configure custom domain (optional)
- [ ] Set up automatic backups (Postgres)

---

## Monitoring

### Health Endpoint
```bash
# Check if backend is running
curl https://your-railway-app/health

# Expected response:
{
  "status": "ok",
  "message": "backend running",
  "uptime_seconds": 3600,
  "authentication": "enabled",
  "cache": {"enabled": true, "hit_rate": 0.75}
}
```

### Logs
1. **Railway Dashboard**: View real-time logs
2. **Structured Logging**: All logs include timestamps + levels
3. **Error Tracking**: Errors logged with full stack traces
4. **Job Tracking**: Each job gets correlation ID in logs

### Metrics
- **Uptime**: Monitored by Railway
- **Response Time**: Check via `/health` endpoint
- **Error Rate**: Monitor 500 errors in logs
- **Database**: Monitor Postgres connection count

---

## Scaling

### Vertical Scaling
1. Go to Railway Project Settings
2. Increase allocated resources (CPU/Memory)
3. Workers auto-scale with available cores

### Horizontal Scaling
Railway auto-scales up to 4 instances based on load:
- CPU > 80% → Add instance
- Memory > 80% → Add instance
- High latency → Add instance

---

## Troubleshooting

### App Won't Start
```bash
# Check logs for errors
# Common issues:
# 1. Missing environment variable
# 2. Database connection failed
# 3. Import error in app.py
```

### Database Connection Error
```bash
# Verify DATABASE_URL is set
env | grep DATABASE_URL

# If missing, add PostgreSQL add-on:
# Railway → Add Service → PostgreSQL
```

### Jobs Timeout (120s limit)
```bash
# Increase timeout in gunicorn.conf.py
# Set: timeout = 300  (5 minutes)
```

### Memory Issues
```bash
# Check memory usage
# Increase Railway resource allocation
# Or reduce MAX_WORKERS in config.py
```

### Redis Not Connecting
```bash
# Add Redis add-on if job state distribution needed
# Railway → Add Service → Redis
# Or disable: REDIS_ENABLED=false
```

---

## Advanced Configuration

### Custom Domain
1. Railway Project → Settings
2. "Domain" section
3. Add custom domain
4. Configure DNS (CNAME to railway.app)

### Environment-Specific Configs
Create `prod.env` for production values:
```bash
FLASK_ENV=production
LOG_LEVEL=WARNING
CACHE_TTL=7200
```

Load in railway.yml (if using):
```yaml
services:
  backend:
    environmentFile: prod.env
```

### Auto-Scaling Config
Edit `gunicorn.conf.py`:
```python
# More workers for high load
workers = max(4, multiprocessing.cpu_count())

# Longer timeout for heavy jobs
timeout = 300
```

---

## Production Best Practices

### Security
- [ ] Use strong `MASTER_API_KEY` (32+ chars)
- [ ] Enable HTTPS (automatic on Railway)
- [ ] Restrict CORS origins to frontend domain only
- [ ] Never commit secrets to GitHub

### Performance
- [ ] Enable caching: `CACHE_ENABLED=true`
- [ ] Set appropriate cache TTL: `CACHE_TTL=3600`
- [ ] Monitor database query performance
- [ ] Use connection pooling (automatic in Postgres)

### Reliability
- [ ] Monitor `/health` endpoint (Railway does this)
- [ ] Set up error alerting
- [ ] Configure automatic backups (Postgres)
- [ ] Keep Database migrations idempotent

### Observability
- [ ] Structured logging to Railway
- [ ] Request correlation IDs
- [ ] Job tracking with timestamps
- [ ] Error tracking with stack traces

---

## Cost Optimization

### Railway Pricing
- **Web Service**: $5-10/month per instance
- **PostgreSQL**: $20-40/month depending on storage
- **Redis**: $5-15/month if enabled
- **Total**: ~$30-50/month for small-to-medium workload

### Cost Reduction
1. Use 1-2 workers (not 4) if traffic is low
2. Disable Redis if not needed (use DB-based state)
3. Optimize database queries
4. Set aggressive cache TTL
5. Clean up old analyses regularly

---

## Rollback

If deployment fails:
1. Go to Railway Deployments
2. Click "Rollback" on previous successful deploy
3. Railway automatically redeploys previous version

---

## Support & Documentation

- [Railway Docs](https://docs.railway.app)
- [Python/Flask Deployment Guide](https://docs.railway.app/guides/python)
- [PostgreSQL on Railway](https://docs.railway.app/guides/postgresql)
- [GitHub Integration](https://docs.railway.app/guides/github)

---

**Last Updated**: 2025-11-23
**Backend Version**: Post-Stabilization (Phase 6)
**Status**: Production-Ready
