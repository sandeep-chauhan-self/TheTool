# Setup script for Trading Signal Analyzer (Windows PowerShell)
# This script initializes the project for first-time use

Write-Host "?? Trading Signal Analyzer - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    } else {
        throw
    }
} catch {
    Write-Host "? Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check if bundled Node.js exists
$bundledNodePath = Join-Path $scriptDir "Prerequisite\node-v20.19.5-win-x64"
$nodeExePath = Join-Path $bundledNodePath "node.exe"

if (Test-Path $nodeExePath) {
    Write-Host "Found bundled Node.js v20.19.5" -ForegroundColor Green
    $nodeInstalled = $true
    $nodePath = $bundledNodePath
    
    # Add to current session PATH
    $env:Path = "$nodePath;$env:Path"
    
    # Add to user PATH permanently if not already there
    $userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if ($userPath -notlike "*$nodePath*") {
        Write-Host "Adding Node.js to system PATH..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$nodePath", [EnvironmentVariableTarget]::User)
        Write-Host "? Node.js added to PATH permanently" -ForegroundColor Green
    }
} else {
    Write-Host "? Bundled Node.js not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "??  Frontend setup will be skipped." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Expected location: $bundledNodePath" -ForegroundColor Yellow
    Write-Host ""
    $nodeInstalled = $false
}

Write-Host ""
Write-Host "Setting up Backend..." -ForegroundColor Cyan
Write-Host "--------------------" -ForegroundColor Cyan

# Backend setup
Set-Location backend

# Create virtual environment
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if Redis is needed for async jobs
Write-Host ""
Write-Host "Checking for Redis/Celery async job system..." -ForegroundColor Yellow
$redisNeeded = $true

if ($redisNeeded) {
    Write-Host ""
    Write-Host "??  IMPORTANT: Async Job Processing System" -ForegroundColor Yellow
    Write-Host "=========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This application uses Redis + Celery for background job processing." -ForegroundColor White
    Write-Host "This is required for analyzing large batches of stocks (100-3000+)." -ForegroundColor White
    Write-Host ""
    
    # Check if Redis is running
    $redisRunning = $false
    try {
        $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if ($redisTest.TcpTestSucceeded) {
            Write-Host "? Redis is running on port 6379" -ForegroundColor Green
            $redisRunning = $true
        }
    } catch {
        # Redis not running
    }
    
    if (-not $redisRunning) {
        Write-Host "? Redis server is NOT running!" -ForegroundColor Red
        Write-Host ""
        Write-Host "?? You need to install Redis to use async job processing:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Option 1 - Memurai (Recommended for Windows):" -ForegroundColor Yellow
        Write-Host "  1. Download from: https://www.memurai.com/get-memurai" -ForegroundColor White
        Write-Host "  2. Install Memurai Developer Edition (Free)" -ForegroundColor White
        Write-Host "  3. It will auto-start as a Windows service" -ForegroundColor White
        Write-Host ""
        Write-Host "Option 2 - Redis via WSL:" -ForegroundColor Yellow
        Write-Host "  1. Install WSL: wsl --install" -ForegroundColor White
        Write-Host "  2. In WSL: sudo apt install redis-server" -ForegroundColor White
        Write-Host "  3. Start: sudo service redis-server start" -ForegroundColor White
        Write-Host ""
        Write-Host "Option 3 - Redis via Docker:" -ForegroundColor Yellow
        Write-Host "  docker run -d -p 6379:6379 --name redis redis:7-alpine" -ForegroundColor White
        Write-Host ""
        Write-Host "?? Full setup guide: ASYNC_JOBS_SETUP.md" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "??  Without Redis, you can only analyze small batches (< 10 stocks)" -ForegroundColor Yellow
        Write-Host "   with 60-second timeout limits." -ForegroundColor Yellow
        Write-Host ""
    }
}

# Create .env file
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -c "from database import init_db; init_db()"

# Create directories
New-Item -ItemType Directory -Force -Path data\cache | Out-Null
New-Item -ItemType Directory -Force -Path data\reports | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null

Write-Host "? Backend setup complete!" -ForegroundColor Green
Write-Host ""

# Frontend setup
Set-Location ..\frontend

if ($nodeInstalled) {
    Write-Host "Setting up Frontend..." -ForegroundColor Cyan
    Write-Host "--------------------" -ForegroundColor Cyan

    # Install dependencies
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install

    # Create .env file
    if (!(Test-Path ".env")) {
        Write-Host "Creating .env file..." -ForegroundColor Yellow
        Copy-Item .env.example .env
    }

    Write-Host "? Frontend setup complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "??  Skipping Frontend setup (Node.js not installed)" -ForegroundColor Yellow
    Write-Host ""
}

