@echo off
echo ========================================
echo Starting Full P2P System with ngrok
echo ========================================
echo.

REM Verificar si Docker está corriendo
echo [1/5] Checking if Docker is running...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo Docker is running! ✓
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

REM Iniciar todos los servicios
echo [2/5] Starting all Docker services...
docker-compose up -d
echo Services started! ✓
echo.

REM Esperar a que el backend esté healthy
echo [3/5] Waiting for backend to be healthy...
:wait_backend
timeout /t 3 /nobreak >nul
docker inspect --format='{{.State.Health.Status}}' p2p_backend 2>nul | findstr "healthy" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Still waiting for backend...
    goto wait_backend
)
echo Backend is healthy! ✓
echo.

REM Verificar ngrok
echo [4/5] Verifying ngrok installation...
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok is not installed or not in PATH!
    echo.
    echo Please install ngrok:
    echo 1. Download from https://ngrok.com/download
    echo 2. Extract ngrok.exe
    echo 3. Run: ngrok config add-authtoken YOUR_TOKEN
    echo    (Get token from: https://dashboard.ngrok.com/get-started/your-authtoken)
    pause
    exit /b 1
)
echo ngrok found! ✓
echo.

REM Mostrar estado de servicios
echo [5/5] Service Status:
echo.
docker-compose ps
echo.

echo ========================================
echo System is ready!
echo ========================================
echo.
echo Services running:
echo - Backend API: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - Grafana: http://localhost:3001
echo - RabbitMQ Management: http://localhost:15672
echo - Prometheus: http://localhost:9090
echo.
echo To expose backend with ngrok, run:
echo   scripts\start-ngrok-backend.bat
echo.
echo Or run ngrok manually:
echo   ngrok http 8000
echo.
pause
