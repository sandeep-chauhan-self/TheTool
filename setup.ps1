# TheTool - Automated Setup Script
# This script sets up the complete environment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   TheTool - Automated Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ? Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ? Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.11+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "`n[2/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ? Found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ? Node.js not found!" -ForegroundColor Red
    Write-Host "  Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Setup Backend
Write-Host "`n[3/6] Setting up Python backend..." -ForegroundColor Yellow
cd backend

# Create virtual environment
if (!(Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "  ? Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ? Virtual environment already exists" -ForegroundColor Green
}

# Install Python packages
Write-Host "  Installing Python packages (this may take 2-3 minutes)..." -ForegroundColor Gray
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
Write-Host "  ? Python packages installed" -ForegroundColor Green

# Initialize database
Write-Host "  Initializing database..." -ForegroundColor Gray
.\venv\Scripts\python.exe database.py
Write-Host "  ? Database initialized" -ForegroundColor Green

cd ..

# Setup Frontend
Write-Host "`n[4/6] Setting up React frontend..." -ForegroundColor Yellow
cd frontend

Write-Host "  Installing Node packages (this may take 2-3 minutes)..." -ForegroundColor Gray
npm install --silent 2>&1 | Out-Null
Write-Host "  ? Node packages installed" -ForegroundColor Green

cd ..

# Create startup scripts
Write-Host "`n[5/6] Creating startup scripts..." -ForegroundColor Yellow

# Backend startup script
$backendScript = @"
@echo off
title TheTool Backend Server
cd backend
echo Starting Flask backend server...
.\venv\Scripts\python.exe app.py
pause
"@
Set-Content -Path "start-backend.bat" -Value $backendScript
Write-Host "  ? Created start-backend.bat" -ForegroundColor Green

# Frontend startup script
$frontendScript = @"
@echo off
title TheTool Frontend
cd frontend
echo Starting React frontend...
npm start
"@
Set-Content -Path "start-frontend.bat" -Value $frontendScript
Write-Host "  ? Created start-frontend.bat" -ForegroundColor Green

# Create .env file if not exists
Write-Host "`n[6/6] Configuring environment..." -ForegroundColor Yellow
if (!(Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env" -ErrorAction SilentlyContinue
    Write-Host "  ? Created .env file" -ForegroundColor Green
} else {
    Write-Host "  ? .env file already exists" -ForegroundColor Green
}

# Success message
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   Setup Complete! ?" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: start-backend.bat" -ForegroundColor Cyan
Write-Host "  2. Run: start-frontend.bat" -ForegroundColor Cyan
Write-Host "  3. Open: http://localhost:3000" -ForegroundColor Cyan

Write-Host "`nOr double-click the .bat files in Windows Explorer`n" -ForegroundColor Gray

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
