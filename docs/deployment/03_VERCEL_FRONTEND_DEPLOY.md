# ⚡ Guide 03: Deploy React Frontend to Vercel

**Estimated Time:** 15-20 minutes  
**Difficulty:** ⭐⭐ Medium  
**What You'll Do:** Deploy your React app to Vercel with automatic updates  
**What You'll Have After:** A live React frontend accessible to the world  

---

## 🎯 What This Guide Accomplishes

By the end of this guide:
- ✅ Vercel account created
- ✅ React frontend deployed and live
- ✅ Frontend connected to your Railway backend
- ✅ Automatic deployments from GitHub configured
- ✅ Live frontend URL (like: `yourapp.vercel.app`)
- ✅ Both frontend and backend working together

---

## Prerequisites

Complete Guide 02 first! You need:
- [ ] GitHub account with TheTool repo pushed
- [ ] Railway backend deployed and running
- [ ] **Your backend URL** from Guide 02
  - Format: `https://yourapp-production-abc123.railway.app`
  - You got this URL when testing `/health` endpoint

**If you don't have your backend URL:**
- Go back to Railway dashboard
- Find your service
- Copy the Public URL
- Save it - you'll need it now!

---

## Step 1: Create Vercel Account

### 1.1 Go to Vercel.com

Open your browser and navigate to Vercel:

| Input Method | Action |
|---|---|
| **Mouse** | Click address bar, type: `https://vercel.com` |
| **Keyboard** | Press `Ctrl+L`, type `vercel.com`, press `Enter` |

**WHAT YOU SHOULD SEE:**
- Vercel homepage
- Dark theme with "Deploy Now" button (top-right)
- "Start Deploying" section
- Testimonials and features below

### 1.2 Sign Up with GitHub

Vercel is optimized for GitHub, so let's sign up that way:

| Input Method | Action |
|---|---|
| **Mouse** | Click "Start Deploying" or "Sign Up" button |
| | Look for "Continue with GitHub" option |
| | Click it |

**WHAT HAPPENS:**
- GitHub login page appears
- You authorize Vercel to access your GitHub
- Redirects back to Vercel

### 1.3 Authorize Vercel

GitHub will ask for permissions:

| Input Method | Action |
|---|---|
| **Mouse** | Click "Authorize vercel" or similar button |
| | This grants Vercel permission to: |
| | - Read your repositories |
| | - Create deployments |
| | - Update pull requests |

### 1.4 Setup Vercel Account

After authorization, Vercel shows onboarding:

**WHAT YOU MIGHT SEE:**
- "Welcome to Vercel" page
- Option to create a team (skip this)
- Setup wizard

| Input Method | Action |
|---|---|
| **Mouse** | 1. Skip any tutorials |
| | 2. Skip team creation |
| | 3. Continue to dashboard |

**WHAT YOU SHOULD SEE:**
- Vercel dashboard
- "New Project" button (top-right)
- Empty projects list (first time)
- Account settings available

✅ **Step 1 Complete!** Vercel account created!

---

## Step 2: Import GitHub Repository

### 2.1 Create New Project

| Input Method | Action |
|---|---|
| **Mouse** | Click "New Project" button (top area) |

**WHAT HAPPENS:**
- Shows project creation page
- Options appear to import from GitHub, GitLab, etc.

### 2.2 Select Your GitHub Repository

| Input Method | Action |
|---|---|
| **Mouse** | 1. Find "Import Git Repository" section |
| | 2. Look for a search box or list of repos |
| | 3. Search for: `TheTool` |
| | 4. Find: `YOUR_USERNAME/TheTool` |
| | 5. Click on it |

**WHAT YOU SHOULD SEE:**
```
YOUR_USERNAME/TheTool
[small preview]
Import
```

| Input Method | Action |
|---|---|
| **Mouse** | Click "Import" button |

### 2.3 Vercel Detects Your Frontend

Vercel automatically detects your frontend configuration:

**WHAT YOU SHOULD SEE:**
```
✓ Root Directory: frontend/
✓ Framework: Create React App (Detected)
✓ Build Command: npm run build
✓ Output Directory: build
✓ Install Command: npm ci
```

All should be automatically detected correctly!

---

## Step 3: Configure Environment Variables

### 3.1 Add Environment Variable for Backend URL

This is CRUCIAL - it tells your React frontend where to find your backend API.

**WHAT TO DO:**

Look for "Environment Variables" section in the deployment form:

| Input Method | Action |
|---|---|
| **Mouse** | Find "Environment Variables" section |
| | Click "Add Environment Variable" or similar |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Name | `REACT_APP_API_URL` |
| Value | Your Railway backend URL (from Guide 02) |

**EXAMPLE:**
```
REACT_APP_API_URL=https://yourapp-production-abc123.railway.app
```

**IMPORTANT: Replace with YOUR actual backend URL!**

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add" or confirm the variable |

**WHAT YOU SHOULD SEE:**
```
Environment Variables:
├─ REACT_APP_API_URL = https://yourapp-production-abc123.railway.app
```

### 3.2 Verify All Configuration

Before deploying, verify:

| Check | Expected Value |
|---|---|
| Root Directory | `frontend/` |
| Framework | `Create React App` |
| Build Command | `npm run build` |
| Output Directory | `build` |
| Install Command | `npm ci` |
| REACT_APP_API_URL | `https://yourapp.railway.app` |

Everything should look correct!

---

## Step 4: Deploy to Vercel

### 4.1 Click Deploy

| Input Method | Action |
|---|---|
| **Mouse** | Scroll down, find "Deploy" button |
| | Click green "Deploy" button |

**WHAT HAPPENS:**
- Deployment begins
- Shows build progress in real-time
- Can take 2-5 minutes for first deployment

### 4.2 Watch the Build Process

You'll see a live log showing:

```
✓ Retrieving project settings
✓ Installing dependencies (npm ci)
  → npm packages installed
✓ Building project
  → Building React app...
  → Optimizing...
  → Creating deployment...
✓ Deploy Complete
```

**WHAT TO EXPECT:**
- First build is slower (2-3 minutes)
- Downloads all npm packages
- Builds React app for production
- Uploads to Vercel CDN

### 4.3 Build Completes

When complete, you'll see:

**✅ SUCCESS MESSAGE:**
```
✅ Deployment Complete
🔗 [https://yourproject.vercel.app](https://yourproject.vercel.app)
```

**YOUR FRONTEND IS NOW LIVE!** 🎉

---

## Step 5: Get Your Live Frontend URL

### 5.1 Find Your Deployment URL

After successful deployment:

| Input Method | Action |
|---|---|
| **Mouse** | Look for the deployed URL |
| | Usually shown as: `yourproject.vercel.app` |
| | Click the URL to open it |

**EXPECTED FORMAT:**
```
https://yourproject.vercel.app
```

