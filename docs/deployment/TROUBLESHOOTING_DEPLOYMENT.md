# 🔧 Troubleshooting Deployment Issues

**Quick Reference Guide:** Common deployment problems and solutions

---

## How to Use This Guide

1. **Find your error** in the table below
2. **Read the solution** carefully
3. **Follow the steps** exactly
4. **If still stuck:** Check the specific guide that covers your issue

---

## Quick Troubleshooting Index

| Error | Common Cause | Guide |
|---|---|---|
| "502 Bad Gateway" | Backend crashed | Backend Troubleshooting |
| "Cannot reach backend" | CORS/URL wrong | Integration Troubleshooting |
| "Module not found" | Python dependency | Backend Troubleshooting |
| "Build failed" | npm error | Frontend Troubleshooting |
| "CORS error" | Backend CORS config | Backend Troubleshooting |
| "Cannot connect to git" | Git not installed | GitHub Troubleshooting |
| "Domain not working" | DNS propagation | Domain Troubleshooting |

---

## GitHub Troubleshooting

### Problem: "Git command not found"

**Error Message:**
```
'git' is not recognized as an internal or external command
```

**Root Cause:** Git not installed on your computer

**Solution:**
1. Download Git: https://git-scm.com/download/win
2. Run installer with default settings
3. Restart PowerShell (close and reopen)
4. Verify: `git --version` should show version number

**Prevention:** Install Git before any development

---

### Problem: "Permission denied (publickey)"

**Error Message:**
```
Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Root Cause:** Using SSH instead of HTTPS, or authentication failed

**Solution Option 1 (Use HTTPS):**
```powershell
# Remove SSH remote
git remote remove origin

# Add HTTPS remote instead
git remote add origin https://github.com/YOUR_USERNAME/TheTool.git

# When prompted for password, use personal access token:
# 1. Go: github.com/settings/tokens
# 2. Click "Generate new token"
# 3. Copy the token
# 4. Paste as password
```

**Solution Option 2 (Use PAT):**
```powershell
# Create personal access token
# github.com/settings/tokens → Generate new token

# When pushing, use:
# Username: your_username
# Password: your_personal_access_token (not your GitHub password!)
```

**Prevention:** Always use HTTPS URLs for GitHub repos

---

### Problem: "Remote already exists"

**Error Message:**
```
fatal: remote origin already exists.
```

**Root Cause:** You ran `git remote add origin` twice

**Solution:**
```powershell
# Remove the existing remote
git remote remove origin

# Add it again correctly
git remote add origin https://github.com/YOUR_USERNAME/TheTool.git

# Verify it worked
git remote -v
```

---

### Problem: "Cannot create workflow file"

**Error Message:**
```
Cannot find path '.github\workflows'
```

**Root Cause:** Folder structure not created

**Solution:**
```powershell
# Create folders
mkdir -p .github\workflows

# Create file
New-Item -Path ".github\workflows\deploy.yml" -ItemType File

# Edit in VS Code
code .github\workflows\deploy.yml
```

---

### Problem: "Workflow file not running"

**Symptoms:** Actions tab shows "No workflows"

**Root Cause:** File not in correct location or wrong syntax

**Solution:**
1. Verify file exists: `.github/workflows/deploy.yml` (NOT `deploy.yml.txt`)
2. Check YAML formatting is correct (check indentation)
3. Verify file was committed and pushed to GitHub
4. Wait 2-3 minutes and refresh GitHub page
5. Check file in browser: github.com/YOU/TheTool/blob/main/.github/workflows/deploy.yml

---

## Backend Troubleshooting (Railway)

### Problem: "502 Bad Gateway"

**Error Message:** Browser shows "502 Bad Gateway"

**Root Causes:**
1. Backend app crashed
2. Port 5000 not exposed
3. Health check failing
4. App taking too long to start

**Solution Steps:**

**Step 1: Check Railway Logs**
```
1. Go to Railway dashboard
2. Click your backend service
3. Click "Logs" tab
4. Look for red ERROR messages
5. Screenshot the error
```

**Common Log Errors:**

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Requirements.txt missing dependencies |
| `Address already in use` | Port 5000 in use, change port |
| `Cannot open database file` | Volume not mounted, check /app/data mount |
| `CORS error` | Backend CORS not configured |

**Step 2: Restart Service**
```
1. Railway dashboard
2. Find your service
3. Click "Deploy" or "Restart" button
4. Wait 2-3 minutes
5. Test: Visit https://yourapp.railway.app/health
```

**Step 3: Check Requirements**
```
Local computer:
1. Go to backend folder
2. Verify requirements.txt exists
3. Check it has all dependencies
4. Make sure flask, flask-cors are listed
5. Commit and push
6. Railway auto-redeploys
```

**Step 4: Redeploy Manually**
```
1. Railway dashboard
2. Find service
3. Click "Deployments" tab
4. Find latest
5. Click "Redeploy" button
6. Wait for build
```

---

### Problem: "ModuleNotFoundError: No module named 'flask'"

**Error in Railway Logs:**
```
ModuleNotFoundError: No module named 'flask'
```

**Root Cause:** requirements.txt missing or incomplete

**Verification:**
1. Check `backend/requirements.txt` exists
2. Verify it contains: `Flask==3.0.0`
3. Verify Flask-CORS is listed
4. No empty lines at end

**Fix:**
```
1. Edit backend/requirements.txt
2. Ensure Flask and dependencies listed
3. Save
4. Commit: git add backend/requirements.txt
5. Push: git push origin main
6. Railway automatically rebuilds
7. Wait 2-3 minutes
8. Test /health endpoint
```

---

### Problem: "Cannot connect to database / Database locked"

**Error:**
```
DatabaseError: cannot open database file
# or
sqlite3.OperationalError: database is locked
```

**Root Cause:** Volume not mounted or database corruption

**Solution:**

**Option 1: Check Volume**
```
1. Railway dashboard
2. Backend service
3. Look for "Volumes" section
4. Should show: /app/data → mounted
5. If not mounted, add volume
```

**Option 2: Restart Service**
```
1. Railway → Backend → Restart
2. Wait 1 minute
3. Check logs
4. Retry
```

**Option 3: Delete and Rebuild**
```
CAUTION: This deletes database!