Set-Location ..

# Create start script for frontend
if ($nodeInstalled) {
    Write-Host "Creating frontend start script..." -ForegroundColor Yellow
    $startScript = @"
@echo off
cd /d %~dp0
set PATH=$nodePath;%PATH%
set GENERATE_SOURCEMAP=false
set DISABLE_ESLINT_PLUGIN=true
set TSC_COMPILE_ON_ERROR=true
set FAST_REFRESH=true
echo Starting frontend (optimized for faster startup)...
npm start
"@
    $startScript | Out-File -FilePath "frontend\start-frontend.bat" -Encoding ASCII
    
    # Create .env.local for frontend performance
    Write-Host "Creating performance optimizations..." -ForegroundColor Yellow
    $envLocal = @"
# Performance optimizations for faster startup
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
TSC_COMPILE_ON_ERROR=true
FAST_REFRESH=true
BROWSER=none
"@
    $envLocal | Out-File -FilePath "frontend\.env.local" -Encoding ASCII
    
    Write-Host "? Frontend start script created" -ForegroundColor Green
    Write-Host "? Performance optimizations applied" -ForegroundColor Green
}

Write-Host ""
Write-Host "?? Setup Complete!" -ForegroundColor Green
Write-Host "=================" -ForegroundColor Green
Write-Host ""

if ($nodeInstalled) {
    Write-Host "To start the application:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "?? Quick Start (3 Terminals Required):" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Terminal 1 - Backend API:" -ForegroundColor Cyan
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host ""
    Write-Host "Terminal 2 - Celery Worker (For async jobs):" -ForegroundColor Cyan
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  celery -A celery_config.celery_app worker --loglevel=info --pool=solo" -ForegroundColor White
    Write-Host ""
    Write-Host "Terminal 3 - Frontend:" -ForegroundColor Cyan
    Write-Host "  cd frontend" -ForegroundColor White
    Write-Host "  .\start-frontend.bat" -ForegroundColor White
    Write-Host ""
    Write-Host "??  IMPORTANT: You must have Redis running!" -ForegroundColor Yellow
    Write-Host "   If Redis is not installed, see ASYNC_JOBS_SETUP.md" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Then open http://localhost:3000 in your browser" -ForegroundColor Green
    Write-Host ""
    Write-Host "Alternative - Docker Deployment:" -ForegroundColor Yellow
    Write-Host "  docker-compose up --build" -ForegroundColor White
} else {
    Write-Host "??  Backend is ready, but Frontend requires Node.js" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Current options:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1 - Start Backend Only:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host "  Then test API at: http://localhost:5000/health" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "Option 2 - Install Node.js for Full UI:" -ForegroundColor Yellow
    Write-Host "  1. Download from https://nodejs.org/" -ForegroundColor White
    Write-Host "  2. Install LTS version" -ForegroundColor White
    Write-Host "  3. Run: cd frontend; npm install; npm start" -ForegroundColor White
    Write-Host ""
    Write-Host "After installing Node.js, open http://localhost:3000" -ForegroundColor Cyan
}
Write-Host ""

Write-Host "?? Documentation:" -ForegroundColor Cyan
Write-Host "  - Setup Summary: SETUP_SUMMARY.md (START HERE!)" -ForegroundColor Yellow
Write-Host "  - Quick Start: QUICK_START.md" -ForegroundColor White
Write-Host "  - Full Documentation: README.md" -ForegroundColor White
Write-Host "  - Async Jobs Setup: ASYNC_JOBS_SETUP.md (Redis + Celery)" -ForegroundColor White
Write-Host "  - Backend Dev Guide: BACKEND_ASYNC_GUIDE.md" -ForegroundColor White
Write-Host ""
Write-Host "?? Helpful Scripts:" -ForegroundColor Cyan
Write-Host "  - Start all services: .\start-all.ps1" -ForegroundColor White
Write-Host "  - Check services status: .\check-services.bat" -ForegroundColor White
Write-Host ""
Write-Host "?? New Features:" -ForegroundColor Cyan
Write-Host "  ? Async job processing with Celery + Redis" -ForegroundColor Green
Write-Host "  ? Process 1000-3000+ stocks overnight" -ForegroundColor Green
Write-Host "  ? Real-time progress tracking" -ForegroundColor Green
Write-Host "  ? Job cancellation support" -ForegroundColor Green
Write-Host "  ? Analysis history (last 10 per stock)" -ForegroundColor Green
Write-Host "  ? Batch processing (100 stocks at a time)" -ForegroundColor Green
Write-Host ""
