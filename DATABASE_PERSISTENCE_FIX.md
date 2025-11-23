# Database Persistence Issue & Solutions

## Problem

When redeploying the backend on Railway, the database is cleared because:

1. **SQLite uses ephemeral filesystem**: Railway containers are ephemeral - filesystem changes don't persist across redeploys
2. **Database file location**: Currently at `./data/trading_app.db` (relative path)
3. **No persistent volume**: Railway needs explicit persistent volume configuration for SQLite

## Solution Options

### Option 1: Use PostgreSQL (RECOMMENDED for Production)

**Why**: PostgreSQL is a managed service on Railway. Data persists automatically. This is the production-ready solution.

**Steps**:

1. In Railway Dashboard, go to your TheTool project
2. Click "Add Service" → Select "PostgreSQL"
3. Railway automatically creates a PostgreSQL instance
4. Railway auto-generates `DATABASE_URL` environment variable
5. Redeploy the backend - it will use PostgreSQL automatically

**Verification**:
```bash
# Check that DATABASE_URL is set
echo $DATABASE_URL
# Should output: postgresql://user:password@host:port/database

# The app will detect DATABASE_TYPE='postgres' and use the managed database
```

**Benefits**:
- ✅ Data persists across redeploys
- ✅ Automatic backups (Railway feature)
- ✅ Scalable to multiple workers
- ✅ No filesystem overhead
- ✅ Production-ready

### Option 2: Configure Railway Persistent Volume (For SQLite)

**Why**: If you want to keep using SQLite, you can mount a persistent volume.

**Steps**:

1. In Railway Dashboard, go to your backend service
2. Click "Settings" → "Volumes"
3. Add a new volume:
   - **Mount Path**: `/data`
   - **Size**: 1GB (or as needed)
4. Ensure `DATA_PATH` environment variable is set to `/data`
5. Redeploy

**Environment Variables to set**:
```
DATA_PATH=/data
```

**Limitations**:
- ⚠️ SQLite is single-threaded (can cause issues with multiple worker processes)
- ⚠️ Limited scalability compared to PostgreSQL
- ⚠️ Manual backup setup required
- ⚠️ Must disable gunicorn workers to avoid locking issues

**Not Recommended for Production**.

### Option 3: Local Development (No Action Needed)

For local development, SQLite at `./data/trading_app.db` works fine since the filesystem persists locally.

## Current Configuration Status

### Automatic Detection
The app now automatically detects the environment:

```python
DATABASE_URL = os.getenv('DATABASE_URL', None)
DATABASE_TYPE = 'postgres' if DATABASE_URL else 'sqlite'
```

**If DATABASE_URL is set**: Uses PostgreSQL (Railway managed)
**If DATABASE_URL is NOT set**: Uses SQLite at `./data/trading_app.db` (local development)

## Implementation

### Deploy with PostgreSQL (Recommended)

1. **Add PostgreSQL to Railway**:
   - In Railway project dashboard
   - Click "Add Service"
   - Select "PostgreSQL"
   - Done! Railway sets DATABASE_URL automatically

2. **No code changes needed** - the app detects and uses it automatically

3. **Verify deployment**:
   - Check Railway logs for "Database initialized successfully"
   - Verify with curl: `curl https://your-app/health`

### Database Initialization

The app automatically initializes the database on startup:

```python
# From app.py - runs on application factory
init_db_if_needed()  # Creates tables if needed (idempotent)
```

**What happens**:
1. Checks if database exists
2. Creates tables with `CREATE TABLE IF NOT EXISTS`
3. Creates indexes for faster queries
4. Doesn't drop existing data

## Troubleshooting

### Symptom: Database resets after redeploy

**Cause**: SQLite file is being lost (ephemeral filesystem)

**Solution**: 
```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# If empty, set it to use PostgreSQL
# In Railway Dashboard → Variables → Add DATABASE_URL

# If you must use SQLite, add persistent volume at /data
```

### Symptom: Permission denied accessing /data

**Cause**: Persistent volume not mounted or wrong path

**Solution**:
1. Check Railway volume settings
2. Verify mount path is `/data`
3. Ensure `DATA_PATH=/data` env var is set

### Symptom: Data lost after Railway restart

**Cause**: Still using SQLite on ephemeral filesystem

**Solution**: Switch to PostgreSQL (Option 1)

## Migration from SQLite to PostgreSQL

If you have existing data in SQLite and want to migrate to PostgreSQL:

1. **Export SQLite data**:
```bash
# Local development
sqlite3 ./data/trading_app.db '.dump' > backup.sql
```

2. **Create PostgreSQL add-on on Railway** (sets DATABASE_URL)

3. **Run schema migration script**:
   - App auto-creates tables
   - Data migration script can be added if needed

4. **Verify data in PostgreSQL**:
```bash
# Connect to PostgreSQL
psql $DATABASE_URL
\d  # List tables
```

## Recommended Production Setup

```
Railway Backend Service
├── PostgreSQL Add-on (managed, auto-backup)
├── Environment: FLASK_ENV=production
├── Workers: 4 (gunicorn)
└── Auto-redeploy: Enabled
```

**Result**: 
- ✅ Data persists across redeploys
- ✅ Automatic backups
- ✅ Scalable
- ✅ Production-ready

## Environment Variables Checklist

For Railway Production:

```bash
FLASK_ENV=production
MASTER_API_KEY=<strong-key>
PORT=8000
DATABASE_URL=postgresql://...  # Auto-set by Railway PostgreSQL add-on
CORS_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO
```

For Local Development:

```bash
FLASK_ENV=development
DEBUG=true
DATABASE_URL=  # Leave empty to use SQLite
DATA_PATH=./data
```

## References

- [Railway PostgreSQL Documentation](https://docs.railway.app/guides/databases)
- [Railway Volumes Documentation](https://docs.railway.app/guides/volumes)
- [SQLite Limitations](https://www.sqlite.org/limitations.html)
