# 🚂 Guide 02: Deploy Flask Backend to Railway

**Estimated Time:** 20-25 minutes  
**Difficulty:** ⭐⭐ Medium  
**What You'll Do:** Deploy your Flask API to Railway and set up automatic deployments  
**What You'll Have After:** A live Flask backend running 24/7 on Railway  

---

## 🎯 What This Guide Accomplishes

By the end of this guide:
- ✅ Railway account created and verified
- ✅ Backend Docker container deployed to Railway
- ✅ SQLite database persisting on Railway volume
- ✅ Automatic deploys from GitHub working
- ✅ Live backend URL (like: `yourapp.railway.app`)
- ✅ Health checks verified working

---

## Prerequisites

Complete Guide 01 first! You need:
- [ ] GitHub account with TheTool repo pushed
- [ ] GitHub repo URL: `github.com/YOUR_USERNAME/TheTool`
- [ ] All code committed and pushed to `main` branch

**Check:** In browser, visit `github.com/YOUR_USERNAME/TheTool` - you should see all your files

---

## Step 1: Create Railway Account

### 1.1 Go to Railway.app

Open your browser and navigate to Railway:

| Input Method | Action |
|---|---|
| **Mouse** | Click address bar, type: `https://railway.app` |
| **Keyboard** | Press `Ctrl+L`, type `railway.app`, press `Enter` |

**WHAT YOU SHOULD SEE:**
- Railway homepage
- Purple and blue gradient background
- "Deploy Now" or "Start Deploying" button (top-right)
- "Sign up free" option

### 1.2 Sign Up with GitHub

Railway makes deployment easiest if you sign up with GitHub:

| Input Method | Action |
|---|---|
| **Mouse** | Click "GitHub" button (if available) or "Sign up free" |
| | Then click "Sign up with GitHub" |

**WHAT HAPPENS:**
- GitHub login page appears
- You authorize Railway to access your GitHub account
- Redirects back to Railway

**IF ASKED FOR AUTHORIZATION:**

| Input Method | Action |
|---|---|
| **Mouse** | Click green "Authorize railwayapp" button |

This allows Railway to:
- Read your repositories
- Automatically deploy from GitHub pushes
- Create status checks on your pull requests

### 1.3 Verify Email (If Needed)

Railway may ask you to verify your email:

| Input Method | Action |
|---|---|
| **Mouse** | Check your email inbox for verification link |
| | Click the verification link |

**WHAT YOU SHOULD SEE:**
- Email from `Railway <notify@railway.app>`
- Verify link inside
- After clicking, confirms "Email verified!"

### 1.4 Setup Payment Method (Important!)

Railway offers:
- **First 30 days:** $5 free credit (trial)
- **After trial:** Pay-as-you-go ($1-10/month for hobby projects)

**Railway requires a credit card** but won't charge until trial ends.

| Input Method | Action |
|---|---|
| **Mouse** | 1. After signup, go to Settings |
| | 2. Click "Billing" in left sidebar |
| | 3. Click "Add Payment Method" |
| | 4. Enter credit card details |

**WHAT YOU ENTER:**
- Credit card number
- Expiration date
- CVC (3-digit code on back)
- Billing address

**IMPORTANT:** This won't charge you for 30 days (trial period). You can cancel anytime.

### 1.5 Create First Project

After signup, Railway shows a dashboard:

| Input Method | Action |
|---|---|
| **Mouse** | Click "+ New Project" button (top area) |

**WHAT HAPPENS:**
- Shows options: GitHub repo, template, Docker image, etc.
- We want to deploy from GitHub

---

## Step 2: Connect GitHub Repository to Railway

### 2.1 Select GitHub Repository

After clicking "New Project", you'll see deployment options:

| Input Method | Action |
|---|---|
| **Mouse** | Click "Deploy from GitHub repo" option |

**WHAT YOU SHOULD SEE:**
- Search box for repositories
- List of your GitHub repositories below

### 2.2 Find and Select TheTool

