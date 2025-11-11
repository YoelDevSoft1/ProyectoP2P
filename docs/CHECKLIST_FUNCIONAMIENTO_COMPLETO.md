# ✅ Checklist: Sistema en Funcionamiento Completo

## 📋 Estado General del Sistema

Este documento lista todas las tareas pendientes y configuraciones necesarias para que el sistema funcione completamente.

---

## 🔴 CRÍTICO - Requerido para Funcionamiento Básico

### 1. Variables de Entorno en `.env`

#### ✅ Configuraciones Básicas (OBLIGATORIAS)
```env
# Base de datos
DATABASE_URL=postgresql://p2p_user:p2p_password_change_me@postgres:5432/p2p_db

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://p2p_user:p2p_password_change_me@rabbitmq:5672//

# Seguridad
SECRET_KEY=genera_una_clave_secreta_segura_aqui_minimo_32_caracteres

# Binance API (OBLIGATORIO)
BINANCE_API_KEY=tu_api_key_de_binance
BINANCE_API_SECRET=tu_api_secret_de_binance
```

**Estado**: ⚠️ **VERIFICAR** - Estas variables deben estar configuradas en tu `.env`

#### ✅ Binance API Keys
- [ ] Crear API Key en Binance (https://www.binance.com/en/my/settings/api-management)
- [ ] Habilitar solo permisos de **lectura** para empezar
- [ ] Configurar restricción de IP (recomendado)
- [ ] **NO** habilitar permisos de retiro
- [ ] Guardar keys en `.env`

---

## 🟡 IMPORTANTE - Funcionalidades Adicionales

### 2. Telegram Bot (Opcional pero Recomendado)

#### Configuración
```env
# Telegram (Opcional)
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
ENABLE_NOTIFICATIONS=true
```

**Pasos para configurar**:
1. [ ] Crear bot en Telegram con [@BotFather](https://t.me/botfather)
2. [ ] Obtener `TELEGRAM_BOT_TOKEN`
3. [ ] Obtener `TELEGRAM_CHAT_ID` (envía un mensaje a tu bot y visita `https://api.telegram.org/bot<TOKEN>/getUpdates`)
4. [ ] Agregar variables al `.env`
5. [ ] Probar con: `POST /api/v1/analytics/test-notification`

**Estado**: ⚠️ **OPCIONAL** - Sin esto, las notificaciones no funcionarán

---

### 3. Alpha Vantage API (Opcional)

#### Configuración
```env
# Alpha Vantage (Opcional - para análisis Forex)
ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
ALPHA_VANTAGE_ENABLED=true
```

**Estado**: ✅ **YA CONFIGURADO** - Tienes la API key: `A828MZ96KHX5QJRF`

**Pasos**:
- [ ] Agregar `ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF` a `.env`
- [ ] Verificar que `ALPHA_VANTAGE_ENABLED=true`
- [ ] Reiniciar backend
- [ ] Probar: `GET /api/v1/forex/realtime/USD/COP`

---

### 4. Binance P2P Browser Automation (Opcional)

#### Configuración
```env
# Binance P2P Browser Automation (Opcional)
BINANCE_EMAIL=tu_email@example.com
BINANCE_PASSWORD=tu_contraseña
BINANCE_2FA_ENABLED=false
BROWSER_HEADLESS=true
```

**Estado**: ⚠️ **OPCIONAL** - Solo necesario para trading automático P2P

**Nota**: Requiere Playwright instalado y configurado. El sistema funciona sin esto en modo manual.

---

## 🟢 RECOMENDADO - Mejoras y Optimizaciones

### 5. Iconos PNG para PWA

**Problema**: Los iconos PNG no existen, causando errores 404 en Vercel.

**Solución**:
- [ ] Abrir `frontend/public/generate-png-from-svg.html` en el navegador
- [ ] Hacer clic en "Generar Iconos PNG"
- [ ] Los archivos se descargarán automáticamente
- [ ] Mover `icon-192.png` e `icon-512.png` a `frontend/public/`
- [ ] Subir a Vercel

**Alternativa**: Usar herramienta online (https://cloudconvert.com/svg-to-png)

**Estado**: ⚠️ **PENDIENTE** - Sin esto, hay warnings en la consola del navegador

---

### 6. Configuración de Trading

#### Verificar Configuración Actual
```env
# Trading Configuration
TRADING_MODE=hybrid  # manual, auto, hybrid
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
MIN_TRADE_AMOUNT=50.0
MAX_TRADE_AMOUNT=1000.0
MAX_DAILY_TRADES=50
STOP_LOSS_PERCENTAGE=1.5
```

**Recomendación para empezar**:
- [ ] Configurar `TRADING_MODE=manual` al principio
- [ ] Verificar que los márgenes sean razonables
- [ ] Ajustar límites de trade según tu capital

**Estado**: ✅ **CONFIGURABLE** - Puedes cambiar desde la página de configuración

---

### 7. Configuración de Monitoreo (Opcional)

#### Grafana Dashboard
- [ ] Acceder a http://localhost:3001
- [ ] Login: `admin` / `admin` (cambiar después del primer login)
- [ ] Verificar que el dashboard `p2p-exchange-overview` esté cargado
- [ ] Verificar que las métricas de Prometheus estén funcionando

**Estado**: ✅ **FUNCIONAL** - Solo verificar acceso

---

## 🔧 Verificaciones de Funcionamiento

### 8. Servicios Docker

#### Verificar que todos los servicios estén corriendo:
```bash
docker-compose ps
```

**Servicios requeridos**:
- [ ] `p2p_postgres` - PostgreSQL
- [ ] `p2p_redis` - Redis
- [ ] `p2p_rabbitmq` - RabbitMQ
- [ ] `p2p_backend` - FastAPI Backend
- [ ] `p2p_celery_worker` - Celery Worker
- [ ] `p2p_celery_beat` - Celery Beat
- [ ] `p2p_frontend` - Next.js Frontend (si está en Docker)
- [ ] `p2p_prometheus` - Prometheus (opcional)
- [ ] `p2p_grafana` - Grafana (opcional)

**Estado**: ⚠️ **VERIFICAR** - Ejecutar `docker-compose ps`

---

### 9. Health Checks

#### Backend Health
```bash
curl http://localhost:8000/api/v1/health
```

**Verificar**:
- [ ] `status: "healthy"`
- [ ] `database: "healthy"`
- [ ] `redis: "healthy"`
- [ ] `rabbitmq: "healthy"`

**Estado**: ⚠️ **VERIFICAR** - Debe retornar todos los servicios healthy

---

### 10. Endpoints Críticos

#### Precios P2P
```bash
curl http://localhost:8000/api/v1/prices/current
```
- [ ] Debe retornar precios P2P
- [ ] Verificar que no haya errores 429 (rate limiting)

#### Métricas
```bash
curl http://localhost:8000/api/v1/metrics
```
- [ ] Debe retornar métricas en formato Prometheus
- [ ] Verificar que el Content-Type sea `text/plain`

#### Configuración
```bash
curl http://localhost:8000/api/v1/config
```
- [ ] Debe retornar la configuración actual
- [ ] Verificar que `trading.mode` esté presente

**Estado**: ⚠️ **VERIFICAR** - Probar cada endpoint

---

### 11. Tareas de Celery

#### Verificar que las tareas se ejecuten:
```bash
# Ver logs de Celery Beat
docker-compose logs -f celery_beat

# Ver logs de Celery Worker
docker-compose logs -f celery_worker
```

**Tareas que deben ejecutarse**:
- [ ] `update-prices` - Cada 30 segundos
- [ ] `update-trm` - Cada 5 minutos
- [ ] `analyze-spread` - Cada 60 segundos
- [ ] `analyze-arbitrage` - Cada 2 minutos
- [ ] `run-trading-bot` - Cada minuto (si no está en modo manual)
- [ ] `cleanup-old-data` - Cada 10 minutos

**Estado**: ⚠️ **VERIFICAR** - Revisar logs

---

### 12. Base de Datos

#### Verificar que las tablas existan:
```bash
# Conectar a PostgreSQL
docker exec -it p2p_postgres psql -U p2p_user -d p2p_db

# Verificar tablas
\dt
```

**Tablas requeridas**:
- [ ] `users`
- [ ] `trades`
- [ ] `price_history`
- [ ] `alerts`
- [ ] `app_config` (nueva tabla para configuración persistente)

**Estado**: ⚠️ **VERIFICAR** - Las tablas se crean automáticamente al iniciar

---

### 13. Frontend

#### Verificar que el frontend funcione:
- [ ] Abrir http://localhost:3000
- [ ] Verificar que la landing page cargue
- [ ] Verificar que no haya errores en la consola
- [ ] Verificar que los precios se actualicen
- [ ] Verificar que el dashboard funcione
- [ ] Verificar que las métricas se muestren

**Estado**: ⚠️ **VERIFICAR** - Probar en el navegador

---

## 🐛 Problemas Conocidos y Soluciones

### 14. Problemas Resueltos Recientemente

#### ✅ Error 422 en `/api/v1/trades/?limit=1000`
- **Estado**: ✅ **RESUELTO** - Límite aumentado a 1000

#### ✅ Error 404 en `/api/v1/forex/expert/analyze/EUR/USD`
- **Estado**: ✅ **RESUELTO** - Normalización de pares mejorada

#### ✅ Error 500 en `/api/v1/p2p-trading/orders`
- **Estado**: ✅ **RESUELTO** - Manejo de errores mejorado

#### ✅ Iconos PNG faltantes
- **Estado**: ⚠️ **PENDIENTE** - Scripts creados, falta generar los PNG

#### ✅ Configuración persistente
- **Estado**: ✅ **IMPLEMENTADO** - Configuración se guarda en base de datos

#### ✅ Limpieza de alertas
- **Estado**: ✅ **CONFIGURADO** - Se ejecuta cada 10 minutos

---

## 📊 Checklist de Funcionalidades

### Funcionalidades Core
- [ ] **Precios P2P**: Obtención de precios de Binance P2P
- [ ] **Análisis de Spreads**: Detección de oportunidades
- [ ] **Arbitraje**: Análisis de arbitraje Spot-P2P
- [ ] **Alertas**: Sistema de alertas funcionando
- [ ] **Trading Bot**: Bot de trading (modo manual/auto/hybrid)
- [ ] **Métricas**: Métricas Prometheus expuestas
- [ ] **Dashboard**: Dashboard de métricas funcionando
- [ ] **Configuración**: Página de configuración funcionando
- [ ] **Limpieza de Alertas**: Limpieza automática cada 10 minutos

### Funcionalidades Opcionales
- [ ] **Telegram**: Notificaciones por Telegram
- [ ] **Alpha Vantage**: Análisis Forex avanzado
- [ ] **P2P Trading**: Trading automático P2P (requiere browser automation)
- [ ] **ML/DL**: Modelos de machine learning entrenados
- [ ] **Grafana**: Dashboards de monitoreo

---

## 🚀 Pasos para Poner el Sistema en Funcionamiento

### Paso 1: Configurar Variables de Entorno
```bash
# Copiar ejemplo
cp .env.example .env

# Editar .env con tus valores
# Mínimo requerido:
# - DATABASE_URL
# - REDIS_URL
# - RABBITMQ_URL
# - SECRET_KEY
# - BINANCE_API_KEY
# - BINANCE_API_SECRET
```

### Paso 2: Iniciar Servicios
```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps
```

### Paso 3: Verificar Health Checks
```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Debe retornar:
# {
#   "status": "healthy",
#   "services": {
#     "database": "healthy",
#     "redis": "healthy",
#     "rabbitmq": "healthy"
#   }
# }
```

### Paso 4: Verificar Frontend
```bash
# Abrir en navegador
open http://localhost:3000

# Verificar que:
# - Landing page carga
# - Precios se muestran
# - Dashboard funciona
# - No hay errores en consola
```

### Paso 5: Configurar Servicios Opcionales
```bash
# Telegram (opcional)
# Agregar al .env:
# TELEGRAM_BOT_TOKEN=tu_token
# TELEGRAM_CHAT_ID=tu_chat_id

# Alpha Vantage (opcional)
# Agregar al .env:
# ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
# ALPHA_VANTAGE_ENABLED=true
```

### Paso 6: Generar Iconos PNG
```bash
# Opción 1: Usar script HTML
# Abrir frontend/public/generate-png-from-svg.html en navegador

# Opción 2: Usar herramienta online
# https://cloudconvert.com/svg-to-png
```

### Paso 7: Verificar Tareas de Celery
```bash
# Ver logs de Celery Beat
docker-compose logs -f celery_beat

# Debe mostrar:
# - update-prices ejecutándose cada 30s
# - cleanup-old-data ejecutándose cada 10 minutos
```

### Paso 8: Probar Funcionalidades
```bash
# Probar obtención de precios
curl http://localhost:8000/api/v1/prices/current

# Probar análisis de spreads
curl http://localhost:8000/api/v1/analytics/spreads

# Probar configuración
curl http://localhost:8000/api/v1/config
```

---

## 🔍 Diagnóstico de Problemas

### Si el backend no inicia:
1. Verificar variables de entorno en `.env`
2. Verificar que PostgreSQL, Redis y RabbitMQ estén corriendo
3. Revisar logs: `docker-compose logs backend`

### Si las tareas de Celery no se ejecutan:
1. Verificar que RabbitMQ esté corriendo
2. Verificar que Celery Beat esté corriendo
3. Revisar logs: `docker-compose logs celery_beat`

### Si el frontend no carga:
1. Verificar que el backend esté corriendo
2. Verificar `NEXT_PUBLIC_API_URL` en `.env`
3. Revisar logs: `docker-compose logs frontend`

### Si las métricas no se muestran:
1. Verificar que Prometheus esté corriendo
2. Verificar que el endpoint `/api/v1/metrics` retorne datos
3. Verificar que Grafana esté configurado correctamente

---

## 📝 Resumen de Pendientes

### 🔴 Crítico (Debe estar configurado)
1. ✅ Variables de entorno básicas (DATABASE_URL, REDIS_URL, RABBITMQ_URL, SECRET_KEY)
2. ✅ Binance API Keys (BINANCE_API_KEY, BINANCE_API_SECRET)
3. ⚠️ Verificar que todos los servicios Docker estén corriendo
4. ⚠️ Verificar health checks del backend
5. ⚠️ Verificar que las tablas de base de datos existan

### 🟡 Importante (Recomendado)
6. ⚠️ Configurar Telegram Bot (para notificaciones)
7. ✅ Configurar Alpha Vantage (API key ya proporcionada)
8. ⚠️ Generar iconos PNG (scripts creados, falta ejecutar)
9. ⚠️ Verificar que las tareas de Celery se ejecuten
10. ⚠️ Probar endpoints críticos

### 🟢 Opcional (Mejoras)
11. ⚠️ Configurar Binance P2P Browser Automation (solo para trading automático)
12. ⚠️ Configurar Grafana dashboards
13. ⚠️ Entrenar modelos ML/DL
14. ⚠️ Configurar ngrok para acceso externo

---

## ✅ Verificación Final

### Checklist Rápido
- [ ] Todos los servicios Docker están corriendo
- [ ] Health check del backend retorna "healthy"
- [ ] Frontend carga correctamente
- [ ] Precios P2P se obtienen correctamente
- [ ] Tareas de Celery se ejecutan
- [ ] Métricas se exponen correctamente
- [ ] Configuración se puede leer y actualizar
- [ ] Alertas se crean y limpian correctamente
- [ ] Notificaciones funcionan (si está configurado Telegram)
- [ ] Análisis Forex funciona (si está configurado Alpha Vantage)

---

## 🎯 Siguiente Paso

Una vez completado el checklist, el sistema debería estar en **funcionamiento completo**.

Si encuentras algún problema, revisa los logs:
```bash
# Logs del backend
docker-compose logs -f backend

# Logs de Celery
docker-compose logs -f celery_worker celery_beat

# Logs del frontend
docker-compose logs -f frontend
```

