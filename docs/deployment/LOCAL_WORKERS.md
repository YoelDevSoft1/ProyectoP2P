# 🔧 Ejecutar Workers de Celery Localmente

Ya que Render.com FREE plan no soporta background workers, puedes ejecutar los workers de Celery en tu máquina local durante desarrollo y pruebas.

---

## 📋 Pre-requisitos

1. Backend desplegado en Render.com ✅
2. Variables de entorno configuradas en Render ✅
3. Python 3.11+ instalado localmente
4. Acceso a las mismas bases de datos (Neon, Upstash, CloudAMQP)

---

## 🚀 Configuración Rápida (5 minutos)

### 1. Clonar Variables de Entorno

Crea un archivo `.env.local` en la raíz del proyecto:

```bash
# Copiar desde Render Dashboard → Settings → Environment
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://default:pass@region.upstash.io:6379
RABBITMQ_URL=amqps://user:pass@region.cloudamqp.com/vhost

# Copiar el mismo SECRET_KEY que usas en Render
SECRET_KEY=tu_secret_key_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# Trading (modo seguro)
TRADING_MODE=manual
PROFIT_MARGIN_COP=2.5
PROFIT_MARGIN_VES=3.0
MIN_TRADE_AMOUNT=50
MAX_TRADE_AMOUNT=1000

# Binance (opcional)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false
```

### 2. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 3. Ejecutar Workers

Abre **2 terminales separadas**:

**Terminal 1 - Celery Worker:**
```bash
cd backend
celery -A celery_app.worker worker --loglevel=info --concurrency=2
```

**Terminal 2 - Celery Beat:**
```bash
cd backend
celery -A celery_app.worker beat --loglevel=info
```

---

## ✅ Verificar que Funcionan

Deberías ver en los logs:

**Worker:**
```
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Connected to amqps://...
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] celery@hostname ready.
```

**Beat:**
```
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] beat: Starting...
[2025-xx-xx xx:xx:xx,xxx: INFO/MainProcess] Scheduler: Sending due task update-prices
```

---

## 🎯 Tareas Programadas

Los workers ejecutarán automáticamente:

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `update-prices` | Cada 10 seg | Actualiza precios P2P de Binance |
| `update-trm` | Cada 5 min | Actualiza TRM de Colombia |
| `analyze-spread` | Cada 30 seg | Analiza oportunidades de spread |
| `analyze-arbitrage` | Cada 2 min | Analiza arbitrajes Spot-P2P |
| `run-trading-bot` | Cada 1 min | Ejecuta bot de trading (si está en auto) |
| `retrain-ml-model` | Diario | Re-entrena modelo ML |
| `cleanup-old-data` | Semanal | Limpia datos antiguos |

---

## 🔍 Monitorear Tareas

### Ver Tareas en Ejecución

```bash
celery -A celery_app.worker inspect active
```

### Ver Tareas Programadas

```bash
celery -A celery_app.worker inspect scheduled
```

### Ver Estado de Workers

```bash
celery -A celery_app.worker status
```

---

## ⚙️ Configuración Avanzada

### Ajustar Concurrencia

Para máquinas con más recursos:

```bash
celery -A celery_app.worker worker --loglevel=info --concurrency=4
```

### Ejecutar Solo Tareas Específicas

```bash
# Solo tareas de precios
celery -A celery_app.worker worker --loglevel=info -Q prices

# Solo tareas de análisis
celery -A celery_app.worker worker --loglevel=info -Q analysis
```

### Modo Debug

```bash
celery -A celery_app.worker worker --loglevel=debug
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to RabbitMQ"
**Solución:** Verifica que `RABBITMQ_URL` esté correcto en `.env.local`

```bash
# Probar conexión
python -c "from celery import Celery; app = Celery(broker='tu_rabbitmq_url'); print(app.connection().connect())"
```

### Error: "Cannot connect to Redis"
**Solución:** Verifica que `REDIS_URL` esté correcto

```bash
# Probar conexión
redis-cli -u redis://default:pass@region.upstash.io:6379 ping
```

### Workers no ejecutan tareas
**Solución:**
1. Verifica que Celery Beat esté corriendo
2. Revisa logs de Beat para ver si envía tareas
3. Verifica que el worker esté escuchando

---

## 💡 Tips

1. **Usa screen/tmux:** Para mantener workers corriendo en background
   ```bash
   # Con screen
   screen -S celery-worker
   celery -A celery_app.worker worker --loglevel=info
   # Ctrl+A, D para detach

   # Reattach
   screen -r celery-worker
   ```

2. **Logs a archivo:**
   ```bash
   celery -A celery_app.worker worker --loglevel=info --logfile=logs/celery.log
   ```

3. **Auto-restart con watchdog:**
   ```bash
   pip install watchdog
   celery -A celery_app.worker worker --loglevel=info --autoreload
   ```

---

## 🚀 Alternativas para Producción

Si necesitas workers 24/7 sin tu computadora encendida:

### Opción 1: Koyeb (FREE)
- 2 servicios gratuitos
- Deploy con Docker
- https://koyeb.com

### Opción 2: Fly.io (FREE)
- 3 VMs gratuitas
- 256MB RAM cada una
- https://fly.io

### Opción 3: Railway (FREE $5 crédito/mes)
- Workers incluidos
- Fácil integración
- https://railway.app

### Opción 4: Render Starter ($7/mes)
- Workers nativos
- Todo en un solo lugar
- Sin cold starts

---

## ✅ Checklist

- [ ] `.env.local` creado con variables correctas
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Worker corriendo (Terminal 1)
- [ ] Beat corriendo (Terminal 2)
- [ ] Logs muestran "ready" sin errores
- [ ] Tareas programadas se ejecutan correctamente

---

**¡Listo! Tus workers están corriendo localmente y procesando tareas.** 🎉

Para detener los workers, presiona `Ctrl+C` en cada terminal.
