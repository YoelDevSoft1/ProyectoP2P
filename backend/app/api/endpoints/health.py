"""
Endpoints de health check.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis.asyncio as aioredis
from typing import Dict, Any

from app.core.database import get_db, get_redis
from app.core.database_async import check_db_health, get_async_db
from app.core.redis_pool import redis_pool
from app.core.rabbitmq_health import rabbitmq_health
from app.core.celery_monitor import celery_monitor
from app.core.config import settings
from app.core.metrics import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Health check endpoint completo.
    Verifica conexión a PostgreSQL, Redis, RabbitMQ y Celery.
    """
    status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "services": {}
    }

    # Check PostgreSQL (síncrono)
    try:
        db.execute(text("SELECT 1"))
        status["services"]["postgresql"] = {"status": "connected"}
    except Exception as e:
        status["services"]["postgresql"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"

    # Check PostgreSQL (asíncrono)
    try:
        db_health = await check_db_health()
        status["services"]["postgresql_async"] = db_health
        if db_health.get("status") != "healthy":
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["postgresql_async"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"

    # Check Redis
    try:
        redis_health = await redis_pool.health_check()
        status["services"]["redis"] = redis_health
        if redis_health.get("status") != "healthy":
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["redis"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"

    # Check RabbitMQ
    try:
        rabbitmq_health_result = await rabbitmq_health.check_health()
        status["services"]["rabbitmq"] = rabbitmq_health_result
        if rabbitmq_health_result.get("status") != "healthy":
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["rabbitmq"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"

    # Check Celery (síncrono)
    try:
        celery_health = celery_monitor.check_health()
        status["services"]["celery"] = celery_health
        if celery_health.get("status") not in ("healthy", "degraded"):
            status["status"] = "degraded"
    except Exception as e:
        status["services"]["celery"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"

    return status


@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    """Health check específico de base de datos"""
    try:
        result = db.execute(text("SELECT COUNT(*) FROM trades")).scalar()
        return {
            "status": "healthy",
            "total_trades": result,
            "database": "postgresql"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health/redis")
async def redis_health():
    """Health check específico de Redis"""
    return await redis_pool.health_check()


@router.get("/health/rabbitmq")
async def rabbitmq_health_endpoint():
    """Health check específico de RabbitMQ"""
    return await rabbitmq_health.check_health()


@router.get("/health/celery")
async def celery_health():
    """Health check específico de Celery"""
    return celery_monitor.check_health()


@router.get("/metrics")
async def metrics_endpoint(response: Response):
    """
    Endpoint de métricas Prometheus.
    """
    response.headers["Content-Type"] = CONTENT_TYPE_LATEST
    return generate_latest()
