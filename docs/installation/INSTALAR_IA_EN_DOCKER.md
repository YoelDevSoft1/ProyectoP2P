# 🚀 Instalar Extensiones de IA en Docker Existente

Esta guía te permite instalar Intel Extension y OpenVINO **SIN modificar tu Dockerfile existente**.

## 📋 Opción 1: Instalación Manual en el Contenedor (Recomendado)

### Paso 1: Iniciar tu contenedor normalmente

```bash
docker-compose up -d
```

### Paso 2: Instalar extensiones dentro del contenedor

#### Windows (PowerShell):
```powershell
# Ejecutar script automático
.\scripts\install-ai-extensions-in-container.ps1

# O manualmente:
docker exec -it p2p-backend pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
docker exec -it p2p-backend pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
docker exec -it p2p-backend pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
```

#### Linux/Mac:
```bash
# Ejecutar script automático
chmod +x scripts/install-ai-extensions-in-container.sh
docker exec -it p2p-backend bash -c "./scripts/install-ai-extensions-in-container.sh"

# O manualmente:
docker exec -it p2p-backend pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
docker exec -it p2p-backend pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
docker exec -it p2p-backend pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
```

### Paso 3: Reiniciar el contenedor

```bash
docker-compose restart backend
```

### Paso 4: Verificar instalación

```bash
docker exec -it p2p-backend python -c "import intel_extension_for_pytorch as ipex; import torch; print('✅ Intel Extension instalado')"
docker exec -it p2p-backend python -c "from openvino.runtime import Core; print('✅ OpenVINO instalado')"
```

## 📋 Opción 2: Crear una Imagen Personalizada (Sin tocar Dockerfile original)

Si quieres que las extensiones estén persistentes, puedes crear una nueva imagen basada en la tuya:

### Crear Dockerfile.custom (nuevo archivo, no modifica el original)

```dockerfile
# Dockerfile.custom - Extiende tu Dockerfile existente
FROM proyecto-p2p-backend:latest

# Instalar extensiones de IA
RUN pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0 && \
    pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
```

### Construir y usar la nueva imagen

```bash
# Construir imagen personalizada
docker build -f Dockerfile.custom -t proyecto-p2p-backend-with-ai .

# Modificar docker-compose.yml temporalmente para usar la nueva imagen
# O crear docker-compose.override.yml:
```

**docker-compose.override.yml** (se carga automáticamente):
```yaml
version: '3.8'
services:
  backend:
    image: proyecto-p2p-backend-with-ai
    # Mantiene toda tu configuración existente
```

## 📋 Opción 3: Usar Volumen para Scripts de Instalación

### Crear script de instalación en el host

```bash
# scripts/install-ai.sh
#!/bin/bash
pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0
pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
```

### Ejecutar desde el host

```bash
# Copiar script al contenedor y ejecutarlo
docker cp scripts/install-ai.sh p2p-backend:/tmp/
docker exec -it p2p-backend bash /tmp/install-ai.sh
```

## 🔄 Hacer los Cambios Persistentes

**⚠️ Importante**: Los cambios en un contenedor se pierden al recrearlo. Para hacerlos persistentes:

### Opción A: Commit de la imagen (Recomendado)

```bash
# Después de instalar las extensiones
docker commit p2p-backend proyecto-p2p-backend-with-ai:latest

# Actualizar docker-compose.yml para usar la nueva imagen
# O crear docker-compose.override.yml
```

### Opción B: Usar Dockerfile personalizado (Sin tocar el original)

Crear `Dockerfile.ai-extensions`:
```dockerfile
FROM proyecto-p2p-backend:latest
RUN pip install --no-cache-dir intel-extension-for-pytorch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0 && \
    pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0
```

```bash
docker build -f Dockerfile.ai-extensions -t proyecto-p2p-backend-ai .
```

## ✅ Verificación

```bash
# Verificar que las extensiones están instaladas
docker exec -it p2p-backend python -c "
import torch
try:
    import intel_extension_for_pytorch as ipex
    print('✅ Intel Extension instalado')
except:
    print('❌ Intel Extension no instalado')

try:
    from openvino.runtime import Core
    print('✅ OpenVINO instalado')
except:
    print('❌ OpenVINO no instalado')
"
```

## 🎯 Recomendación

**Para desarrollo**: Usa la Opción 1 (instalación manual en contenedor)
**Para producción**: Usa la Opción 2 (Dockerfile personalizado que extiende el tuyo)

## 📝 Notas

- ✅ **NO modifica tu Dockerfile.backend original**
- ✅ **NO modifica tu docker-compose.yml original**
- ✅ **Puedes deshacer los cambios fácilmente**
- ✅ **Mantiene tu configuración existente**

## 🚨 Si algo sale mal

```bash
# Recrear el contenedor desde cero (sin las extensiones)
docker-compose down
docker-compose up -d
```

Tus archivos originales no se han modificado. 🎉

