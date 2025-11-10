# Script para instalar GPU Intel Arc A750 directamente en Windows
# Esto permite usar GPU con máximo rendimiento (fuera de Docker)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "Directamente en Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esta instalación permite usar GPU con máximo rendimiento" -ForegroundColor Yellow
Write-Host "sin las limitaciones de Docker Desktop" -ForegroundColor Yellow
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

# Verificar Python
Write-Host "2. Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado" -ForegroundColor Red
    Write-Host "   Por favor, instala Python 3.11+" -ForegroundColor Yellow
    Write-Host "   Descarga desde: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Verificar pip
Write-Host "3. Verificando pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "✅ pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Instalar PyTorch
Write-Host "4. Instalando PyTorch..." -ForegroundColor Yellow
Write-Host "   Instalando PyTorch 2.1.0 CPU (base para Intel Extension)..." -ForegroundColor Cyan
pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error instalando PyTorch" -ForegroundColor Red
    exit 1
}

Write-Host "✅ PyTorch instalado" -ForegroundColor Green
Write-Host ""

# Instalar Intel Extension con soporte XPU
Write-Host "5. Instalando Intel Extension for PyTorch con soporte XPU..." -ForegroundColor Yellow
Write-Host "   Esto puede tardar varios minutos (descargando ~500 MB)..." -ForegroundColor Cyan
Write-Host ""

# Intentar instalar con soporte XPU desde el repositorio oficial de Intel
pip install --no-cache-dir intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  No se pudo instalar con soporte XPU" -ForegroundColor Yellow
    Write-Host "   Intentando instalación CPU-only..." -ForegroundColor Cyan
    pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error instalando Intel Extension" -ForegroundColor Red
        Write-Host "   Continuando sin Intel Extension (PyTorch estándar funcionará)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Intel Extension CPU instalado" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Intel Extension con soporte XPU instalado" -ForegroundColor Green
}

Write-Host ""

# Instalar OpenVINO
Write-Host "6. Instalando OpenVINO..." -ForegroundColor Yellow
pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Error instalando OpenVINO" -ForegroundColor Yellow
} else {
    Write-Host "✅ OpenVINO instalado" -ForegroundColor Green
}

Write-Host ""

# Verificar instalación
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Verificando instalación GPU..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Verificando PyTorch..." -ForegroundColor Yellow
python -c "import torch; print('✅ PyTorch:', torch.__version__)" 2>&1

Write-Host ""
Write-Host "Verificando Intel Extension y GPU..." -ForegroundColor Yellow
python -c @"
import sys
try:
    import intel_extension_for_pytorch as ipex
    import torch
    print('✅ Intel Extension: Instalado')
    
    # Verificar soporte XPU
    if hasattr(torch, 'xpu'):
        if torch.xpu.is_available():
            print('✅ GPU Intel Arc A750: DISPONIBLE')
            print(f'   Dispositivos XPU: {torch.xpu.device_count()}')
            for i in range(torch.xpu.device_count()):
                print(f'   - Dispositivo {i}: {torch.xpu.get_device_name(i)}')
        else:
            print('⚠️  GPU Intel Arc A750: No disponible')
            print('   Verifica que los drivers de Intel Arc estén instalados')
            print('   Descarga drivers desde: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html')
    else:
        print('⚠️  Soporte XPU no disponible')
        print('   Modo: CPU')
except ImportError as e:
    print('⚠️  Intel Extension: No se pudo importar')
    print(f'   Error: {str(e)}')
    print('   PyTorch estándar funcionará correctamente')
except Exception as e:
    print(f'⚠️  Error: {str(e)}')
"@

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación Completada" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Para usar GPU en tu código Python:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   from app.ml.gpu_utils import get_device, to_device" -ForegroundColor White
Write-Host "   " -ForegroundColor White
Write-Host "   device = get_device()  # Detecta automáticamente GPU o CPU" -ForegroundColor White
Write-Host "   model = model.to(device)  # Mueve modelo a GPU si está disponible" -ForegroundColor White
Write-Host ""

Write-Host "Para verificar el estado de GPU:" -ForegroundColor Yellow
$verifyCmd = "python -c `"from app.ml.gpu_utils import print_gpu_status; print_gpu_status()`""
Write-Host "   $verifyCmd" -ForegroundColor White
Write-Host ""

Write-Host "Nota: Si GPU no está disponible, verifica:" -ForegroundColor Cyan
Write-Host "  1. Drivers de Intel Arc instalados y actualizados" -ForegroundColor White
Write-Host "  2. GPU reconocida en Administrador de dispositivos" -ForegroundColor White
Write-Host "  3. Sistema reiniciado después de instalar drivers" -ForegroundColor White
Write-Host ""

