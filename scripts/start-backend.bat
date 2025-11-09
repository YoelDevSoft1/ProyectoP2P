@echo off
echo ========================================
echo Starting Backend API (FastAPI + Uvicorn)
echo ========================================
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."
cd backend

echo Loading environment from .env.local...
copy /Y .env.local .env >nul
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
