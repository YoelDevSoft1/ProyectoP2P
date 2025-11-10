# 🚀 Inicio Rápido - Instalar IA en Windows con Docker Desktop

## Pasos Rápidos (3 minutos)

### 1️⃣ Asegúrate que Docker Desktop está corriendo

- Abre Docker Desktop
- Espera a que el icono en la bandeja del sistema muestre "Docker Desktop is running"

### 2️⃣ Inicia tus contenedores

```powershell
docker-compose up -d
```

### 3️⃣ Ejecuta el script de instalación

```powershell
.\scripts\install-ai-windows.ps1
```

¡Listo! El script hará todo automáticamente.

## ¿Qué hace el script?

1. ✅ Verifica que Docker Desktop está corriendo
2. ✅ Verifica que el contenedor `p2p_backend` está activo
3. ✅ Instala Intel Extension for PyTorch
4. ✅ Instala OpenVINO
5. ✅ Instala optimizaciones Intel MKL
6. ✅ Verifica que todo está instalado correctamente
7. ✅ Te ofrece hacer commit de la imagen (para persistencia)

## Verificar que funciona

```powershell
# Verificar instalación
docker exec -it p2p_backend python -c "import intel_extension_for_pytorch as ipex; print('✅ Intel Extension OK')"
docker exec -it p2p_backend python -c "from openvino.runtime import Core; print('✅ OpenVINO OK')"
```

## Hacer cambios persistentes (Recomendado)

Para que las extensiones sobrevivan a `docker-compose down`:

```powershell
# Crear imagen personalizada
docker commit p2p_backend proyecto-p2p-backend-with-ai:latest
```

## Reiniciar el contenedor

```powershell
docker-compose restart backend
```

## Solución de Problemas

### Si el script dice "Contenedor no encontrado"

```powershell
# Verificar que el contenedor está corriendo
docker ps

# Si no está, iniciarlo
docker-compose up -d
```

### Si hay errores de permisos en PowerShell

```powershell
# Ejecutar PowerShell como administrador
# O cambiar la política de ejecución temporalmente:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

## ¿Necesitas más ayuda?

Ver `INSTALACION_WINDOWS_DOCKER.md` para guía completa.

