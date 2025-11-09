# Script para iniciar ngrok con Docker Compose
# Verifica que el token esté configurado antes de iniciar

Write-Host "🔍 Verificando configuración de ngrok..." -ForegroundColor Cyan

# Verificar que el archivo .env existe
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: El archivo .env no existe" -ForegroundColor Red
    Write-Host "   Por favor, crea el archivo .env y agrega NGROK_AUTHTOKEN" -ForegroundColor Yellow
    exit 1
}

# Verificar que NGROK_AUTHTOKEN está configurado
$envContent = Get-Content .env -Raw
if ($envContent -notmatch 'NGROK_AUTHTOKEN\s*=') {
    Write-Host "❌ Error: NGROK_AUTHTOKEN no está configurado en .env" -ForegroundColor Red
    Write-Host "   Por favor, agrega NGROK_AUTHTOKEN=tu_token_aqui al archivo .env" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Token de ngrok configurado" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Iniciando contenedor de ngrok..." -ForegroundColor Cyan

# Iniciar el contenedor de ngrok
docker-compose up -d ngrok

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Contenedor de ngrok iniciado" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Ver logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f ngrok" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🌐 Interfaz web:" -ForegroundColor Cyan
    Write-Host "   http://localhost:4040" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔗 Obtener URL pública:" -ForegroundColor Cyan
    Write-Host "   curl http://localhost:4040/api/tunnels" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "❌ Error al iniciar el contenedor de ngrok" -ForegroundColor Red
    Write-Host "   Revisa los logs: docker-compose logs ngrok" -ForegroundColor Yellow
    exit 1
}

