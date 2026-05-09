@echo off
cd /d "%~dp0"
echo Starting Janus Dashboard...
call npm run dev
pause
