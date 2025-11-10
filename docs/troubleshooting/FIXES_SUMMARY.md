# Resumen de Correcciones Aplicadas

## Problemas Identificados y Solucionados

### 1. Error de MetricsMiddleware - `rabbitmq_connection_status`
**Problema**: `'MetricsMiddleware' object has no attribute 'rabbitmq_connection_status'`

**Solución**: 
- ✅ Cambiado el import en `backend/app/core/rabbitmq_health.py` para importar directamente `rabbitmq_connection_status` del módulo `metrics` en lugar de acceder a través de la instancia `metrics`.

### 2. Error de Celery Monitor - `Inspect.active() timeout`
**Problema**: `Inspect.active() got an unexpected keyword argument 'timeout'`

**Solución**:
- ✅ Removido el parámetro `timeout` de las llamadas a `inspect.active()`, `inspect.registered()`, `inspect.stats()`, y `inspect.active_queues()` en `backend/app/core/celery_monitor.py`. La API de Celery maneja los timeouts internamente.

### 3. Error de Prometheus - Content-Type incorrecto
**Problema**: Prometheus no puede parsear las métricas porque el endpoint retorna `application/json` en lugar de `text/plain`

**Solución**:
- ✅ Actualizado `backend/app/api/endpoints/health.py` para retornar un `Response` con `content_type=CONTENT_TYPE_LATEST` (que es `text/plain; version=0.0.4; charset=utf-8`).

### 4. Error 429 (Too Many Requests) - Rate Limiting
**Problema**: Binance P2P API está rechazando solicitudes porque se están haciendo demasiadas peticiones simultáneas desde múltiples workers.

**Solución**:
- ✅ Implementado rate limiting global usando Redis (`backend/app/core/rate_limiter.py`) que coordina solicitudes entre todos los workers de Celery.
- ✅ Integrado el rate limiter global en `BinanceService.get_p2p_ads()`.
- ✅ Configurado para permitir 8 requests por segundo (más conservador que 10).
- ✅ Burst de 15 requests para permitir ráfagas cortas.
- ✅ El rate limiter usa un token bucket distribuido implementado con Redis y scripts Lua para operaciones atómicas.

### 5. Configuración de Assets/Fiats - Demasiados pares
**Problema**: Los logs muestran que se están procesando 29 pares válidos, lo que sugiere que hay variables de entorno o configuración que están sobreescribiendo los valores por defecto.

**Solución**:
- ✅ Cambiado `P2P_MONITORED_ASSETS`, `P2P_MONITORED_FIATS`, `ARBITRAGE_MONITORED_ASSETS`, y `ARBITRAGE_MONITORED_FIATS` de `List[str]` a `str` en `backend/app/core/config.py`.
- ✅ Agregados validadores `@field_validator` para parsear correctamente desde variables de entorno (soporta strings separados por comas y JSON arrays).
- ✅ Agregadas propiedades `p2p_monitored_assets_list`, `p2p_monitored_fiats_list`, `arbitrage_monitored_assets_list`, y `arbitrage_monitored_fiats_list` para obtener las listas parseadas.
- ✅ Actualizado `backend/celery_app/tasks.py` para usar las nuevas propiedades.
- ✅ Valores por defecto reducidos: `P2P_MONITORED_ASSETS="USDT,BTC"`, `P2P_MONITORED_FIATS="COP,VES,BRL,ARS"`.

### 6. Error de Grafana Dashboard
**Problema**: `Dashboard title cannot be empty`

**Nota**: El dashboard parece estar bien estructurado. Este error puede ser causado por:
- Grafana esperando un formato diferente del JSON
- Problemas con la codificación del archivo
- Necesidad de reiniciar el contenedor de Grafana después de cambios

**Recomendación**: 
- Verificar que el archivo `docker/grafana/dashboards/p2p-exchange-overview.json` esté correctamente formateado.
- Reiniciar el contenedor de Grafana después de cambios en los dashboards.
- Verificar los logs de Grafana para más detalles del error.

## Archivos Modificados

1. `backend/app/core/rabbitmq_health.py` - Corregido import de `rabbitmq_connection_status`
2. `backend/app/core/celery_monitor.py` - Removido parámetro `timeout` de inspect methods
3. `backend/app/api/endpoints/health.py` - Corregido endpoint de métricas para retornar formato Prometheus correcto
4. `backend/app/core/config.py` - Cambiado configuración de assets/fiats a strings con validadores y propiedades
5. `backend/app/core/rate_limiter.py` - Nuevo archivo con rate limiter global usando Redis
6. `backend/app/services/binance_service.py` - Integrado rate limiter global
7. `backend/celery_app/tasks.py` - Actualizado para usar nuevas propiedades de configuración

## Próximos Pasos

1. **Reiniciar servicios**: Reiniciar los contenedores de Docker para aplicar los cambios:
   ```bash
   docker-compose restart backend celery_worker celery_beat
   ```

2. **Verificar configuración**: Verificar que no hay variables de entorno que estén sobreescribiendo los valores por defecto:
   ```bash
   docker-compose exec backend env | grep -E "P2P_MONITORED|ARBITRAGE_MONITORED"
   ```

3. **Monitorear logs**: Verificar que los errores 429 han disminuido:
   ```bash
   docker-compose logs -f celery_worker | grep "429"
   ```

4. **Verificar rate limiting**: Verificar que el rate limiter está funcionando correctamente:
   ```bash
   docker-compose exec redis redis-cli KEYS "rate_limit:*"
   ```

5. **Dashboard de Grafana**: Si el error persiste, verificar:
   - Formato JSON del dashboard
   - Permisos del archivo
   - Logs de Grafana para más detalles

## Configuración Recomendada

Para evitar errores 429, se recomienda:
- **P2P_MONITORED_ASSETS**: `USDT,BTC` (2 assets)
- **P2P_MONITORED_FIATS**: `COP,VES,BRL,ARS` (4 fiats)
- **Total de pares**: 2 × 4 = 8 pares (reducido de 29)
- **Rate limit**: 8 requests por segundo
- **Cache TTL**: 30 segundos

Esto debería reducir significativamente la carga en la API de Binance y evitar errores 429.

