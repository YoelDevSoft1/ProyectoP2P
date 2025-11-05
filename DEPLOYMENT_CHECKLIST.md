# ✅ Checklist de Deployment a Producción

## 🎯 Resumen Rápido

**Objetivo:** Subir backend a producción con servicios gratuitos
**Tiempo estimado:** 30-45 minutos
**Costo:** ~$5-10/mes (Railway) + FREE tier de otros servicios

---

## 📋 Pre-requisitos

- [ ] Cuenta de GitHub
- [ ] Repositorio en GitHub con el código
- [ ] Frontend ya deployado en Vercel ✅
- [ ] Binance API keys (opcional para empezar)

---

## 🚀 Paso 1: Servicios Externos (15 min)

### PostgreSQL - Neon (FREE)

1. [ ] Ir a https://neon.tech
2. [ ] Registrarse con GitHub
3. [ ] Crear proyecto "p2p-arbitrage"
4. [ ] Copiar Connection String
5. [ ] Guardar como `DATABASE_URL`

```
postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
```

### Redis - Upstash (FREE)

1. [ ] Ir a https://upstash.com
2. [ ] Registrarse con GitHub
3. [ ] Crear database "p2p-redis"
4. [ ] Región: us-east-1
5. [ ] Copiar Redis URL
6. [ ] Guardar como `REDIS_URL`

```
redis://default:pass@region.upstash.io:6379
```

### RabbitMQ - CloudAMQP (FREE)

1. [ ] Ir a https://www.cloudamqp.com
2. [ ] Registrarse
3. [ ] Crear instancia "Lemur" (FREE)
4. [ ] Región: US-East-1
5. [ ] Copiar AMQP URL
6. [ ] Guardar como `RABBITMQ_URL`

```
amqps://user:pass@region.cloudamqp.com/vhost
```

---

## 🚂 Paso 2: Railway Setup (10 min)

### Crear Proyecto

1. [ ] Ir a https://railway.app
2. [ ] Registrarse con GitHub
3. [ ] Click "New Project"
4. [ ] Seleccionar "Deploy from GitHub repo"
5. [ ] Seleccionar repositorio `ProyectoP2P`

### Crear Servicios

#### Servicio 1: Backend API

1. [ ] Click "+ New" → "Empty Service"
2. [ ] Nombrar: `backend-api`
3. [ ] Settings → Root Directory: `/backend`
4. [ ] Settings → Start Command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. [ ] Deploy → Connect to GitHub
6. [ ] Branch: `main`

#### Servicio 2: Celery Worker

1. [ ] Click "+ New" → "Empty Service"
2. [ ] Nombrar: `celery-worker`
3. [ ] Settings → Root Directory: `/backend`
4. [ ] Settings → Start Command:
   ```
   celery -A celery_app.worker worker --loglevel=info --concurrency=2
   ```

#### Servicio 3: Celery Beat

1. [ ] Click "+ New" → "Empty Service"
2. [ ] Nombrar: `celery-beat`
3. [ ] Settings → Root Directory: `/backend`
4. [ ] Settings → Start Command:
   ```
   celery -A celery_app.worker beat --loglevel=info
   ```

---

## 🔐 Paso 3: Variables de Entorno (10 min)

En Railway → Tu Proyecto → Variables (para cada servicio):

### Variables COMPARTIDAS (aplicar a los 3 servicios)

```bash
# Bases de datos
DATABASE_URL=<tu_neon_url>
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

REDIS_URL=<tu_upstash_url>
RABBITMQ_URL=<tu_cloudamqp_url>

# Seguridad (generar con: openssl rand -hex 32)
SECRET_KEY=<tu_secret_key_generado>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Trading (empezar en manual)
TRADING_MODE=manual
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
MIN_TRADE_AMOUNT=50
MAX_TRADE_AMOUNT=1000
MAX_DAILY_TRADES=50

# CORS - TU URL DE VERCEL
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app
```

### Variables OPCIONALES (configurar después)

```bash
# Binance (puedes dejarlo vacío por ahora)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false

# Notificaciones (opcional)
ENABLE_NOTIFICATIONS=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## 🧪 Paso 4: Verificación (5 min)

### Health Check

1. [ ] Ir a Railway → backend-api → Deployments
2. [ ] Esperar que el build termine (3-5 min)
3. [ ] Click en "View Logs"
4. [ ] Buscar: "Application startup complete"
5. [ ] Copiar URL pública (Settings → Generate Domain)
6. [ ] Probar:

```bash
curl https://tu-backend.railway.app/api/v1/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### Verificar Workers

