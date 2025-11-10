# 🎮 Intel XPU Manager - Monitoreo de GPU Intel Arc

## 📋 Descripción

Intel XPU Manager es una herramienta gratuita y de código abierto diseñada para monitorear y gestionar GPUs Intel en centros de datos. Ofrece una interfase de línea de comandos (CLI) para administración local y una API RESTful para gestión remota.

**Referencia**: [Intel XPU Manager en Docker Hub](https://hub.docker.com/r/intel/xpumanager)

## 🎯 Características

- **Monitoreo de salud y telemetría**: Proporciona métricas detalladas sobre el rendimiento y estado de las GPUs
- **Configuración y políticas de GPU**: Permite ajustar configuraciones y establecer políticas para optimizar el uso de las GPUs
- **Actualización de firmware**: Facilita la actualización del firmware de las GPUs para mantenerlas al día
- **API RESTful**: Permite integración con otros servicios y monitoreo remoto

## ⚠️ Limitaciones Importantes

1. **GPUs de Data Center**: A partir de la versión 1.3.3, Intel ha descontinuado el soporte para las series de GPUs Data Center GPU Max y Data Center GPU Flex en XPU Manager. Se recomienda a los usuarios de estas GPUs que utilicen la serie 1.2 de XPU Manager.

2. **Intel Arc A750 (GPU de Consumo)**: Intel XPU Manager está principalmente diseñado para GPUs de Data Center. Para GPUs de consumo como la Intel Arc A750, el soporte puede ser limitado o experimental.

3. **Docker Desktop en Windows**: Docker Desktop en Windows tiene limitaciones conocidas para acceso a GPU, especialmente para GPUs que no son NVIDIA. El acceso a la GPU desde contenedores Docker puede no funcionar correctamente.

## 🚀 Instalación y Uso

### Opción 1: Como Servicio Docker (Recomendado para Monitoreo)

Hemos creado un archivo `docker-compose.xpu-monitor.yml` que puedes usar para ejecutar XPU Manager como servicio de monitoreo:

```bash
# Iniciar el servicio de monitoreo XPU
docker-compose -f docker-compose.yml -f docker-compose.xpu-monitor.yml up -d xpu-manager

# Ver logs
docker-compose -f docker-compose.yml -f docker-compose.xpu-monitor.yml logs -f xpu-manager

# Verificar que el servicio está corriendo
curl http://localhost:12788/api/v1/health
```

### Opción 2: Instalación Directa en el Host (Mejor para Acceso GPU)

Si necesitas acceso directo a la GPU (no desde Docker), instala XPU Manager directamente en el sistema:

```bash
# En Linux/WSL2
sudo apt-get update
sudo apt-get install -y intel-xpumanager

# Verificar instalación
xpumanager --version

# Iniciar servicio
sudo systemctl start xpumanager
sudo systemctl enable xpumanager
```

## 📊 Uso en el Proyecto

### Endpoints de API

Hemos integrado XPU Manager en nuestros endpoints de analytics:

#### 1. Estado de GPU

```bash
GET /api/v1/analytics/gpu/status
```

Obtiene el estado de la GPU, combinando información de PyTorch y XPU Manager.

**Respuesta**:
```json
{
  "pytorch_gpu": {
    "available": true,
    "device": "xpu:0",
    "count": 1,
    "names": ["Intel Arc A750"],
    "intel_extension": true
  },
  "xpu_manager": {
    "available": true,
    "gpus": [
      {
        "device_id": 0,
        "device_name": "Intel Arc A750",
        "health": {...},
        "metrics": {...}
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### 2. Métricas de GPU

```bash
GET /api/v1/analytics/gpu/metrics?device_id=0
```

Obtiene métricas detalladas de la GPU (temperatura, uso, memoria, etc.).

**Respuesta**:
```json
{
  "device_id": 0,
  "health": {
    "status": "healthy",
    "temperature": 45,
    "power_usage": 120
  },
  "metrics": {
    "gpu_utilization": 75,
    "memory_used": 4096,
    "memory_total": 8192,
    "temperature": 45,
    "power_usage": 120
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### Servicio de Monitoreo

El servicio `XPUMonitorService` está disponible en `backend/app/services/xpu_monitor_service.py`:

```python
from app.services.xpu_monitor_service import get_xpu_monitor_service

# Obtener instancia del servicio
monitor = get_xpu_monitor_service()

# Verificar disponibilidad
if monitor.available:
    # Obtener lista de GPUs
    gpus = monitor.get_gpu_list()
    
    # Obtener métricas de una GPU específica
    metrics = monitor.get_gpu_metrics(device_id=0)
    
    # Obtener salud de la GPU
    health = monitor.get_gpu_health(device_id=0)
```

## 🔧 Configuración

### Variables de Entorno

Puedes configurar la URL de XPU Manager mediante variable de entorno:

```bash
# En .env o docker-compose.yml
XPU_MANAGER_URL=http://xpu-manager:12788
```

### Docker Compose

El servicio XPU Manager se configura en `docker-compose.xpu-monitor.yml`:

```yaml
services:
  xpu-manager:
    image: intel/xpumanager:latest
    container_name: p2p_xpu_manager
    privileged: true  # Necesario para acceder a dispositivos GPU
    devices:
      - /dev/dri:/dev/dri  # Direct Rendering Infrastructure
    volumes:
      - /sys:/sys:ro
      - /dev:/dev:ro
    ports:
      - "12788:12788"
    networks:
      - p2p_network
```

## ⚠️ Notas Importantes

1. **Privileged Mode**: XPU Manager requiere modo privilegiado para acceder a dispositivos GPU. Esto es necesario pero tiene implicaciones de seguridad.

2. **Docker Desktop Windows**: El acceso a GPU desde Docker Desktop en Windows es limitado. XPU Manager puede no funcionar correctamente en este entorno.

3. **WSL2**: Si estás usando WSL2, asegúrate de que los drivers de Intel GPU estén instalados en WSL2, no solo en Windows.

4. **Alternativa**: Si XPU Manager no funciona en Docker, considera ejecutar el monitoreo directamente en el host y exponer la API RESTful.

## 📚 Referencias

- [Intel XPU Manager en Docker Hub](https://hub.docker.com/r/intel/xpumanager)
- [Documentación Oficial de Intel XPU Manager](https://intel.github.io/xpumanager/)
- [Intel XPU Manager en GitHub](https://github.com/intel/xpumanager)

## 🎯 Recomendaciones

1. **Para Desarrollo**: Usa el sistema híbrido que ya implementamos (detectar GPU, usar CPU si no está disponible). Esto funciona perfectamente para desarrollo y testing.

2. **Para Producción con GPU**: Si necesitas acceso real a GPU en producción, considera:
   - Ejecutar en Linux nativo (no Docker Desktop)
   - Usar WSL2 con drivers Intel instalados
   - Configurar device passthrough correctamente

3. **Para Monitoreo**: XPU Manager es útil para monitorear la GPU desde el host, pero no es estrictamente necesario para que PyTorch use la GPU.

## 🔍 Troubleshooting

### XPU Manager no está disponible

```bash
# Verificar que el servicio está corriendo
docker ps | grep xpu-manager

# Ver logs
docker logs p2p_xpu_manager

# Verificar conectividad
curl http://localhost:12788/api/v1/health
```

### Error de permisos

```bash
# Asegúrate de que el contenedor tiene acceso a /dev/dri
ls -la /dev/dri/

# Verificar que el usuario tiene permisos
groups
```

### GPU no detectada

```bash
# Verificar GPU en el host
lspci | grep -i intel

# Verificar drivers
lsmod | grep i915

# Verificar en Docker
docker exec p2p_xpu_manager ls -la /dev/dri/
```

