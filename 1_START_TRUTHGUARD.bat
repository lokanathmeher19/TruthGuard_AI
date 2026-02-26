@echo off
TITLE TruthGuard AI - Forensic Backend Server
COLOR 0B

echo =======================================================
echo     TRUTHGUARD AI - MULTIMODAL DEEPFAKE DETECTOR
echo =======================================================
echo.
echo [1] Initializing Backend Analytical Engine...
echo [2] Loading PyTorch Models and Computer Vision Heuristics...
echo [3] Booting FastAPI Frontend Web UI...
echo.

:: Automatically open the web browser to the dashboard
echo [!] Launching User Interface in your Default Browser...
start http://127.0.0.1:8000/

:: Start the Python Backend Server
echo [!] Starting local Uvicorn Server on Port 8000...
echo.
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause 













