"""
Cliente Redis con pool de conexiones y reconexión automática.
Mejora el rendimiento y la robustez del sistema.
"""
import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from typing import Optional
import structlog
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.metrics import metrics

logger = structlog.get_logger()


class RedisPool:
    """
    Pool de conexiones Redis con reconexión automática y health checks.
    """
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(seconds=30)
        self._is_healthy = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
    
    async def initialize(self) -> bool:
        """Inicializar pool de conexiones Redis"""
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            self._client = aioredis.Redis(connection_pool=self._pool)
            
            # Verificar conexión
            await self._client.ping()
            self._is_healthy = True
            self._reconnect_attempts = 0
            self._last_health_check = datetime.utcnow()
            
            logger.info("Redis pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Redis pool", error=str(e))
            self._is_healthy = False
            metrics.track_redis_operation("ping", 0.0, "error")
            return False
    
    async def get_client(self) -> aioredis.Redis:
        """Obtener cliente Redis del pool"""
        if self._client is None:
            await self.initialize()
        
        # Verificar salud periódicamente
        await self._ensure_healthy()
        
        return self._client
    
    async def _ensure_healthy(self) -> bool:
        """Asegurar que el pool está saludable"""
        # Si ya verificamos recientemente y está saludable, retornar
        if (
            self._is_healthy 
            and self._last_health_check 
            and (datetime.utcnow() - self._last_health_check) < self._health_check_interval
        ):
            return True
        
        # Verificar salud
        try:
            if self._client is None:
                return await self.initialize()
            
            start_time = datetime.utcnow()
            await self._client.ping()
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self._is_healthy = True
            self._reconnect_attempts = 0
            self._last_health_check = datetime.utcnow()
            metrics.track_redis_operation("ping", duration, "success")
            
            return True
            
        except Exception as e:
            logger.warning("Redis health check failed", error=str(e))
            self._is_healthy = False
            metrics.track_redis_operation("ping", 0.0, "error")
            
            # Intentar reconectar
            if self._reconnect_attempts < self._max_reconnect_attempts:
                self._reconnect_attempts += 1
                logger.info(
                    "Attempting to reconnect Redis",
                    attempt=self._reconnect_attempts,
                    max_attempts=self._max_reconnect_attempts
                )
                await asyncio.sleep(1 * self._reconnect_attempts)  # Backoff exponencial
                return await self.initialize()
            
            return False
    
    async def close(self):
        """Cerrar pool de conexiones"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.aclose()
            self._pool = None
        
        self._is_healthy = False
        logger.info("Redis pool closed")
    
    async def health_check(self) -> dict:
        """Verificar salud del pool Redis"""
        try:
            start_time = datetime.utcnow()
            client = await self.get_client()
            await client.ping()
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Obtener información del pool
            pool_info = {
                "status": "healthy",
                "latency_ms": round(duration * 1000, 2),
                "pool_size": self._pool.size if hasattr(self._pool, 'size') else None,
                "created_connections": self._pool.created_connections if hasattr(self._pool, 'created_connections') else None,
                "available_connections": self._pool.available_connections if hasattr(self._pool, 'available_connections') else None,
            }
            
            # Intentar obtener info de Redis
            try:
                info = await client.info("server")
                pool_info["redis_version"] = info.get("redis_version")
                pool_info["used_memory_human"] = info.get("used_memory_human")
                pool_info["connected_clients"] = info.get("connected_clients")
            except Exception:
                pass  # Si no podemos obtener info, no es crítico
            
            metrics.track_redis_operation("health_check", duration, "success")
            return pool_info
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            metrics.track_redis_operation("health_check", 0.0, "error")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @property
    def is_healthy(self) -> bool:
        """Verificar si el pool está saludable"""
        return self._is_healthy


# Instancia global del pool
redis_pool = RedisPool()


# Dependency para FastAPI
async def get_redis_pool() -> aioredis.Redis:
    """
    Dependency que proporciona cliente Redis del pool.
    """
    return await redis_pool.get_client()


# Importar asyncio para sleep
import asyncio

