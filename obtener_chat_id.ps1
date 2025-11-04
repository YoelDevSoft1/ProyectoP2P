# Script para obtener el Chat ID usando el token del bot
# Uso: .\obtener_chat_id.ps1

$token = "8519988770:AAHvjXA_goCW-vGz20K4Au_xT3naVF0UCBs"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Obteniendo Chat ID desde Telegram API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  IMPORTANTE: Primero debes enviar un mensaje a tu bot" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pasos:" -ForegroundColor Cyan
Write-Host "1. Busca tu bot en Telegram (usa el username que creaste)" -ForegroundColor White
Write-Host "2. Abre la conversación con tu bot" -ForegroundColor White
Write-Host "3. Envía cualquier mensaje (ejemplo: /start o 'Hola')" -ForegroundColor White
Write-Host "4. Presiona Enter aquí para continuar..." -ForegroundColor Yellow
Write-Host ""

Read-Host "Presiona Enter después de enviar el mensaje a tu bot"

Write-Host ""
Write-Host "⏳ Consultando la API de Telegram..." -ForegroundColor Yellow

try {
    $url = "https://api.telegram.org/bot$token/getUpdates"
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    if ($response.ok -and $response.result.Count -gt 0) {
        # Obtener el último mensaje recibido
        $lastUpdate = $response.result[-1]
        $chatId = $lastUpdate.message.chat.id
        
        Write-Host ""
        Write-Host "✅ ¡Chat ID encontrado!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Tu información:" -ForegroundColor Cyan
        Write-Host "   Chat ID: $chatId" -ForegroundColor White
        Write-Host "   Nombre: $($lastUpdate.message.chat.first_name)" -ForegroundColor White
        if ($lastUpdate.message.chat.username) {
            Write-Host "   Username: @$($lastUpdate.message.chat.username)" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "📝 Copia esto en tu archivo .env:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "ENABLE_NOTIFICATIONS=true" -ForegroundColor Green
        Write-Host "TELEGRAM_BOT_TOKEN=$token" -ForegroundColor Green
        Write-Host "TELEGRAM_CHAT_ID=$chatId" -ForegroundColor Green
        Write-Host ""
        
        # También mostrar la respuesta completa por si acaso
        Write-Host "📄 Respuesta completa de la API:" -ForegroundColor Gray
        $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Gray
        
    } else {
        Write-Host ""
        Write-Host "❌ No se encontraron mensajes" -ForegroundColor Red
        Write-Host ""
        Write-Host "Asegúrate de:" -ForegroundColor Yellow
        Write-Host "1. Haber enviado un mensaje a tu bot" -ForegroundColor White
        Write-Host "2. Que el token sea correcto" -ForegroundColor White
        Write-Host "3. Esperar unos segundos y volver a ejecutar el script" -ForegroundColor White
        Write-Host ""
        
        # Mostrar la respuesta para debug
        Write-Host "Respuesta de la API:" -ForegroundColor Gray
        $response | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Gray
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error al consultar la API:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifica que:" -ForegroundColor Yellow
    Write-Host "1. Tienes conexión a internet" -ForegroundColor White
    Write-Host "2. El token es correcto" -ForegroundColor White
}

