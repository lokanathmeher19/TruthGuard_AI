@echo off
echo Installing requirements...
.\venv\Scripts\pip install -r requirements.txt

echo Starting TruthGuard Server...
.\venv\Scripts\uvicorn backend.main:app --reload
pause