1. [ ] Railway → celery-worker → Ver logs
2. [ ] Buscar: "celery@xxx ready"
3. [ ] Railway → celery-beat → Ver logs
4. [ ] Buscar: "beat: Starting..."

---

## 🔗 Paso 5: Conectar Frontend (5 min)

### Actualizar Vercel

1. [ ] Ir a Vercel → Tu Proyecto → Settings → Environment Variables
2. [ ] Actualizar:
   ```
   NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
   ```
3. [ ] Guardar
4. [ ] Ir a Deployments → Redeploy

### Verificar Conexión

1. [ ] Abrir tu frontend: https://tu-app.vercel.app
2. [ ] Abrir DevTools (F12)
3. [ ] Ir a Network
4. [ ] Debería ver requests a tu backend en Railway
5. [ ] Verificar que no hay errores CORS

---

## 📊 Paso 6: Monitoreo (Opcional)

### Uptime Robot (FREE)

1. [ ] Ir a https://uptimerobot.com
2. [ ] Crear monitor
3. [ ] Type: HTTP(s)
4. [ ] URL: `https://tu-backend.railway.app/api/v1/health`
5. [ ] Interval: 5 minutos
6. [ ] Email de alertas

### Sentry (Opcional - FREE)

1. [ ] Ir a https://sentry.io
2. [ ] Crear proyecto Python/FastAPI
3. [ ] Copiar DSN
4. [ ] Agregar a variables de Railway:
   ```
   SENTRY_DSN=tu_sentry_dsn
   ```

---

## ✅ Checklist Final

### Backend
- [ ] Backend API deployado y corriendo
- [ ] Celery Worker activo
- [ ] Celery Beat activo
- [ ] Health check responde 200 OK
- [ ] Logs sin errores críticos

### Bases de Datos
- [ ] PostgreSQL conectado (Neon)
- [ ] Redis conectado (Upstash)
- [ ] RabbitMQ conectado (CloudAMQP)

### Frontend
- [ ] Variable NEXT_PUBLIC_API_URL actualizada
- [ ] Frontend redesplegado
- [ ] Requests llegan al backend
- [ ] No hay errores CORS

### Seguridad
- [ ] SECRET_KEY generado y configurado
- [ ] CORS configurado correctamente
- [ ] Variables sensibles en Railway (no en código)

### Opcional
- [ ] Binance API configurado
- [ ] Telegram notificaciones configuradas
- [ ] Uptime monitoring activo
- [ ] Sentry para error tracking

---

## 🆘 Troubleshooting Común

### ❌ Error: "Cannot connect to database"
**Solución:**
- Verifica DATABASE_URL en Railway variables
- Prueba conexión desde local con esa URL
- Verifica que Neon esté activo

### ❌ Error: "Redis connection refused"
**Solución:**
- Verifica REDIS_URL
- Prueba: `redis-cli -u <REDIS_URL> ping`
- Verifica que Upstash esté activo

### ❌ Error: "CORS policy"
**Solución:**
- Verifica BACKEND_CORS_ORIGINS incluya tu URL de Vercel
- Incluye https:// en la URL
- Redeploy backend después de cambiar

### ❌ Workers no ejecutan tareas
**Solución:**
- Verifica RABBITMQ_URL
- Revisa logs de celery-worker
- Verifica que celery-beat esté corriendo

---

## 💰 Costos Estimados

| Servicio | Plan | Costo |
|----------|------|-------|
| Railway | Hobby | ~$5-10/mes |
| Neon | FREE | $0 |
| Upstash | FREE | $0 |
| CloudAMQP | Lemur FREE | $0 |
| Vercel | FREE | $0 |
| **TOTAL** | | **~$5-10/mes** |

---

## 📚 Documentación Adicional

- **Guía Completa:** [docs/DEPLOYMENT_PRODUCTION.md](docs/DEPLOYMENT_PRODUCTION.md)
- **Script Automático:** `scripts/deploy_railway.sh`
- **Variables de Entorno:** `.env.production.example`

---

## 🎉 ¡Listo!

Tu sistema de arbitraje de criptos está en producción. 🚀

**Próximos pasos:**
1. Monitorear logs durante las primeras 24h
2. Verificar que las tareas de Celery se ejecuten correctamente
3. Probar el sistema en modo `manual`
4. Cuando estés listo, cambiar a modo `hybrid` o `auto`

**Dashboard URLs:**
- Frontend: https://tu-app.vercel.app
- Backend: https://tu-backend.railway.app
- Railway: https://railway.app/project/<tu-proyecto>