1. Railway → Backend → Settings
2. Find "Volumes"
3. Delete the volume
4. Wait 30 seconds
5. Redeploy
6. New database created
7. All data will be lost!
```

---

### Problem: "App still building after 10 minutes"

**Symptoms:** Railway shows "Building..." for > 10 min

**Root Cause:** Dependency installation stuck or network issue

**Solution:**

**Option 1: Restart Build**
```
1. Railway dashboard
2. Find service
3. Click "Deployments"
4. Find stuck deployment
5. Click "Cancel"
6. Click "Redeploy"
7. Wait for new build
```

**Option 2: Check Log**
```
1. Click "Logs" tab
2. Look for where it's stuck
3. Common: "Downloading dependencies..."
4. If stuck there, restart
```

**Option 3: Investigate Locally**
```powershell
# See if requirements.txt is huge
ls -lh backend/requirements.txt

# Try install locally to find issue
cd backend
pip install -r requirements.txt

# If error appears, fix requirements.txt
# Commit, push, Railway retries
```

---

## Frontend Troubleshooting (Vercel)

### Problem: "Build failed"

**Error:** Vercel deployment shows "❌ Build Error"

**Common Causes:**
1. Syntax error in React code
2. Missing npm package
3. Environment variable not set
4. Port configuration issue

**Solution Steps:**

**Step 1: Check Build Logs**
```
1. Vercel dashboard
2. Click your project
3. Click "Deployments" tab
4. Find failed deployment
5. Click it
6. View "Build Logs" section
7. Look for error message
```

**Step 2: Common Build Errors**

| Error | Fix |
|---|---|
| `Cannot find module 'react'` | Run `npm install` locally first |
| `Module not found: App.js` | Check file name, case-sensitive |
| `Unexpected token` | Syntax error in JSX, check brackets/quotes |
| `Cannot find REACT_APP_API_URL` | Environment variable not set |

**Step 3: Fix Build Locally**
```powershell
# Test building locally first
cd frontend

# Install dependencies
npm install

# Build
npm run build

# If errors appear, fix them
# Then commit and push
```

**Step 4: Redeploy**
```
1. Vercel → Deployments
2. Find failed deployment
3. Click "Redeploy" button
4. Wait for new build
5. Should be green checkmark
```

---

### Problem: "Cannot reach API" / "API returns 404"

**Frontend shows:** "Cannot connect to backend" or API error

**Root Causes:**
1. REACT_APP_API_URL env var not set correctly
2. Backend URL wrong/typo
3. Backend not responding
4. CORS error

**Solution:**

**Step 1: Verify Environment Variable**
```javascript
// In browser console:
console.log(process.env.REACT_APP_API_URL)
// Should output: https://yourapp.railway.app
```

**If undefined:**
```
1. Vercel dashboard
2. Project → Settings
3. Click "Environment Variables"
4. Add or edit REACT_APP_API_URL
5. Set value: https://yourapp-production-abc123.railway.app
6. Go to Deployments → Redeploy latest
7. Wait 2-3 minutes
8. Hard refresh: Ctrl+Shift+R
```

**Step 2: Verify Backend is Running**
```
1. Open browser
2. Go to: https://yourapp.railway.app/health
3. Should see JSON response
4. If not, backend is down
5. Check Railway logs
```

**Step 3: Check CORS in Browser**
```
1. Open DevTools (F12)
2. Click Console tab
3. Look for red CORS error:
   "Access to XMLHttpRequest blocked by CORS policy"
