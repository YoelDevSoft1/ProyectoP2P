# Script para solucionar el conflicto de dominio de ngrok
# Detiene todas las instancias y reinicia ngrok

Write-Host "🔧 Solucionando conflicto de dominio de ngrok..." -ForegroundColor Cyan
Write-Host ""

# Paso 1: Detener todas las instancias
Write-Host "1️⃣ Deteniendo todas las instancias de ngrok..." -ForegroundColor Yellow
.\scripts\stop-all-ngrok.ps1

Write-Host ""
Write-Host "2️⃣ Esperando 5 segundos para que los túneles se cierren..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Paso 2: Verificar dashboard de ngrok
Write-Host ""
Write-Host "3️⃣ Verificando túneles en el dashboard de ngrok..." -ForegroundColor Yellow
Write-Host "   Ve a: https://dashboard.ngrok.com/cloud-edge/tunnels" -ForegroundColor Cyan
Write-Host "   Si ves el túnel 'denver-unbrooded-miley.ngrok-free.dev' activo, deténlo manualmente" -ForegroundColor Yellow
Write-Host "   Presiona Enter cuando hayas verificado/detenido el túnel..." -ForegroundColor Gray
Read-Host

# Paso 3: Limpiar y reiniciar
Write-Host ""
Write-Host "4️⃣ Limpiando contenedor de ngrok..." -ForegroundColor Yellow
docker-compose rm -f ngrok 2>$null

Write-Host ""
Write-Host "5️⃣ Reiniciando ngrok..." -ForegroundColor Yellow
docker-compose up -d ngrok

Write-Host ""
Write-Host "⏳ Esperando 10 segundos para que ngrok se inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Paso 4: Verificar estado
Write-Host ""
Write-Host "6️⃣ Verificando estado de ngrok..." -ForegroundColor Yellow
$logs = docker-compose logs --tail=20 ngrok 2>&1
if ($logs -match "Session Status.*online") {
    Write-Host "   ✅ ngrok está en línea" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  ngrok puede estar aún iniciando o hay un error" -ForegroundColor Yellow
    Write-Host "   Verifica los logs: docker-compose logs -f ngrok" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📊 Obtener URL pública:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:4040/api/tunnels" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Interfaz web: http://localhost:4040" -ForegroundColor Cyan
Write-Host ""

