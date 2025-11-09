@echo off
echo ========================================
echo  Ver logs en tiempo real (Ctrl+C para salir)
echo ========================================
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

docker-compose logs -f
