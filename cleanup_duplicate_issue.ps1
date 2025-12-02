#!/usr/bin/env pwsh
# Script to resolve the duplicate stock count issue in bulk analysis

Write-Host "===========================================" -ForegroundColor Green
Write-Host "RESOLVING BULK ANALYSIS DUPLICATE ISSUE" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

Write-Host "ISSUE DIAGNOSED:" -ForegroundColor Yellow
Write-Host "  - UI shows 4921 total stocks to analyze (1481 completed + 534 failed + 2906 pending)"
Write-Host "  - CSV actually has 2192 stocks"
Write-Host "  - Database backend/data/trading_app.db has only 5 stocks (test job)"
Write-Host ""
Write-Host "ROOT CAUSE:" -ForegroundColor Yellow
Write-Host "  - Backend Flask app has STALE in-memory job cache from previous runs"
Write-Host "  - Numbers shown in UI are from Redis/in-memory, not from database"
Write-Host "  - Need to restart backend to clear the cache"
Write-Host ""

Write-Host "SOLUTION:" -ForegroundColor Cyan
Write-Host "  1. Stop the backend server (Ctrl+C if running)"
Write-Host "  2. Run this cleanup script (it deletes old databases)"
Write-Host "  3. Restart the backend"
Write-Host "  4. Run 'Analyze All' again with fresh state"
Write-Host ""

Write-Host "Proceed with cleanup? (y/n): " -NoNewline -ForegroundColor White
$response = Read-Host

if ($response -ne "y") {
    Write-Host "Cancelled" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "CLEANING UP DATABASE FILES" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# List all database files
$dbs = @(
    "backend\trading_app.db",
    "backend\data\trading_app.db", 
    "data\trading_app.db"
)

foreach ($db in $dbs) {
    if (Test-Path $db) {
        $size = (Get-Item $db).Length
        $modified = (Get-Item $db).LastWriteTime
        Write-Host "  Found: $db" -ForegroundColor Gray
        Write-Host "    Size: $size bytes | Modified: $modified" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Keeping ONLY: backend\data\trading_app.db (current database)" -ForegroundColor Green
Write-Host "Deleting old copies..." -ForegroundColor Yellow
Write-Host ""

# Keep the current database, delete old ones
Remove-Item "backend\trading_app.db" -ErrorAction SilentlyContinue
if ($?) { Write-Host "  ✓ Deleted backend\trading_app.db" -ForegroundColor Green }

Remove-Item "data\trading_app.db" -ErrorAction SilentlyContinue  
if ($?) { Write-Host "  ✓ Deleted data\trading_app.db" -ForegroundColor Green }

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "CLEANUP COMPLETE" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Stop the backend if running (Ctrl+C in the terminal)"
Write-Host "2. Restart the backend:"
Write-Host "     cd backend"
Write-Host "     python app.py"
Write-Host ""
Write-Host "3. The in-memory cache will be cleared on restart"
Write-Host "4. Run 'Analyze All' again - it should now show correct 2192 stocks"
Write-Host ""
