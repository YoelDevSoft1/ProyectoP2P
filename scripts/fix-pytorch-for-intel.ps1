# Script para corregir instalación de PyTorch para Intel Extension
# Cambia PyTorch CUDA a PyTorch CPU-only

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Corrigiendo PyTorch para Intel Extension" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if (-not $containerName) {
    Write-Host "❌ Error: Contenedor no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host "Contenedor: $containerName" -ForegroundColor Green
Write-Host ""

# Verificar versión actual de PyTorch
Write-Host "Verificando versión actual de PyTorch..." -ForegroundColor Yellow
$currentVersion = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Versión actual: $currentVersion" -ForegroundColor Cyan
    
    if ($currentVersion -like "*+cpu*") {
        Write-Host "✅ PyTorch CPU ya está instalado. No se requiere cambio." -ForegroundColor Green
        exit 0
    }
}

Write-Host ""
Write-Host "Desinstalando PyTorch CUDA..." -ForegroundColor Yellow
docker exec $containerName pip uninstall -y torch torchvision torchaudio

Write-Host ""
Write-Host "Instalando PyTorch CPU-only..." -ForegroundColor Yellow
docker exec $containerName pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ PyTorch CPU instalado correctamente" -ForegroundColor Green
    
    # Verificar
    $newVersion = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
    Write-Host "Nueva versión: $newVersion" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Ahora puedes reinstalar Intel Extension:" -ForegroundColor Yellow
    Write-Host "   docker exec $containerName pip install --no-cache-dir intel-extension-for-pytorch==2.1.0 --extra-index-url https://download.pytorch.org/whl/cpu" -ForegroundColor White
} else {
    Write-Host "❌ Error instalando PyTorch CPU" -ForegroundColor Red
    exit 1
}

