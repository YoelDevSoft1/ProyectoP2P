# 🐳 Guía Rápida: Imágenes Docker de Intel para PyTorch

## 🚀 Inicio Rápido

### Opción 1: Intel Extension for PyTorch (GPU + CPU)

```bash
# Usar imágenes oficiales de Intel con soporte GPU
docker-compose -f docker-compose.yml -f docker-compose.intel.yml up -d backend

# Verificar
curl http://localhost:8000/api/v1/analytics/gpu/status
```

### Opción 2: Intel Optimized PyTorch (Solo CPU)

```bash
# Modificar docker-compose.intel.yml para usar Dockerfile.backend.intel-optimized
# Luego ejecutar
docker-compose -f docker-compose.yml -f docker-compose.intel.yml up -d backend
```

## 📊 ¿Cuál usar?

| Si tienes... | Usa... | Ventaja |
|--------------|--------|---------|
| GPU Intel Arc A750 | `Dockerfile.backend.intel` | 5-10x más rápido en GPU |
| CPU Intel (sin GPU) | `Dockerfile.backend.intel-optimized` | 20-30% más rápido en CPU |
| Cualquier hardware | `Dockerfile.backend` (original) | Máxima compatibilidad |

## 🔍 Verificar Instalación

```bash
# Verificar PyTorch e Intel Extension
docker exec -it p2p_backend_intel python -c "import torch; import intel_extension_for_pytorch as ipex; print(f'PyTorch: {torch.__version__}, Intel Extension: {ipex.__version__}')"

# Verificar GPU
docker exec -it p2p_backend_intel python -c "import torch; print('GPU disponible' if hasattr(torch, 'xpu') and torch.xpu.is_available() else 'Usando CPU')"
```

## 📚 Documentación Completa

- [Documentación detallada](docs/INTEL_DOCKER_IMAGES.md)
- [Resumen de implementación](RESUMEN_INTEL_DOCKER_IMAGES.md)

## 🔗 Referencias

- [Intel Extension for PyTorch - Docker Hub](https://hub.docker.com/r/intel/intel-extension-for-pytorch)
- [Intel Optimized PyTorch - Docker Hub](https://hub.docker.com/r/intel/intel-optimized-pytorch)

