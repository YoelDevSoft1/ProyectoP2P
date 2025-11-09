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
async def metrics_endpoint():
    """
    Endpoint de métricas Prometheus.
    Retorna métricas en formato Prometheus (text/plain).
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    metrics_output = generate_latest()
    
    # Decodificar si es bytes
    if isinstance(metrics_output, bytes):
        content = metrics_output.decode('utf-8')
    else:
        content = metrics_output
    
    # Retornar Response con Content-Type correcto
    # CONTENT_TYPE_LATEST es "text/plain; version=0.0.4; charset=utf-8"
    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/endpoints")
async def list_endpoints():
    """
    Lista todos los endpoints disponibles en la API.
    Útil para descubrir y documentar todos los endpoints.
    """
    from fastapi.routing import APIRoute
    from app.main import app
    
    endpoints = []
    
    # Recorrer todas las rutas registradas
    for route in app.routes:
        # Solo procesar rutas APIRoute (endpoints reales)
        if isinstance(route, APIRoute):
            # Obtener métodos HTTP permitidos
            methods = list(route.methods) if hasattr(route, 'methods') else ['GET']
            
            # Filtrar métodos OPTIONS y HEAD
            methods = [m for m in methods if m not in ['OPTIONS', 'HEAD']]
            
            if not methods:
                continue
            
            # Obtener path
            path = route.path
            
            # Obtener tags
            tags = route.tags if hasattr(route, 'tags') and route.tags else []
            
            # Obtener nombre de la operación
            name = route.name if hasattr(route, 'name') else ""
            
            # Obtener descripción del endpoint
            description = ""
            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__doc__'):
                doc = route.endpoint.__doc__
                if doc:
                    # Tomar la primera línea de la docstring como descripción
                    description = doc.strip().split('\n')[0]
            
            # Obtener summary si existe
            summary = ""
            if hasattr(route, 'summary') and route.summary:
                summary = route.summary
            
            # Agregar endpoint a la lista
            for method in methods:
                endpoints.append({
                    "method": method,
                    "path": path,
                    "tags": tags,
                    "name": name,
                    "summary": summary,
                    "description": description,
                })
    
    # Ordenar por path y luego por método
    endpoints.sort(key=lambda x: (x['path'], x['method']))
    
    # Agrupar por tags
    endpoints_by_tag = {}
    for endpoint in endpoints:
        for tag in endpoint['tags']:
            if tag not in endpoints_by_tag:
                endpoints_by_tag[tag] = []
            endpoints_by_tag[tag].append(endpoint)
    
    return {
        "total": len(endpoints),
        "base_url": settings.API_V1_STR,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
        "endpoints": endpoints,
        "endpoints_by_tag": endpoints_by_tag,
    }