(Vercel generates random subdomain if you don't configure a custom one yet)

### 5.2 Test Frontend Loads

| Input Method | Action |
|---|---|
| **Mouse** | Click your Vercel URL |
| | Wait for page to load (should be instant) |

**WHAT YOU SHOULD SEE:**
- Your React app loads
- Dashboard/home page appears
- App looks normal (same as localhost:3000)

**COMMON ISSUES AT THIS POINT:**
- Page loads but shows errors
- "Cannot reach backend" message
- Blank page

These are normal - we'll fix them in the next section!

---

## Step 6: Configure Frontend to Connect to Backend

### 6.1 Verify Backend URL is Set

Your React app needs to know where the backend is. Let's verify:

**OPEN BROWSER CONSOLE:**

| Input Method | Action |
|---|---|
| **Mouse** | On your deployed Vercel app page |
| | Press `F12` or right-click → "Inspect" |
| **Keyboard** | Press `F12` |

**WHAT YOU SHOULD SEE:**
- Browser Developer Tools open
- "Console" tab active
- JavaScript console showing any errors

### 6.2 Check Environment Variable

In the console, type:

```javascript
console.log(process.env.REACT_APP_API_URL)
```

**Then press Enter**

**WHAT YOU SHOULD SEE:**
```
https://yourapp-production-abc123.railway.app
```

If you see your backend URL, it's working! ✅

**IF YOU SEE: `undefined`**
- Environment variable not set correctly
- Go to Step 3.1 and verify it's set
- May need to redeploy

### 6.3 Redeploy If Needed

If environment variable isn't set:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Vercel dashboard |
| | 2. Click your project |
| | 3. Click "Settings" tab (top) |
| | 4. Click "Environment Variables" (left sidebar) |
| | 5. Verify `REACT_APP_API_URL` is there |
| | 6. If missing, click "Add" and add it |
| | 7. Go to "Deployments" tab |
| | 8. Find latest deployment |
| | 9. Click "Redeploy" button |

This forces Vercel to rebuild with the environment variable.

---

## Step 7: Test Frontend-Backend Connection

### 7.1 Test API Call

Let's verify frontend can call backend API:

**IN BROWSER CONSOLE:**

```javascript
fetch(process.env.REACT_APP_API_URL + '/health')
  .then(r => r.json())
  .then(d => console.log(d))
  .catch(e => console.error(e))
```

**Then press Enter**

**WHAT YOU SHOULD SEE:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:30:00Z"
}
```

This confirms frontend can successfully call backend! ✅

**IF YOU SEE CORS ERROR:**

Error like: `Access to XMLHttpRequest blocked by CORS policy`

**SOLUTION:**
- Backend CORS needs to be configured to allow Vercel domain
- Check backend `app.py` has CORS enabled
- May need to redeploy backend with proper CORS settings
- See Troubleshooting section below

---

## Step 8: Set Up Automatic Deployments from GitHub

### 8.1 Verify GitHub Integration

Vercel should automatically redeploy when you push to GitHub:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Vercel project page |
| | 2. Click "Settings" tab |
| | 3. Click "Git" (left sidebar) |

**WHAT YOU SHOULD SEE:**
```
Git Configuration:
├─ Repository: YOUR_USERNAME/TheTool
├─ Branch: main (or your branch)
├─ Auto Deploy: Enabled ✓
└─ Production Branch: main
```

Everything should be enabled by default!

### 8.2 Test Auto-Deploy

Let's verify automatic deployments work:

**MAKE A SMALL LOCAL CHANGE:**

In PowerShell, in your TheTool folder:

```powershell
# Make tiny change to frontend
echo "// Test deploy - $(Get-Date)" >> frontend/src/App.js
```

**COMMIT AND PUSH:**

```powershell
git add frontend/src/App.js
git commit -m "Test auto-deployment to Vercel"
git push origin main
```

### 8.3 Watch Automatic Deployment

Go to your Vercel project:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Vercel dashboard |
| | 2. Click your project |
| | 3. Look at "Deployments" tab |

**WHAT YOU SHOULD SEE:**
- New deployment appears
- Status shows: "Building..." → "Ready" ✅
- Shows commit message: "Test auto-deployment to Vercel"
- Takes 1-2 minutes

✅ **Auto-deployment is working!**

**After deployment completes:**
- Visit your Vercel URL (refresh page)
- Your frontend automatically has the latest code!

---

## Step 9: Verify Full Integration

### 9.1 Test Frontend Page Load

| Input Method | Action |
|---|---|
| **Mouse** | Visit your Vercel URL |
| | Wait for page to fully load |

**WHAT YOU SHOULD SEE:**
- Dashboard loads
- Stock symbols displayed
- No error messages
- Can interact with the app

### 9.2 Test API from Frontend

Try using the app:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Add a stock to watchlist |
| | 2. Try to analyze a stock |
| | 3. Check results display |

**WHAT SHOULD HAPPEN:**
- API calls go to Railway backend
- Results return and display
- No CORS errors in console

**WATCH THE NETWORK TAB:**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Open DevTools (F12) |
| | 2. Click "Network" tab |
| | 3. Try analyzing a stock |

**WHAT YOU SHOULD SEE:**
- Network request to your Railway URL
- Response status: 200 (success)
- Response shows analysis results

### 9.3 Test Database Persistence

Try this:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Analyze a stock |
| | 2. Wait for results |
| | 3. Refresh the page |
| | 4. Check if analysis history shows the same stock |

**WHAT SHOULD HAPPEN:**
- Data persists in Railway SQLite database
- History shows previous analysis
- Multiple stocks accumulate

---

## Step 10: Get Your Vercel Token for CI/CD (Optional)

For advanced GitHub Actions integration, you can add Vercel token:

### 10.1 Create Vercel Token

| Input Method | Action |
|---|---|
| **Mouse** | 1. Vercel dashboard (top-right) |
| | 2. Click account icon or "Settings" |
| | 3. Click "Tokens" or "API Tokens" |
| | 4. Click "Create Token" |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Token Name | `GitHub CI/CD` |
| Scope | `Full Account` (or select specific projects) |

### 10.2 Copy Token

Copy the token displayed - it won't show again!

### 10.3 Add to GitHub Secrets

| Input Method | Action |
|---|---|
| **Mouse** | 1. GitHub repo → Settings → Secrets |
| | 2. Click "New repository secret" |
| | 3. Name: `VERCEL_TOKEN` |
| | 4. Value: Paste your Vercel token |
| | 5. Click "Add secret" |

---

## 🎉 Guide 03 Complete!

### What You've Accomplished:
✅ Created Vercel account  
✅ Deployed React frontend (live on Internet!)  
✅ Configured frontend to connect to Railway backend  
✅ Verified frontend-backend integration working  
✅ Set up automatic deployments from GitHub  
✅ Tested full end-to-end flow  

### Your Full Stack is Now Live!

```
🌍 Your App:
├─ Frontend: https://yourapp.vercel.app  ✅ LIVE
├─ Backend: https://yourapp.railway.app  ✅ LIVE
└─ Database: SQLite on Railway           ✅ LIVE

