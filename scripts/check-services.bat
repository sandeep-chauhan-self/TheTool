@echo off
REM Check Redis Status Script for Trading Signal Analyzer

echo.
echo ============================================
echo Redis + Celery Status Check
echo ============================================
echo.

REM Check if Redis is running on port 6379
echo [1/3] Checking Redis server...
echo.

powershell -Command "$test = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; if ($test.TcpTestSucceeded) { Write-Host '? Redis is running on port 6379' -ForegroundColor Green } else { Write-Host '? Redis is NOT running!' -ForegroundColor Red; Write-Host '  Install Redis/Memurai - see ASYNC_JOBS_SETUP.md' -ForegroundColor Yellow }"

echo.
echo [2/3] Checking Celery worker process...
echo.

powershell -Command "$celery = Get-Process celery -ErrorAction SilentlyContinue; if ($celery) { Write-Host '? Celery worker is running (PID:' $celery.Id ')' -ForegroundColor Green } else { Write-Host '? Celery worker is NOT running!' -ForegroundColor Red; Write-Host '  Start with: celery -A celery_config.celery_app worker --loglevel=info --pool=solo' -ForegroundColor Yellow }"

echo.
echo [3/3] Checking Backend API...
echo.

powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000/health' -TimeoutSec 2 -ErrorAction Stop; Write-Host '? Backend API is running' -ForegroundColor Green } catch { Write-Host '? Backend API is NOT running!' -ForegroundColor Red; Write-Host '  Start with: python app.py' -ForegroundColor Yellow }"

echo.
echo ============================================
echo Summary
echo ============================================
echo.
echo For async job processing to work, ALL three components must be running:
echo   1. Redis server (Memurai/WSL/Docker)
echo   2. Celery worker (in separate terminal)
echo   3. Backend API (Flask app)
echo.
echo See ASYNC_JOBS_SETUP.md for detailed setup instructions.
echo.
pause
