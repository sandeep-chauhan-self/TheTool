# VERCEL CONFIGURATION - CRITICAL FOR CORS FIX

## Step 1: Go to Vercel Dashboard
https://vercel.com/dashboard

## Step 2: Select TheTool Project

## Step 3: Go to Settings → Environment Variables

## Step 4: Add This Variable for PREVIEW Deployments

**Name:** `REACT_APP_API_BASE_URL`  
**Value:** `https://thetool-development.up.railway.app`  
**Environments:** Check ✅ **Preview** (NOT Production)

## Step 5: Save and Redeploy

1. Click "Save"
2. Go to Deployments
3. Find your development branch deployment
4. Click the three dots → "Redeploy"
5. Wait 3-5 minutes for redeploy

---

## What This Does

- **Preview deployments** (from any branch): `REACT_APP_API_BASE_URL=https://thetool-development.up.railway.app`
- **Production deployment** (the-tool-theta.vercel.app): `REACT_APP_API_BASE_URL` NOT set (uses hostname detection)

---

## Verification After Deploy

1. Open: https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app
2. Open DevTools Console (F12)
3. Look for GREEN message: `[API] Using REACT_APP_API_BASE_URL override: https://thetool-development.up.railway.app`
4. OR ORANGE message: `[API ROUTING] hostname="..." → backend="https://thetool-development.up.railway.app"`
5. Go to "All Stocks" → Should load without CORS error ✅

---

## If Still Getting CORS Error

1. Hard refresh: `Ctrl+Shift+R`
2. Check console for GREEN message (override is working)
3. If GREEN message shows **production** backend URL → variable is set wrong
4. Re-check Vercel dashboard Settings → Environment Variables

---

## Technical Details

The code now has TWO levels of routing:

**Priority 1 (HIGHEST):** `REACT_APP_API_BASE_URL` environment variable
- If set on Vercel → use it
- This is where we force development backend for previews

**Priority 2:** Hostname detection
- If env var not set → detect from `window.location.hostname`
- Production: `the-tool-theta.vercel.app` → production backend
- Everything else → development backend

This is **fool-proof** because:
1. Environment variables always override code
2. Vercel's environment variable system is reliable
3. No caching or build issues can bypass this

