# 🐳 Imágenes Docker Oficiales de Intel para PyTorch

## 📋 Descripción

Intel ofrece dos imágenes Docker oficiales optimizadas para PyTorch que pueden mejorar significativamente el rendimiento en hardware Intel (CPUs y GPUs Intel Arc):

1. **Intel® Extension for PyTorch** (`intel/intel-extension-for-pytorch`)
2. **Intel® Optimized PyTorch** (`intel/intel-optimized-pytorch`)

**Referencias**:
- [Intel Extension for PyTorch en Docker Hub](https://hub.docker.com/r/intel/intel-extension-for-pytorch)
- [Intel Optimized PyTorch en Docker Hub](https://hub.docker.com/r/intel/intel-optimized-pytorch)

## 🎯 Diferencias entre las Imágenes

### Intel® Extension for PyTorch
- **Incluye**: PyTorch + Intel Extension for PyTorch preinstalado
- **Soporte**: CPU y GPU Intel (incluyendo Intel Arc A750)
- **Optimizaciones**: 
  - AVX-512 y VNNI en CPUs
  - XMX en GPUs Intel Arc
  - Optimizaciones de kernel específicas para Intel
- **Ideal para**: Usuarios que quieren aprovechar GPUs Intel Arc o CPUs Intel de última generación

### Intel® Optimized PyTorch
- **Incluye**: PyTorch optimizado para hardware Intel
- **Soporte**: Principalmente CPU (optimizaciones AVX-512, VNNI)
- **Optimizaciones**: Optimizaciones de compilación y runtime para CPUs Intel
- **Ideal para**: Usuarios que quieren mejor rendimiento en CPU sin necesidad de GPU

## 🚀 Uso en el Proyecto

### Opción 1: Usar Dockerfile Basado en Intel Extension (Recomendado para GPU)

Hemos creado un Dockerfile alternativo que usa la imagen oficial de Intel Extension for PyTorch:

```bash
# Construir con Intel Extension
docker build -f docker/Dockerfile.backend.intel -t p2p-backend-intel ./backend

# O usar docker-compose
docker-compose -f docker-compose.yml -f docker-compose.intel.yml up -d backend
```

**Ventajas**:
- ✅ PyTorch e Intel Extension preinstalados
- ✅ Optimizaciones automáticas para CPU y GPU Intel
- ✅ Soporte para Intel Arc A750 (si está disponible)
- ✅ Menos problemas de compatibilidad

### Opción 2: Usar Dockerfile Basado en Intel Optimized PyTorch (Solo CPU)

Para optimización solo en CPU:

```bash
# Construir con Intel Optimized PyTorch
docker build -f docker/Dockerfile.backend.intel-optimized -t p2p-backend-intel-cpu ./backend
```

**Ventajas**:
- ✅ PyTorch optimizado para CPU Intel
- ✅ Mejor rendimiento en CPUs Intel sin GPU
- ✅ Imagen más ligera

## 📊 Comparación de Rendimiento

### Con Intel Extension for PyTorch (GPU Intel Arc)
- **Entrenamiento**: 5-10x más rápido que CPU (dependiendo del modelo)
- **Inferencia**: 3-5x más rápido que CPU
- **Memoria**: Mejor gestión de memoria GPU

### Con Intel Optimized PyTorch (CPU)
- **Entrenamiento**: 20-30% más rápido que PyTorch estándar
- **Inferencia**: 15-25% más rápido que PyTorch estándar
- **Memoria**: Optimizaciones de memoria para CPUs Intel

## 🔧 Configuración

### Variables de Entorno

Para Intel Extension for PyTorch:

```bash
# Habilitar XPU (GPU Intel)
USE_XPU=1
ZE_FLAT_DEVICE_HIERARCHY=COMPOSITE

# Configurar Intel Extension
INTEL_EXTENSION_FOR_PYTORCH_SKIP_BINDING=0
```

### Docker Compose

Hemos creado `docker-compose.intel.yml` que usa las imágenes de Intel:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend.intel
    environment:
      - USE_XPU=1
      - INTEL_EXTENSION_FOR_PYTORCH_SKIP_BINDING=0
    devices:
      - /dev/dri:/dev/dri  # Para acceso a GPU
```

## 🎯 Cuándo Usar Cada Imagen

### Usa Intel Extension for PyTorch si:
- ✅ Tienes GPU Intel Arc A750 (o otra GPU Intel)
- ✅ Quieres el mejor rendimiento posible
- ✅ Necesitas soporte para CPU y GPU
- ✅ Estás entrenando modelos grandes

### Usa Intel Optimized PyTorch si:
- ✅ Solo tienes CPU Intel (sin GPU)
- ✅ Quieres mejor rendimiento en CPU
- ✅ No necesitas soporte GPU
- ✅ Quieres una imagen más ligera

### Usa el Dockerfile Original si:
- ✅ No tienes hardware Intel específico
- ✅ Quieres máxima compatibilidad
- ✅ No necesitas optimizaciones específicas de Intel

## 🔍 Verificación

### Verificar que Intel Extension está funcionando

```bash
# Entrar al contenedor
docker exec -it p2p_backend_intel python

# En Python
import torch
import intel_extension_for_pytorch as ipex

print(f"PyTorch version: {torch.__version__}")
print(f"Intel Extension available: {ipex.__version__}")

# Verificar GPU
if hasattr(torch, 'xpu') and torch.xpu.is_available():
    print(f"GPU available: {torch.xpu.get_device_name(0)}")
else:
    print("GPU not available, using CPU")
```

### Verificar rendimiento

```bash
# Probar endpoint de GPU status
curl http://localhost:8000/api/v1/analytics/gpu/status

# Ver logs del contenedor
docker logs p2p_backend_intel | grep -i "intel\|gpu\|xpu"
```

## ⚠️ Limitaciones

### Docker Desktop Windows
- **Acceso a GPU**: Puede no funcionar correctamente en Docker Desktop Windows
- **Solución**: Usar WSL2 o ejecutar directamente en Windows

### Compatibilidad
- **Solo Intel**: Estas optimizaciones están diseñadas específicamente para hardware Intel
- **AMD/ARM**: No se beneficiarán de estas optimizaciones

### Tamaño de Imagen
- **Intel Extension**: Imagen más grande (~2-3GB)
- **Intel Optimized**: Imagen mediana (~1-2GB)
- **Original**: Imagen más pequeña (~500MB-1GB)

## 🚀 Migración

### Desde Dockerfile Original

1. **Backup**: Guarda tu `docker-compose.yml` actual
2. **Prueba**: Usa `docker-compose.intel.yml` para probar
3. **Verifica**: Asegúrate de que todo funciona correctamente
4. **Reemplaza**: Si todo está bien, puedes reemplazar el Dockerfile original

```bash
# Probar con Intel Extension
docker-compose -f docker-compose.yml -f docker-compose.intel.yml up -d backend

# Verificar que funciona
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/analytics/gpu/status

# Si funciona bien, puedes hacer el cambio permanente
```

## 📚 Referencias

- [Intel Extension for PyTorch - Docker Hub](https://hub.docker.com/r/intel/intel-extension-for-pytorch)
- [Intel Optimized PyTorch - Docker Hub](https://hub.docker.com/r/intel/intel-optimized-pytorch)
- [Intel Extension for PyTorch - Documentación](https://intel.github.io/intel-extension-for-pytorch/)
- [Intel Optimized PyTorch - GitHub](https://github.com/intel/intel-extension-for-pytorch)

## 🎯 Recomendaciones

1. **Para Desarrollo**: Usa el Dockerfile original (más rápido de construir, suficiente para desarrollo)

2. **Para Producción con GPU Intel**: Usa `Dockerfile.backend.intel` (mejor rendimiento con GPU)

3. **Para Producción solo CPU Intel**: Usa `Dockerfile.backend.intel-optimized` (mejor rendimiento en CPU)

4. **Para Testing**: Prueba ambas opciones y mide el rendimiento en tu hardware específico

## 🔍 Troubleshooting

### Error: "Intel Extension not found"
```bash
# Verificar que la imagen se construyó correctamente
docker images | grep intel

# Reconstruir la imagen
docker-compose -f docker-compose.intel.yml build --no-cache backend
```

### Error: "GPU not available"
```bash
# Verificar acceso a dispositivos GPU
docker exec p2p_backend_intel ls -la /dev/dri/

# Verificar drivers en el host
lspci | grep -i intel
```

### Error: "Import error"
```bash
# Verificar que PyTorch está instalado correctamente
docker exec p2p_backend_intel python -c "import torch; print(torch.__version__)"

# Verificar Intel Extension
docker exec p2p_backend_intel python -c "import intel_extension_for_pytorch as ipex; print(ipex.__version__)"
```

