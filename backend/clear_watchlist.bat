@echo off
REM Batch wrapper for clear_watchlist.py to make it executable on Windows
REM This allows the script to be run directly while maintaining the shebang
python "%~dp0clear_watchlist.py" %*
