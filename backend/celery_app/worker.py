"""
Celery worker para tareas asíncronas.
"""
import os
import time

from celery import Celery
from celery.schedules import crontab
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_retry,
    before_task_publish,
)
from kombu import Exchange, Queue
import structlog

from app.core.config import settings
from app.core.metrics import (
    metrics,
    celery_tasks_active,
    rabbitmq_messages_published_total,
    rabbitmq_messages_consumed_total,
    celery_task_retries_total,
)

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

task_exchange = Exchange("tasks", type="topic", durable=True)
dead_letter_exchange = Exchange("tasks.dlx", type="fanout", durable=True)

celery_app.conf.task_queues = (
    Queue(
        "high_priority",
        exchange=task_exchange,
        routing_key="task.high",
        durable=True,
        queue_arguments={"x-dead-letter-exchange": dead_letter_exchange.name},
    ),
    Queue(
        "default",
        exchange=task_exchange,
        routing_key="task.default",
        durable=True,
        queue_arguments={"x-dead-letter-exchange": dead_letter_exchange.name},
    ),
    Queue(
        "low_priority",
        exchange=task_exchange,
        routing_key="task.low",
        durable=True,
        queue_arguments={"x-dead-letter-exchange": dead_letter_exchange.name},
    ),
    Queue(
        "dead_letter",
        exchange=dead_letter_exchange,
        routing_key="task.dead",
        durable=True,
    ),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = task_exchange.name
celery_app.conf.task_default_exchange_type = task_exchange.type
celery_app.conf.task_default_routing_key = "task.default"
celery_app.conf.task_default_delivery_mode = "persistent"

# Configuración
is_redis_backend = CELERY_RESULT_BACKEND.startswith("redis")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos (default, se sobrescribe por tarea)
    task_soft_time_limit=240,  # 4 minutos (default, se sobrescribe por tarea)
    worker_prefetch_multiplier=2,  # Optimizado: de 1 a 2 para mejor throughput
    worker_max_tasks_per_child=1000,

    # Configuración de reliability (global para todas las tareas)
    task_acks_late=True,  # Acknowledge después de completar (no al recibir)
    task_reject_on_worker_lost=True,  # Reintentar si worker muere

    broker_heartbeat=30,
    broker_pool_limit=10,
    broker_connection_timeout=10,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
        "max_retries": 5,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },

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
    } if is_redis_backend else {},

    # No fallar si el backend no está disponible inmediatamente
    result_backend_always_retry=True,
    result_backend_max_retries=10,
)

# Importar tasks
from celery_app import tasks

# Configurar routing de tareas a colas específicas
# ALTA PRIORIDAD: Tareas críticas y de baja latencia
# DEFAULT: Tareas normales
# BAJA PRIORIDAD: Tareas pesadas o no críticas
celery_app.conf.task_routes = {
    # Cola de alta prioridad (tareas críticas)
    'celery_app.tasks.update_prices': {'queue': 'high_priority', 'routing_key': 'task.high'},
    'celery_app.tasks.update_trm': {'queue': 'high_priority', 'routing_key': 'task.high'},
    'celery_app.tasks.run_trading_bot': {'queue': 'high_priority', 'routing_key': 'task.high'},
    'celery_app.tasks.send_notification': {'queue': 'high_priority', 'routing_key': 'task.high'},

    # Cola default (tareas normales)
    'celery_app.tasks.analyze_spread_opportunities': {'queue': 'default', 'routing_key': 'task.default'},
    'celery_app.tasks.analyze_arbitrage': {'queue': 'default', 'routing_key': 'task.default'},

    # Cola de baja prioridad (tareas pesadas)
    'celery_app.tasks.retrain_ml_model': {'queue': 'low_priority', 'routing_key': 'task.low'},
    'celery_app.tasks.cleanup_old_data': {'queue': 'low_priority', 'routing_key': 'task.low'},
}

