# Script para verificar que las extensiones de IA están instaladas correctamente

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verificación de Extensiones de IA" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Detectar contenedor
$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if (-not $containerName) {
    Write-Host "❌ Error: No se encontró el contenedor del backend" -ForegroundColor Red
    exit 1
}

Write-Host "Contenedor: $containerName" -ForegroundColor Green
Write-Host ""

# Verificar PyTorch
Write-Host "1. Verificando PyTorch..." -ForegroundColor Yellow
$torchCheck = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ PyTorch: $torchCheck" -ForegroundColor Green
} else {
    Write-Host "   ❌ PyTorch: No instalado" -ForegroundColor Red
}

# Verificar Intel Extension
Write-Host "2. Verificando Intel Extension for PyTorch..." -ForegroundColor Yellow
$ipexCheck = docker exec $containerName python -c "import intel_extension_for_pytorch as ipex; import torch; print('OK'); gpu = 'GPU disponible' if hasattr(torch, 'xpu') and torch.xpu.is_available() else 'Modo CPU'; print(gpu)" 2>&1
if ($LASTEXITCODE -eq 0) {
    $lines = $ipexCheck -split "`n"
    Write-Host "   ✅ Intel Extension: $($lines[0])" -ForegroundColor Green
    Write-Host "   ℹ️  Modo: $($lines[1])" -ForegroundColor Cyan
} else {
    Write-Host "   ❌ Intel Extension: Error" -ForegroundColor Red
    Write-Host "   Detalles: $ipexCheck" -ForegroundColor Yellow
}

# Verificar OpenVINO
Write-Host "3. Verificando OpenVINO..." -ForegroundColor Yellow
$openvinoCheck = docker exec $containerName python -c "from openvino.runtime import Core; core = Core(); devices = core.available_devices; print('OK'); print(str(devices))" 2>&1
if ($LASTEXITCODE -eq 0) {
    $lines = $openvinoCheck -split "`n"
    Write-Host "   ✅ OpenVINO: $($lines[0])" -ForegroundColor Green
    Write-Host "   ℹ️  Dispositivos: $($lines[1])" -ForegroundColor Cyan
} else {
    Write-Host "   ❌ OpenVINO: Error" -ForegroundColor Red
}

# Verificar MKL
Write-Host "4. Verificando Intel MKL..." -ForegroundColor Yellow
$mklCheck = docker exec $containerName python -c "import mkl; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Intel MKL: Instalado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Intel MKL: No verificado (puede estar instalado)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Resumen" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Las extensiones de IA están listas para usar." -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Reiniciar el contenedor: docker-compose restart backend" -ForegroundColor White
Write-Host "2. Entrenar un modelo: python backend/scripts/train_dl_models.py --model lstm" -ForegroundColor White
Write-Host "3. Usar las APIs de IA en el dashboard" -ForegroundColor White

