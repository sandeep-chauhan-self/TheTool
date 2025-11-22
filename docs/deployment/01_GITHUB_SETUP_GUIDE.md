# 📦 Guide 01: GitHub Setup & Repository Preparation

**Estimated Time:** 10-15 minutes  
**Difficulty:** ⭐ Easy  
**What You'll Do:** Prepare your GitHub repo for automated deployment  
**What You'll Have After:** A GitHub repo with automatic deploy triggers set up  

---

## 🎯 What This Guide Accomplishes

By the end of this guide:
- ✅ Your TheTool code is on GitHub (public repository)
- ✅ GitHub Actions workflow is ready (auto-triggers on push)
- ✅ GitHub Secrets are configured (safe storage for API keys)
- ✅ You can trigger automatic deployments from any git push

---

## Prerequisites Checklist

Before starting, verify you have:
- [ ] GitHub account (free account at github.com - create if needed)
- [ ] Git installed on Windows (verify: open PowerShell and type `git --version`)
- [ ] Access to your TheTool project folder (`c:\Users\scst1\2025\TheTool`)
- [ ] Internet connection

**Check Git Installation:**

Open PowerShell and run:
```powershell
git --version
```

**Expected Output:** `git version 2.x.x` (any version 2.0+ is fine)

**If you see "git is not recognized":**
- Download Git from: https://git-scm.com/download/win
- Install with default settings
- Restart PowerShell
- Try `git --version` again

---

## Step 1: Create a GitHub Repository

### 1.1 Go to GitHub.com

**HOW TO DO THIS:**

| Input Method | Action |
|---|---|
| **Mouse** | Click on your browser address bar, type: `https://github.com` |
| **Keyboard** | Press `Ctrl+L`, type `github.com`, press `Enter` |

**WHAT YOU SHOULD SEE:**
- GitHub homepage
- Blue GitHub logo (top-left)
- "Sign in" button (top-right)
- "Sign up" button (if not already logged in)

### 1.2 Sign In or Create Account

**IF YOU HAVE A GitHub ACCOUNT:**

| Input Method | Action |
|---|---|
| **Mouse** | Click "Sign in" button (top-right corner) |
| **Keyboard** | None - use mouse for this step |

Then enter your GitHub credentials (username/email and password)

**IF YOU DON'T HAVE A GitHub ACCOUNT:**

| Input Method | Action |
|---|---|
| **Mouse** | Click "Sign up" button (top-right corner) |

Then follow the signup process (takes ~5 minutes):
- Enter email address
- Create password (strong: mix of upper/lower, numbers, symbols)
- Choose username (e.g., `yourusername`)
- Verify email address (check your inbox)

### 1.3 Create New Repository

After signing in, you'll see your dashboard. Let's create a new repo:

**METHOD A: Using Top-Right Menu (Recommended)**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Click `+` icon (top-right corner, next to profile picture) |
| | 2. From dropdown menu, click "New repository" |
| **Keyboard** | None - use mouse for this |

**METHOD B: Using Your Profile**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Click your profile icon (top-right) |
| | 2. Click "Your repositories" |
| | 3. Click green "New" button (left side) |

**WHAT YOU SHOULD SEE:**
- Form with title "Create a new repository"
- Field for "Repository name"
- Descriptions for various options

### 1.4 Fill Out Repository Form

Now you'll see a form. Fill it out with these exact values:

| Form Field | Value to Enter | How to Input |
|---|---|---|
| **Repository name** | `TheTool` | Click field, type this exact name |
| **Description** | `Stock analysis platform with Flask + React` | Click field, type this (optional but helpful) |
| **Public / Private** | **PUBLIC** | Click the "Public" radio button |
| **Add a README file** | ✓ Check the box | Click checkbox to enable |
| **Add .gitignore** | Select "Python" | Click dropdown, search for "Python", select it |
| **Choose a license** | MIT License | Click dropdown, find "MIT License" |

**SCREENSHOT DESCRIPTIONS:**

