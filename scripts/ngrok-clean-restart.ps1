# Script para limpiar y reiniciar ngrok
# Útil cuando hay conflictos de dominio o errores

Write-Host "🧹 Limpiando y reiniciando ngrok..." -ForegroundColor Cyan
Write-Host ""

# Detener todas las instancias
Write-Host "1. Deteniendo todas las instancias de ngrok..." -ForegroundColor Yellow
.\scripts\stop-all-ngrok.ps1

Write-Host ""
Write-Host "2. Esperando 3 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Limpiar contenedor
Write-Host "3. Eliminando contenedor de ngrok..." -ForegroundColor Yellow
docker-compose rm -f ngrok 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Contenedor eliminado" -ForegroundColor Green
}

# Reiniciar
Write-Host ""
Write-Host "4. Reiniciando ngrok..." -ForegroundColor Yellow
docker-compose up -d ngrok

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ ngrok reiniciado" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Ver logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f ngrok" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🌐 Interfaz web: http://localhost:4040" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⏳ Esperando 5 segundos para que ngrok se inicie..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "🔗 Obteniendo URL pública..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
        if ($response.tunnels -and $response.tunnels.Count -gt 0) {
            $publicUrl = $response.tunnels[0].public_url
            Write-Host "   ✅ URL pública: $publicUrl" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  No se encontraron túneles activos" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  No se pudo obtener la URL pública (ngrok puede estar aún iniciando)" -ForegroundColor Yellow
        Write-Host "   Verifica los logs: docker-compose logs ngrok" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ Error al reiniciar ngrok" -ForegroundColor Red
    Write-Host "   Revisa los logs: docker-compose logs ngrok" -ForegroundColor Yellow
}

Write-Host ""

