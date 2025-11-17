#!/usr/bin/env pwsh
# Start all services for Trading Signal Analyzer

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Trading Signal Analyzer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check Redis
Write-Host "[1/4] Checking Redis server..." -ForegroundColor Yellow
$redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue

if (-not $redisTest.TcpTestSucceeded) {
    Write-Host "  ? Redis is NOT running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please start Redis first:" -ForegroundColor Yellow
    Write-Host "    - Memurai: Restart-Service Memurai" -ForegroundColor White
    Write-Host "    - WSL: wsl sudo service redis-server start" -ForegroundColor White
    Write-Host "    - Docker: docker start redis" -ForegroundColor White
    Write-Host ""
    Write-Host "  See ASYNC_JOBS_SETUP.md for installation help." -ForegroundColor Cyan
    Write-Host ""
    exit 1
} else {
    Write-Host "  ? Redis is running" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/4] Starting Backend API..." -ForegroundColor Yellow

# Start Backend in new terminal
$backendPath = Join-Path $scriptDir "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; Write-Host '=== Backend API ===' -ForegroundColor Cyan; python app.py"

Write-Host "  ? Backend starting in new terminal..." -ForegroundColor Green
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[3/4] Starting Celery Worker..." -ForegroundColor Yellow

# Start Celery worker in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; Write-Host '=== Celery Worker ===' -ForegroundColor Cyan; celery -A celery_config.celery_app worker --loglevel=info --pool=solo"

Write-Host "  ? Celery worker starting in new terminal..." -ForegroundColor Green
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[4/4] Starting Frontend..." -ForegroundColor Yellow

# Start Frontend in new terminal
$frontendPath = Join-Path $scriptDir "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '=== Frontend ===' -ForegroundColor Cyan; npm start"

Write-Host "  ? Frontend starting in new terminal..." -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  - Backend API: http://localhost:5000" -ForegroundColor White
Write-Host "  - Frontend UI: http://localhost:3000 (opens automatically)" -ForegroundColor White
Write-Host "  - Celery Worker: Running in background terminal" -ForegroundColor White
Write-Host ""
Write-Host "Check status with: .\check-services.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop services, close the terminal windows." -ForegroundColor Yellow
Write-Host ""
