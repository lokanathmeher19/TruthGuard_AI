@echo off
title TruthGuard AI - Permanent Server
echo ===================================================
echo   TruthGuard AI - Auto-Restarting Server Guard
echo ===================================================

:: Ensure requirements are up to date
call .\venv\Scripts\pip install -r requirements.txt

:RESTART
echo.
echo [%time%] Starting TruthGuard API Server...
:: Using host 0.0.0.0 allows connection from any device on your local network
call .\venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000

echo.
echo [%time%] Server stopped or crashed! Auto-restarting in 3 seconds to ensure permanent connection...
timeout /t 3
goto RESTART
