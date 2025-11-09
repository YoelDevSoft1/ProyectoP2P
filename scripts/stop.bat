@echo off
echo ========================================
echo  Deteniendo servicios...
echo ========================================

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

docker-compose down
echo.
echo Servicios detenidos correctamente.
pause
