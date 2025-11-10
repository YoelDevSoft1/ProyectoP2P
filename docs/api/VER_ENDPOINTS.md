# Cómo Ver Todos los Endpoints de la API

## 📍 Formas de Ver los Endpoints

### 1. **Documentación Interactiva de FastAPI (Swagger UI)** ⭐ RECOMENDADO

FastAPI genera automáticamente documentación interactiva donde puedes ver y probar todos los endpoints.

**URL:** `http://localhost:8000/api/v1/docs`

**Características:**
- ✅ Ver todos los endpoints organizados por tags
- ✅ Ver parámetros y tipos de datos
- ✅ Probar endpoints directamente desde el navegador
- ✅ Ver ejemplos de requests y responses
- ✅ Ver esquemas de datos

**Pasos:**
1. Inicia el backend: `docker-compose up -d` o `uvicorn app.main:app --reload`
2. Abre tu navegador en: `http://localhost:8000/api/v1/docs`
3. Explora los endpoints organizados por categorías

### 2. **ReDoc (Documentación Alternativa)**

ReDoc proporciona una documentación más visual y organizada.

**URL:** `http://localhost:8000/api/v1/redoc`

**Características:**
- ✅ Documentación más visual
- ✅ Mejor para leer y entender
- ✅ No permite probar endpoints (solo lectura)

### 3. **OpenAPI JSON Schema**

El schema OpenAPI en formato JSON que usa FastAPI.

**URL:** `http://localhost:8000/api/v1/openapi.json`

**Características:**
- ✅ Schema completo en JSON
- ✅ Útil para generar clientes automáticamente
- ✅ Puede ser usado por herramientas externas

### 4. **Endpoint de Listado de Endpoints** (Nuevo)

He creado un endpoint especial que lista todos los endpoints de forma programática.

**URL:** `http://localhost:8000/api/v1/health/endpoints`

**Características:**
- ✅ Lista todos los endpoints con métodos HTTP
- ✅ Incluye paths completos
- ✅ Incluye tags/categorías
- ✅ Formato JSON fácil de parsear

### 5. **En el Código**

Los endpoints están definidos en los siguientes archivos:

```
backend/app/api/endpoints/
├── health.py              # Health checks y métricas
├── prices.py              # Precios P2P
├── trades.py              # Operaciones de trading
├── analytics.py           # Analytics y análisis
├── spot.py                # Trading spot
├── advanced_arbitrage.py  # Arbitraje avanzado
├── dynamic_pricing.py     # Precios dinámicos
├── market_making.py       # Market making
└── order_execution.py     # Ejecución de órdenes
```

## 📋 Lista Completa de Endpoints

### Health & Metrics
- `GET /api/v1/health` - Health check completo
- `GET /api/v1/health/db` - Health check de PostgreSQL
- `GET /api/v1/health/redis` - Health check de Redis
- `GET /api/v1/health/rabbitmq` - Health check de RabbitMQ
- `GET /api/v1/health/celery` - Health check de Celery
- `GET /api/v1/health/endpoints` - Lista todos los endpoints
- `GET /api/v1/metrics` - Métricas Prometheus

### Prices (P2P)
- `GET /api/v1/prices/current` - Precios actuales
- `GET /api/v1/prices/history` - Historial de precios
- `GET /api/v1/prices/trm` - TRM de Colombia
- `GET /api/v1/prices/spread-analysis` - Análisis de spreads

### Trades
- `GET /api/v1/trades/` - Listar trades
- `GET /api/v1/trades/{trade_id}` - Obtener trade específico
- `POST /api/v1/trades/` - Crear nuevo trade
- `GET /api/v1/trades/stats/summary` - Estadísticas de trades

### Analytics
- `GET /api/v1/analytics/dashboard` - Datos del dashboard
- `GET /api/v1/analytics/performance` - Métricas de rendimiento
- `GET /api/v1/analytics/alerts` - Listar alertas
- `POST /api/v1/analytics/alerts/{alert_id}/read` - Marcar alerta como leída
- `GET /api/v1/analytics/triangle-arbitrage` - Oportunidades de arbitraje triangular
- `GET /api/v1/analytics/liquidity` - Análisis de liquidez
- `GET /api/v1/analytics/ml-predictions` - Predicciones ML
- `GET /api/v1/analytics/risk/calculate-var` - Calcular VaR
- `GET /api/v1/analytics/risk/calculate-sharpe` - Calcular Sharpe Ratio
- `GET /api/v1/analytics/risk/calculate-sortino` - Calcular Sortino Ratio

