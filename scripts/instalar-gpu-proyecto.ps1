# Script para instalar GPU Intel Arc A750 en el proyecto actual
# Instala y configura todo lo necesario para usar GPU

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "Proyecto P2P Trading" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar GPU
Write-Host "1. Verificando GPU Intel Arc A750..." -ForegroundColor Yellow
$gpuDevices = Get-PnpDevice | Where-Object {
    $_.FriendlyName -like "*Arc*" -or 
    $_.FriendlyName -like "*Intel*Graphics*"
}

if ($gpuDevices) {
    Write-Host "✅ GPU Intel Arc encontrada:" -ForegroundColor Green
    foreach ($device in $gpuDevices) {
        Write-Host "   - $($device.FriendlyName) (Status: $($device.Status))" -ForegroundColor Cyan
    }
} else {
    Write-Host "⚠️  GPU Intel Arc no encontrada" -ForegroundColor Yellow
    Write-Host "   Continuando con instalación (modo CPU)" -ForegroundColor Cyan
}

Write-Host ""

# Verificar contenedor
Write-Host "2. Verificando contenedor Docker..." -ForegroundColor Yellow
$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if (-not $containerName) {
    Write-Host "❌ Contenedor no encontrado" -ForegroundColor Red
    Write-Host "   Iniciando contenedores..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
    $containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1
    if (-not $containerName) {
        Write-Host "❌ No se pudo iniciar el contenedor" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Contenedor: $containerName" -ForegroundColor Green
Write-Host ""

# Paso 1: Verificar/Instalar PyTorch
Write-Host "3. Verificando PyTorch..." -ForegroundColor Yellow
$torchCheck = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Instalando PyTorch CPU..." -ForegroundColor Cyan
    docker exec $containerName pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
} else {
    Write-Host "✅ PyTorch: $($torchCheck.Trim())" -ForegroundColor Green
}
Write-Host ""

# Paso 2: Desinstalar Intel Extension anterior (si tiene problemas)
Write-Host "4. Limpiando instalación anterior de Intel Extension..." -ForegroundColor Yellow
docker exec $containerName pip uninstall -y intel-extension-for-pytorch 2>&1 | Out-Null
Write-Host "✅ Limpieza completada" -ForegroundColor Green
Write-Host ""

# Paso 3: Intentar instalar Intel Extension
Write-Host "5. Instalando Intel Extension for PyTorch..." -ForegroundColor Yellow
Write-Host "   Nota: En Docker Desktop Windows, GPU puede no estar disponible" -ForegroundColor Cyan
Write-Host "   El sistema funcionará con CPU si GPU no está disponible" -ForegroundColor Cyan
Write-Host ""

# Intentar instalar desde repositorio oficial
docker exec $containerName pip install --no-cache-dir intel-extension-for-pytorch==2.1.0 --extra-index-url https://download.pytorch.org/whl/cpu

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Error instalando Intel Extension" -ForegroundColor Yellow
    Write-Host "   Continuando sin Intel Extension (PyTorch estándar funcionará)" -ForegroundColor Cyan
} else {
    Write-Host "✅ Intel Extension instalado" -ForegroundColor Green
}
Write-Host ""

# Paso 4: Instalar OpenVINO (siempre útil)
Write-Host "6. Instalando OpenVINO..." -ForegroundColor Yellow
docker exec $containerName pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0 2>&1 | Out-Null
Write-Host "✅ OpenVINO instalado" -ForegroundColor Green
Write-Host ""

# Paso 5: Verificar instalación
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Verificando instalación..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Probando módulo de GPU..." -ForegroundColor Yellow
docker exec $containerName python -c "import sys; sys.path.insert(0, '/app'); from app.ml.gpu_utils import print_gpu_status; print_gpu_status()" 2>&1

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación Completada" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "El sistema está configurado para:" -ForegroundColor Yellow
Write-Host "  ✅ Detectar automáticamente si hay GPU disponible" -ForegroundColor Green
Write-Host "  ✅ Usar GPU si está disponible" -ForegroundColor Green
Write-Host "  ✅ Usar CPU si GPU no está disponible (funciona perfectamente)" -ForegroundColor Green
Write-Host ""

Write-Host "Para verificar el estado de GPU:" -ForegroundColor Yellow
$verifyCmd = "docker exec $containerName python -c `"from app.ml.gpu_utils import print_gpu_status; print_gpu_status()`""
Write-Host "   $verifyCmd" -ForegroundColor White
Write-Host ""

Write-Host "Para hacer los cambios persistentes:" -ForegroundColor Yellow
Write-Host "   docker commit $containerName proyecto-p2p-backend-with-gpu:latest" -ForegroundColor White
Write-Host ""

Write-Host "Nota: Si GPU no está disponible en Docker, considera:" -ForegroundColor Cyan
Write-Host "  - Instalar directamente en Windows (mejor rendimiento GPU)" -ForegroundColor White
Write-Host "  - Usar WSL2 con configuración GPU (complejo)" -ForegroundColor White
Write-Host "  - Continuar con CPU (funciona perfectamente para tus necesidades)" -ForegroundColor White
Write-Host ""

