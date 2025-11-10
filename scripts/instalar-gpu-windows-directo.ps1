# Script para instalar GPU Intel Arc A750 directamente en Windows
# Usa 'py' launcher de Python

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Instalación GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "Directamente en Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esta instalación permite usar GPU con máximo rendimiento" -ForegroundColor Yellow
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
    $pythonVersion = py --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado" -ForegroundColor Red
    Write-Host "   Por favor, instala Python 3.11+" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar pip
Write-Host "3. Verificando pip..." -ForegroundColor Yellow
try {
    $pipVersion = py -m pip --version
    Write-Host "✅ pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Instalar PyTorch CPU (base)
Write-Host "4. Instalando PyTorch CPU (base)..." -ForegroundColor Yellow
Write-Host "   Esto puede tardar varios minutos (~185 MB)..." -ForegroundColor Cyan
py -m pip install --no-cache-dir torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error instalando PyTorch" -ForegroundColor Red
    exit 1
}

Write-Host "✅ PyTorch instalado" -ForegroundColor Green
Write-Host ""

# Instalar Intel Extension con soporte XPU (GPU)
Write-Host "5. Instalando Intel Extension for PyTorch con soporte XPU (GPU)..." -ForegroundColor Yellow
Write-Host "   Esto puede tardar varios minutos (~500 MB)..." -ForegroundColor Cyan
Write-Host "   Instalando desde repositorio oficial de Intel..." -ForegroundColor Cyan
Write-Host ""

# Intentar instalar con soporte XPU
py -m pip install --no-cache-dir intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  No se pudo instalar con soporte XPU desde repositorio Intel" -ForegroundColor Yellow
    Write-Host "   Intentando instalación alternativa..." -ForegroundColor Cyan
    
    # Intentar instalación alternativa
    py -m pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error instalando Intel Extension" -ForegroundColor Red
        Write-Host "   Continuando sin Intel Extension (PyTorch estándar funcionará)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Intel Extension CPU instalado" -ForegroundColor Green
        Write-Host "   Nota: Puede no tener soporte XPU completo" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Intel Extension con soporte XPU instalado" -ForegroundColor Green
}

Write-Host ""

# Instalar OpenVINO
Write-Host "6. Instalando OpenVINO..." -ForegroundColor Yellow
py -m pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Error instalando OpenVINO" -ForegroundColor Yellow
} else {
    Write-Host "✅ OpenVINO instalado" -ForegroundColor Green
}

Write-Host ""

# Instalar Intel MKL
Write-Host "7. Instalando Intel MKL (optimizaciones)..." -ForegroundColor Yellow
py -m pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Error instalando MKL" -ForegroundColor Yellow
} else {
    Write-Host "✅ MKL instalado" -ForegroundColor Green
}

Write-Host ""

# Verificar instalación
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Verificando instalación GPU..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Verificando PyTorch..." -ForegroundColor Yellow
py -c "import torch; print('✅ PyTorch:', torch.__version__)" 2>&1

Write-Host ""
Write-Host "Verificando Intel Extension y GPU..." -ForegroundColor Yellow
py -c @"
import sys
try:
    import intel_extension_for_pytorch as ipex
    import torch
    print('✅ Intel Extension: Instalado')
    
    # Verificar soporte XPU
    if hasattr(torch, 'xpu'):
        print('✅ Soporte XPU: Disponible')
        if torch.xpu.is_available():
            print('✅ GPU Intel Arc A750: DISPONIBLE')
            print(f'   Dispositivos XPU: {torch.xpu.device_count()}')
            for i in range(torch.xpu.device_count()):
                device_name = torch.xpu.get_device_name(i)
                print(f'   - Dispositivo {i}: {device_name}')
            
            # Test básico
            print('')
            print('Probando GPU...')
            x = torch.randn(5, 5, device='xpu:0')
            y = torch.matmul(x, x)
            print('✅ GPU funciona correctamente!')
        else:
            print('⚠️  GPU Intel Arc A750: No disponible')
            print('   Verifica que los drivers de Intel Arc estén instalados')
            print('   Descarga desde: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html')
    else:
        print('⚠️  Soporte XPU no disponible')
        print('   Modo: CPU')
except ImportError as e:
    print('⚠️  Intel Extension: No se pudo importar')
    print(f'   Error: {str(e)}')
    print('   PyTorch estándar funcionará correctamente')
except Exception as e:
    print(f'⚠️  Error: {str(e)}')
    import traceback
    traceback.print_exc()
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
$verifyCmd = "py -c `"from app.ml.gpu_utils import print_gpu_status; print_gpu_status()`""
Write-Host "   $verifyCmd" -ForegroundColor White
Write-Host ""

Write-Host "Nota: Si GPU no está disponible, verifica:" -ForegroundColor Cyan
Write-Host "  1. Drivers de Intel Arc instalados y actualizados" -ForegroundColor White
Write-Host "  2. GPU reconocida en Administrador de dispositivos" -ForegroundColor White
Write-Host "  3. Sistema reiniciado después de instalar drivers" -ForegroundColor White
Write-Host "  4. Descarga drivers desde:" -ForegroundColor White
Write-Host "     https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html" -ForegroundColor Cyan
Write-Host ""
