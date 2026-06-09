@echo off
title Answer Evaluator - Production Server
color 0B

echo ==========================================================
echo       AI-POWERED ANSWER EVALUATOR PRODUCTION SERVER
echo ==========================================================
echo.

:: 1. Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run local setup first.
    pause
    exit /b 1
)

:: 2. Check if frontend build exists
if not exist frontend\dist\index.html (
    echo [WARNING] Production frontend build was not found in 'frontend\dist'.
    echo Building React assets now...
    echo.
    cd frontend
    call npm run build
    cd ..
    echo.
)

:: 3. Set environment variables
set FLASK_ENV=production
set PYTHONPATH=backend
set SECRET_KEY=prod-secret-key-change-in-production
set JWT_SECRET_KEY=prod-jwt-secret-key-change-in-production
:: Use local SQLite database
set DATABASE_URL=sqlite:///app.db

echo [INFO] Environment configured.
echo [INFO] Running Flask API and serving React UI on http://localhost:5000
echo [INFO] Press CTRL+C to stop the server.
echo.

:: 4. Start Waitress WSGI Server
venv\Scripts\waitress-serve --port=5000 app:app