# Configurar tareas programadas (Celery Beat)
celery_app.conf.beat_schedule = {
    # Actualizar precios cada 30 segundos (optimizado desde 10s)
    # Reducción de carga: de 8,640 a 2,880 ejecuciones/día (-67%)
    "update-prices": {
        "task": "celery_app.tasks.update_prices",
        "schedule": 30.0,  # Cambio: 10s → 30s
    },
    # Actualizar TRM cada 5 minutos (sin cambios - frecuencia adecuada)
    "update-trm": {
        "task": "celery_app.tasks.update_trm",
        "schedule": settings.TRM_UPDATE_INTERVAL,
    },
    # Analizar oportunidades de spread cada 60 segundos (optimizado desde 30s)
    # Reducción de carga: de 2,880 a 1,440 ejecuciones/día (-50%)
    "analyze-spread": {
        "task": "celery_app.tasks.analyze_spread_opportunities",
        "schedule": 60.0,  # Cambio: 30s → 60s
    },
    # Analizar arbitrajes Spot-P2P cada 2 minutos (sin cambios)
    "analyze-arbitrage": {
        "task": "celery_app.tasks.analyze_arbitrage",
        "schedule": 120.0,
    },
    # Ejecutar bot de trading cada minuto (sin cambios - crítico para trading)
    "run-trading-bot": {
        "task": "celery_app.tasks.run_trading_bot",
        "schedule": 60.0,
    },
    # Re-entrenar modelo ML cada 24 horas (medianoche UTC)
    "retrain-ml-model": {
        "task": "celery_app.tasks.retrain_ml_model",
        "schedule": crontab(hour=0, minute=0),
    },
    # Limpiar datos antiguos cada semana (domingo 3am UTC)
    "cleanup-old-data": {
        "task": "celery_app.tasks.cleanup_old_data",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Tarea de debug"""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok"}
# Signal handlers para métricas

_task_start_times = {}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handler ejecutado antes de una tarea"""
    _task_start_times[task_id] = time.time()
    task_obj = task or sender
    task_name = getattr(task_obj, "name", "unknown")
    
    # Registrar métrica de tarea iniciada
    try:
        metrics.track_celery_task(task_name, status="started")
        celery_tasks_active.labels(task_name=task_name).inc()
    except Exception as e:
        logger.warning("Failed to track Celery task start", error=str(e))

    delivery_info = {}
    if task_obj and getattr(task_obj, "request", None):
        delivery_info = getattr(task_obj.request, "delivery_info", {}) or {}

    queue_name = (
        delivery_info.get("routing_key")
        or delivery_info.get("queue")
        or celery_app.conf.task_default_queue
    )
    rabbitmq_messages_consumed_total.labels(queue=queue_name or "unknown").inc()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handler ejecutado después de una tarea"""
    start_time = _task_start_times.pop(task_id, None)
    duration = time.time() - start_time if start_time else None
    task_obj = task or sender
    task_name = getattr(task_obj, "name", "unknown")
    
    # Registrar métrica de tarea completada
    try:
        metrics.track_celery_task(task_name, duration=duration, status="succeeded")
        celery_tasks_active.labels(task_name=task_name).dec()
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
        metrics.track_celery_task(task_name, duration=duration, status="failed")
        celery_tasks_active.labels(task_name=task_name).dec()
    except Exception as e:
        logger.warning("Failed to track Celery task failure", error=str(e))


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handler ejecutado cuando una tarea se reintenta"""
    # Registrar métrica de reintento
    try:
        celery_task_retries_total.labels(task_name=sender.name).inc()
    except Exception as e:
        logger.warning("Failed to track Celery task retry", error=str(e))


@before_task_publish.connect
def before_task_publish_handler(sender=None, headers=None, body=None, **kwargs):
    """Registrar métricas cuando se publica un mensaje en RabbitMQ."""
    routing_key = (
        (headers or {}).get("routing_key")
        or kwargs.get("routing_key")
        or celery_app.conf.task_default_routing_key
    )
    exchange = (
        (headers or {}).get("exchange")
        or kwargs.get("exchange")
        or celery_app.conf.task_default_exchange
    )

    rabbitmq_messages_published_total.labels(
        exchange=exchange or "unknown",
        routing_key=routing_key or "unknown",
    ).inc()


if __name__ == "__main__":
    celery_app.start()
