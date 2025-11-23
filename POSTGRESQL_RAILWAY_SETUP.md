# PostgreSQL Setup Guide for Railway Deployment

## Overview
Your TheTool application is now configured to use **PostgreSQL on Railway**, which ensures data persists across deployments. This replaces the ephemeral SQLite setup that was losing data.

---

## Step 1: Verify PostgreSQL is Added to Your Railway Project

### In Railway Dashboard:
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on your **TheTool** project
3. You should see two services:
   - **backend** (your Flask app)
   - **postgres** (PostgreSQL database)

If PostgreSQL is not there:
- Click **"Add Service"** → Select **"PostgreSQL"**
- Railway automatically creates the database and sets `DATABASE_URL`

---

## Step 2: Configure the DATABASE_URL Variable

Railway should automatically inject the `DATABASE_URL`, but verify it's set:

1. In your **backend** service settings, go to **Variables** tab
2. You should see:
   ```
   DATABASE_URL = postgresql://postgres:<password>@<host>:<port>/<database>
   ```

If missing, add it manually:
```
DATABASE_URL = ${Postgres.DATABASE_URL}
```

(This references the PostgreSQL service's connection string)

---

## Step 3: Initialize the Database Schema

Your app needs the schema (tables, indexes) in PostgreSQL. Choose ONE method:

### Option A: Automatic Initialization (Recommended)
The app automatically creates tables on first startup via `init_db()`.

Just redeploy your app and the schema will be created automatically.

### Option B: Manual Initialization (If Option A Fails)

1. **Locally (if you have DATABASE_URL):**
   
   **Windows (Command Prompt):**
   ```bash
   cd backend
   pip install -r requirements.txt
   set DATABASE_URL=postgresql://postgres:<password>@<host>:<port>/<database>
   python init_postgres.py
   ```
   
   **Linux/Mac (Bash/Zsh):**
   ```bash
   cd backend
   pip install -r requirements.txt
   export DATABASE_URL=postgresql://postgres:<password>@<host>:<port>/<database>
   python init_postgres.py
   ```

2. **Via Railway CLI (works on all platforms):**
   ```bash
   railway login
   railway link  # (select your TheTool project)
   railway run python init_postgres.py
   ```

---

## Step 4: Redeploy Your Application

Push changes to GitHub and Railway will auto-deploy:

```bash
cd backend
git add requirements.txt database.py config.py
git commit -m "Enable PostgreSQL support for Railway"
git push origin main
```

Railway will:
1. Deploy the updated backend code
2. Automatically run `init_db()` on startup
3. Connect to PostgreSQL using `DATABASE_URL`
4. Create all tables and indexes

---

## Step 5: Verify Everything Works

### Check Railway Logs:
1. Go to Railway Dashboard → **backend** service
2. Click **"Logs"** tab
3. Look for these messages:
   ```
   PostgreSQL database initialized successfully
   Database initialized successfully
   INFO: Connected to PostgreSQL
   ```

### Check Data Persistence:
1. Run an analysis on the frontend
2. Redeploy your backend (`git push`)
3. Check if the analysis results still appear
   - **Before (SQLite)**: Data would be gone after redeploy
   - **Now (PostgreSQL)**: Data persists ✓

---

## Troubleshooting

### "DATABASE_URL not set"
- Verify PostgreSQL service exists in your Railway project
- Check Variables tab has `DATABASE_URL` set
- Redeploy the backend

### "Connection refused"
- Ensure PostgreSQL service is running (check Railway logs)
- Verify `DATABASE_URL` format: should start with `postgresql://`
- Try restarting both services

### "FATAL: authentication failed"
- Check the password in `DATABASE_URL`
- Go to Postgres service settings and reset password if needed
- Update `DATABASE_URL` variable accordingly

### Tables not created
- Check backend logs for errors during `init_db()`
- Run `python init_postgres.py` manually to see detailed errors
- Check PostgreSQL logs in Railway

---

## How Your App Now Works

### Local Development (SQLite):
```
No DATABASE_URL → Uses SQLite at ./data/trading_app.db
```

### Railway Production (PostgreSQL):
```
DATABASE_URL set → Uses PostgreSQL
Data persists across deployments ✓
```

---

## File Changes Made

1. **`requirements.txt`**: Added `psycopg2-binary` for PostgreSQL support
2. **`config.py`**: Updated to handle `postgres://` → `postgresql://` URL conversion
3. **`database.py`**: Enhanced to support both SQLite and PostgreSQL connections
4. **`init_postgres.py`**: New script for manual schema initialization on Railway

---

## Next Steps

✅ PostgreSQL is now configured  
✅ Your app detects and uses it automatically  
✅ Data will persist across deployments  

**Action**: Redeploy your app and verify data persists!

```bash
git push origin main
```

Then check the Railway logs to confirm PostgreSQL initialization.
