# Script rápido para instalar extensiones de IA en el contenedor Docker
# NO modifica ningún archivo existente

param(
    [string]$ContainerName = "p2p-backend"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación Rápida de Extensiones de IA" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el contenedor está corriendo
$containerRunning = docker ps --format "{{.Names}}" | Select-String -Pattern $ContainerName
if (-not $containerRunning) {
    Write-Host "❌ Error: Contenedor '$ContainerName' no está corriendo" -ForegroundColor Red
    Write-Host "   Ejecuta primero: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Contenedor encontrado: $ContainerName" -ForegroundColor Green
Write-Host ""

# Instalar Intel Extension
Write-Host "1/3 Instalando Intel Extension for PyTorch..." -ForegroundColor Yellow
docker exec -it $ContainerName pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando Intel Extension" -ForegroundColor Yellow
}

# Instalar OpenVINO
Write-Host "2/3 Instalando OpenVINO..." -ForegroundColor Yellow
docker exec -it $ContainerName pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando OpenVINO" -ForegroundColor Yellow
}

# Instalar MKL
Write-Host "3/3 Instalando optimizaciones Intel MKL..." -ForegroundColor Yellow
docker exec -it $ContainerName pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando MKL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Instalación completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Verificar instalación
Write-Host "Verificando instalación..." -ForegroundColor Cyan
docker exec -it $ContainerName python -c "import torch; print('✅ PyTorch:', torch.__version__)" 2>$null
docker exec -it $ContainerName python -c "import intel_extension_for_pytorch as ipex; print('✅ Intel Extension instalado')" 2>$null
docker exec -it $ContainerName python -c "from openvino.runtime import Core; print('✅ OpenVINO instalado')" 2>$null

Write-Host ""
Write-Host "📝 Nota: Para hacer los cambios persistentes, crea un commit:" -ForegroundColor Yellow
Write-Host "   docker commit $ContainerName proyecto-p2p-backend-with-ai:latest" -ForegroundColor White
Write-Host ""
Write-Host "   O reinicia el contenedor para aplicar cambios:" -ForegroundColor Yellow
Write-Host "   docker-compose restart backend" -ForegroundColor White

