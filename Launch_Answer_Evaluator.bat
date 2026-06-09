@echo off
title Launching Answer Evaluator...
echo Checking if the server is already running on port 5000...

:: Check if port 5000 is in use
netstat -ano | findstr :5000 >nul
if %errorlevel% equ 0 (
    echo Server is already running. Opening browser directly...
) else (
    echo Server is not running. Starting production WSGI server in the background...
    :: Start the production waitress server in a minimized window
    start /min "" cmd.exe /c start_production.bat
    echo Waiting for the server to spin up...
    :: Wait 3 seconds
    timeout /t 3 /nobreak >nul
)

echo Opening browser...
:: Open the web browser
start http://localhost:5000

echo Launch successful! You can close this window.
timeout /t 2 /nobreak >nul