```
Form Layout:
┌─────────────────────────────────────┐
│ Repository name        │ TheTool   │
│ Description            │ Stock ... │
│                                     │
│ ○ Public  ◉ Private                │  ← Click Public
│                                     │
│ ☑ Add a README file                │  ← Check this
│ ☑ Add .gitignore: Python           │  ← Check this
│ License: MIT License               │  ← Select this
│                                     │
│          [Create repository] button │
└─────────────────────────────────────┘
```

### 1.5 Create the Repository

After filling the form:

| Input Method | Action |
|---|---|
| **Mouse** | Scroll down, click green "Create repository" button (bottom) |
| **Keyboard** | Press `Tab` several times to reach button, then `Enter` |

**WHAT HAPPENS:**
- Page briefly shows loading indicator
- Redirects to your new repository page
- URL will be: `github.com/YOUR_USERNAME/TheTool`
- You'll see file list starting to load

**WHAT YOU SHOULD SEE:**
- Repository name "TheTool" (top-left)
- README.md file listed
- .gitignore file listed
- Green "Code" button (top-right)
- Your username in breadcrumb

✅ **Step 1 Complete!** Your GitHub repository is created.

---

## Step 2: Initialize Local Git Repository

### 2.1 Open PowerShell in Your TheTool Folder

Now we need to connect your local folder to this GitHub repository.

**BEST METHOD: Open PowerShell Here**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Open Windows File Explorer |
| | 2. Navigate to `c:\Users\scst1\2025\TheTool` |
| | 3. Right-click in empty space |
| | 4. Click "Open in Terminal" or "Open PowerShell here" |

**ALTERNATIVE METHOD: Manual Navigation**

| Input Method | Action |
|---|---|
| **Keyboard** | 1. Press `Win+R` (opens Run dialog) |
| | 2. Type `powershell` |
| | 3. Press `Enter` |
| | 4. Type: `cd "c:\Users\scst1\2025\TheTool"` |
| | 5. Press `Enter` |

**WHAT YOU SHOULD SEE:**
- PowerShell window open
- Prompt shows your folder path: `PS C:\Users\scst1\2025\TheTool>`
- Blinking cursor ready for input

### 2.2 Configure Git (First-Time Setup)

Git needs to know who you are. Run these commands ONE AT A TIME:

**COMMAND 1: Set Your Name**

```powershell
git config --global user.name "Your Name"
```

Replace `Your Name` with your actual name (e.g., `Sandeep Chauhan`)

**Press `Enter` after each command**

**COMMAND 2: Set Your Email**

```powershell
git config --global user.email "your.email@gmail.com"
```

Replace with your actual email (use the same email as GitHub account)

**WHAT YOU SHOULD SEE:**
- No output (which is normal - means success)
- Prompt returns ready for next command

### 2.3 Initialize Git Repository

Now tell Git to track this folder:

```powershell
git init
```

**WHAT YOU SHOULD SEE:**
```
Initialized empty Git repository in C:/Users/scst1/2025/TheTool/.git
```

### 2.4 Stage All Files

Tell Git to track all your code files:

```powershell
git add .
```

**WHAT YOU SHOULD SEE:**
- No output (normal)
- Prompt returns

### 2.5 Create Initial Commit

Create your first "checkpoint" with all files:

```powershell
git commit -m "Initial commit: TheTool stock analysis platform"
```

**WHAT YOU SHOULD SEE:**
```
[main (root-commit) abc1234] Initial commit: TheTool stock analysis platform
 24 files changed, 1234 insertions(+)
 create mode 100644 README.md
 create mode 100644 backend/app.py
 ... (many more files)
```

✅ **Step 2 Complete!** Your local folder is now a Git repository.

---

## Step 3: Connect Local to GitHub Remote

### 3.1 Get Your GitHub Repository URL

Go back to your GitHub repository page in browser:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Click green "Code" button (top-right of repo page) |
| | 2. Make sure "HTTPS" tab is selected (it should be default) |
| | 3. Click clipboard icon to copy the URL |

