@echo off
title Launching AI Answer Evaluator
color 0A
echo ==========================================================
echo       STARTING AI-POWERED ANSWER EVALUATOR SERVER
echo ==========================================================
echo.
echo Checking if port 5000 is already in use...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do taskkill /f /pid %%a
echo.
echo Scheduling browser launch to http://localhost:5000 ...
start /b cmd /c "ping 127.0.0.1 -n 4 >nul && start http://localhost:5000"
echo.
echo Launching Waitress production server...
call start_production.bat
pause
