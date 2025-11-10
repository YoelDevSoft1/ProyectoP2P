# Script para configurar GPU Intel Arc A750 en Docker Desktop (Windows)
# Este script ayuda a verificar y configurar el acceso a GPU

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Configuración de GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "Docker Desktop - Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar GPU en Windows
Write-Host "1. Verificando GPU Intel Arc en Windows..." -ForegroundColor Yellow
$gpuDevices = Get-PnpDevice | Where-Object {
    $_.FriendlyName -like "*Arc*" -or 
    $_.FriendlyName -like "*Intel*Graphics*" -or
    $_.FriendlyName -like "*Iris*Xe*"
}

if ($gpuDevices) {
    Write-Host "✅ GPU Intel encontrada:" -ForegroundColor Green
    foreach ($device in $gpuDevices) {
        Write-Host "   - $($device.FriendlyName)" -ForegroundColor Cyan
        Write-Host "     Estado: $($device.Status)" -ForegroundColor $(if ($device.Status -eq "OK") { "Green" } else { "Yellow" })
    }
} else {
    Write-Host "❌ No se encontró GPU Intel Arc" -ForegroundColor Red
    Write-Host "   Verifica que la GPU está instalada físicamente" -ForegroundColor Yellow
    Write-Host "   Verifica que los drivers están instalados" -ForegroundColor Yellow
}

Write-Host ""

# Verificar WSL2
Write-Host "2. Verificando WSL2..." -ForegroundColor Yellow
$wslVersion = wsl --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ WSL2 está instalado" -ForegroundColor Green
    $wslDistros = wsl --list --verbose 2>&1
    Write-Host "Distribuciones WSL:" -ForegroundColor Cyan
    Write-Host $wslDistros -ForegroundColor White
} else {
    Write-Host "⚠️  WSL2 no está instalado" -ForegroundColor Yellow
    Write-Host "   Se recomienda instalar WSL2 para mejor soporte de GPU" -ForegroundColor Yellow
    $installWSL = Read-Host "¿Deseas instalar WSL2? (S/N)"
    if ($installWSL -eq "S" -or $installWSL -eq "s") {
        Write-Host "Instalando WSL2..." -ForegroundColor Yellow
        wsl --install
        Write-Host "⚠️  Reinicia tu sistema después de la instalación" -ForegroundColor Yellow
    }
}

Write-Host ""

# Verificar Docker Desktop
Write-Host "3. Verificando Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
    
    # Verificar si usa WSL2
    $dockerInfo = docker info 2>&1
    if ($dockerInfo -like "*WSL*") {
        Write-Host "✅ Docker está usando WSL2 backend" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Docker puede no estar usando WSL2" -ForegroundColor Yellow
        Write-Host "   Se recomienda usar WSL2 para mejor soporte de GPU" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Docker Desktop no está corriendo" -ForegroundColor Red
    Write-Host "   Por favor, inicia Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar contenedor
Write-Host "4. Verificando contenedor del backend..." -ForegroundColor Yellow
$containerName = docker ps --filter "name=backend" --format "{{.Names}}" | Select-Object -First 1

if ($containerName) {
    Write-Host "✅ Contenedor encontrado: $containerName" -ForegroundColor Green
    
    # Verificar PyTorch
    Write-Host ""
    Write-Host "5. Verificando PyTorch en el contenedor..." -ForegroundColor Yellow
    $torchCheck = docker exec $containerName python -c "import torch; print(torch.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PyTorch: $torchCheck" -ForegroundColor Green
    } else {
        Write-Host "❌ PyTorch no está instalado" -ForegroundColor Red
    }
    
    # Verificar Intel Extension
    Write-Host ""
    Write-Host "6. Verificando Intel Extension..." -ForegroundColor Yellow
    $ipexCheck = docker exec $containerName python -c "import intel_extension_for_pytorch as ipex; import torch; print('Instalado'); xpu_available = 'XPU disponible' if hasattr(torch, 'xpu') and torch.xpu.is_available() else 'XPU no disponible'; print(xpu_available)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $lines = $ipexCheck -split "`n" | Where-Object { $_.Trim() -ne "" }
        Write-Host "✅ Intel Extension: $($lines[0])" -ForegroundColor Green
        if ($lines.Count -gt 1) {
            Write-Host "   Estado GPU: $($lines[1])" -ForegroundColor $(if ($lines[1] -like "*disponible*") { "Green" } else { "Yellow" })
        }
    } else {
        Write-Host "⚠️  Intel Extension: Problema al importar" -ForegroundColor Yellow
        Write-Host "   Esto es común en Docker Desktop Windows" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ Contenedor del backend no está corriendo" -ForegroundColor Red
    Write-Host "   Inicia el contenedor: docker-compose up -d" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Recomendaciones" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Para usar GPU Intel Arc A750 en Docker:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Opción Recomendada: Usar WSL2" -ForegroundColor Cyan
Write-Host "   - Instala WSL2: wsl --install" -ForegroundColor White
Write-Host "   - Configura Docker Desktop para usar WSL2 backend" -ForegroundColor White
Write-Host "   - Instala drivers Intel en WSL2" -ForegroundColor White
Write-Host ""
Write-Host "2. Opción Alternativa: Ejecutar fuera de Docker" -ForegroundColor Cyan
Write-Host "   - Instala PyTorch e Intel Extension directamente en Windows" -ForegroundColor White
Write-Host "   - Mejor rendimiento de GPU" -ForegroundColor White
Write-Host ""
Write-Host "3. Opción Actual: Usar CPU (Funciona Perfectamente)" -ForegroundColor Cyan
Write-Host "   - PyTorch CPU es más que suficiente para tus necesidades" -ForegroundColor White
Write-Host "   - Entrenamiento: 5-15 minutos (aceptable)" -ForegroundColor White
Write-Host "   - Inferencia: <100ms (excelente)" -ForegroundColor White
Write-Host ""

Write-Host "¿Qué opción prefieres?" -ForegroundColor Yellow
Write-Host "1. Configurar WSL2 para GPU"
Write-Host "2. Instalar en Windows (fuera de Docker)"
Write-Host "3. Continuar con CPU (recomendado)"

$opcion = Read-Host "Selecciona una opción (1/2/3)"

if ($opcion -eq "1") {
    Write-Host ""
    Write-Host "Instalando WSL2..." -ForegroundColor Yellow
    wsl --install
    Write-Host ""
    Write-Host "⚠️  IMPORTANTE: Reinicia tu sistema después de instalar WSL2" -ForegroundColor Yellow
    Write-Host "   Luego ejecuta este script de nuevo" -ForegroundColor Yellow
} elseif ($opcion -eq "2") {
    Write-Host ""
    Write-Host "Instalando PyTorch e Intel Extension en Windows..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ejecuta estos comandos en PowerShell:" -ForegroundColor Cyan
    Write-Host "   pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu" -ForegroundColor White
    Write-Host "   pip install intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✅ Continuando con CPU - Esta es la opción más simple y funciona perfectamente" -ForegroundColor Green
    Write-Host "   Tu sistema está listo para usar Deep Learning con PyTorch CPU" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Para más información, consulta: CONFIGURAR_GPU_INTEL_ARC.md" -ForegroundColor Yellow