| Input Method | Action |
|---|---|
| **Mouse** | 1. In search box, type: `TheTool` |
| | 2. Find "YOUR_USERNAME/TheTool" in results |
| | 3. Click on it to select |

**WHAT YOU SHOULD SEE:**
- TheTool repo highlighted
- Brief loading indicator

### 2.3 Authorize Railway to GitHub

Railway needs permission to read your repo and set up webhooks:

| Input Method | Action |
|---|---|
| **Mouse** | If prompted, click "Authorize" or "Approve installation" |

**WHAT HAPPENS:**
- Railway installs webhook on your GitHub repo
- This tells Railway whenever you push code
- Railway automatically redeploys your app

### 2.4 Railway Detects Your Backend

Railway automatically detects your Docker setup:

**WHAT YOU SHOULD SEE:**
- "Detected Backend from Dockerfile"
- Shows it will use: `backend/Dockerfile`
- Shows detected Python version
- Shows detected port: 5000
- Option to "Add service"

| Input Method | Action |
|---|---|
| **Mouse** | If everything looks correct, click "Deploy" button |

**EXPECTED OUTPUT:**
```
✓ Using Dockerfile from backend/
✓ Building container image
✓ Deploying to Railway
```

---

## Step 3: Configure Environment Variables

Railway is now building and deploying your backend. While it deploys, let's configure environment variables.

### 3.1 Wait for Deployment to Start

You should see a screen showing:
- Build logs in real-time
- "Building..." status
- "Deploying..." status
- Progress indicators

**WHAT TO EXPECT:**
- First build takes 2-3 minutes (installs dependencies)
- Subsequent builds are faster (1-2 minutes)

### 3.2 Access Environment Configuration

While deployment runs, let's configure environment variables:

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard, look for your service |
| | 2. Click on the service name (likely "backend") |
| | 3. Click "Variables" tab (top) |

**WHAT YOU SHOULD SEE:**
- Section titled "Environment"
- Currently may have some auto-detected variables
- Button to "Add Variable"

### 3.3 Add Required Variables

Add these environment variables (create each one):

**VARIABLE 1: FLASK_ENV**

| Field | Value |
|---|---|
| Key | `FLASK_ENV` |
| Value | `production` |

| Input Method | Action |
|---|---|
| **Mouse** | 1. Click "Add Variable" button |
| | 2. Type "FLASK_ENV" in key field |
| | 3. Type "production" in value field |
| | 4. Press Enter or click save |

**VARIABLE 2: DATA_PATH**

| Field | Value |
|---|---|
| Key | `DATA_PATH` |
| Value | `/app/data` |

**VARIABLE 3: LOG_LEVEL**

| Field | Value |
|---|---|
| Key | `LOG_LEVEL` |
| Value | `INFO` |

**WHAT YOU SHOULD SEE:**
```
Environment Variables:
├─ FLASK_ENV = production
├─ DATA_PATH = /app/data
└─ LOG_LEVEL = INFO
```

### 3.4 Verify Backend is Running

Go back and check the deployment status:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Click back to see service overview |
| | 2. Look for "Deployments" tab |
| | 3. Check latest deployment status |

**WHAT YOU SHOULD SEE:**
- Status changes: "Building" → "Deploying" → "Running" ✅
- Green checkmark indicating success
- Deploy time (usually 2-3 minutes total)

---

## Step 4: Get Your Live Backend URL

### 4.1 Find the Public URL

Once deployment completes successfully:

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard, find your service |
| | 2. Look for "Public URL" or "Networking" section |
| | 3. You'll see a URL like: |
| | `https://yourapp-production-abc123.railway.app` |

**COPY THIS URL** - you'll need it soon!

### 4.2 Test Backend is Working

Let's verify the backend API is running:

| Input Method | Action |
|---|---|
| **Mouse** | Copy the URL and paste it in browser address bar |
| | Add `/health` to the end |
| | Example: `https://yourapp-production.railway.app/health` |
| | Press Enter |

**WHAT YOU SHOULD SEE:**
```json
{"status": "healthy", "timestamp": "2025-11-18T10:30:00Z"}
```

If you see this JSON response, your backend is working! ✅

