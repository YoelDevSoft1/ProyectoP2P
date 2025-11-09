# Script para detener todas las instancias de ngrok
# Útil cuando hay conflictos de dominio

Write-Host "🛑 Deteniendo todas las instancias de ngrok..." -ForegroundColor Cyan
Write-Host ""

# Detener contenedor de Docker
Write-Host "1. Deteniendo contenedor Docker de ngrok..." -ForegroundColor Yellow
docker-compose stop ngrok 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Contenedor Docker detenido" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No se encontró contenedor Docker de ngrok" -ForegroundColor Yellow
}

# Detener procesos de ngrok en Windows
Write-Host "2. Deteniendo procesos de ngrok en Windows..." -ForegroundColor Yellow
$ngrokProcesses = Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}
if ($ngrokProcesses) {
    $ngrokProcesses | Stop-Process -Force
    Write-Host "   ✅ Procesos de ngrok detenidos" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  No se encontraron procesos de ngrok" -ForegroundColor Gray
}

# Verificar túneles activos en ngrok dashboard
Write-Host ""
Write-Host "3. Verificando túneles activos..." -ForegroundColor Yellow
Write-Host "   ℹ️  Para verificar y detener túneles activos, visita:" -ForegroundColor Gray
Write-Host "   https://dashboard.ngrok.com/cloud-edge/tunnels" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Todas las instancias de ngrok han sido detenidas" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Para reiniciar ngrok, ejecuta:" -ForegroundColor Cyan
Write-Host "   docker-compose up -d ngrok" -ForegroundColor Yellow
Write-Host ""

