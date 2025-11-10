# Script para configurar WSL2 con soporte GPU para Intel Arc A750
# Ejecutar como Administrador

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Configuración de WSL2 para GPU Intel Arc" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Este script debe ejecutarse como Administrador" -ForegroundColor Yellow
Write-Host ""

# Verificar si es Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Error: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host "   Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Ejecutando como Administrador" -ForegroundColor Green
Write-Host ""

# Paso 1: Instalar WSL2
Write-Host "1. Instalando WSL2..." -ForegroundColor Yellow
wsl --install
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  WSL2 puede ya estar instalado o hubo un error" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2. Configurando WSL2 como versión por defecto..." -ForegroundColor Yellow
wsl --set-default-version 2

Write-Host ""
Write-Host "3. Verificando distribución WSL2..." -ForegroundColor Yellow
$wslDistros = wsl --list --verbose
Write-Host $wslDistros

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Próximos Pasos" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. REINICIA tu sistema Windows" -ForegroundColor Yellow
Write-Host "2. Después del reinicio, ejecuta estos comandos en WSL2:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Entrar a WSL2" -ForegroundColor White
Write-Host "   wsl" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # Instalar drivers Intel en WSL2" -ForegroundColor White
Write-Host "   sudo apt-get update" -ForegroundColor Cyan
Write-Host "   sudo apt-get install -y intel-opencl-icd intel-level-zero-gpu level-zero" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # Verificar GPU" -ForegroundColor White
Write-Host "   lspci | grep -i intel" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Configura Docker Desktop para usar WSL2 backend" -ForegroundColor Yellow
Write-Host "4. Reinicia Docker Desktop" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para más información, consulta: CONFIGURAR_GPU_INTEL_ARC.md" -ForegroundColor Cyan