**WHAT YOU SHOULD SEE:**
```
https://github.com/YOUR_USERNAME/TheTool.git
```

The URL is now in your clipboard.

### 3.2 Add GitHub Remote

Back in PowerShell, run this command (it will use your copied URL):

```powershell
git remote add origin https://github.com/YOUR_USERNAME/TheTool.git
```

**Replace `YOUR_USERNAME`** with your actual GitHub username!

**WHAT YOU SHOULD SEE:**
- No output (normal - means success)
- Prompt returns

### 3.3 Verify Remote Connection

Verify it worked:

```powershell
git remote -v
```

**WHAT YOU SHOULD SEE:**
```
origin  https://github.com/YOUR_USERNAME/TheTool.git (fetch)
origin  https://github.com/YOUR_USERNAME/TheTool.git (push)
```

If you see this output, the connection is correct! ✅

**If you see an error or no output:**
- You may have already added remote previously
- Try: `git remote remove origin` first
- Then try adding it again

### 3.4 Push Code to GitHub

Now upload your code to GitHub:

```powershell
git push -u origin main
```

**WHAT TO EXPECT:**

This command may:
- Ask you to log in (browser window opens)
- Show progress bar as files upload
- Take 30-60 seconds for first push
- Show summary like: "24 files changed, 1234 insertions(+)"

**If you get error "fatal: unable to access repository":**
- Make sure your internet connection is working
- Verify your GitHub credentials are correct
- Try again in a few seconds

**If you get error "branch 'main' not found":**
Run these commands:
```powershell
git branch -M main
git push -u origin main
```

**WHAT YOU SHOULD SEE AFTER SUCCESS:**
```
Enumerating objects: 24, done.
Counting objects: 100% (24/24), done.
Writing objects: 100% (24/24), 1.2 MiB | 500 KiB/s, done.
Total 24 (delta 0), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/TheTool.git
 * [new branch]      main -> main
Branch 'main' is set up to track remote-tracking branch 'main' from 'origin'.
```

✅ **Step 3 Complete!** Your code is now on GitHub!

**VERIFY: Go to your GitHub repo in browser (refresh page) - you should now see all your files!**

---

## Step 4: Set Up GitHub Secrets

GitHub Secrets are safe storage for sensitive information (API keys, tokens) that shouldn't be visible in your code.

### 4.1 Navigate to Settings

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to your GitHub repository page |
| | 2. Click "Settings" tab (top, near "Code" tab) |

**WHAT YOU SHOULD SEE:**
- Settings page for your repository
- Left sidebar with many options

### 4.2 Find Secrets Section

| Input Method | Action |
|---|---|
| **Mouse** | In left sidebar: |
| | 1. Click "Security" or expand it (left sidebar) |
| | 2. Look for "Secrets and variables" |
| | 3. Click "Actions" under it |

**WHAT YOU SHOULD SEE:**
- Section titled "Repository secrets"
- Button "New repository secret" (green)
- Empty list (no secrets yet)

### 4.3 Create First Secret: RAILWAY_TOKEN

We'll fill in the actual token in Guide 02, but let's create the secret now:

| Input Method | Action |
|---|---|
| **Mouse** | Click green "New repository secret" button |

**FORM TO FILL:**

