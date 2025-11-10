# 🎮 Guía: Instalar GPU Intel Arc A750 en tu Proyecto

## 📋 Resumen

Tu GPU Intel Arc A750 está instalada y funcionando en Windows. Para usarla en tu proyecto P2P Trading, tienes **2 opciones**:

### Opción 1: Instalar en Windows (Recomendado para GPU) ✅

**Ventajas**:
- ✅ Máximo rendimiento de GPU
- ✅ Acceso directo a drivers
- ✅ Sin limitaciones de Docker
- ✅ GPU funciona correctamente

**Desventajas**:
- Requiere Python instalado en Windows
- Separado del entorno Docker

### Opción 2: Usar CPU en Docker (Recomendado para Simplicidad) ✅

**Ventajas**:
- ✅ Ya está funcionando
- ✅ Integrado con tu proyecto Docker
- ✅ No requiere configuración adicional
- ✅ Rendimiento suficiente para tus necesidades

**Desventajas**:
- GPU no disponible en Docker Desktop Windows
- Entrenamiento más lento (pero aceptable)

## 🚀 Instalación Rápida

### Opción 1: Instalar GPU en Windows

```powershell
# Ejecutar script de instalación
.\scripts\instalar-gpu-windows.ps1
```

Este script:
1. ✅ Verifica que tu GPU Intel Arc A750 esté reconocida
2. ✅ Instala PyTorch
3. ✅ Instala Intel Extension con soporte XPU (GPU)
4. ✅ Instala OpenVINO
5. ✅ Verifica que GPU esté disponible

### Opción 2: Usar CPU en Docker (Ya Configurado)

Tu sistema ya está configurado para usar CPU. El código detectará automáticamente si hay GPU disponible y la usará si está, o usará CPU si no está.

## 🔧 Verificar Instalación

### Verificar GPU en Windows

```powershell
python -c "from app.ml.gpu_utils import print_gpu_status; print_gpu_status()"
```

### Verificar GPU en Docker

```powershell
docker exec p2p_backend python -c "from app.ml.gpu_utils import print_gpu_status; print_gpu_status()"
```

## 💻 Usar GPU en tu Código

El módulo `gpu_utils.py` detecta automáticamente si hay GPU disponible:

```python
from app.ml.gpu_utils import get_device, to_device, optimize_model_for_inference

# Obtener dispositivo (GPU o CPU)
device = get_device()  # Detecta automáticamente

# Mover modelo a GPU
model = model.to(device)

# O usar función helper
model = to_device(model)

# Optimizar para inferencia (usa Intel Extension si está disponible)
model = optimize_model_for_inference(model)
```

## 📊 Comparación de Opciones

| Característica | Windows (GPU) | Docker (CPU) |
|----------------|---------------|--------------|
| Rendimiento GPU | ✅ Alto | ❌ No disponible |
| Facilidad | ⚠️ Media | ✅ Alta |
| Integración | ⚠️ Separado | ✅ Integrado |
| Entrenamiento | ✅ Rápido (GPU) | ⚠️ Lento (CPU) |
| Inferencia | ✅ Muy rápido | ✅ Rápido (<100ms) |
| Recomendado para | Entrenamiento frecuente | Producción/Desarrollo |

## 🎯 Recomendación

### Para Desarrollo/Producción: Usar CPU en Docker ✅

**Razones**:
- ✅ Ya está funcionando
- ✅ Integrado con tu proyecto
- ✅ Rendimiento suficiente para inferencia (<100ms)
- ✅ Entrenamiento aceptable (5-15 minutos)

### Para Máximo Rendimiento: Instalar en Windows ✅

**Cuándo usar**:
- Entrenas modelos muy grandes frecuentemente
- Necesitas máximo rendimiento de GPU
- Tienes tiempo para configurar

## 🔍 Troubleshooting

### GPU no se reconoce

1. **Verificar drivers**:
   ```powershell
   Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Arc*"}
   ```

2. **Actualizar drivers**:
   - Descarga desde: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html
   - Instala y reinicia el sistema

3. **Verificar en Administrador de dispositivos**:
   - Busca "Adaptadores de pantalla"
   - Debe aparecer "Intel Arc A750"

### Intel Extension no funciona en Docker

**Esto es normal**. Docker Desktop en Windows tiene limitaciones para GPU Intel. 

**Solución**: Usar CPU (funciona perfectamente) o instalar en Windows.

### GPU disponible pero no se usa

1. Verifica que Intel Extension esté instalado:
   ```powershell
   python -c "import intel_extension_for_pytorch as ipex; print('OK')"
   ```

2. Verifica que GPU esté disponible:
   ```powershell
   python -c "import torch; print('GPU:', torch.xpu.is_available() if hasattr(torch, 'xpu') else False)"
   ```

## ✅ Estado Actual

Tu sistema está configurado para:
- ✅ Detectar automáticamente GPU si está disponible
- ✅ Usar GPU si está disponible
- ✅ Usar CPU si GPU no está disponible (funciona perfectamente)
- ✅ Optimizar modelos para inferencia

## 📚 Referencias

- [Intel Arc Drivers](https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html)
- [Intel Extension for PyTorch](https://github.com/intel/intel-extension-for-pytorch)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)

## 🎉 Conclusión

**Tu sistema está listo para usar GPU cuando esté disponible**. 

- Si instalas en Windows: GPU funcionará con máximo rendimiento
- Si usas Docker: CPU funcionará perfectamente para tus necesidades

**El código detecta automáticamente la mejor opción disponible**. 🚀