**IF YOU SEE ERRORS:**
- "502 Bad Gateway" → Backend crashed, check logs (Step 5)
- "Connection refused" → Container still starting, wait 30 seconds
- "404 Not Found" → URL is wrong, verify `/health` endpoint exists

### 4.3 Copy Your Backend URL

This URL is important - copy it now:

**EXAMPLE:** `https://yourapp-production-abc123.railway.app`

**Save it somewhere safe** - you'll paste it in Vercel configuration in Guide 03!

---

## Step 5: Check Deployment Logs

### 5.1 View Real-Time Logs

To verify everything deployed correctly:

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard, find your service |
| | 2. Click "Logs" tab |
| | 3. Scroll to see all logs |

**WHAT YOU SHOULD SEE:**
```
INFO: Application startup complete
INFO: Uvicorn running on 0.0.0.0:5000
✓ Database initialized
✓ Indicators loaded
```

These messages indicate successful startup.

### 5.2 Common Log Messages

| Log Message | Meaning | Action |
|---|---|---|
| "Application startup complete" | App started successfully | ✅ Good, continue |
| "ERROR: Connection refused" | Port already in use | Check other services |
| "ModuleNotFoundError" | Python dependency missing | Check requirements.txt |
| "Permission denied" | Can't write to filesystem | Check volume mounts |

### 5.3 If You See Errors

**COMMON FIX:**

If you see "ModuleNotFoundError: No module named 'flask'":

1. Check that `requirements.txt` is in the `backend/` folder
2. Verify it has all dependencies listed
3. Redeploy: Click deploy button in Railway dashboard
4. Wait for rebuild (2-3 minutes)

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard |
| | 2. Find "Deployments" section |
| | 3. Click "Redeploy" or "Deploy" button |
| | 4. Watch logs update |

---

## Step 6: Set Up Automatic GitHub Deployments

### 6.1 Enable GitHub Auto-Deploy

Railway can automatically redeploy whenever you push code to GitHub:

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard for your service |
| | 2. Click "Settings" tab |
| | 3. Look for "GitHub" or "Deploy" section |
| | 4. Find "Auto Deploy" option |

**WHAT YOU SHOULD SEE:**
- Toggle switch for "Deploy on push"
- Should be enabled (turned ON)
- Shows which branches to deploy from (usually: `main`)

### 6.2 Verify Webhook is Installed

Railway installs a GitHub webhook to listen for pushes:

**VERIFY ON GITHUB:**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to GitHub repo page |
| | 2. Click "Settings" tab |
| | 3. Click "Webhooks" in left sidebar |

**WHAT YOU SHOULD SEE:**
- Entry for `railway.app` webhook
- Shows when it was last triggered
- Recent deliveries listed

---

## Step 7: Generate Railway API Token (For GitHub)

### 7.1 Access Railway Account Settings

| Input Method | Action |
|---|---|
| **Mouse** | 1. In Railway dashboard (top-right) |
| | 2. Click your profile/account icon |
| | 3. Click "Account settings" |

**WHAT YOU SHOULD SEE:**
- Account settings page
- Personal information
- API tokens section

### 7.2 Create API Token

| Input Method | Action |
|---|---|
| **Mouse** | 1. Scroll to find "API Tokens" or "Auth Tokens" |
| | 2. Click "Create Token" or "New Token" button |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Token Name | `GitHub CI/CD` or `Deployment Token` |
| Permissions | Select "All" or appropriate deployment permissions |

### 7.3 Copy the Token

**IMPORTANT: Copy the token NOW** - Railway only shows it once!

| Input Method | Action |
|---|---|
| **Mouse** | Click copy icon next to the token |
| **Keyboard** | Ctrl+C to copy (after selecting) |

**SAVE THIS TOKEN** - you need it for GitHub Secrets next!

---

## Step 8: Add Railway Token to GitHub Secrets

Now let's add the Railway token to GitHub so deployments can happen automatically.

### 8.1 Go to GitHub Repository Settings

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to GitHub repo page |
| | 2. Click "Settings" tab |
| | 3. In left sidebar: "Secrets and variables" → "Actions" |

