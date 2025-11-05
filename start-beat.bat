@echo off
echo ========================================
echo Starting Celery Beat (Scheduler)
echo ========================================
echo.
cd backend
echo Loading environment from .env.local...
copy /Y .env.local .env >nul
REM Si Redis no está disponible localmente, usar RabbitMQ RPC como backend
REM Esto evita errores de conexión a Redis en desarrollo local
set CELERY_USE_RPC_FALLBACK=true
python -m celery -A celery_app.worker beat --loglevel=info
