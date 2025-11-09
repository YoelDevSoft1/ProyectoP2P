"""
Celery worker para tareas asíncronas.
"""
from celery import Celery
from celery.schedules import crontab
import structlog
import os

from app.core.config import settings

logger = structlog.get_logger()

# Determinar backend de resultados
# Prioridad:
# 1. Variable de entorno CELERY_RESULT_BACKEND (si está configurada)
# 2. Si CELERY_USE_RPC_FALLBACK=true, usar rpc:// (útil para desarrollo sin Redis)
# 3. Usar Redis de settings.REDIS_URL

CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

if not CELERY_RESULT_BACKEND:
    # Verificar si se debe usar RPC fallback
    use_rpc_fallback = os.getenv("CELERY_USE_RPC_FALLBACK", "false").lower() == "true"
    if use_rpc_fallback:
        logger.info("Usando RabbitMQ RPC como backend de resultados (fallback)")
        CELERY_RESULT_BACKEND = "rpc://"
    else:
        CELERY_RESULT_BACKEND = settings.REDIS_URL

# Crear instancia de Celery
celery_app = Celery(
    "p2p_trading",
    broker=settings.RABBITMQ_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configuración
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos
    task_soft_time_limit=240,  # 4 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Configuración para backend de resultados
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_policy": {
            "timeout": 5.0,
            "interval_start": 0,
            "interval_step": 0.2,
            "interval_max": 0.2,
            "max_retries": 3,
        },
        "visibility_timeout": 3600,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
    } if CELERY_RESULT_BACKEND.startswith("redis") else {},
    # No fallar si el backend no está disponible inmediatamente
    result_backend_always_retry=True,
    result_backend_max_retries=10,
    # Configuración para evitar warnings de deprecación en Celery 6.0+
    broker_connection_retry_on_startup=True,
)

# Importar tasks
from celery_app import tasks

# Configurar tareas programadas (Celery Beat)
celery_app.conf.beat_schedule = {
    # Actualizar precios cada 10 segundos
    "update-prices": {
        "task": "celery_app.tasks.update_prices",
        "schedule": settings.UPDATE_PRICE_INTERVAL,
    },
    # Actualizar TRM cada 5 minutos
    "update-trm": {
        "task": "celery_app.tasks.update_trm",
        "schedule": settings.TRM_UPDATE_INTERVAL,
    },
    # Analizar oportunidades de spread cada 30 segundos
    "analyze-spread": {
        "task": "celery_app.tasks.analyze_spread_opportunities",
        "schedule": 30.0,
    },
    # Analizar arbitrajes Spot-P2P cada 2 minutos
    "analyze-arbitrage": {
        "task": "celery_app.tasks.analyze_arbitrage",
        "schedule": 120.0,
    },
    # Ejecutar bot de trading cada minuto (si está en modo automático)
    "run-trading-bot": {
        "task": "celery_app.tasks.run_trading_bot",
        "schedule": 60.0,
    },
    # Re-entrenar modelo ML cada 24 horas
    "retrain-ml-model": {
        "task": "celery_app.tasks.retrain_ml_model",
        "schedule": crontab(hour=0, minute=0),  # Medianoche
    },
    # Limpiar datos antiguos cada semana
    "cleanup-old-data": {
        "task": "celery_app.tasks.cleanup_old_data",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Domingo 3am
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Tarea de debug"""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok"}


# Signal handlers para métricas
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
import time

_task_start_times = {}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handler ejecutado antes de una tarea"""
    _task_start_times[task_id] = time.time()
    
    # Registrar métrica de tarea iniciada
    try:
        from app.core.metrics import metrics, celery_tasks_active
        metrics.track_celery_task(task.name, status="started")
        celery_tasks_active.labels(task_name=task.name).inc()
    except Exception as e:
        logger.warning("Failed to track Celery task start", error=str(e))


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handler ejecutado después de una tarea"""
    start_time = _task_start_times.pop(task_id, None)
    duration = time.time() - start_time if start_time else None
    
    # Registrar métrica de tarea completada
    try:
        from app.core.metrics import metrics, celery_tasks_active
        metrics.track_celery_task(task.name, duration=duration, status="succeeded")
        celery_tasks_active.labels(task_name=task.name).dec()
    except Exception as e:
        logger.warning("Failed to track Celery task completion", error=str(e))


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handler ejecutado cuando una tarea falla"""
    start_time = _task_start_times.pop(task_id, None)
    duration = time.time() - start_time if start_time else None
    
    # Obtener nombre de la tarea
    task_name = sender.name if sender else "unknown"
    
    # Registrar métrica de tarea fallida
    try:
        from app.core.metrics import metrics, celery_tasks_active
        metrics.track_celery_task(task_name, duration=duration, status="failed")
        celery_tasks_active.labels(task_name=task_name).dec()
    except Exception as e:
        logger.warning("Failed to track Celery task failure", error=str(e))


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handler ejecutado cuando una tarea se reintenta"""
    # Registrar métrica de reintento
    try:
        from app.core.metrics import metrics
        metrics.celery_task_retries_total.labels(task_name=sender.name).inc()
    except Exception as e:
        logger.warning("Failed to track Celery task retry", error=str(e))


if __name__ == "__main__":
    celery_app.start()
