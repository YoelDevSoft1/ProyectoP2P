# Script para instalar extensiones de IA en Docker Desktop (Windows)
# NO modifica tu Dockerfile ni docker-compose.yml

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación de Extensiones de IA" -ForegroundColor Cyan
Write-Host "Docker Desktop - Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Detectar el nombre del contenedor del backend (según docker-compose.yml)
$containerName = "p2p_backend"

# Verificar que Docker Desktop está corriendo
Write-Host "Verificando Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Desktop no está corriendo o no está instalado" -ForegroundColor Red
    Write-Host "   Por favor, inicia Docker Desktop e intenta de nuevo" -ForegroundColor Yellow
    exit 1
}

# Verificar que el contenedor está corriendo
Write-Host ""
Write-Host "Verificando contenedor '$containerName'..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=$containerName" --format "{{.Names}}"
if (-not $containerStatus) {
    Write-Host "❌ Error: Contenedor '$containerName' no está corriendo" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, inicia el contenedor primero:" -ForegroundColor Yellow
    Write-Host "   docker-compose up -d" -ForegroundColor White
    Write-Host ""
    $startContainer = Read-Host "¿Deseas iniciar el contenedor ahora? (S/N)"
    if ($startContainer -eq "S" -or $startContainer -eq "s") {
        Write-Host "Iniciando contenedores..." -ForegroundColor Yellow
        docker-compose up -d
        Start-Sleep -Seconds 5
        $containerStatus = docker ps --filter "name=$containerName" --format "{{.Names}}"
        if (-not $containerStatus) {
            Write-Host "❌ Error: No se pudo iniciar el contenedor" -ForegroundColor Red
            exit 1
        }
    } else {
        exit 1
    }
}

Write-Host "✅ Contenedor encontrado: $containerName" -ForegroundColor Green
Write-Host ""

# Instalar Intel Extension for PyTorch
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1/3 Instalando Intel Extension for PyTorch" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
docker exec -it $containerName pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Hubo un problema instalando Intel Extension" -ForegroundColor Yellow
    Write-Host "   Continuando con la instalación..." -ForegroundColor Yellow
} else {
    Write-Host "✅ Intel Extension instalado correctamente" -ForegroundColor Green
}
Write-Host ""

# Instalar OpenVINO
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "2/3 Instalando OpenVINO" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
docker exec -it $containerName pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Hubo un problema instalando OpenVINO" -ForegroundColor Yellow
    Write-Host "   Continuando con la instalación..." -ForegroundColor Yellow
} else {
    Write-Host "✅ OpenVINO instalado correctamente" -ForegroundColor Green
}
Write-Host ""

# Instalar Intel MKL
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "3/3 Instalando optimizaciones Intel MKL" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
docker exec -it $containerName pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Hubo un problema instalando MKL" -ForegroundColor Yellow
} else {
    Write-Host "✅ Intel MKL instalado correctamente" -ForegroundColor Green
}
Write-Host ""

# Verificar instalación
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verificando instalación" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar PyTorch
Write-Host "Verificando PyTorch..." -ForegroundColor Yellow
docker exec -it $containerName python -c "import torch; print('✅ PyTorch', torch.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ PyTorch no encontrado" -ForegroundColor Red
}

# Verificar Intel Extension
Write-Host "Verificando Intel Extension..." -ForegroundColor Yellow
docker exec -it $containerName python -c "import intel_extension_for_pytorch as ipex; import torch; print('✅ Intel Extension instalado'); print('   GPU disponible:' if hasattr(torch, 'xpu') and torch.xpu.is_available() else '   Modo CPU')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Intel Extension no encontrado" -ForegroundColor Red
}

# Verificar OpenVINO
Write-Host "Verificando OpenVINO..." -ForegroundColor Yellow
docker exec -it $containerName python -c "from openvino.runtime import Core; core = Core(); print('✅ OpenVINO instalado'); print('   Dispositivos:', core.available_devices)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ OpenVINO no encontrado" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Instalación completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Información importante
Write-Host "📝 NOTAS IMPORTANTES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Los cambios están aplicados en el contenedor actual" -ForegroundColor White
Write-Host "2. Para hacer los cambios persistentes (sobrevivan a docker-compose down):" -ForegroundColor White
Write-Host "   docker commit $containerName proyecto-p2p-backend-with-ai:latest" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Para reiniciar el contenedor y aplicar cambios:" -ForegroundColor White
Write-Host "   docker-compose restart backend" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Si recreas el contenedor (docker-compose down), las extensiones se perderán" -ForegroundColor White
Write-Host "   a menos que hayas hecho commit de la imagen" -ForegroundColor White
Write-Host ""

# Preguntar si quiere hacer commit
$makeCommit = Read-Host "¿Deseas hacer commit de la imagen para hacer los cambios persistentes? (S/N)"
if ($makeCommit -eq "S" -or $makeCommit -eq "s") {
    Write-Host ""
    Write-Host "Creando imagen personalizada..." -ForegroundColor Yellow
    docker commit $containerName proyecto-p2p-backend-with-ai:latest
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Imagen creada: proyecto-p2p-backend-with-ai:latest" -ForegroundColor Green
        Write-Host ""
        Write-Host "Para usar esta imagen en el futuro, modifica docker-compose.yml:" -ForegroundColor Yellow
        Write-Host "   services:" -ForegroundColor White
        Write-Host "     backend:" -ForegroundColor White
        Write-Host "       image: proyecto-p2p-backend-with-ai:latest" -ForegroundColor Cyan
        Write-Host "       # Comenta o elimina la línea 'build:'" -ForegroundColor White
    } else {
        Write-Host "❌ Error al crear la imagen" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "¡Listo! Las extensiones de IA están instaladas." -ForegroundColor Green
Write-Host "Puedes reiniciar el contenedor para aplicar los cambios:" -ForegroundColor Yellow
Write-Host "   docker-compose restart backend" -ForegroundColor Cyan

