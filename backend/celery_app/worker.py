"""
Celery worker para tareas asíncronas.
"""
from celery import Celery
from celery.schedules import crontab
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Crear instancia de Celery
celery_app = Celery(
    "p2p_trading",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL
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


if __name__ == "__main__":
    celery_app.start()
