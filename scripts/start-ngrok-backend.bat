@echo off
echo ========================================
echo Starting Backend API with ngrok
echo ========================================
echo.

REM Verificar si Docker está corriendo
echo Checking if Docker is running...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

REM Verificar si los contenedores están corriendo
echo Checking if backend container is running...
docker ps | findstr "p2p_backend" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Backend container not running. Starting with docker-compose...
    docker-compose up -d backend
    timeout /t 10 /nobreak >nul
)

REM Verificar que el backend esté healthy
echo Waiting for backend to be healthy...
:wait_backend
docker inspect --format='{{.State.Health.Status}}' p2p_backend 2>nul | findstr "healthy" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Backend not ready yet, waiting...
    timeout /t 3 /nobreak >nul
    goto wait_backend
)

echo Backend is healthy!
echo.

REM Verificar si ngrok está instalado
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok is not installed or not in PATH!
    echo.
    echo Please install ngrok:
    echo 1. Download from https://ngrok.com/download
    echo 2. Extract ngrok.exe to a folder
    echo 3. Add that folder to your PATH or copy ngrok.exe to this folder
    pause
    exit /b 1
)

REM Verificar si ngrok está autenticado
echo Checking ngrok authentication...
ngrok config check >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: ngrok might not be configured!
    echo If this fails, run: ngrok config add-authtoken YOUR_TOKEN
    echo Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken
    echo.
    pause
)

echo.
echo ========================================
echo Starting ngrok tunnel for backend (port 8000)...
echo ========================================
echo.
echo IMPORTANT: Keep this window open!
echo The tunnel will close if you close this window.
echo.
echo Your backend will be accessible at the ngrok URL shown below.
echo Press Ctrl+C to stop the tunnel.
echo.

REM Iniciar ngrok (esto bloqueará la terminal)
ngrok http 8000 --log=stdout
