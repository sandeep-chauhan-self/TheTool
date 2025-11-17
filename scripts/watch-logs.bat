@echo off
REM Watch application logs in real-time

echo.
echo ============================================
echo Watching Application Logs (Real-time)
echo ============================================
echo.
echo Press Ctrl+C to stop watching
echo.

cd C:\Users\H569808\2025\TheTool\backend\logs

if not exist app.log (
    echo Log file not found! Starting watch...
    echo Waiting for logs to appear...
    echo.
)

powershell -Command "Get-Content app.log -Wait -Tail 100 | ForEach-Object { if ($_ -match 'ERROR') { Write-Host $_ -ForegroundColor Red } elseif ($_ -match 'WARNING') { Write-Host $_ -ForegroundColor Yellow } elseif ($_ -match 'INFO') { Write-Host $_ -ForegroundColor Cyan } elseif ($_ -match 'DEBUG') { Write-Host $_ -ForegroundColor Gray } else { Write-Host $_ } }"