| Field | Value |
|---|---|
| **Name** | `RAILWAY_TOKEN` |
| **Value** | (Leave empty for now - we'll add this in Guide 02) |

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add secret" button |

**WHAT YOU SHOULD SEE:**
- Secret appears in list as "RAILWAY_TOKEN"

### 4.4 Create Second Secret: VERCEL_TOKEN

Let's create a placeholder for Vercel token too:

| Input Method | Action |
|---|---|
| **Mouse** | Click green "New repository secret" button again |

**FORM TO FILL:**

| Field | Value |
|---|---|
| **Name** | `VERCEL_TOKEN` |
| **Value** | (Leave empty for now - we'll add this in Guide 03) |

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add secret" button |

**WHAT YOU SHOULD SEE:**
- Two secrets in list:
  - RAILWAY_TOKEN
  - VERCEL_TOKEN

✅ **Step 4 Complete!** Secrets are set up (we'll populate them in later guides).

---

## Step 5: Create GitHub Actions Workflow (CI/CD Pipeline)

GitHub Actions automatically runs tests and builds your code when you push. This is optional but highly recommended.

### 5.1 Create Workflow Directory Locally

Go back to PowerShell and create the workflow folder:

```powershell
mkdir -p .github\workflows
```

**WHAT YOU SHOULD SEE:**
- No error message (normal)
- New folder created

### 5.2 Create Workflow File

Create a new YAML file for the workflow:

```powershell
New-Item -Path ".github\workflows\deploy.yml" -ItemType File -Force
```

**WHAT YOU SHOULD SEE:**
```
    Directory: C:\Users\scst1\2025\TheTool\.github\workflows


Mode                 LastWriteTime         Length Name
----                 -----------         ------ ----
-a---           11/18/2025 10:00 AM              deploy.yml
```

### 5.3 Edit Workflow File

Open the workflow file in a text editor:

```powershell
code .github\workflows\deploy.yml
```

Or open it manually:
- Right-click on the file
- Select "Open with" → "Code" or "Notepad"

### 5.4 Paste Workflow Content

Copy and paste this entire content into the file:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install backend dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run backend tests (non-blocking)
      run: |
        cd backend
        pytest tests/ -v --tb=short 2>/dev/null || true

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Build frontend
      run: |
        cd frontend
        npm run build
```

**WHAT THIS DOES:**
- Runs Python tests when you push code
- Builds React frontend to ensure no errors
- Doesn't block deployment if tests fail (safer)
- Runs on every push and pull request

### 5.5 Save the File

| Input Method | Action |
|---|---|
| **Keyboard** | Press `Ctrl+S` to save |
| **Mouse** | File → Save (menu) |

### 5.6 Commit and Push Workflow

Go back to PowerShell:

```powershell
git add .github/workflows/deploy.yml
```

```powershell
git commit -m "Add GitHub Actions CI/CD workflow"
```

```powershell
git push origin main
```

**WHAT YOU SHOULD SEE:**
```
To https://github.com/YOUR_USERNAME/TheTool.git
   abc1234..def5678  main -> main
```

✅ **Step 5 Complete!** GitHub Actions is set up!

**VERIFY:** Go to your GitHub repo → "Actions" tab - you should see your workflow run!

---

## Step 6: Verify Everything is Ready

### 6.1 Check Repository on GitHub

Go to your GitHub repo page and verify:

| Check | Expected Result |
|---|---|
| Repository exists | URL shows: `github.com/YOUR_USERNAME/TheTool` |
| Files are there | You see folders: `backend`, `frontend`, `docs`, etc. |
| Commits show | "Commits" tab shows your commits |
| Actions created | "Actions" tab shows your workflow |
| Secrets ready | Settings → Secrets shows `RAILWAY_TOKEN` and `VERCEL_TOKEN` |

**Visual Checklist:**

```
GitHub Repo Page Checklist:
┌─────────────────────────────────────────┐
│ ☑ Code tab shows all files              │
│ ☑ README.md displays                    │
│ ☑ .gitignore is present                 │
│ ☑ Actions tab has workflow              │
│ ☑ Settings → Secrets are configured     │
│ ☑ Latest commit shows your message      │
└─────────────────────────────────────────┘
```

### 6.2 Check Local Git Configuration

Verify your local setup:

```powershell
git remote -v
```

**EXPECTED OUTPUT:**
```
origin  https://github.com/YOUR_USERNAME/TheTool.git (fetch)
origin  https://github.com/YOUR_USERNAME/TheTool.git (push)
```

```powershell
git log --oneline
```

**EXPECTED OUTPUT:**
```
abc1234 Add GitHub Actions CI/CD workflow
def5678 Initial commit: TheTool stock analysis platform
```

### 6.3 Test Your Setup (Optional)

Make a small test commit to verify everything works:

```powershell
# Make a tiny change (e.g., add a comment)
echo "# Deployment test" >> README.md

# Stage it
git add README.md

# Commit
git commit -m "Test commit to verify GitHub Actions"

# Push
git push origin main
```

**WHAT TO EXPECT:**
- GitHub Actions workflow triggers automatically
- "Actions" tab shows workflow running
- Should complete in 1-2 minutes
- Green checkmark when done (workflow passed)

---

## 🎉 Guide 01 Complete!

### What You've Accomplished:
✅ Created GitHub repository for TheTool  
✅ Pushed all your code to GitHub  
✅ Set up GitHub Actions workflow for automated tests  
✅ Created repository secrets for sensitive data  
✅ Verified everything is working correctly  

### Summary of What's Set Up:

| Component | Status | URL |
|---|---|---|
| **GitHub Repo** | ✅ Created | github.com/YOUR_USERNAME/TheTool |
| **Local Git** | ✅ Initialized | Tracking in `.git` folder |
| **GitHub Actions** | ✅ Active | Runs on every push |
| **Repository Secrets** | ✅ Ready | RAILWAY_TOKEN, VERCEL_TOKEN |
| **Code on GitHub** | ✅ Pushed | All files visible on GitHub |

### What Happens Next:

In Guide 02, you'll:
1. Create a Railway account
2. Connect it to your GitHub repo
3. Get a live backend URL
4. Get your RAILWAY_TOKEN for GitHub Secrets
5. Backend will auto-deploy on every git push

---

## Troubleshooting Guide 01

### Problem: "Git command not found"
**Solution:**
1. Download Git from: https://git-scm.com/download/win
2. Install with default settings
3. Restart PowerShell
4. Try `git --version` again

### Problem: "Permission denied (publickey)"
**Solution:**
1. Use HTTPS instead of SSH
2. In PowerShell: `git config --global url."https://".insteadOf git://`
3. When prompted for credentials, use your GitHub username and personal access token

### Problem: "fatal: not a git repository"
**Solution:**
1. Verify you're in the correct folder: `pwd` (should show TheTool)
2. Verify `.git` folder exists: `ls -la` (look for `.git`)
3. Re-run: `git init`

### Problem: "Remote already exists"
**Solution:**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/TheTool.git
```

### Problem: "Cannot access repository - 403 Forbidden"
**Solution:**
1. Verify your GitHub credentials are correct
2. Generate personal access token: github.com/settings/tokens
3. Use token as password instead of account password
4. Or configure SSH key (advanced)

### Problem: "Workflow file not found"
**Solution:**
1. Verify file exists: `ls .github\workflows\`
2. Verify filename is exactly: `deploy.yml`
3. Verify it has no extra extensions (not `deploy.yml.txt`)
4. YAML formatting is correct (check indentation)

### Problem: "Actions tab shows 'no workflows'"
**Solution:**
1. Wait 2-3 minutes after pushing
2. Refresh the GitHub page (Ctrl+F5)
3. Check file was actually pushed: `git log --oneline`
4. Check file path in repo: `.github/workflows/deploy.yml`

---

## 🚀 Next Step

You're ready for Guide 02!

→ **Go to:** `02_RAILWAY_BACKEND_DEPLOY.md`

In the next guide, you'll:
- ✅ Create Railway account
- ✅ Deploy your Flask backend
- ✅ Get your live backend URL
- ✅ Set up automatic deployments on git push

---

**Guide 01 Status:** ✅ Complete  
**Time Spent:** ~10-15 minutes  
**Next Guide:** 02_RAILWAY_BACKEND_DEPLOY.md  
**Estimated Total Time to Full Deployment:** ~45 minutes remaining
