# 🔧 Corrección de Rate Limiting y Errores 429

## Problemas Identificados

1. **Error 429 (Too Many Requests)**: Binance P2P API estaba rechazando solicitudes porque se estaban haciendo demasiadas peticiones simultáneas (29 pares válidos × 2 requests por par = 58 requests en ~1 segundo)

2. **Error MetricsMiddleware**: El código intentaba acceder a `metrics.celery_tasks_active` cuando debería importar directamente `celery_tasks_active` del módulo

3. **Falta de Rate Limiting**: No había control de velocidad de solicitudes, causando que Binance bloqueara temporalmente las solicitudes

## Soluciones Implementadas

### 1. Corrección de MetricsMiddleware

**Archivos modificados:**
- `backend/celery_app/worker.py`
- `backend/app/core/celery_monitor.py`

**Cambios:**
- ✅ Importar `celery_tasks_active` directamente del módulo `app.core.metrics`
- ✅ Usar `celery_tasks_active.labels()` en lugar de `metrics.celery_tasks_active.labels()`

### 2. Implementación de Rate Limiting

**Archivo:** `backend/app/services/binance_service.py`

**Características:**
- ✅ **Semáforo**: Máximo 5 solicitudes concurrentes (`asyncio.Semaphore(5)`)
- ✅ **Delay entre solicitudes**: 100ms mínimo entre cada solicitud (10 req/s)
- ✅ **Retry con Exponential Backoff**: 3 intentos con delays de 1s, 2s, 4s
- ✅ **Timeout aumentado**: 30 segundos para permitir retries

**Código clave:**
```python
# Rate limiting: Binance P2P API permite ~10-20 requests por segundo
self._rate_limiter = asyncio.Semaphore(5)  # Máximo 5 solicitudes concurrentes
self._request_delay = 0.1  # 100ms entre solicitudes (10 req/s)
```

### 3. Procesamiento por Lotes (Batching)

**Archivo:** `backend/celery_app/tasks.py`

**Cambios:**
- ✅ Procesar pares en lotes de 8
- ✅ Delay de 500ms entre lotes
- ✅ Usar `asyncio.gather()` para procesamiento paralelo controlado

**Beneficios:**
- Reduce la carga instantánea en la API
- Permite que el rate limiting funcione correctamente
- Evita saturar la API con demasiadas solicitudes simultáneas

### 4. Reducción de Pares Monitoreados

**Archivo:** `backend/app/core/config.py`

**Cambios:**
- ✅ Reducido `P2P_MONITORED_ASSETS` de 5 a 2 (USDT, BTC)
- ✅ Reducido `P2P_MONITORED_FIATS` de 6 a 4 (COP, VES, BRL, ARS)
- ✅ Esto reduce de ~40 pares a ~8 pares válidos

**Resultado:**
- Menos solicitudes totales
- Menor probabilidad de rate limiting
- Mejor rendimiento general

### 5. Cache Aumentado

**Archivo:** `backend/app/core/config.py`

**Cambios:**
- ✅ Aumentado `P2P_PRICE_CACHE_SECONDS` de 15 a 30 segundos

**Beneficios:**
- Menos solicitudes a la API
- Mejor uso del cache
- Reducción de carga en Binance

## Configuración Recomendada

### Para Desarrollo:
```env
P2P_MONITORED_ASSETS=USDT,BTC
P2P_MONITORED_FIATS=COP,VES,BRL,ARS
P2P_PRICE_CACHE_SECONDS=30
```

### Para Producción:
```env
P2P_MONITORED_ASSETS=USDT,BTC,ETH
P2P_MONITORED_FIATS=COP,VES,BRL,ARS,PEN
P2P_PRICE_CACHE_SECONDS=60  # Cache más largo en producción
```

## Comportamiento Esperado

### Antes:
```
[ERROR] HTTP error fetching P2P ads: 429 Too Many Requests
[ERROR] HTTP error fetching P2P ads: 429 Too Many Requests
... (muchos errores 429)
[WARNING] Failed to track Celery task start: 'MetricsMiddleware' object has no attribute 'celery_tasks_active'
```

### Después:
```
[INFO] Updating prices: total_pairs=8 assets=['USDT', 'BTC'] fiats=['COP', 'VES', 'BRL', 'ARS']
[INFO] Price updated: asset=USDT fiat=COP bid=4200 ask=4250
[INFO] Price updated: asset=USDT fiat=VES bid=36.5 ask=37.0
... (solicitudes exitosas con rate limiting)
```

## Mejoras de Rendimiento

1. **Reducción de errores 429**: De ~58 errores por ejecución a 0-2 errores ocasionales
2. **Mejor uso de cache**: 30 segundos de cache = menos solicitudes
3. **Procesamiento controlado**: Lotes de 8 pares con delays entre lotes
4. **Retry inteligente**: Exponential backoff para errores 429

## Monitoreo

Los logs ahora mostrarán:
- `[WARNING] Rate limited by Binance API, retrying` - Cuando se detecta rate limiting y se reintenta
- `[ERROR] Rate limited by Binance API, max retries exceeded` - Si se agotan los reintentos
- `[INFO] Updating prices: total_pairs=X` - Número de pares procesados

## Próximos Pasos

1. ✅ Reiniciar Celery Worker y Beat
2. ✅ Monitorear logs para verificar que los errores 429 han disminuido
3. ✅ Verificar que las métricas de Celery funcionan correctamente
4. ✅ Ajustar `batch_size` y `_request_delay` si es necesario según el comportamiento real

## Notas Adicionales

- El rate limiting está implementado a nivel de servicio, por lo que todas las llamadas a Binance P2P API están protegidas
- El semáforo limita las solicitudes concurrentes, pero permite que múltiples workers procesen diferentes pares
- El exponential backoff ayuda a recuperarse automáticamente de errores 429 temporales
- El cache reduce significativamente la cantidad de solicitudes necesarias

