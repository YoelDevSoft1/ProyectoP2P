@echo off
echo ========================================
echo Starting Celery Worker
echo ========================================
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."
cd backend

echo Loading environment from .env.local...
copy /Y .env.local .env >nul
REM Si Redis no está disponible localmente, usar RabbitMQ RPC como backend
REM Esto evita errores de conexión a Redis en desarrollo local
set CELERY_USE_RPC_FALLBACK=true
python -m celery -A celery_app.worker worker --loglevel=info --concurrency=2 --pool=solo