### 8.2 Add RAILWAY_TOKEN Secret

| Input Method | Action |
|---|---|
| **Mouse** | 1. Find existing "RAILWAY_TOKEN" secret |
| | 2. Click "Update" or edit it |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Name | `RAILWAY_TOKEN` (already set) |
| Value | Paste the token you copied from Railway |

| Input Method | Action |
|---|---|
| **Mouse** | Click "Update secret" button |

**WHAT YOU SHOULD SEE:**
- Secret updated successfully
- Shows last updated timestamp

---

## Step 9: Test Automatic Deployment

Let's verify that changes push automatically from GitHub to Railway:

### 9.1 Make a Small Local Change

In PowerShell, in your TheTool folder:

```powershell
# Edit a comment or add a small change
echo "# Test deployment - $(Get-Date)" >> backend/app.py
```

### 9.2 Commit and Push

```powershell
# Stage the change
git add backend/app.py

# Commit
git commit -m "Test auto-deployment from GitHub"

# Push to GitHub
git push origin main
```

**WHAT YOU SHOULD SEE:**
```
To https://github.com/YOUR_USERNAME/TheTool.git
   abc1234..def5678  main -> main
```

### 9.3 Watch Railway Auto-Deploy

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Railway dashboard |
| | 2. Click on your backend service |
| | 3. Look at "Deployments" tab |

**WHAT YOU SHOULD SEE:**
- New deployment starts automatically
- Status shows: "Building..." → "Deploying..." → "Running"
- Takes 2-3 minutes
- Green checkmark when complete

✅ **Auto-deployment is working!**

---

## Step 10: Verify Database Persistence

Railway volumes ensure your SQLite database persists even if the app restarts.

### 10.1 Check Volume Configuration

| Input Method | Action |
|---|---|
| **Mouse** | 1. Railway dashboard, select your service |
| | 2. Click "Variables" or "Settings" tab |
| | 3. Look for "Volumes" or "Disk" section |

**WHAT YOU SHOULD SEE:**
```
Volumes:
├─ Mount Path: /app/data
└─ Mounted: Yes ✓
```

### 10.2 Verify Database File

The SQLite database should be at: `/app/data/trading_app.db`

**This file persists automatically** - no manual backups needed!

### 10.3 Test Persistence

To verify data survives app restarts:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Test API call to save data |
| | 2. Wait 30 seconds |
| | 3. Restart the app (click restart in Railway) |
| | 4. Verify data still exists with API call |

---

## 🎉 Guide 02 Complete!

### What You've Accomplished:
✅ Created Railway account (with $5 trial credit)  
✅ Deployed Flask backend Docker container  
✅ Configured environment variables  
✅ Verified backend is running (tested /health endpoint)  
✅ Got live backend URL  
✅ Set up automatic GitHub deployments  
✅ Verified database persistence setup  

### Your Backend is Now:
- ✅ **Live 24/7** on Railway
- ✅ **Running on a real URL** (like: `yourapp.railway.app`)
- ✅ **Auto-deploying** when you push to GitHub
- ✅ **Persisting data** in SQLite
- ✅ **Ready for frontend** to connect

### Important URLs & Credentials:

| Item | Value | Where to Find |
|---|---|---|
| **Backend URL** | `https://yourapp.railway.app` | Railway dashboard → Networking |
| **Railway Dashboard** | `https://railway.app/dashboard` | Browser bookmarks |
| **GitHub Webhook** | Configured | GitHub Settings → Webhooks |
| **RAILWAY_TOKEN** | Added to GitHub | GitHub Settings → Secrets |

### Summary of Backend Configuration:

```
Railway Service Configuration:
├─ Name: backend
├─ Language: Python 3.11
├─ Framework: Flask
├─ Port: 5000
├─ Build: Dockerfile (auto-detected)
├─ Environment:
│  ├─ FLASK_ENV=production
│  ├─ DATA_PATH=/app/data
│  └─ LOG_LEVEL=INFO
├─ Volume: /app/data (persistent)
├─ Health Check: /health endpoint ✓
├─ Auto-Deploy: Enabled (on GitHub push)
└─ Status: Running ✅
```

