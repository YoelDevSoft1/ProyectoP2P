# 🚀 Guía: Backend Local + ngrok

Esta guía te permite correr todo el sistema localmente y exponerlo a internet con ngrok.

---

## ✅ Prerequisitos Completados

- [x] Python 3.13.7 instalado
- [x] Dependencias instalándose
- [x] Archivo `.env.local` configurado con bases de datos remotas
- [x] Scripts de inicio creados

---

## 📦 Paso 1: Verificar que todo esté instalado

Una vez que termine la instalación de dependencias, verifica:

```bash
cd backend
python -m pip list | findstr "celery fastapi uvicorn"
```

Deberías ver:
```
celery       5.3.6
fastapi      0.109.0
uvicorn      0.27.0
```

---

## 🚀 Paso 2: Iniciar los Servicios (3 Terminales)

### Terminal 1: Backend API

```bash
# Desde la raíz del proyecto
scripts\start-backend.bat
```

**Espera a ver:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Celery Worker

```bash
# Desde la raíz del proyecto
scripts\start-worker.bat
```

**Espera a ver:**
```
[tasks]
  . celery_app.tasks.update_prices
  . celery_app.tasks.analyze_spread_opportunities
  ...

[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] celery@hostname ready.
```

### Terminal 3: Celery Beat

```bash
# Desde la raíz del proyecto
scripts\start-beat.bat
```

**Espera a ver:**
```
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] beat: Starting...
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Scheduler: Sending due task update-prices
```

---

## 🧪 Paso 3: Probar que el Backend Funciona

Abre tu navegador y ve a:

```
http://localhost:8000/api/v1/health
```

**Deberías ver:**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0",
  "services": {
    "postgresql": "connected",
    "redis": "connected"
  }
}
```

**Documentación interactiva:**
```
http://localhost:8000/api/v1/docs
```

---

## 🌐 Paso 4: Instalar y Configurar ngrok

### 4.1 Descargar ngrok

1. Ve a: **https://ngrok.com**
2. Click en **"Download"**
3. O instala con Chocolatey:
   ```bash
   choco install ngrok
   ```

### 4.2 Crear Cuenta (Gratis)

1. Ve a: **https://dashboard.ngrok.com/signup**
2. Regístrate con GitHub o Email
3. Copia tu **Authtoken** desde: https://dashboard.ngrok.com/get-started/your-authtoken

### 4.3 Configurar ngrok

```bash
ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

### 4.4 Exponer el Backend

Abre una **4ta terminal**:

```bash
ngrok http 8000
```

**Verás algo como:**
```
Session Status                online
Account                       Tu Cuenta (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**COPIA la URL de "Forwarding":** `https://xxxx-xxx-xxx-xxx.ngrok-free.app`

---

## 🔗 Paso 5: Conectar Frontend con ngrok

### 5.1 Actualizar Variable en Vercel

1. Ve a: **https://vercel.com/dashboard**
2. Click en tu proyecto **"proyecto-p2-p"**
3. Click en **"Settings"** → **"Environment Variables"**
4. Edita o crea `NEXT_PUBLIC_API_URL`:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://xxxx-xxx-xxx-xxx.ngrok-free.app` (tu URL de ngrok)
   - **Environment:** Production, Preview, Development
5. Click **"Save"**

### 5.2 Redeploy Frontend

```bash
git commit --allow-empty -m "Update API URL to ngrok"
git push origin main
```

O desde Vercel:
- **Deployments** → Click en los 3 puntos → **"Redeploy"**

---

## 🎉 Paso 6: Probar Todo Junto

1. Abre tu frontend: **https://proyecto-p2-p.vercel.app**
2. Abre DevTools (F12) → **Network**
3. Recarga la página
4. Deberías ver requests a tu URL de ngrok
5. Verifica que las respuestas sean **200 OK**

**Probar health check desde internet:**
```bash
curl https://tu-url.ngrok-free.app/api/v1/health
```

---

## 🎯 Resumen de Servicios Corriendo

Una vez que todo esté activo:

| Servicio | Puerto | URL Local | URL Pública (ngrok) |
|----------|--------|-----------|---------------------|
| Backend API | 8000 | http://localhost:8000 | https://xxxx.ngrok-free.app |
| Celery Worker | - | - | - |
| Celery Beat | - | - | - |
| ngrok Web Interface | 4040 | http://localhost:4040 | - |

**Bases de Datos Remotas:**
- PostgreSQL: Neon (cloud)
- Redis: Upstash (cloud)
- RabbitMQ: CloudAMQP (cloud)

---

## 📊 Monitorear Logs

### Ver requests en tiempo real:

**ngrok Web Interface:**
```
http://localhost:4040
```

Aquí puedes ver:
- Todas las requests que llegan
- Response status codes
- Request/response bodies
- Tiempos de respuesta

### Ver logs del backend:

Los logs se mostrarán en las terminales donde corriste los scripts.

---

## 🛑 Detener Servicios

Para detener cada servicio, presiona **Ctrl+C** en cada terminal.

**Orden recomendado:**
1. Detener ngrok (Terminal 4)
2. Detener Celery Beat (Terminal 3)
3. Detener Celery Worker (Terminal 2)
4. Detener Backend API (Terminal 1)

---

## ⚠️ Notas Importantes

### ngrok Free Tier:

- ✅ **HTTPS incluido**
- ✅ **40 requests/minuto**
- ⚠️ **La URL cambia cada vez que reinicias ngrok**
- ⚠️ **Sesión máxima: 2 horas** (después reconecta automáticamente)

**Solución para URL fija:** Actualiza a ngrok Pro ($8/mes) para tener una URL permanente.

### Para Development:

Si solo necesitas probar localmente (sin exponer a internet):
1. Corre el frontend localmente también: `cd frontend && npm run dev`
2. El frontend usará `http://localhost:8000` automáticamente

---

## 🆘 Troubleshooting

### Error: "Cannot connect to PostgreSQL"
**Solución:** Verifica que la `DATABASE_URL` en `.env.local` sea correcta.

### Error: "Cannot connect to Redis"
**Solución:** Verifica que la `REDIS_URL` en `.env.local` sea correcta.

### Error: "Celery worker not starting"
**Solución:**
```bash
cd backend
python -m celery -A celery_app.worker worker --loglevel=debug
```
Revisa los logs para ver el error específico.

### ngrok: "ERR_NGROK_108"
**Solución:** Tu authtoken no está configurado correctamente. Ejecuta:
```bash
ngrok config add-authtoken TU_AUTHTOKEN
```

### Frontend no se conecta al backend
**Solución:**
1. Verifica que ngrok esté corriendo
2. Verifica que la variable `NEXT_PUBLIC_API_URL` en Vercel tenga la URL correcta de ngrok
3. Verifica que hayas redesplegado el frontend después de cambiar la variable

---

## 🎉 ¡Listo!

Tu sistema de arbitraje de criptos está corriendo localmente con conexión a bases de datos en la nube, y expuesto a internet con ngrok.

**Próximos pasos:**
- Probar operaciones de trading
- Verificar que las tareas de Celery se ejecuten correctamente
- Monitorear logs para detectar errores
- Cuando estés listo para producción 24/7, desplegar en Fly.io o similares