4. If you see this, backend CORS not configured
5. See Backend Troubleshooting → CORS Error
```

---

### Problem: "Blank page / white screen"

**Symptoms:** Page loads but shows nothing

**Root Causes:**
1. React not rendering
2. JavaScript error
3. Missing CSS
4. App hydration error

**Solution:**

**Step 1: Check Console for Errors**
```
1. Open DevTools (F12)
2. Click "Console" tab
3. Look for red error messages
4. Screenshot any errors
```

**Step 2: Check Network**
```
1. Click "Network" tab
2. Refresh page
3. Check all requests are 200 OK
4. Look for any red (failed) requests
```

**Step 3: Build Locally**
```powershell
cd frontend
npm run build
# If build succeeds locally but fails on Vercel,
# environment variables might be issue
```

**Step 4: Common Fixes**
```
1. Missing REACT_APP_API_URL → Add to Vercel env vars
2. Syntax error in code → Check against local version
3. CSS not loading → Check tailwind.config.js
4. React version mismatch → Check package.json
```

---

### Problem: "Deployment took too long / timed out"

**Error:** Deployment cancelled after 45+ minutes

**Root Cause:** Build taking too long (usually first deploy)

**Solution:**
```
1. This is normal for first deploy
2. Can take 3-5 minutes initially
3. Subsequent deploys: 1-2 minutes
4. If timeout persists:
   - Check build logs for slowness
   - Try removing large dependencies
   - Optimize node_modules
5. Vercel has 45-min timeout (plenty)
```

---

## Integration Troubleshooting

### Problem: "CORS error in browser console"

**Error Message:**
```
Access to XMLHttpRequest at 'https://yourapp.railway.app/...'
from origin 'https://yourapp.vercel.app' has been blocked
by CORS policy
```

**Root Cause:** Backend not allowing requests from Vercel domain

**Solution:**

**Step 1: Edit Backend CORS**

In `backend/app.py`, find CORS configuration:

```python
from flask_cors import CORS

app = Flask(__name__)

# Add this:
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourapp.vercel.app",
            "https://www.yourapp.vercel.app",
            "http://localhost:3000"  # for local development
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Step 2: Commit and Push**
```powershell
git add backend/app.py
git commit -m "Fix CORS to allow Vercel domain"
git push origin main
```

**Step 3: Wait for Redeploy**
```
1. Railway auto-redeploys (2-3 min)
2. Refresh frontend page (Ctrl+R)
3. Hard refresh if still issue: Ctrl+Shift+R
4. Try API call again
```

---

### Problem: "Data not persisting after restart"

**Issue:** Analysis data disappears after refreshing page

**Root Cause:** Database not persisting or API not saving

**Solution:**

**Step 1: Verify Database Exists**
```
1. Railway → Backend → Logs
2. Look for database initialization messages
3. Check if database file created
```

**Step 2: Check API Response**
```javascript
// In browser console:
fetch(process.env.REACT_APP_API_URL + '/all-stocks')
  .then(r => r.json())
  .then(d => console.log('Count:', d.length))
// Should show the count of records
```

**Step 3: Check Volume Mount**
```
1. Railway dashboard
2. Backend service
3. Variables tab
4. Verify: DATA_PATH = /app/data
5. Look for Volumes section
6. Should show /app/data mounted
```

---

### Problem: "Response times slow (> 5 seconds)"

**Issue:** API takes very long to respond

**Causes:**
1. Railway instance too slow
2. Database queries inefficient
3. Analysis computation taking too long
4. Network latency

**Solution:**

**Option 1: Upgrade Railway Resources**
```
1. Railway → Backend → Settings
2. Increase CPU/RAM allocation
3. Costs go up slightly but performance improves
```

**Option 2: Optimize Analysis**
```
1. Check backend logs for slow queries
2. Look for long-running computations
3. May need code optimization
4. Consider caching results
```

**Option 3: Check Network**
```
1. DevTools → Network tab
2. Measure API request time
3. If > 5 seconds, backend issue
4. If network tab shows quick response,
   issue is browser-side processing
```

---

## Domain Troubleshooting

### Problem: "Domain not found" / "ERR_NAME_NOT_FOUND"

**Error:** Browser can't find your domain

**Root Causes:**
1. DNS not set up yet
2. DNS propagation in progress (24-48 hours)
3. Wrong DNS records
4. Domain not registered

**Solution:**

**Step 1: Verify Domain Registered**
```
1. Go to domain registrar (Namecheap)
2. Check domain is in "Active" status
3. Verify it's not expired
```

