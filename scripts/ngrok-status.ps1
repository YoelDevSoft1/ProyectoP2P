# Script para ver el estado de ngrok

Write-Host "📊 Estado del contenedor de ngrok:" -ForegroundColor Cyan
Write-Host ""

docker-compose ps ngrok

Write-Host ""
Write-Host "📋 Logs recientes:" -ForegroundColor Cyan
Write-Host ""

docker-compose logs --tail=20 ngrok

Write-Host ""
Write-Host "🔗 Para obtener la URL pública, ejecuta:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:4040/api/tunnels" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Interfaz web: http://localhost:4040" -ForegroundColor Cyan