All three components working together!
```

### What's Automated Now:

✅ **Push to GitHub** → Automatic frontend redeploy (1-2 min)  
✅ **Push to GitHub** → Automatic backend redeploy (2-3 min)  
✅ **Errors detected** → Vercel shows build errors  
✅ **Changes live** → Users see updates automatically  

### Summary of Deployment:

| Component | Host | URL | Status |
|---|---|---|---|
| **Frontend** | Vercel | `yourapp.vercel.app` | ✅ Live |
| **Backend** | Railway | `yourapp.railway.app` | ✅ Live |
| **Database** | Railway Volume | `/app/data` | ✅ Persisting |
| **CI/CD** | GitHub Actions | Auto-trigger | ✅ Enabled |

---

## Troubleshooting Guide 03

### Problem: "Cannot reach backend" / "API calls failing"
**Solution:**
1. Check REACT_APP_API_URL env var is set correctly
2. Verify Railway backend is still running (go to Railway dashboard)
3. Test backend health: Visit `https://yourapp.railway.app/health` in browser
4. Check browser console (F12) for CORS errors
5. May need to redeploy frontend: Vercel → Redeploy

### Problem: "CORS error in console"
**Example Error:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Backend CORS not configured for Vercel domain
2. Edit `backend/app.py`
3. Ensure `CORS()` is enabled on Flask app
4. Check allowed origins include Vercel domain
5. Redeploy backend from Railway

