@echo off
echo ========================================
echo  Casa de Cambio P2P - Inicio Rapido
echo ========================================
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

REM Verificar si existe .env
if not exist .env (
    echo [!] El archivo .env no existe. Copiando desde .env.example...
    copy .env.example .env
    echo.
    echo [!] IMPORTANTE: Edita el archivo .env y agrega tus API keys de Binance
    echo [!] Luego ejecuta este script nuevamente.
    echo.
    pause
    exit /b 1
)

echo [1/3] Construyendo imagenes de Docker...
docker-compose build

echo.
echo [2/3] Iniciando servicios...
docker-compose up -d

echo.
echo [3/3] Verificando estado de los servicios...
timeout /t 5 /nobreak >nul
docker-compose ps

echo.
echo ========================================
echo  Sistema Iniciado Correctamente
echo ========================================
echo.
echo Accede a las siguientes URLs:
echo   - Landing Page: http://localhost:3000
echo   - Dashboard:    http://localhost:3000/dashboard
echo   - API Docs:     http://localhost:8000/api/v1/docs
echo.
echo Para ver los logs: docker-compose logs -f
echo Para detener:     docker-compose down
echo.
pause
