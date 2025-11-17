@echo off
cd /d %~dp0
set PATH=C:\Users\H569808\2025\TheTool\Prerequisite\node-v20.19.5-win-x64;%PATH%
set GENERATE_SOURCEMAP=false
set DISABLE_ESLINT_PLUGIN=true
set TSC_COMPILE_ON_ERROR=true
set FAST_REFRESH=true
echo Starting frontend (optimized for faster startup)...
npm start
