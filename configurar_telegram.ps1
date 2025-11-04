# Script para configurar Telegram Bot en el archivo .env
# Uso: .\configurar_telegram.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuración del Bot de Telegram" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el archivo .env existe
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: No se encontró el archivo .env" -ForegroundColor Red
    Write-Host "   Por favor, crea el archivo .env primero" -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Por favor, proporciona la siguiente información:" -ForegroundColor Yellow
Write-Host ""

# Solicitar Token del Bot
$botToken = Read-Host "1. Ingresa el TELEGRAM_BOT_TOKEN (obtenido de @BotFather)"

if ([string]::IsNullOrWhiteSpace($botToken)) {
    Write-Host "❌ Error: El token no puede estar vacío" -ForegroundColor Red
    exit 1
}

# Solicitar Chat ID
$chatId = Read-Host "2. Ingresa el TELEGRAM_CHAT_ID (tu ID de usuario)"

if ([string]::IsNullOrWhiteSpace($chatId)) {
    Write-Host "❌ Error: El Chat ID no puede estar vacío" -ForegroundColor Red
    exit 1
}

# Validar que el Chat ID sea un número
if ($chatId -notmatch '^\d+$') {
    Write-Host "⚠️  Advertencia: El Chat ID debería ser un número" -ForegroundColor Yellow
    $continue = Read-Host "¿Continuar de todas formas? (s/n)"
    if ($continue -ne 's' -and $continue -ne 'S') {
        exit 0
    }
}

Write-Host ""
Write-Host "⏳ Actualizando archivo .env..." -ForegroundColor Yellow

# Leer el contenido del .env
$envContent = Get-Content .env -Raw

# Reemplazar las variables
$envContent = $envContent -replace 'TELEGRAM_BOT_TOKEN=.*', "TELEGRAM_BOT_TOKEN=$botToken"
$envContent = $envContent -replace 'TELEGRAM_CHAT_ID=.*', "TELEGRAM_CHAT_ID=$chatId"

# Asegurar que ENABLE_NOTIFICATIONS esté en true
if ($envContent -notmatch 'ENABLE_NOTIFICATIONS=') {
    # Agregar si no existe
    $envContent += "`nENABLE_NOTIFICATIONS=true`n"
} else {
    # Asegurar que esté en true
    $envContent = $envContent -replace 'ENABLE_NOTIFICATIONS=(false|0|False|FALSE)', 'ENABLE_NOTIFICATIONS=true'
}

# Guardar el archivo
$envContent | Set-Content .env -NoNewline

Write-Host "✅ Archivo .env actualizado exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Resumen de cambios:" -ForegroundColor Cyan
Write-Host "   - TELEGRAM_BOT_TOKEN: $($botToken.Substring(0, [Math]::Min(20, $botToken.Length)))..." -ForegroundColor Gray
Write-Host "   - TELEGRAM_CHAT_ID: $chatId" -ForegroundColor Gray
Write-Host "   - ENABLE_NOTIFICATIONS: true" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "   1. Reinicia el backend para que los cambios surtan efecto" -ForegroundColor Yellow
Write-Host "   2. Prueba la configuración con:" -ForegroundColor Yellow
Write-Host "      Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/analytics/test-notification' -Method POST" -ForegroundColor Cyan
Write-Host ""

