# Script para verificar GPU Intel Arc A750 en Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verificando GPU Intel Arc A750" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar PyTorch
Write-Host "1. Verificando PyTorch..." -ForegroundColor Yellow
try {
    $torchOutput = py -c "import torch; print(torch.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK PyTorch: $torchOutput" -ForegroundColor Green
    } else {
        Write-Host "ERROR: PyTorch no funciona" -ForegroundColor Red
        Write-Host $torchOutput -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR: No se pudo verificar PyTorch" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verificar Intel Extension
Write-Host "2. Verificando Intel Extension..." -ForegroundColor Yellow
try {
    $ipexOutput = py -c "import intel_extension_for_pytorch as ipex; import torch; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK Intel Extension: Instalado" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Intel Extension no funciona" -ForegroundColor Red
        Write-Host $ipexOutput -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR: No se pudo verificar Intel Extension" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Crear script temporal de Python
$tempScript = Join-Path $env:TEMP "check_gpu.py"
$pythonCode = @'
import torch
import intel_extension_for_pytorch as ipex

print("Intel Extension: Instalado")

if hasattr(torch, 'xpu'):
    print("Soporte XPU: Disponible")
    if torch.xpu.is_available():
        print("GPU Intel Arc A750: DISPONIBLE")
        print(f"Dispositivos XPU: {torch.xpu.device_count()}")
        for i in range(torch.xpu.device_count()):
            device_name = torch.xpu.get_device_name(i)
            print(f"Dispositivo {i}: {device_name}")
        
        # Test basico
        print("")
        print("Probando GPU...")
        x = torch.randn(5, 5, device='xpu:0')
        y = torch.matmul(x, x)
        print("GPU funciona correctamente!")
    else:
        print("GPU Intel Arc A750: No disponible")
        print("Verifica que los drivers esten instalados")
else:
    print("Soporte XPU: No disponible")
'@

$pythonCode | Out-File -FilePath $tempScript -Encoding utf8

# Verificar GPU
Write-Host "3. Verificando GPU Intel Arc A750..." -ForegroundColor Yellow
try {
    $gpuOutput = py $tempScript 2>&1
    Write-Host $gpuOutput
    
    if ($gpuOutput -like "*DISPONIBLE*") {
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host "EXITO: GPU Intel Arc A750 funciona!" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
    } elseif ($gpuOutput -like "*No disponible*") {
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Yellow
        Write-Host "GPU no disponible" -ForegroundColor Yellow
        Write-Host "==========================================" -ForegroundColor Yellow
        Write-Host "Verifica:" -ForegroundColor Cyan
        Write-Host "1. Drivers de Intel Arc instalados" -ForegroundColor White
        Write-Host "2. GPU reconocida en Administrador de dispositivos" -ForegroundColor White
        Write-Host "3. Sistema reiniciado despues de instalar drivers" -ForegroundColor White
        Write-Host ""
        Write-Host "Descarga drivers desde:" -ForegroundColor Cyan
        Write-Host "https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html" -ForegroundColor White
    }
} catch {
    Write-Host "ERROR: No se pudo verificar GPU" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
} finally {
    # Limpiar archivo temporal
    if (Test-Path $tempScript) {
        Remove-Item $tempScript -Force
    }
}

Write-Host ""
