# 🧹 Limpieza Automática de Alertas

## Configuración

La tarea de limpieza de alertas se ejecuta **cada 10 minutos** automáticamente mediante Celery Beat.

## Comportamiento

### ¿Qué hace la limpieza?

1. **Mantiene solo las 40 alertas más recientes**
   - Elimina todas las alertas excepto las 40 más nuevas
   - Las alertas se ordenan por `created_at` descendente
   - No importa si están leídas o no, solo se mantienen las más recientes

2. **Elimina price history antiguo**
   - Elimina registros de `price_history` mayores a 90 días
   - Ayuda a mantener la base de datos optimizada

### Frecuencia

- **Ejecución**: Cada 10 minutos (600 segundos)
- **Timeout**: 10 minutos máximo por ejecución
- **Reintentos**: Hasta 2 reintentos con espera de 1 minuto entre intentos

### Configuración

La configuración se encuentra en:
- **Schedule**: `backend/celery_app/worker.py` (línea 203-206)
- **Tarea**: `backend/celery_app/tasks.py` (función `cleanup_old_data`)

```python
# backend/celery_app/worker.py
"cleanup-old-data": {
    "task": "celery_app.tasks.cleanup_old_data",
    "schedule": 600.0,  # Cada 10 minutos (600 segundos)
},
```

## Ejecución Manual

También puedes ejecutar la limpieza manualmente usando el endpoint API:

```bash
POST /api/v1/analytics/alerts/cleanup?max_alerts=40
```

## Logs

La tarea registra información detallada en los logs:

```
Old alerts cleaned up
  deleted_alerts: 8560
  total_alerts_before: 8600
  alerts_kept: 40
  max_alerts: 40
```

## Beneficios

1. **Base de datos optimizada**: Mantiene solo datos relevantes
2. **Mejor rendimiento**: Menos registros = consultas más rápidas
3. **Espacio de almacenamiento**: Reduce el uso de disco
4. **Alertas frescas**: Siempre muestra las alertas más recientes

## Notas

- La limpieza se ejecuta automáticamente, no requiere intervención manual
- Las alertas eliminadas no se pueden recuperar
- El número de alertas a mantener (40) se puede cambiar en el código si es necesario
- La limpieza de price history (90 días) es independiente de la limpieza de alertas

