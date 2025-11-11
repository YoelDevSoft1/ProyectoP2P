# Script para verificar que PostgreSQL esté accesible desde DBeaver

Write-Host "🔍 Verificando PostgreSQL..." -ForegroundColor Cyan
Write-Host ""

# Verificar que el contenedor esté corriendo
Write-Host "📦 Verificando contenedor PostgreSQL..." -ForegroundColor Yellow
$postgresRunning = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-String "postgres"

if ($postgresRunning) {
    Write-Host "✅ Contenedor PostgreSQL está corriendo: $postgresRunning" -ForegroundColor Green
} else {
    Write-Host "❌ Contenedor PostgreSQL NO está corriendo" -ForegroundColor Red
    Write-Host "   Ejecuta: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar que el puerto esté abierto
Write-Host "🔌 Verificando puerto 5432..." -ForegroundColor Yellow
$portOpen = Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue

if ($portOpen) {
    Write-Host "✅ Puerto 5432 está abierto y accesible" -ForegroundColor Green
} else {
    Write-Host "❌ Puerto 5432 NO está accesible" -ForegroundColor Red
    Write-Host "   Verifica que el contenedor esté corriendo y el puerto esté expuesto" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar conexión a la base de datos
Write-Host "🗄️  Verificando conexión a la base de datos..." -ForegroundColor Yellow
try {
    $result = docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Conexión a la base de datos exitosa" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al conectar a la base de datos" -ForegroundColor Red
        Write-Host "   Verifica las credenciales" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error al verificar conexión: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ PostgreSQL está listo para DBeaver" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Configuración para DBeaver:" -ForegroundColor Cyan
Write-Host "   Host: localhost" -ForegroundColor White
Write-Host "   Port: 5432" -ForegroundColor White
Write-Host "   Database: p2p_db" -ForegroundColor White
Write-Host "   Username: p2p_user" -ForegroundColor White
Write-Host "   Password: p2p_password_change_me" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Siguiente paso: Instalar DBeaver" -ForegroundColor Cyan
Write-Host "   https://dbeaver.io/download/" -ForegroundColor White

