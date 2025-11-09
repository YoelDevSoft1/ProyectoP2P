# Script para detener ngrok

Write-Host "🛑 Deteniendo contenedor de ngrok..." -ForegroundColor Cyan

docker-compose stop ngrok

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Contenedor de ngrok detenido" -ForegroundColor Green
} else {
    Write-Host "❌ Error al detener el contenedor" -ForegroundColor Red
    exit 1
}

