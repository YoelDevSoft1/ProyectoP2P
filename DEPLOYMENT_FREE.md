# 🆓 Deployment 100% GRATIS - Backend

Esta guía te mostrará cómo desplegar tu backend de arbitraje de criptos **completamente gratis** usando servicios con free tier.

---

## 💰 Costo Total: $0/mes

| Servicio | Uso | Costo | Límites FREE |
|----------|-----|-------|--------------|
| **Render.com** | Backend API + Workers | **$0** | 750 horas/mes |
| **Neon** | PostgreSQL | **$0** | 3 GB, 1 proyecto |
| **Upstash** | Redis | **$0** | 10k comandos/día |
| **CloudAMQP** | RabbitMQ | **$0** | 1M mensajes/mes |
| **Vercel** | Frontend | **$0** | Ilimitado |
| **TOTAL** | | **$0/mes** | ✅ Gratis Forever |

---

## ⚠️ Limitaciones del Plan Gratuito

**Render.com FREE tier:**
- ✅ 750 horas/mes de compute (suficiente para 1 servicio 24/7)
- ⚠️ Los servicios "duermen" después de 15 min de inactividad
- ⚠️ Tiempo de "despertar": 30-60 segundos
- ✅ SSL/HTTPS incluido
- ✅ Custom domains
- ✅ Deploy automático desde Git

**Solución:** El frontend despertará el backend en la primera request. Es perfecto para desarrollo, testing y demo.

---

## 🚀 Deployment en 5 Pasos (20 minutos)

### Paso 1: Bases de Datos Gratuitas (10 min)

#### 1.1 PostgreSQL - Neon (FREE Forever)

1. Ve a: **https://neon.tech**
2. Regístrate con GitHub
3. Click "Create Project"
   - Name: `p2p-arbitrage`
   - Region: `US East (Ohio)` (más cercano)
   - PostgreSQL: `15`
4. Copiar **Connection String**:
   ```
   postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Guardar como `DATABASE_URL`

**Límites FREE:**
- ✅ 3 GB storage
- ✅ 1 proyecto activo
- ✅ Backups automáticos (7 días)

#### 1.2 Redis - Upstash (FREE Forever)

1. Ve a: **https://upstash.com**
2. Regístrate con GitHub
3. Click "Create Database"
   - Name: `p2p-redis`
   - Type: `Regional`
   - Region: `us-east-1`
4. En tab "Details", copiar **Redis URL**:
   ```
   redis://default:pass@region.upstash.io:6379
   ```
5. Guardar como `REDIS_URL`

**Límites FREE:**
- ✅ 10,000 comandos por día
- ✅ 256 MB storage
- ✅ TLS/SSL incluido

#### 1.3 RabbitMQ - CloudAMQP (FREE Forever)

1. Ve a: **https://www.cloudamqp.com**
2. Regístrate con email
3. Click "Create New Instance"
   - Plan: **"Lemur" (FREE)**
   - Name: `p2p-rabbitmq`
   - Region: `US-East-1 (Northern Virginia)`
4. Click en tu instancia → copiar **AMQP URL**:
   ```
   amqps://user:pass@region.cloudamqp.com/vhost
   ```
5. Guardar como `RABBITMQ_URL`

**Límites FREE:**
- ✅ 1 millón de mensajes/mes
- ✅ 20 conexiones concurrentes
- ✅ Perfecto para este proyecto

---

### Paso 2: Deploy en Render.com (5 min)

#### 2.1 Crear cuenta

1. Ve a: **https://render.com**
2. Click "Get Started for Free"
3. Regístrate con GitHub
4. Autoriza acceso a tus repositorios

#### 2.2 Crear Servicios Automáticamente (Opción Fácil)

**Render detectará automáticamente tu `render.yaml`:**

1. En Render Dashboard, click **"New +"** → **"Blueprint"**
2. Conecta tu repositorio `ProyectoP2P`
3. Render leerá `render.yaml` y creará:
   - ✅ **p2p-backend** (Web Service)
   - ✅ **p2p-celery-worker** (Background Worker)
   - ✅ **p2p-celery-beat** (Background Worker)
4. Click **"Apply"**

#### 2.3 O Crear Manualmente (Opción Control)

**Servicio 1: Backend API**

1. Click "New +" → "Web Service"
2. Connect repository → Selecciona `ProyectoP2P`
3. Configurar:
   - **Name:** `p2p-backend`
   - **Region:** `Oregon (US West)`
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `../docker/Dockerfile.backend`
   - **Plan:** **FREE**
4. Click "Create Web Service"

**Servicio 2: Celery Worker**

1. Click "New +" → "Background Worker"
2. Usar mismo repo
3. Configurar:
   - **Name:** `p2p-celery-worker`
   - **Root Directory:** `backend`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `../docker/Dockerfile.backend`
   - **Start Command:**
     ```
     celery -A celery_app.worker worker --loglevel=info --concurrency=1
     ```
   - **Plan:** **FREE**

**⚠️ IMPORTANTE:** Render FREE tier solo permite **750 horas/mes total**. Si despliegas 3 servicios 24/7, superarás el límite.

**Solución:** Desplegar solo el **Backend API** en Render FREE. Los workers puedes:
- Ejecutarlos localmente durante desarrollo
- O usar otro servicio FREE adicional (Koyeb, Fly.io)

---

### Paso 3: Configurar Variables de Entorno (3 min)

En Render → Tu servicio → "Environment"

#### Variables CRÍTICAS (copiar y pegar):

```bash
# Bases de datos (pegar las URLs que copiaste)
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://default:pass@region.upstash.io:6379
RABBITMQ_URL=amqps://user:pass@region.cloudamqp.com/vhost