### Spot Trading
- `GET /api/v1/spot/prices` - Precios spot
- `GET /api/v1/spot/orderbook` - Order book
- `POST /api/v1/spot/order/market` - Orden market
- `POST /api/v1/spot/order/limit` - Orden limit

### Advanced Arbitrage
- `GET /api/v1/advanced-arbitrage/opportunities` - Oportunidades de arbitraje
- `GET /api/v1/advanced-arbitrage/funding-rate` - Arbitraje de funding rate
- `GET /api/v1/advanced-arbitrage/statistical` - Arbitraje estadístico
- `GET /api/v1/advanced-arbitrage/delta-neutral` - Arbitraje delta neutral
- `GET /api/v1/advanced-arbitrage/triangle` - Arbitraje triangular avanzado

### Dynamic Pricing
- `GET /api/v1/dynamic-pricing/calculate` - Calcular precio dinámico
- `GET /api/v1/dynamic-pricing/summary` - Resumen de precios

### Market Making
- `POST /api/v1/market-making/start` - Iniciar market making
- `GET /api/v1/market-making/status` - Estado del market making
- `POST /api/v1/market-making/update` - Actualizar market making
- `POST /api/v1/market-making/stop` - Detener market making

### Order Execution
- `POST /api/v1/order-execution/twap` - Ejecutar TWAP
- `POST /api/v1/order-execution/vwap` - Ejecutar VWAP
- `POST /api/v1/order-execution/iceberg` - Ejecutar Iceberg

### Root
- `GET /` - Información de la API

## 🚀 Uso Rápido

### Ver en el Navegador

```bash
# Inicia el backend
docker-compose up -d

# O si estás en desarrollo
cd backend
uvicorn app.main:app --reload

# Abre en tu navegador
# Swagger UI: http://localhost:8000/api/v1/docs
# ReDoc: http://localhost:8000/api/v1/redoc
```

### Ver desde la Línea de Comandos

```bash
# Ver OpenAPI schema
curl http://localhost:8000/api/v1/openapi.json | jq

# Ver lista de endpoints
curl http://localhost:8000/api/v1/health/endpoints | jq

# Ver health check
curl http://localhost:8000/api/v1/health | jq
```

### Ver desde Python

```python
import requests

# Obtener lista de endpoints
response = requests.get('http://localhost:8000/api/v1/health/endpoints')
endpoints = response.json()

for endpoint in endpoints:
    print(f"{endpoint['method']} {endpoint['path']}")
```

### Ver desde el Frontend

```typescript
// En tu componente React/Next.js
const response = await fetch('http://localhost:8000/api/v1/health/endpoints')
const endpoints = await response.json()

endpoints.forEach(endpoint => {
  console.log(`${endpoint.method} ${endpoint.path}`)
})
```

## 📝 Notas

- Todos los endpoints usan el prefijo `/api/v1` (definido en `settings.API_V1_STR`)
- Los endpoints están organizados por tags/categorías
- La documentación se genera automáticamente desde los docstrings de Python
- Puedes probar los endpoints directamente desde Swagger UI

## 🔍 Buscar Endpoints Específicos

### Por Categoría

En Swagger UI, los endpoints están organizados por tags:
- `health` - Health checks
- `metrics` - Métricas
- `prices` - Precios
- `trades` - Trades
- `analytics` - Analytics
- `spot` - Spot trading
- `advanced-arbitrage` - Arbitraje avanzado
- `dynamic-pricing` - Precios dinámicos
- `market-making` - Market making
- `order-execution` - Ejecución de órdenes

### Por Método HTTP

- `GET` - Obtener datos
- `POST` - Crear/ejecutar
- `PUT` - Actualizar
- `DELETE` - Eliminar

## ✅ Verificación Rápida

Para verificar que todos los endpoints están disponibles:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Lista de endpoints
curl http://localhost:8000/api/v1/health/endpoints

# OpenAPI schema
curl http://localhost:8000/api/v1/openapi.json
```

## 🎯 Recomendación

**La mejor forma de ver y probar los endpoints es usar Swagger UI:**
1. Abre `http://localhost:8000/api/v1/docs`
2. Explora los endpoints por categoría
3. Prueba los endpoints directamente desde el navegador
4. Ve los ejemplos de requests y responses

¡Es la forma más rápida y fácil de explorar tu API!

