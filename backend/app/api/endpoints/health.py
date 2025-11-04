"""
Endpoints de health check.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis.asyncio as aioredis

from app.core.database import get_db, get_redis
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Health check endpoint.
    Verifica conexión a PostgreSQL y Redis.
    """
    status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "services": {}
    }

    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        status["services"]["postgresql"] = "connected"
    except Exception as e:
        status["services"]["postgresql"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check Redis
    try:
        await redis.ping()
        status["services"]["redis"] = "connected"
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
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
