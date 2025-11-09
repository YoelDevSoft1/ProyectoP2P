# Script para verificar el estado de ngrok y túneles activos

Write-Host "🔍 Verificando estado de ngrok..." -ForegroundColor Cyan
Write-Host ""

# Verificar contenedor Docker
Write-Host "1. Contenedor Docker:" -ForegroundColor Yellow
$container = docker ps -a --filter "name=ngrok" --format "{{.Names}}\t{{.Status}}"
if ($container) {
    Write-Host "   $container" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No se encontró contenedor de ngrok" -ForegroundColor Yellow
}

Write-Host ""

# Verificar procesos de ngrok
Write-Host "2. Procesos de ngrok en Windows:" -ForegroundColor Yellow
$processes = Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}
if ($processes) {
    $processes | ForEach-Object {
        Write-Host "   - $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    Write-Host "   ℹ️  No se encontraron procesos de ngrok" -ForegroundColor Gray
}

Write-Host ""

# Verificar API de ngrok (si está corriendo)
Write-Host "3. API de ngrok (localhost:4040):" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -TimeoutSec 2 -ErrorAction Stop
    if ($response.tunnels -and $response.tunnels.Count -gt 0) {
        Write-Host "   ✅ ngrok está corriendo" -ForegroundColor Green
        $response.tunnels | ForEach-Object {
            Write-Host "   - Túnel: $($_.name)" -ForegroundColor Cyan
            Write-Host "     URL pública: $($_.public_url)" -ForegroundColor Cyan
            Write-Host "     Estado: $($_.proto)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  ngrok está corriendo pero no hay túneles activos" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ℹ️  ngrok no está corriendo en localhost:4040" -ForegroundColor Gray
    Write-Host "      (Esto es normal si ngrok no está iniciado)" -ForegroundColor Gray
}

Write-Host ""

# Verificar dashboard de ngrok
Write-Host "4. Dashboard de ngrok:" -ForegroundColor Yellow
Write-Host "   Ve a: https://dashboard.ngrok.com/cloud-edge/tunnels" -ForegroundColor Cyan
Write-Host "   Verifica si hay túneles activos que necesiten detenerse" -ForegroundColor Gray

Write-Host ""
Write-Host "📋 Resumen:" -ForegroundColor Cyan
Write-Host "   - Si hay un túnel activo en el dashboard, deténlo primero" -ForegroundColor Yellow
Write-Host "   - Luego reinicia ngrok: docker-compose restart ngrok" -ForegroundColor Yellow
Write-Host ""

