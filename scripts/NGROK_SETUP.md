# Configuración de ngrok para Exponer el Backend

## Problema Común
Si los scripts de ngrok se cierran automáticamente, es porque **ngrok no está configurado correctamente** en esta PC.

## Solución Paso a Paso

### 1. Instalar ngrok (si no lo tienes)

```bash
# Opción A: Descargar desde el sitio oficial
# Ve a: https://ngrok.com/download
# Descarga el ZIP para Windows y extráelo

# Opción B: Con Chocolatey (si lo tienes instalado)
choco install ngrok
```

### 2. Configurar tu Token de Autenticación

**IMPORTANTE**: Esto es necesario hacerlo UNA SOLA VEZ por computadora.

1. Ve a: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copia tu token (se ve así: `2abc123def456ghi789jkl`)
3. Ejecuta este comando en tu terminal:

```bash
ngrok config add-authtoken TU_TOKEN_AQUI
```

Ejemplo:
```bash
ngrok config add-authtoken 2abc123def456ghi789jkl
```

### 3. Verificar que Funciona

```bash
ngrok http 8000
```

Si ves una pantalla con una URL como `https://1234-5678-9012.ngrok-free.app`, ¡funciona! ✓

Presiona `Ctrl+C` para detenerlo.

## Usar los Scripts

### Opción 1: Sistema Completo + ngrok

```bash
# 1. Inicia todo el sistema (Docker + servicios)
cd scripts
start-all-with-ngrok.bat

# 2. En otra terminal, inicia ngrok
start-ngrok-backend.bat
```

### Opción 2: Solo ngrok (si ya tienes Docker corriendo)

```bash
cd scripts
start-ngrok-backend.bat
```

### Opción 3: Manual (más control)

```bash
# 1. Asegúrate que Docker esté corriendo
docker-compose up -d

# 2. En otra terminal, ejecuta ngrok
ngrok http 8000

# O con opciones específicas:
ngrok http 8000 --region us --log=stdout
```

## Regiones Disponibles de ngrok

Puedes especificar la región más cercana para mejor latencia:

```bash
# Estados Unidos
ngrok http 8000 --region us

# Europa
ngrok http 8000 --region eu

# Asia/Pacífico
ngrok http 8000 --region ap

# Australia
ngrok http 8000 --region au

# América del Sur
ngrok http 8000 --region sa

# Japón
ngrok http 8000 --region jp

# India
ngrok http 8000 --region in
```

## Solución de Problemas

### Error: "command not found: ngrok"
- ngrok no está en tu PATH
- Solución: Copia `ngrok.exe` a la carpeta `scripts/` del proyecto

### Error: "authentication failed"
- No has configurado tu authtoken
- Solución: Ejecuta `ngrok config add-authtoken TU_TOKEN`

### La ventana se cierra inmediatamente
- Probablemente Docker no está corriendo
- Solución: Inicia Docker Desktop primero

### Error: "failed to listen on localhost:8000"
- El puerto 8000 ya está en uso
- Solución: Detén otros servicios en ese puerto o usa otro puerto:
  ```bash
  ngrok http 8001
  ```

## Consejos Pro

### 1. Dominio Personalizado (Plan Paid)

Si tienes cuenta pagada de ngrok, puedes usar un dominio fijo:

```bash
ngrok http 8000 --domain=tu-dominio.ngrok-free.app
```

### 2. Ver Requests en Tiempo Real

Ngrok tiene una interfaz web en: http://localhost:4040

Muestra todas las requests que pasan por el túnel.

### 3. Usar Archivo de Configuración

Crea `ngrok.yml` en tu home directory (`~/.ngrok2/ngrok.yml`):

```yaml
version: "2"
authtoken: TU_TOKEN_AQUI
tunnels:
  backend:
    proto: http
    addr: 8000
    inspect: true
  frontend:
    proto: http
    addr: 3000
    inspect: true
```

Luego ejecuta:
```bash
ngrok start backend
```

### 4. Múltiples Túneles al Mismo Tiempo

```bash
# Terminal 1: Backend
ngrok http 8000

# Terminal 2: Frontend
ngrok http 3000
```

## URLs Importantes

- **Dashboard de ngrok**: https://dashboard.ngrok.com/
- **Documentación**: https://ngrok.com/docs
- **Status de ngrok**: https://status.ngrok.com/
- **Interfaz local**: http://localhost:4040 (cuando ngrok está corriendo)

## Diferencias entre Trabajo y Casa

### En el Trabajo
- Ya tienes ngrok configurado con authtoken
- Scripts funcionan directamente

### En Casa
- Necesitas configurar authtoken (una sola vez)
- Después funcionará igual que en el trabajo

**El authtoken es por CUENTA, no por computadora**. Si usas la misma cuenta de ngrok en ambas PCs, solo necesitas ejecutar el comando `ngrok config add-authtoken` una vez en cada PC.
