@echo off
REM Batch wrapper for migrate_add_job_id.py to make it executable on Windows
REM This allows the script to be run directly while maintaining the shebang
python "%~dp0migrate_add_job_id.py" %*
