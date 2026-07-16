@echo off
echo ========================================
echo   AI Resume Analyzer - Single Server
echo ========================================
echo.

echo [1/3] Installing frontend dependencies...
cd /d "%~dp0frontend"
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json
call npm install

echo.
echo [2/3] Building frontend...
call npm run build

echo.
echo [3/3] Starting server on port 8000...
cd /d "%~dp0backend"
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
call pip install -r requirements.txt -q
call uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
