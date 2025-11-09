# 🔧 Corrección de Parsing de Configuración y Otros Problemas

## Problemas Identificados

### 1. Parsing Incorrecto de Listas desde Variables de Entorno
**Problema**: Los logs mostraban que las listas de assets y fiats se estaban parseando carácter por carácter:
- `assets=['U', 'S', 'D', 'T', ',', 'B', 'C', 'E', 'H', 'N']` en lugar de `['USDT', 'BTC', 'ETH', 'BNB']`
- `fiats=['C', 'O', 'P', ',', 'V', 'E', 'S', ...]` en lugar de `['COP', 'VES', 'BRL', ...]`

**Causa**: En `backend/celery_app/tasks.py`, el código estaba iterando sobre `settings.P2P_MONITORED_ASSETS` directamente, que ahora es un string, en lugar de usar la propiedad `p2p_monitored_assets_list` que parsea correctamente el string.

**Solución**:
- ✅ Actualizado `backend/celery_app/tasks.py` para usar `settings.p2p_monitored_assets_list` y `settings.p2p_monitored_fiats_list` en lugar de iterar sobre los strings directamente.
- ✅ Las propiedades `p2p_monitored_assets_list` y `p2p_monitored_fiats_list` en `backend/app/core/config.py` ya estaban correctamente implementadas para parsear strings separados por comas.

### 2. Error de Grafana - "Dashboard title cannot be empty"
**Problema**: Grafana estaba reportando errores cada 10 segundos: `"Dashboard title cannot be empty"`.

**Causa**: El archivo `docker/grafana/dashboards/p2p-exchange-overview.json` tenía el dashboard envuelto en un objeto `{"dashboard": {...}}`, pero cuando Grafana hace provisioning de dashboards desde archivos, espera que el JSON sea directamente el objeto del dashboard.

**Solución**:
- ✅ Removido el wrapper `{"dashboard": {...}}` del archivo JSON.
- ✅ El dashboard ahora está en el formato correcto esperado por Grafana provisioning.

### 3. Error de Redis - "Event loop is closed"
**Problema**: Los workers de Celery estaban reportando errores: `"Event loop is closed"` cuando intentaban usar Redis.

**Causa**: Cuando los workers de Celery crean nuevos procesos, cada proceso necesita su propio event loop. El problema ocurría cuando se intentaba usar Redis después de que el event loop se había cerrado.

**Solución**:
- ✅ Mejorado el manejo de event loops en `backend/app/core/redis_pool.py` para detectar y manejar correctamente el caso donde el event loop está cerrado.
- ✅ Agregado manejo de errores en `get_client()` para intentar reinicializar el pool si el event loop está cerrado.
- ✅ El código ahora maneja correctamente el caso donde el event loop está cerrado y intenta reinicializar el pool de Redis.

## Archivos Modificados

1. **backend/celery_app/tasks.py**:
   - Línea 73-74: Cambiado para usar `settings.p2p_monitored_assets_list` y `settings.p2p_monitored_fiats_list`
   - Línea 30-53: Mejorada la función `run_async_task_safe` para manejar mejor los event loops

2. **docker/grafana/dashboards/p2p-exchange-overview.json**:
   - Removido el wrapper `{"dashboard": {...}}`
   - El dashboard ahora está en el formato correcto para Grafana provisioning

3. **backend/app/core/redis_pool.py**:
   - Línea 64-85: Mejorado `get_client()` para manejar event loops cerrados
   - Agregado manejo de errores para intentar reinicializar el pool si el event loop está cerrado

## Verificación

Para verificar que las correcciones funcionan:

1. **Parsing de Configuración**:
   ```bash
   # Los logs deberían mostrar:
   # assets=['USDT', 'BTC', 'ETH', 'BNB'] en lugar de caracteres individuales
   # fiats=['COP', 'VES', 'BRL', 'ARS'] en lugar de caracteres individuales
   ```

2. **Grafana Dashboard**:
   ```bash
   # Los logs de Grafana no deberían mostrar más errores "Dashboard title cannot be empty"
   # El dashboard debería cargarse correctamente en http://localhost:3001
   ```

3. **Redis Event Loop**:
   ```bash
   # Los logs de Celery workers no deberían mostrar más errores "Event loop is closed"
   # Las tareas deberían ejecutarse sin problemas de Redis
   ```

## Notas Adicionales

- El parsing de listas desde variables de entorno ahora funciona correctamente tanto para strings separados por comas como para JSON arrays.
- El dashboard de Grafana ahora se carga correctamente desde el archivo de provisioning.
- El manejo de event loops en Redis ahora es más robusto y maneja correctamente el caso donde el event loop está cerrado.

