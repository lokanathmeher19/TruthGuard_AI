@echo off
echo ===================================================
echo   Starting TruthGuard UI in your Web Browser...
echo ===================================================
echo.
echo Make sure the backend server (run_forever.bat or start_background.vbs) is already running!
echo Launching http://127.0.0.1:8000/ ...
timeout /t 2
start http://127.0.0.1:8000/
