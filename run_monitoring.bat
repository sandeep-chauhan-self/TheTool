@echo off
REM 48-Hour Monitoring Helper for Unified Table Migration
REM Run this script every 6 hours

echo ====================================================================
echo UNIFIED TABLE MIGRATION - MONITORING CHECK
echo ====================================================================
echo.

cd /d "%~dp0backend"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run monitoring
echo Running monitoring check...
python monitor_unified_table.py

echo.
echo ====================================================================
echo Next monitoring check: 6 hours from now
echo ====================================================================
echo.

REM Show trends after 3rd check
python monitor_unified_table.py --trends

pause