# Seguridad (generar nuevo)
SECRET_KEY=GENERA_CON_OPENSSL_RAND_HEX_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Trading (modo seguro)
TRADING_MODE=manual
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
MIN_TRADE_AMOUNT=50
MAX_TRADE_AMOUNT=1000
MAX_DAILY_TRADES=50
STOP_LOSS_PERCENTAGE=1.5

# CORS - Tu URL de Vercel
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app

# P2P Config
P2P_PRICE_CACHE_SECONDS=5
P2P_MIN_SURPLUS_USDT=10

# Binance (opcional - puedes configurar después)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false

# Notificaciones (opcional)
ENABLE_NOTIFICATIONS=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

#### Generar SECRET_KEY:

**En tu terminal local:**
```bash
openssl rand -hex 32
```

Copia el resultado y pégalo en `SECRET_KEY`

---

### Paso 4: Deploy y Verificar (2 min)

#### 4.1 Iniciar Deploy

Render iniciará el build automáticamente. Logs en tiempo real en:
- Render Dashboard → Tu servicio → "Logs"

**Tiempo de build:** 3-5 minutos primera vez

#### 4.2 Obtener URL Pública

1. Una vez deployado, ir a "Settings"
2. Copiar la URL: `https://p2p-backend-xxxx.onrender.com`

#### 4.3 Verificar Health Check

```bash
curl https://tu-backend.onrender.com/api/v1/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```

---

### Paso 5: Conectar Frontend (2 min)

#### 5.1 Actualizar Vercel

1. Ve a **Vercel** → Tu proyecto → **Settings** → **Environment Variables**
2. Editar/Agregar:
   ```
   NEXT_PUBLIC_API_URL=https://tu-backend.onrender.com
   ```
3. Click **"Save"**

#### 5.2 Redeploy Frontend

```bash
git commit --allow-empty -m "Update API URL to Render"
git push origin main
```

Vercel redesplegará automáticamente (~1 minuto)

#### 5.3 Probar Conexión

1. Abre tu frontend: `https://tu-app.vercel.app`
2. Abre DevTools (F12) → Network
3. Deberías ver requests a `tu-backend.onrender.com`
4. Verificar respuestas 200 OK

---

## ⚡ Optimizaciones para Plan Gratuito

### Problema: Backend "duerme" después de 15 min

**Solución 1: Keepalive desde Frontend**

Agregar en tu frontend un ping cada 10 minutos:

```javascript
// frontend/src/utils/keepalive.js
setInterval(async () => {
  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/health`);
  } catch (error) {
    // Silently fail
  }
}, 10 * 60 * 1000); // Cada 10 minutos
```

**Solución 2: UptimeRobot (FREE)**

1. Ve a: https://uptimerobot.com
2. Crear monitor:
   - Type: **HTTP(s)**
   - URL: `https://tu-backend.onrender.com/api/v1/health`
   - Monitoring Interval: **5 minutes**
3. Esto mantendrá tu backend despierto 24/7

**Solución 3: Cron-job.org (FREE)**

1. Ve a: https://cron-job.org
2. Crear job:
   - URL: `https://tu-backend.onrender.com/api/v1/health`
   - Interval: **Every 10 minutes**

---

## 🔧 Mantenimiento

### Ver Logs en Tiempo Real

