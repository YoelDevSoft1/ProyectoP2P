# 🚀 Guía Completa de Deployment a Producción - Backend

Esta guía te llevará paso a paso para subir tu backend de arbitraje de criptos a producción usando servicios gratuitos/económicos.

## 📋 Tabla de Contenidos

1. [Arquitectura de Producción](#arquitectura)
2. [Servicios Necesarios](#servicios)
3. [Deployment con Railway](#railway)
4. [Configuración de Bases de Datos](#databases)
5. [Variables de Entorno](#environment)
6. [Verificación y Testing](#testing)
7. [Monitoreo](#monitoring)

---

## 🏗️ Arquitectura de Producción <a name="arquitectura"></a>

Tu sistema necesita:

```
┌─────────────────┐
│   Frontend      │
│   (Vercel) ✅   │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│   Backend API   │
│   (Railway)     │
└────────┬────────┘
         │
    ┌────┴────────────────┬──────────────┐
    │                     │              │
    ▼                     ▼              ▼
┌─────────┐        ┌──────────┐    ┌─────────┐
│PostgreSQL│        │  Redis   │    │RabbitMQ │
│ (Neon)   │        │(Upstash) │    │(CloudAM)│
└─────────┘        └──────────┘    └─────────┘
         │
         ▼
   ┌─────────────┐
   │Celery Worker│
   │Celery Beat  │
   └─────────────┘
```

---

## 🔧 Servicios Necesarios <a name="servicios"></a>

### Servicios Gratuitos Recomendados:

1. **Railway** (Backend + Workers)
   - Plan: $5/mes + $5 gratis iniciales
   - URL: https://railway.app

2. **Neon** (PostgreSQL con TimescaleDB)
   - Plan: FREE hasta 3 GB
   - URL: https://neon.tech

3. **Upstash** (Redis)
   - Plan: FREE hasta 10k comandos/día
   - URL: https://upstash.com

4. **CloudAMQP** (RabbitMQ)
   - Plan: FREE "Lemur" - 1M mensajes/mes
   - URL: https://www.cloudamqp.com

---

## 🚂 Deployment con Railway <a name="railway"></a>

### Paso 1: Crear cuenta en Railway

1. Ve a https://railway.app
2. Regístrate con GitHub
3. Verifica tu email

### Paso 2: Crear nuevo proyecto

```bash
# En la terminal local
cd C:\ProyectoP2P

# Iniciar sesión en Railway CLI (opcional)
# npm i -g @railway/cli
# railway login
```

### Paso 3: Deploy desde GitHub

1. En Railway Dashboard, click "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Autoriza Railway a acceder a tu repo
4. Selecciona el repositorio `ProyectoP2P`
5. Railway detectará automáticamente el `railway.json`

### Paso 4: Configurar servicios en Railway

Railway te permite crear múltiples servicios en un proyecto:

#### Servicio 1: Backend API

```
Name: backend-api
Root Directory: /backend
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Servicio 2: Celery Worker

```
Name: celery-worker
Root Directory: /backend
Start Command: celery -A celery_app.worker worker --loglevel=info --concurrency=2
```

#### Servicio 3: Celery Beat

```
Name: celery-beat
Root Directory: /backend
Start Command: celery -A celery_app.worker beat --loglevel=info
```

### Paso 5: Agregar PostgreSQL Plugin (Opcional)

Si prefieres usar Railway para PostgreSQL:

1. En tu proyecto, click "+ New"
2. Selecciona "Database" → "Add PostgreSQL"
3. Railway creará automáticamente la variable `DATABASE_URL`

---

## 💾 Configuración de Bases de Datos <a name="databases"></a>

### Opción A: Neon PostgreSQL (Recomendado - FREE)

1. **Crear cuenta en Neon:**
   - Ve a https://neon.tech
   - Regístrate con GitHub
   - Crea un nuevo proyecto

2. **Obtener Connection String:**
   ```
   PostgreSQL: postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb
   ```

3. **Habilitar TimescaleDB (Opcional):**
   ```sql
   -- Conectar a Neon y ejecutar:
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   ```

### Opción B: Upstash Redis (Recomendado - FREE)

1. **Crear base de datos Redis:**
   - Ve a https://upstash.com
   - Regístrate con GitHub
   - Crea una nueva database Redis
   - Región: Más cercana a tu Railway region

2. **Obtener Connection String:**
   ```
   Redis URL: redis://default:password@region.upstash.io:6379
   ```

### Opción C: CloudAMQP RabbitMQ (Recomendado - FREE)

1. **Crear instancia:**
   - Ve a https://www.cloudamqp.com
   - Regístrate y crea una instancia "Lemur" (FREE)
   - Región: Más cercana posible

2. **Obtener AMQP URL:**
   ```
   AMQP URL: amqps://user:password@region.cloudamqp.com/vhost
   ```

---

## 🔐 Variables de Entorno en Railway <a name="environment"></a>

En Railway Dashboard → Tu Proyecto → Variables:

### Variables Críticas:

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://default:pass@host:6379

# RabbitMQ
RABBITMQ_URL=amqps://user:pass@host/vhost

# Binance
BINANCE_API_KEY=tu_api_key
BINANCE_API_SECRET=tu_api_secret
BINANCE_TESTNET=false

# Trading
TRADING_MODE=manual
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
MIN_TRADE_AMOUNT=50
MAX_TRADE_AMOUNT=1000

# Seguridad
SECRET_KEY=tu_secret_key_generado_con_openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - URL de tu frontend en Vercel
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Notificaciones (opcional)
ENABLE_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
```

### Generar SECRET_KEY seguro:

```bash
# En tu terminal local:
openssl rand -hex 32
```

---

## 🧪 Verificación y Testing <a name="testing"></a>

### 1. Health Check

Una vez deployado, verifica:

```bash
curl https://tu-backend-url.up.railway.app/api/v1/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0"
}
```

### 2. Verificar Base de Datos

```bash
curl https://tu-backend-url.up.railway.app/api/v1/prices/current?asset=USDT&fiat=COP
```

### 3. Logs en Railway

1. Ve a tu servicio en Railway
2. Click en "Deployments"
3. Click en el deployment actual
4. Ver logs en tiempo real

### 4. Ejecutar Migraciones

Si usas Alembic para migraciones:

```bash
# En Railway, agregar comando de inicio:
sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

---

## 📊 Monitoreo <a name="monitoring"></a>

### 1. Railway Metrics (Incluido)

Railway proporciona:
- CPU usage
- Memory usage
- Network traffic
- Deployment logs

### 2. Sentry (Opcional - FREE tier)

Para tracking de errores:

1. Crear cuenta en https://sentry.io
2. Crear nuevo proyecto Python
3. Agregar a `requirements.txt`:
   ```
   sentry-sdk[fastapi]==1.40.0
   ```

4. Configurar en `app/main.py`:
   ```python
   import sentry_sdk

   if settings.ENVIRONMENT == "production":
       sentry_sdk.init(
           dsn="tu_sentry_dsn",
           traces_sample_rate=1.0,
       )
   ```

### 3. Uptime Monitoring (FREE)

Usar https://uptimerobot.com para monitorear disponibilidad:
- Crear monitor HTTP(s)
- URL: `https://tu-backend.up.railway.app/api/v1/health`
- Intervalo: 5 minutos
- Alertas por email

---

## 🔄 Actualizar el Frontend

Actualiza las variables de entorno en Vercel:

```bash
NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app
```

Luego redeploya el frontend:
```bash
git commit --allow-empty -m "Update API URL"
git push origin main
```

---

## 📝 Checklist Final

- [ ] Backend deployado en Railway
- [ ] PostgreSQL configurado (Neon o Railway)
- [ ] Redis configurado (Upstash)
- [ ] RabbitMQ configurado (CloudAMQP)
- [ ] Variables de entorno configuradas
- [ ] Celery Worker funcionando
- [ ] Celery Beat funcionando
- [ ] Health check responde OK
- [ ] Frontend conectado al backend
- [ ] Monitoreo configurado
- [ ] Logs accesibles

---

## 🆘 Troubleshooting

### Error: "Cannot connect to database"

- Verifica que `DATABASE_URL` esté configurado correctamente
- Verifica que la IP de Railway esté permitida en Neon (generalmente todo está permitido por defecto)
- Revisa logs: `railway logs`

### Error: "Redis connection refused"

- Verifica `REDIS_URL` en variables de entorno
- Verifica que Upstash esté activo
- Prueba la conexión con `redis-cli -u <REDIS_URL> ping`

### Error: "Module not found"

- Asegúrate de que `requirements.txt` esté en `/backend/`
- Verifica logs de build en Railway

### Workers no ejecutan tareas

- Verifica que RabbitMQ esté configurado
- Revisa logs de celery-worker y celery-beat
- Verifica que `RABBITMQ_URL` sea correcto

---

## 💡 Tips de Producción

1. **Empezar en modo `manual`**: No ejecutar trades automáticos inicialmente
2. **Monitorear logs**: Revisar regularmente por errores
3. **Backup de BD**: Neon hace backups automáticos, pero considera exports adicionales
4. **Rate limits**: Binance tiene límites de API, monitorear uso
5. **Notificaciones**: Configurar Telegram para alertas críticas
6. **Costos**: Railway: ~$5-10/mes, otros servicios FREE

---

## 📞 Soporte

- Railway: https://railway.app/help
- Neon: https://neon.tech/docs
- Upstash: https://upstash.com/docs
- CloudAMQP: https://www.cloudamqp.com/docs/

---

¡Listo! Tu backend de arbitraje de criptos estará en producción. 🎉