---

## Troubleshooting Guide 02

### Problem: "502 Bad Gateway"
**Solution:**
1. Check Railway logs for errors
2. Verify all environment variables are set correctly
3. Verify requirements.txt is up-to-date
4. Restart the service in Railway dashboard
5. Check if port 5000 is hardcoded correctly

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Solution:**
1. Verify `backend/requirements.txt` exists and is not empty
2. Verify file is in the `backend/` folder, not root
3. Check that Flask is listed in requirements.txt
4. Redeploy (click Deploy button)
5. Wait for rebuild to complete

### Problem: "Connection timeout"
**Solution:**
1. App may still be starting - wait 1-2 minutes
2. Check Railway logs to verify app started
3. Verify backend URL is correct (no typos)
4. Check if app crashed - look for errors in logs

### Problem: "Cannot find Dockerfile"
**Solution:**
1. Verify `backend/Dockerfile` exists
2. Verify it's in the `backend/` folder specifically
3. Verify filename has no extension issues
4. Try disconnecting and reconnecting GitHub repo

### Problem: "Database file growing too large"
**Solution:**
1. Check current database size in Railway volume
2. Run cleanup script if implemented
3. If >1GB, may need to upgrade storage
4. Can delete old analysis results in database

### Problem: "Auto-deploy not working"
**Solution:**
1. Verify webhook is installed: GitHub Settings → Webhooks
2. Verify RAILWAY_TOKEN is in GitHub Secrets
3. Check GitHub Actions logs for errors
4. Try manual deploy: Railway dashboard → Deploy button
5. Verify you pushed to `main` branch (not other branch)

### Problem: "Health check endpoint returns 404"
**Solution:**
1. Verify `/health` endpoint exists in `backend/app.py`
2. Check if Flask app is correctly routing that endpoint
3. Verify FLASK_ENV=production doesn't disable health checks
4. Try accessing other endpoints like `/api/indicators`

---

## Next Steps

You now have a live Flask backend! Next step is deploying your React frontend.

**What Happens Next in Guide 03:**
- Create Vercel account
- Deploy React frontend
- Configure frontend to connect to your Railway backend
- Get live frontend URL
- Test integration

---

## Important Notes

### Railway Trial Credit
- **Valid for 30 days** from signup
- Includes **$5 free credit**
- After trial: Pay-as-you-go billing
- Typical hobby project: $1-5/month
- Can cancel anytime without being charged

### Monitoring Your Usage
To avoid surprise charges:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Railway dashboard |
| | 2. Click "Settings" (left sidebar) |
| | 3. Click "Billing" |
| | 4. View current usage & estimated cost |

### Backing Up Your Database

Railway automatically persists your data, but consider:
1. **Export database periodically** (manual)
2. **Enable version control** for database snapshots
3. **Monitor database size** to ensure it doesn't grow too large

---

## 🚀 You're Halfway Done!

**Progress:**
- ✅ Guide 01: GitHub Setup - COMPLETE
- ✅ Guide 02: Railway Backend - COMPLETE  
- ⏳ Guide 03: Vercel Frontend - NEXT
- ⏳ Guide 04: Integration Testing
- ⏳ Guide 05: Custom Domain (Optional)
- ⏳ Guide 06: Monitoring & Maintenance

**Time Remaining:** ~30-40 minutes to full deployment!

→ **Go to:** `03_VERCEL_FRONTEND_DEPLOY.md`

In the next guide, you'll:
- ✅ Create Vercel account
- ✅ Deploy your React frontend
- ✅ Configure it to use your Railway backend
- ✅ Get your live frontend URL

---

**Guide 02 Status:** ✅ Complete  
**Backend Status:** ✅ Running Live  
**Time Spent:** ~20-25 minutes  
**Next Guide:** 03_VERCEL_FRONTEND_DEPLOY.md  
**Estimated Remaining Time:** ~30 minutes to full deployment
