# 🚀 Instalación de Extensiones de IA en Windows con Docker Desktop

Guía específica para instalar Intel Extension for PyTorch y OpenVINO en Windows usando Docker Desktop.

## ✅ Requisitos Previos

1. **Docker Desktop** instalado y corriendo
2. **Windows 10/11**
3. **PowerShell** (viene incluido en Windows)

## 🚀 Instalación Rápida (Recomendado)

### Paso 1: Iniciar Docker Desktop

Asegúrate de que Docker Desktop está corriendo (verifica el icono en la bandeja del sistema).

### Paso 2: Iniciar los contenedores

```powershell
# Navegar al directorio del proyecto
cd C:\Users\Yoel\Documents\GitHub\ProyectoP2P

# Iniciar contenedores
docker-compose up -d
```

### Paso 3: Ejecutar script de instalación

```powershell
# Ejecutar script automático
.\scripts\install-ai-windows.ps1
```

El script:
- ✅ Verifica que Docker Desktop está corriendo
- ✅ Verifica que el contenedor está activo
- ✅ Instala Intel Extension for PyTorch
- ✅ Instala OpenVINO
- ✅ Instala optimizaciones Intel MKL
- ✅ Verifica la instalación
- ✅ Te permite hacer commit de la imagen (opcional)

## 📝 Instalación Manual (Alternativa)

Si prefieres hacerlo manualmente:

```powershell
# 1. Verificar que el contenedor está corriendo
docker ps

# 2. Instalar Intel Extension
docker exec -it p2p-backend pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu

# 3. Instalar OpenVINO
docker exec -it p2p-backend pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0

# 4. Instalar Intel MKL
docker exec -it p2p-backend pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0

# 5. Reiniciar contenedor
docker-compose restart backend
```

## 🔍 Verificar Instalación

```powershell
# Verificar PyTorch
docker exec -it p2p-backend python -c "import torch; print('PyTorch:', torch.__version__)"

# Verificar Intel Extension
docker exec -it p2p-backend python -c "import intel_extension_for_pytorch as ipex; print('Intel Extension: OK')"

# Verificar OpenVINO
docker exec -it p2p-backend python -c "from openvino.runtime import Core; print('OpenVINO: OK')"
```

## 💾 Hacer Cambios Persistentes

**⚠️ Importante**: Los cambios en el contenedor se pierden al recrearlo. Para hacerlos persistentes:

### Opción 1: Commit de la Imagen (Recomendado)

```powershell
# Crear una nueva imagen desde el contenedor actual
docker commit p2p-backend proyecto-p2p-backend-with-ai:latest

# Verificar que la imagen se creó
docker images | Select-String "proyecto-p2p-backend"
```

### Opción 2: Usar la Imagen en docker-compose.yml

Después de hacer commit, puedes modificar `docker-compose.yml` para usar la nueva imagen:

```yaml
services:
  backend:
    # Comentar esta línea:
    # build:
    #   context: .
    #   dockerfile: docker/Dockerfile.backend
    
    # Añadir esta línea:
    image: proyecto-p2p-backend-with-ai:latest
```

**Nota**: Esto es opcional. Puedes seguir usando `docker-compose up` normalmente, pero si haces `docker-compose down`, las extensiones se perderán a menos que uses la imagen commiteada.

## 🔄 Reiniciar el Contenedor

```powershell
# Reiniciar solo el backend
docker-compose restart backend

# O reiniciar todos los servicios
docker-compose restart
```

## 🐛 Solución de Problemas

### Error: "Docker Desktop no está corriendo"

**Solución:**
1. Abre Docker Desktop
2. Espera a que se inicie completamente (icono en bandeja del sistema)
3. Vuelve a ejecutar el script

### Error: "Contenedor no encontrado"

**Solución:**
```powershell
# Verificar contenedores corriendo
docker ps

# Si no está corriendo, iniciarlo
docker-compose up -d

# Verificar logs si hay problemas
docker-compose logs backend
```

### Error: "No se puede conectar a Docker daemon"

**Solución:**
1. Reinicia Docker Desktop
2. Verifica que Docker Desktop está corriendo (icono en bandeja)
3. Ejecuta Docker Desktop como administrador si es necesario

### Error al instalar extensiones

**Solución:**
```powershell
# Verificar que el contenedor tiene conexión a internet
docker exec -it p2p-backend ping -c 3 google.com

# Reintentar instalación manualmente
docker exec -it p2p-backend pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
```

## 📊 Verificar que las Extensiones Funcionan

```powershell
# Test completo
docker exec -it p2p-backend python -c "
import torch
print('PyTorch:', torch.__version__)

try:
    import intel_extension_for_pytorch as ipex
    print('✅ Intel Extension: Instalado')
    if hasattr(torch, 'xpu') and torch.xpu.is_available():
        print('✅ GPU Intel Arc: Disponible')
    else:
        print('ℹ️  GPU Intel Arc: No disponible (usando CPU optimizado)')
except ImportError:
    print('❌ Intel Extension: No instalado')

try:
    from openvino.runtime import Core
    core = Core()
    print('✅ OpenVINO: Instalado')
    print('   Dispositivos:', core.available_devices)
except ImportError:
    print('❌ OpenVINO: No instalado')
"
```

## 🎯 Próximos Pasos

1. **Entrenar un modelo de prueba:**
   ```powershell
   docker exec -it p2p-backend python backend/scripts/train_dl_models.py --model lstm --asset USDT --fiat COP --days 7
   ```

2. **Usar las APIs de IA:**
   - Accede a `http://localhost:8000/api/v1/docs`
   - Prueba los endpoints de Deep Learning

3. **Monitorear el uso:**
   ```powershell
   # Ver uso de recursos del contenedor
   docker stats p2p-backend
   ```

## ✅ Checklist

- [ ] Docker Desktop instalado y corriendo
- [ ] Contenedores iniciados (`docker-compose up -d`)
- [ ] Script de instalación ejecutado
- [ ] Extensiones verificadas
- [ ] Imagen commiteada (opcional pero recomendado)
- [ ] Contenedor reiniciado
- [ ] Test de verificación exitoso

## 📝 Notas Importantes

1. **No se modifica tu Dockerfile**: Los cambios se aplican directamente en el contenedor
2. **Cambios temporales**: Se pierden al recrear el contenedor (a menos que hagas commit)
3. **Docker Desktop**: Asegúrate de que tiene suficientes recursos asignados (CPU/RAM)
4. **GPU Intel Arc**: Si tienes GPU Intel Arc A750, los drivers deben estar instalados en Windows (no en Docker)

## 🆘 Ayuda Adicional

Si tienes problemas:

1. Verifica los logs del contenedor:
   ```powershell
   docker-compose logs backend
   ```

2. Verifica el estado de Docker:
   ```powershell
   docker info
   ```

3. Reinicia Docker Desktop completamente

4. Recrea los contenedores desde cero:
   ```powershell
   docker-compose down
   docker-compose up -d
   # Luego ejecuta el script de instalación de nuevo
   ```

¡Listo! Ahora tienes todas las extensiones de IA instaladas en tu contenedor Docker. 🚀

