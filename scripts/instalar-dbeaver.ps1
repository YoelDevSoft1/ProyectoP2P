# Script para ayudar a instalar DBeaver

Write-Host "🚀 Instalador de DBeaver - Asistente" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si DBeaver está instalado
Write-Host "🔍 Verificando si DBeaver está instalado..." -ForegroundColor Yellow

$dbeaverPath = Get-Command dbeaver -ErrorAction SilentlyContinue
if ($dbeaverPath) {
    Write-Host "✅ DBeaver ya está instalado en: $($dbeaverPath.Source)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Para configurar la conexión:" -ForegroundColor Cyan
    Write-Host "   1. Abrir DBeaver" -ForegroundColor White
    Write-Host "   2. Click en 'Nueva Conexión' (icono de enchufe)" -ForegroundColor White
    Write-Host "   3. Seleccionar 'PostgreSQL'" -ForegroundColor White
    Write-Host "   4. Configurar:" -ForegroundColor White
    Write-Host "      - Host: localhost" -ForegroundColor Gray
    Write-Host "      - Port: 5432" -ForegroundColor Gray
    Write-Host "      - Database: p2p_db" -ForegroundColor Gray
    Write-Host "      - Username: p2p_user" -ForegroundColor Gray
    Write-Host "      - Password: p2p_password_change_me" -ForegroundColor Gray
    Write-Host "   5. Click 'Test Connection'" -ForegroundColor White
    Write-Host "   6. Click 'Finish'" -ForegroundColor White
    exit 0
}

Write-Host "❌ DBeaver NO está instalado" -ForegroundColor Yellow
Write-Host ""

# Verificar PostgreSQL
Write-Host "🔍 Verificando PostgreSQL..." -ForegroundColor Yellow
$postgresRunning = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-String "postgres"

if ($postgresRunning) {
    Write-Host "✅ PostgreSQL está corriendo" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL NO está corriendo" -ForegroundColor Red
    Write-Host "   Ejecuta: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Instrucciones de instalación
Write-Host "📥 Pasos para instalar DBeaver:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Descargar DBeaver:" -ForegroundColor Yellow
Write-Host "   - Visitar: https://dbeaver.io/download/" -ForegroundColor White
Write-Host "   - Click: 'Windows 64 bit (installer)'" -ForegroundColor White
Write-Host "   - Descargar archivo .exe" -ForegroundColor White
Write-Host ""
Write-Host "2. Instalar DBeaver:" -ForegroundColor Yellow
Write-Host "   - Ejecutar el archivo .exe descargado" -ForegroundColor White
Write-Host "   - Seguir wizard de instalación" -ForegroundColor White
Write-Host "   - Click 'Next' → 'Install' → 'Finish'" -ForegroundColor White
Write-Host ""
Write-Host "3. Configurar conexión:" -ForegroundColor Yellow
Write-Host "   - Abrir DBeaver" -ForegroundColor White
Write-Host "   - Click en 'Nueva Conexión' (icono de enchufe)" -ForegroundColor White
Write-Host "   - Seleccionar 'PostgreSQL'" -ForegroundColor White
Write-Host "   - Configurar:" -ForegroundColor White
Write-Host "     * Host: localhost" -ForegroundColor Gray
Write-Host "     * Port: 5432" -ForegroundColor Gray
Write-Host "     * Database: p2p_db" -ForegroundColor Gray
Write-Host "     * Username: p2p_user" -ForegroundColor Gray
Write-Host "     * Password: p2p_password_change_me" -ForegroundColor Gray
Write-Host "   - Click 'Test Connection'" -ForegroundColor White
Write-Host "   - Click 'Finish'" -ForegroundColor White
Write-Host ""
Write-Host "4. ¡Listo! Ya puedes usar DBeaver" -ForegroundColor Green
Write-Host ""

# Abrir navegador para descargar
$response = Read-Host "¿Quieres abrir el navegador para descargar DBeaver? (S/N)"
if ($response -eq "S" -or $response -eq "s" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host "🌐 Abriendo navegador..." -ForegroundColor Cyan
    Start-Process "https://dbeaver.io/download/"
    Write-Host "✅ Navegador abierto" -ForegroundColor Green
}

Write-Host ""
Write-Host "📚 Para más información, revisa:" -ForegroundColor Cyan
Write-Host "   - docs/GUIA_DBEAVER_PASO_A_PASO.md" -ForegroundColor White
Write-Host "   - docs/DBEAVER_INSTALACION_RAPIDA.md" -ForegroundColor White

