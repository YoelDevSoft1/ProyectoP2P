# Script PowerShell para instalar extensiones de IA DENTRO del contenedor Docker
# NO modifica el Dockerfile - se ejecuta después de que el contenedor está corriendo

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalando extensiones de IA en el contenedor" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Detectar automáticamente el nombre del contenedor
Write-Host "Buscando contenedor del backend..." -ForegroundColor Yellow
$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if (-not $containerName) {
    Write-Host "❌ Error: No se encontró el contenedor del backend" -ForegroundColor Red
    Write-Host ""
    Write-Host "Contenedores disponibles:" -ForegroundColor Yellow
    docker ps --format "{{.Names}}"
    Write-Host ""
    Write-Host "Por favor, inicia los contenedores primero:" -ForegroundColor Yellow
    Write-Host "   docker-compose up -d" -ForegroundColor White
    exit 1
}

Write-Host "✅ Contenedor encontrado: $containerName" -ForegroundColor Green
Write-Host ""

# Verificar si PyTorch está instalado (sin -it para evitar problemas en Windows)
Write-Host "Verificando PyTorch..." -ForegroundColor Yellow
$torchCheck = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  PyTorch no está instalado. Instalando PyTorch CPU-only..." -ForegroundColor Yellow
    Write-Host "0/4 Instalando PyTorch CPU-only (esto puede tardar varios minutos, ~185 MB)..." -ForegroundColor Yellow
    Write-Host "   Usando versión CPU-only para compatibilidad con Intel Extension..." -ForegroundColor Cyan
    docker exec $containerName pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: No se pudo instalar PyTorch" -ForegroundColor Red
        Write-Host "   Por favor, verifica que el contenedor tiene conexión a internet" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ PyTorch CPU-only instalado" -ForegroundColor Green
    Write-Host ""
} else {
    # Verificar si es versión CPU o CUDA
    $torchVersion = $torchCheck.Trim()
    if ($torchVersion -like "*+cpu*") {
        Write-Host "✅ PyTorch CPU ya está instalado: $torchVersion" -ForegroundColor Green
    } elseif ($torchVersion -like "*+cu*") {
        Write-Host "⚠️  PyTorch CUDA detectado: $torchVersion" -ForegroundColor Yellow
        Write-Host "   Se recomienda usar PyTorch CPU-only para Intel Extension" -ForegroundColor Yellow
        $reinstall = Read-Host "¿Deseas reinstalar PyTorch CPU-only? (S/N)"
        if ($reinstall -eq "S" -or $reinstall -eq "s") {
            Write-Host "Reinstalando PyTorch CPU-only..." -ForegroundColor Yellow
            docker exec $containerName pip uninstall -y torch torchvision torchaudio
            docker exec $containerName pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
        }
    } else {
        Write-Host "✅ PyTorch ya está instalado: $torchVersion" -ForegroundColor Green
    }
    Write-Host ""
}

# Instalar Intel Extension for PyTorch (sin -it para Windows)
# Usar versión compatible con PyTorch 2.1.0
Write-Host "1/4 Instalando Intel Extension for PyTorch (versión compatible con PyTorch 2.1.0)..." -ForegroundColor Yellow
docker exec $containerName pip install --no-cache-dir intel-extension-for-pytorch==2.1.0 --extra-index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando Intel Extension" -ForegroundColor Yellow
} else {
    Write-Host "✅ Intel Extension instalado" -ForegroundColor Green
}
Write-Host ""

# Instalar OpenVINO (sin -it para Windows)
Write-Host "2/4 Instalando OpenVINO..." -ForegroundColor Yellow
docker exec $containerName pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando OpenVINO" -ForegroundColor Yellow
} else {
    Write-Host "✅ OpenVINO instalado" -ForegroundColor Green
}
Write-Host ""

# Instalar optimizaciones Intel MKL (sin -it para Windows)
Write-Host "3/4 Instalando optimizaciones Intel MKL (esto puede tardar, ~250 MB)..." -ForegroundColor Yellow
docker exec $containerName pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Error instalando MKL" -ForegroundColor Yellow
} else {
    Write-Host "✅ MKL instalado" -ForegroundColor Green
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Instalación completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Verificar instalación
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verificando instalación..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar PyTorch (sin -it para Windows)
Write-Host "Verificando PyTorch..." -ForegroundColor Yellow
$torchCheck = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PyTorch: $torchCheck" -ForegroundColor Green
} else {
    Write-Host "❌ PyTorch: No encontrado" -ForegroundColor Red
    Write-Host "   Error: $torchCheck" -ForegroundColor Yellow
}

# Verificar Intel Extension (sin -it para Windows)
Write-Host "Verificando Intel Extension..." -ForegroundColor Yellow
$ipexCheck = docker exec $containerName python -c "import intel_extension_for_pytorch as ipex; import torch; print('Instalado'); gpu_available = 'GPU disponible' if hasattr(torch, 'xpu') and torch.xpu.is_available() else 'Modo CPU'; print(gpu_available)" 2>&1
if ($LASTEXITCODE -eq 0) {
    $lines = $ipexCheck -split "`n" | Where-Object { $_.Trim() -ne "" }
    Write-Host "✅ Intel Extension: $($lines[0])" -ForegroundColor Green
    if ($lines.Count -gt 1) {
        Write-Host "   Modo: $($lines[1])" -ForegroundColor Cyan
    }
} else {
    Write-Host "⚠️  Intel Extension: Problema al importar (puede ser problema de Docker)" -ForegroundColor Yellow
    Write-Host "   El sistema funcionará con PyTorch estándar (CPU)" -ForegroundColor Cyan
    Write-Host "   Detalles: $($ipexCheck -split '`n' | Select-Object -First 2 -Join ' ')" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Nota: Esto es común en Docker debido a restricciones de seguridad." -ForegroundColor Yellow
    Write-Host "   PyTorch CPU funcionará perfectamente para entrenamiento e inferencia." -ForegroundColor Cyan
}

# Verificar OpenVINO (sin -it para Windows)
Write-Host "Verificando OpenVINO..." -ForegroundColor Yellow
$openvinoCheck = docker exec $containerName python -c "from openvino.runtime import Core; core = Core(); devices = core.available_devices; print('Instalado'); print('Dispositivos: ' + str(devices))" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ OpenVINO: $openvinoCheck" -ForegroundColor Green
} else {
    Write-Host "❌ OpenVINO: No encontrado" -ForegroundColor Red
    Write-Host "   Error: $openvinoCheck" -ForegroundColor Yellow
}

# Verificar MKL (sin -it para Windows)
Write-Host "Verificando Intel MKL..." -ForegroundColor Yellow
$mklCheck = docker exec $containerName python -c "import mkl; print('Instalado')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Intel MKL: $mklCheck" -ForegroundColor Green
} else {
    Write-Host "⚠️  Intel MKL: No verificado (puede estar instalado pero no importable directamente)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Para reiniciar el contenedor y aplicar cambios:" -ForegroundColor Yellow
Write-Host "   docker-compose restart backend" -ForegroundColor White
Write-Host ""
Write-Host "Para hacer los cambios persistentes (sobrevivan a docker-compose down):" -ForegroundColor Yellow
Write-Host "   docker commit $containerName proyecto-p2p-backend-with-ai:latest" -ForegroundColor White

