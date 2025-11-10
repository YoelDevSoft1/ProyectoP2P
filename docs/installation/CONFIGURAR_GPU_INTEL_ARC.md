# 🎮 Configurar GPU Intel Arc A750 en Docker Desktop (Windows)

Guía completa para habilitar y usar tu GPU Intel Arc A750 en Docker Desktop para Windows.

## 📋 Requisitos Previos

1. **GPU Intel Arc A750** instalada en tu sistema
2. **Docker Desktop** instalado
3. **WSL2** habilitado (recomendado para mejor soporte de GPU)
4. **Drivers de Intel Arc** instalados y actualizados

## 🔧 Paso 1: Verificar GPU en Windows

### Verificar que la GPU está reconocida

```powershell
# Verificar GPU Intel Arc
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Arc*" -or $_.FriendlyName -like "*Intel*Graphics*"}

# Verificar con DirectX
dxdiag
```

### Verificar Drivers

1. Abre **Administrador de dispositivos** (`devmgmt.msc`)
2. Busca **Adaptadores de pantalla**
3. Verifica que aparece "Intel Arc A750" o similar
4. Si hay un triángulo amarillo, actualiza los drivers

### Instalar/Actualizar Drivers Intel Arc

1. Descarga los drivers más recientes desde:
   - https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html
2. Instala los drivers
3. Reinicia el sistema

## 🐳 Paso 2: Configurar Docker Desktop para GPU

### Opción A: Usar WSL2 Backend (Recomendado)

1. **Habilitar WSL2 en Windows:**
   ```powershell
   # Ejecutar como Administrador
   wsl --install
   wsl --set-default-version 2
   ```

2. **Configurar Docker Desktop:**
   - Abre Docker Desktop
   - Settings → General
   - Activa "Use the WSL 2 based engine"
   - Settings → Resources → WSL Integration
   - Activa integración con tu distribución WSL2

3. **Reiniciar Docker Desktop**

### Opción B: Usar Hyper-V (Alternativa)

Si no puedes usar WSL2, Docker Desktop usará Hyper-V por defecto, pero el soporte de GPU puede ser limitado.

## 🔌 Paso 3: Configurar GPU Passthrough en Docker

### Modificar docker-compose.yml

Añade configuración para acceso a GPU:

```yaml
services:
  backend:
    # ... configuración existente
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia  # Para NVIDIA (no aplica a Intel)
            # Para Intel Arc, necesitamos configuración diferente
```

### Para Intel Arc en Windows/Linux

Intel Arc usa diferentes drivers. Necesitamos:

1. **Instalar Intel GPU Plugin para Docker** (en Linux/WSL2)
2. **Configurar device passthrough**

## 🚀 Paso 4: Instalar Intel Extension con Soporte XPU

### En WSL2 (Recomendado)

```bash
# Entrar a WSL2
wsl

# Instalar drivers Intel en WSL2
sudo apt-get update
sudo apt-get install -y intel-opencl-icd intel-level-zero-gpu level-zero

# Verificar GPU
lspci | grep -i intel
```

### Instalar Intel Extension con XPU

```bash
# Desde dentro del contenedor Docker
docker exec -it p2p_backend bash

# Instalar Intel Extension con soporte XPU
pip install intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
```

## 📝 Paso 5: Script de Configuración Completa

He creado un script que hace todo automáticamente. Ver `scripts/configurar-gpu-intel-arc.ps1`

## ⚠️ Limitaciones en Windows Docker Desktop

**Importante**: Docker Desktop en Windows tiene limitaciones para acceso directo a GPU:

1. **WSL2 Backend**: Mejor soporte, pero aún limitado
2. **Hyper-V Backend**: Soporte de GPU muy limitado
3. **Intel Arc**: Requiere drivers específicos en el contenedor

## 🎯 Solución Recomendada

### Opción 1: Usar Host Directo (Mejor Rendimiento)

Ejecutar PyTorch directamente en Windows (fuera de Docker):

```powershell
# Instalar PyTorch e Intel Extension en Windows
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
pip install intel-extension-for-pytorch[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
```

### Opción 2: Usar WSL2 con GPU Passthrough

1. Instalar Ubuntu en WSL2
2. Instalar drivers Intel en WSL2
3. Configurar Docker en WSL2 para usar GPU

### Opción 3: Aceptar CPU (Funciona Perfectamente)

PyTorch CPU funciona excelentemente para:
- ✅ Entrenamiento de modelos (5-15 minutos)
- ✅ Inferencia en tiempo real (<100ms)
- ✅ Todas las funcionalidades de Deep Learning

**GPU solo acelera el entrenamiento**, pero CPU es más que suficiente para producción.

## 🔍 Verificar Configuración GPU

### En Windows:

```powershell
# Verificar GPU
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Arc*"}
```

### En Docker:

```bash
# Verificar si Docker puede ver la GPU
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
# (Esto es para NVIDIA, Intel requiere configuración diferente)
```

### En WSL2:

```bash
# Verificar GPU en WSL2
lspci | grep -i intel
```

## 📚 Referencias

- [Intel Arc GPU Drivers](https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html)
- [Intel Extension for PyTorch XPU](https://github.com/intel/intel-extension-for-pytorch)
- [Docker Desktop WSL2](https://docs.docker.com/desktop/wsl/)
- [WSL2 GPU Support](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute)

## ✅ Checklist

- [ ] GPU Intel Arc A750 instalada físicamente
- [ ] Drivers de Intel Arc instalados en Windows
- [ ] GPU reconocida en Windows (Administrador de dispositivos)
- [ ] WSL2 instalado y configurado
- [ ] Docker Desktop usando WSL2 backend
- [ ] Drivers Intel instalados en WSL2 (si usas WSL2)
- [ ] Intel Extension instalado con soporte XPU
- [ ] GPU verificada y funcionando

## 🆘 Troubleshooting

### GPU no se reconoce en Docker

**Solución**: Docker Desktop en Windows tiene soporte limitado para GPU. Considera:
1. Usar WSL2 backend
2. Ejecutar directamente en Windows (fuera de Docker)
3. Usar PyTorch CPU (funciona perfectamente)

### Intel Extension no encuentra GPU

**Solución**: 
1. Verifica que los drivers están instalados
2. Verifica que la GPU es reconocida por el sistema
3. Considera usar PyTorch CPU (es suficiente)

### Errores de permisos

**Solución**: Ejecuta PowerShell/Docker como Administrador