```
Render Dashboard → Tu servicio → Logs
```

### Restart Servicio

```
Render Dashboard → Tu servicio → Manual Deploy → "Clear build cache & deploy"
```

### Actualizar Código

```bash
git add .
git commit -m "Update backend"
git push origin main
```

Render detectará el push y redesplegará automáticamente.

---

## 📊 Monitoreo FREE

### 1. Render Metrics (Incluido)

Render Dashboard muestra:
- CPU Usage
- Memory Usage
- Request Count
- Response Times
- Logs en tiempo real

### 2. UptimeRobot (FREE - Recomendado)

- 50 monitors gratis
- Check cada 5 minutos
- Alertas por email
- Status page público

### 3. Sentry (FREE - Opcional)

Error tracking:
1. Crear cuenta: https://sentry.io
2. Crear proyecto Python
3. Agregar a `requirements.txt`:
   ```
   sentry-sdk[fastapi]==1.40.0
   ```
4. Configurar en `app/main.py`

---

## 🎯 Checklist Final

### Backend en Render
- [ ] Servicio `p2p-backend` creado y deployado
- [ ] Plan: **FREE** ✅
- [ ] Health check responde 200 OK
- [ ] Logs sin errores críticos
- [ ] URL pública obtenida

### Bases de Datos
- [ ] Neon PostgreSQL conectado
- [ ] Upstash Redis conectado
- [ ] CloudAMQP RabbitMQ conectado
- [ ] Variables de entorno configuradas

### Frontend
- [ ] `NEXT_PUBLIC_API_URL` actualizado en Vercel
- [ ] Frontend redesplegado
- [ ] Conexión verificada (DevTools Network)
- [ ] No hay errores CORS

### Optimizaciones
- [ ] UptimeRobot configurado (keepalive)
- [ ] O Cron-job configurado
- [ ] Monitoreo de logs activo

---

## 🆘 Troubleshooting

### ❌ Error: "Build failed"

**Causa:** Dependencias o Dockerfile
**Solución:**
```bash
# Verificar que requirements.txt esté en /backend/
# Verificar que Dockerfile.backend esté en /docker/
# Ver logs completos en Render
```

### ❌ Error: "Application failed to start"

**Causa:** Variables de entorno faltantes
**Solución:**
- Verificar que DATABASE_URL, REDIS_URL, RABBITMQ_URL estén configuradas
- Verificar que SECRET_KEY esté generado
- Ver logs en Render para más detalles

### ❌ Error: "Cannot connect to database"

**Causa:** URL de Neon incorrecta
**Solución:**
- Verificar que incluya `?sslmode=require` al final
- Probar conexión desde local con esa URL
- Verificar que proyecto Neon esté activo

### ❌ Backend despierta muy lento (>30s)

**Causa:** Cold start en Render FREE
**Solución:**
- Implementar keepalive con UptimeRobot
- O mejorar a plan Starter ($7/mes) sin cold starts

---

## 💡 Tips para Plan Gratuito

1. **Un solo servicio:** Deploy solo el backend API en Render FREE
2. **Workers locales:** Ejecuta celery workers localmente durante desarrollo
3. **Keepalive:** Usa UptimeRobot para evitar sleep
4. **Logs:** Monitorea logs regularmente
5. **Cache:** Redis ayuda a reducir latencia
6. **Modo manual:** Empieza en `TRADING_MODE=manual`

---

## 🚀 Upgrade Path (Opcional)

Si necesitas más poder después:

| Servicio | Plan | Costo | Beneficio |
|----------|------|-------|-----------|
| Render Starter | Individual | $7/mes | Sin cold starts, más recursos |
| Neon Pro | Pro | $19/mes | 10 proyectos, más storage |
| Upstash Pro | Pay-as-you-go | Desde $0 | Sin límites |

**Pero el FREE tier es suficiente para empezar y probar el sistema.** 🎉

---

## ✅ Todo Listo - 100% GRATIS

**Resultado:**
```
✅ Backend API: https://tu-backend.onrender.com
✅ Frontend: https://tu-app.vercel.app
✅ PostgreSQL: Neon (3 GB FREE)
✅ Redis: Upstash (10k comandos/día FREE)
✅ RabbitMQ: CloudAMQP (1M mensajes/mes FREE)
✅ Hosting: Render + Vercel (FREE Forever)

💰 Costo Total: $0/mes
```

---

¡Tu sistema de arbitraje de criptos está en producción GRATIS! 🎉🆓