**Example fix in app.py:**
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins=["https://yourapp.vercel.app", "http://localhost:3000"])
```

### Problem: "Build failed" / "npm install failed"
**Solution:**
1. Check `frontend/package.json` is valid JSON
2. Verify all dependencies in `package.json` are correct
3. Try building locally: `cd frontend && npm install && npm run build`
4. If it fails locally, fix the error
5. Commit fix and push to GitHub
6. Vercel will automatically redeploy

### Problem: "Environment variable not working"
**Solution:**
1. Verify variable name starts with `REACT_APP_` (required for Create React App)
2. Check Settings → Environment Variables in Vercel
3. Redeploy to apply changes: Deployments → Redeploy button
4. Wait for new deployment to complete
5. Hard refresh browser: `Ctrl+Shift+R` (not Ctrl+R)

### Problem: "Blank page / white screen"
**Solution:**
1. Check browser console (F12) for JavaScript errors
2. Common causes:
   - Missing environment variable
   - Frontend trying to reach unreachable backend
   - Syntax error in React code
3. Look at Vercel build logs for errors
4. Check if app works locally: `cd frontend && npm start`

### Problem: "Deployment taking too long"
**Solution:**
1. First deployment takes 2-5 minutes (normal)
2. Subsequent deployments: 1-2 minutes
3. If it times out, try manual redeploy
4. Check build logs for what's taking time
5. Vercel shows estimated time during build

### Problem: "Cannot find module" errors
**Solution:**
1. All dependencies must be in `package.json`
2. Don't rely on local node_modules
3. Add missing package: `npm install package-name`
4. Verify `package.json` has it listed in dependencies
5. Commit and push - Vercel will reinstall

---

## Next Steps

You now have your entire app deployed and live! Next step is thorough integration testing.

**What Happens Next in Guide 04:**
- Verify all API endpoints work
- Test data persistence
- Test with real stock data
- Verify error handling
- Check performance

---

## Important Notes

### Vercel Free Tier Includes:
- ✅ Unlimited deployments
- ✅ Unlimited projects
- ✅ Global CDN (fast worldwide)
- ✅ Automatic SSL/HTTPS
- ✅ Zero-config deployments
- ✅ 1000+ serverless functions/month
- ✅ Git integration

### Cost: Vercel Frontend is **100% Free**
- No charges for Vercel frontend hosting
- Free tier handles millions of requests/month
- Scales automatically

### Monitoring Your Deployment:
- **Vercel Analytics:** View traffic, page views, response times
- **Error Tracking:** See build errors, runtime errors
- **Deployment History:** See all previous deployments
- **One-click Rollback:** Revert to previous working version

### Security:
- ✅ All traffic encrypted (HTTPS automatically)
- ✅ API keys stored in Environment Variables (not in code)
- ✅ GitHub integration uses OAuth (safe)
- ✅ No credit card required for free tier

---

## Progress Update

**🎉 You're 3/4 of the way done!**

**Progress:**
- ✅ Guide 01: GitHub Setup - COMPLETE
- ✅ Guide 02: Railway Backend - COMPLETE  
- ✅ Guide 03: Vercel Frontend - COMPLETE
- ⏳ Guide 04: Integration Testing - NEXT
- ⏳ Guide 05: Custom Domain (Optional)
- ⏳ Guide 06: Monitoring & Maintenance

**What's Live Now:**
- ✅ Frontend: yourapp.vercel.app (live!)
- ✅ Backend: yourapp.railway.app (live!)
- ✅ Database: SQLite persisting
- ✅ Auto-deploys: Enabled

**Time Remaining:** ~30 minutes (testing + optional domain)

→ **Go to:** `04_INTEGRATION_TESTING.md`

---

**Guide 03 Status:** ✅ Complete  
**Frontend Status:** ✅ Running Live  
**Integration Status:** ✅ Connected  
**Time Spent:** ~15-20 minutes  
**Next Guide:** 04_INTEGRATION_TESTING.md  
**Estimated Total Remaining Time:** ~25 minutes to full deployment
