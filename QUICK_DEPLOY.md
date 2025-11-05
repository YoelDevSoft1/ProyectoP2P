# ⚡ Quick Deploy - Comandos Rápidos

## 🚀 Deploy Rápido en 5 Pasos

### 1️⃣ Crear Bases de Datos (5 min)

```bash
# PostgreSQL - Neon
# 1. Ir a: https://neon.tech
# 2. Crear proyecto → Copiar URL
DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb"

# Redis - Upstash
# 1. Ir a: https://upstash.com
# 2. Crear database → Copiar URL
REDIS_URL="redis://default:pass@region.upstash.io:6379"

# RabbitMQ - CloudAMQP
# 1. Ir a: https://www.cloudamqp.com
# 2. Crear instancia Lemur → Copiar URL
RABBITMQ_URL="amqps://user:pass@region.cloudamqp.com/vhost"
```

### 2️⃣ Setup Railway (2 min)

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Crear proyecto
railway init

# Linkear repo de GitHub
railway link
```

### 3️⃣ Configurar Variables (3 min)

```bash
# Generar SECRET_KEY
openssl rand -hex 32

# Configurar en Railway Dashboard
# Ir a: https://railway.app/project/<tu-proyecto>/variables

# Variables críticas:
DATABASE_URL=<tu_neon_url>
REDIS_URL=<tu_upstash_url>
RABBITMQ_URL=<tu_cloudamqp_url>
SECRET_KEY=<tu_secret_generado>
ENVIRONMENT=production
TRADING_MODE=manual
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app
```

### 4️⃣ Deploy (5 min)

```bash
# Seleccionar servicio backend
railway service

create backend-api

# Deploy
railway up -d

# Crear Worker
railway service create celery-worker

# Deploy Worker
railway up -d

# Crear Beat
railway service create celery-beat

# Deploy Beat
railway up -d
```

### 5️⃣ Verificar (2 min)

```bash
# Obtener URL
railway domain

# Test Health Check
curl https://tu-backend.railway.app/api/v1/health

# Ver logs
railway logs
```

---

## 🔗 URLs Importantes

| Servicio | URL | Purpose |
|----------|-----|---------|
| Neon | https://neon.tech | PostgreSQL |
| Upstash | https://upstash.com | Redis |
| CloudAMQP | https://www.cloudamqp.com | RabbitMQ |
| Railway | https://railway.app | Hosting |
| Vercel | https://vercel.com | Frontend |

---

## 📋 Variables de Entorno Mínimas

```bash
# REQUERIDAS
DATABASE_URL=
REDIS_URL=
RABBITMQ_URL=
SECRET_KEY=
BACKEND_CORS_ORIGINS=

# RECOMENDADAS
ENVIRONMENT=production
TRADING_MODE=manual
LOG_LEVEL=INFO

# OPCIONALES (configurar después)
BINANCE_API_KEY=
BINANCE_API_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## 🧪 Test Rápido

```bash
# Health Check
curl https://tu-backend.railway.app/api/v1/health

# Get Prices
curl https://tu-backend.railway.app/api/v1/prices/current?asset=USDT&fiat=COP

# Dashboard
curl https://tu-backend.railway.app/api/v1/analytics/dashboard
```

---

## 📊 Monitoreo Rápido

```bash
# Railway logs en tiempo real
railway logs -f

# Ver deployments
railway status

# Railway dashboard
railway open
```

---

## 🆘 Troubleshooting One-Liners

```bash
# Restart servicio
railway restart

# Re-deploy
railway up --detach

# Verificar variables
railway variables

# Rollback
railway rollback

# Shell en container
railway run bash
```

---

## 💡 Tips

1. **Empezar en modo manual:** `TRADING_MODE=manual`
2. **Monitorear primeras 24h:** `railway logs -f`
3. **Verificar health cada 5min:** UptimeRobot
4. **Backup de BD:** Neon hace automático
5. **Rate limits:** Binance = 1200 req/min

---

## ⏱️ Tiempo Total Estimado

| Tarea | Tiempo |
|-------|--------|
| Crear bases de datos | 5 min |
| Setup Railway | 2 min |
| Config variables | 3 min |
| Deploy servicios | 5 min |
| Verificación | 2 min |
| **TOTAL** | **~17 minutos** |

---

## 🎯 Resultado Final

```
✅ Backend API: https://tu-backend.railway.app
✅ Frontend: https://tu-app.vercel.app
✅ Health Check: 200 OK
✅ Workers: Running
✅ Databases: Connected
```

---

## 📚 Documentación Completa

- **Guía Detallada:** [docs/DEPLOYMENT_PRODUCTION.md](docs/DEPLOYMENT_PRODUCTION.md)
- **Checklist Completo:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Script Automático:** [scripts/deploy_railway.sh](scripts/deploy_railway.sh)

---

¡Listo en menos de 20 minutos! 🚀