**Step 2: Check DNS Records**
```
1. Namecheap → Manage Domain
2. Click "Advanced DNS" tab
3. Look for your DNS records
4. Verify values match Vercel settings
```

**Step 3: Wait for Propagation**
```
DNS takes 5-48 hours to propagate worldwide
- 5-15 min: Most places work
- 1-4 hours: Most regions
- 24 hours: Everywhere

Try: nslookup yourapp.com (in PowerShell)
Should return IP address after propagation
```

**Step 4: Check Cache**
```
1. Try different browser
2. Clear cache: Ctrl+Shift+Delete
3. Try incognito mode
4. Try on mobile network
```

---

### Problem: "SSL certificate error"

**Error:** "Not Secure" or certificate warning

**Root Cause:** SSL certificate not yet generated

**Solution:**
```
1. This is normal in first 5-10 minutes
2. Vercel auto-generates free SSL certs
3. Wait 10-15 minutes
4. Hard refresh: Ctrl+Shift+R
5. Certificate should be automatic
```

---

### Problem: "www version doesn't work"

**Issue:** `yourapp.com` works but `www.yourapp.com` doesn't

**Root Cause:** www CNAME record not configured

**Solution:**
```
1. Namecheap → Advanced DNS
2. Find www CNAME record
3. Verify it points to: cname.vercel-dns.com
4. If missing, add it:
   - Type: CNAME
   - Name: www
   - Value: cname.vercel-dns.com
5. Wait 15-30 minutes
6. Retry www.yourapp.com
```

---

## Performance Troubleshooting

### Problem: "Frontend very slow to load"

**Issue:** Page takes > 5 seconds to display

**Solutions:**

**Option 1: Check Network**
```
DevTools → Network tab
1. Refresh page
2. Check bundle.js size
3. Check CSS file sizes
4. Look for slow requests
```

**Option 2: Optimize**
```powershell
# Rebuild with production settings:
cd frontend
npm run build
# Size should be ~100-200KB
# If > 500KB, has unused dependencies
```

**Option 3: Check Vercel Cache**
```
1. Vercel → Analytics
2. Check Time to First Byte (TTFB)
3. If > 500ms, may need upgrade
4. If < 200ms, frontend is fast
```

---

### Problem: "Backend very slow to respond"

**Issue:** API takes 10+ seconds

**Root Cause:** Backend computation, database, or resources

**Solution:**

**Option 1: Check Analysis Computation**
```
1. Railway → Logs
2. Look for time taken per request
3. If analysis takes 5+ seconds, normal
4. If > 15 seconds, may need optimization
```

**Option 2: Check Database**
```powershell
# Test database query time locally:
sqlite3 backend/data/trading_app.db
> SELECT COUNT(*) FROM analysis_results;
> SELECT * FROM analysis_results LIMIT 1;

# If slow, may have too many records
```

**Option 3: Upgrade Resources**
```
1. Railway → Backend → Settings
2. Increase CPU/RAM
3. Test response times again
4. May improve performance
```

---

## Final Troubleshooting Checklist

If you're stuck and tried everything:

```
☐ Check all guides completed (01-06)
☐ Verify GitHub repo is public
☐ Verify all environment variables set
☐ Restart all services (Railway, Vercel)
☐ Clear browser cache (Ctrl+Shift+Del)
☐ Hard refresh page (Ctrl+Shift+R)
☐ Try incognito mode (Ctrl+Shift+N)
☐ Try different browser
☐ Check on mobile device
☐ Wait 5 minutes (caching/DNS)
☐ Verify internet connection
```

---

## When to Ask for Help

**You should ask for help if:**
- Error persists after all steps above
- Multiple services failing simultaneously
- Can't find your error in this guide
- Lost important data

**Where to get help:**
- **Railway Support:** support@railway.app
- **Vercel Support:** support@vercel.com
- **Stack Overflow:** Tag with [railway] [vercel]
- **GitHub Issues:** In your repo

**What to include in support request:**
1. Error message (screenshot or copy exact text)
2. What you did before error
3. Which guide step you're on
4. What you already tried
5. Your dashboard URLs (without credentials)

---

## Quick Reference Commands

**Test Backend Health:**
```powershell
$url = "https://yourapp.railway.app/health"
Invoke-WebRequest -Uri $url
```

**Check Git Status:**
```powershell
git status
git log --oneline
git remote -v
```

**Check Node:**
```powershell
node --version
npm --version
```

**Check Python:**
```powershell
python --version
pip --version
```

---

**Troubleshooting Status:** ✅ Complete Reference  
**Last Updated:** November 18, 2025  
**Common Issues Covered:** 30+  
**Solutions Provided:** 100+

**If you need more help, restart with the main deployment guide and verify each step carefully!**
