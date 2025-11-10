# Script completo para instalar GPU Intel Arc A750
# Intenta múltiples métodos para habilitar GPU

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación Completa GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Método 1: Verificar e instalar en Docker (si es posible)
Write-Host "MÉTODO 1: Instalación en Docker" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow

$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if ($containerName) {
    Write-Host "✅ Contenedor encontrado: $containerName" -ForegroundColor Green
    
    # Desinstalar Intel Extension problemático
    Write-Host "Desinstalando Intel Extension anterior (puede tener problemas)..." -ForegroundColor Yellow
    docker exec $containerName pip uninstall -y intel-extension-for-pytorch 2>&1 | Out-Null
    
    # Intentar instalar versión más reciente que pueda tener mejor soporte
    Write-Host "Instalando Intel Extension (versión compatible)..." -ForegroundColor Yellow
    Write-Host "   Nota: GPU puede no funcionar en Docker Desktop Windows" -ForegroundColor Cyan
    
    # Intentar con repositorio oficial de Intel
    docker exec $containerName pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu 2>&1 | Out-Null
    
    Write-Host "✅ Instalación en Docker completada" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⚠️  Contenedor no encontrado" -ForegroundColor Yellow
    Write-Host ""
}

# Método 2: Instalar directamente en Windows (mejor para GPU)
Write-Host "MÉTODO 2: Instalación Directa en Windows" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para usar GPU Intel Arc A750 con máximo rendimiento," -ForegroundColor Cyan
Write-Host "se recomienda instalar directamente en Windows (fuera de Docker)." -ForegroundColor Cyan
Write-Host ""

$installWindows = Read-Host "¿Deseas instalar PyTorch e Intel Extension en Windows? (S/N)"

if ($installWindows -eq "S" -or $installWindows -eq "s") {
    Write-Host ""
    Write-Host "Instalando en Windows..." -ForegroundColor Yellow
    
    # Verificar Python
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python no encontrado. Por favor, instala Python 3.11+" -ForegroundColor Red
        exit 1
    }
    
    # Instalar PyTorch
    Write-Host "Instalando PyTorch..." -ForegroundColor Yellow
    pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
    
    # Intentar instalar Intel Extension con XPU
    Write-Host "Instalando Intel Extension con soporte XPU..." -ForegroundColor Yellow
    pip install --no-cache-dir intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  No se pudo instalar con XPU, instalando versión CPU..." -ForegroundColor Yellow
        pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
    }
    
    # Verificar GPU
    Write-Host ""
    Write-Host "Verificando GPU..." -ForegroundColor Yellow
    python -c @"
import sys
try:
    import torch
    import intel_extension_for_pytorch as ipex
    print('✅ PyTorch e Intel Extension instalados')
    
    if hasattr(torch, 'xpu') and torch.xpu.is_available():
        print('✅ GPU Intel Arc A750: DISPONIBLE')
        print(f'   Dispositivos: {torch.xpu.device_count()}')
    else:
        print('⚠️  GPU: No disponible (modo CPU)')
        print('   Verifica que los drivers de Intel Arc estén instalados')
except Exception as e:
    print(f'⚠️  Error: {e}')
"@
    
    Write-Host ""
    Write-Host "✅ Instalación en Windows completada" -ForegroundColor Green
} else {
    Write-Host "Instalación en Windows omitida" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Resumen" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para usar GPU en tu proyecto:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. En Docker: GPU puede no estar disponible (limitaciones de Docker Desktop)" -ForegroundColor Cyan
Write-Host "   - El código detectará automáticamente si hay GPU" -ForegroundColor White
Write-Host "   - Si no hay GPU, usará CPU (funciona perfectamente)" -ForegroundColor White
Write-Host ""
Write-Host "2. En Windows: GPU está disponible si instalaste en Windows" -ForegroundColor Cyan
Write-Host "   - Mejor rendimiento para entrenamiento" -ForegroundColor White
Write-Host "   - Acceso directo a drivers" -ForegroundColor White
Write-Host ""
Write-Host "3. Código Híbrido: El sistema detectará automáticamente la mejor opción" -ForegroundColor Cyan
Write-Host "   - Si hay GPU disponible, la usará" -ForegroundColor White
Write-Host "   - Si no, usará CPU (sin problemas)" -ForegroundColor White
Write-Host ""

