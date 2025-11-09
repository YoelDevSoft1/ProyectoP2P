"""
Cliente Redis con pool de conexiones y reconexión automática.
Mejora el rendimiento y la robustez del sistema.
"""
import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from typing import Optional
import structlog
import asyncio
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
        self._loop_id: Optional[int] = None  # Track which asyncio loop owns the pool
    
    async def initialize(self) -> bool:
        """Inicializar pool de conexiones Redis"""
        try:
            current_loop = asyncio.get_running_loop()
            self._loop_id = id(current_loop)
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
    
    async def get_client(self) -> Optional[aioredis.Redis]:
        """Obtener cliente Redis del pool"""
        try:
            # Verificar que hay un event loop corriendo
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No hay event loop corriendo, no podemos usar Redis
                logger.warning("No running event loop, cannot get Redis client")
                return None
            
            # Si el pool fue creado con otro loop (por ejemplo, cada llamada a asyncio.run
            # en los workers de Celery crea un nuevo loop), debemos reconstruirlo
            if self._loop_id and self._loop_id != id(loop):
                logger.debug(
                    "Detected event loop change, rebuilding Redis pool",
                    previous_loop_id=self._loop_id,
                    new_loop_id=id(loop),
                )
                await self.close()
            
            if self._client is None:
                # Intentar inicializar dentro del event loop actual
                initialized = await self.initialize()
                if not initialized:
                    return None
            
            # Verificar salud periódicamente
            try:
                await self._ensure_healthy()
            except RuntimeError as e:
                # Si el event loop se cerró durante la verificación, retornar None
                if "Event loop is closed" in str(e) or "no running event loop" in str(e).lower():
                    logger.warning("Event loop closed during health check, Redis unavailable")
                    self._client = None
                    self._pool = None
                    self._is_healthy = False
                    return None
                raise
            
            return self._client
        except RuntimeError as e:
            # Si el event loop está cerrado, no podemos usar Redis
            if "Event loop is closed" in str(e) or "no running event loop" in str(e).lower():
                logger.debug("Event loop is closed, Redis unavailable", error=str(e))
                # Limpiar el cliente y pool para forzar reinicialización en el próximo uso
                self._client = None
                self._pool = None
                self._is_healthy = False
                return None
            raise
        except Exception as e:
            logger.error("Unexpected error getting Redis client", error=str(e))
            return None
    
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
        try:
            if self._client:
                await self._client.close()
                self._client = None
            
            if self._pool:
                await self._pool.aclose()
                self._pool = None
        finally:
            self._is_healthy = False
            self._loop_id = None
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
                info_server = await client.info("server")
                info_memory = await client.info("memory")
                info_stats = await client.info("stats")
                
                pool_info["redis_version"] = info_server.get("redis_version")
                pool_info["used_memory_human"] = info_memory.get("used_memory_human")
                pool_info["used_memory"] = info_memory.get("used_memory", 0)
                pool_info["used_memory_peak"] = info_memory.get("used_memory_peak", 0)
                pool_info["mem_fragmentation_ratio"] = info_memory.get("mem_fragmentation_ratio", 0)
                pool_info["connected_clients"] = info_server.get("connected_clients", 0)
                pool_info["keyspace_hits"] = info_stats.get("keyspace_hits", 0)
                pool_info["keyspace_misses"] = info_stats.get("keyspace_misses", 0)
                pool_info["evicted_keys"] = info_stats.get("evicted_keys", 0)
                
                # Actualizar métricas de memoria y estadísticas
                from app.core.metrics import (
                    redis_memory_used,
                    redis_memory_peak,
                    redis_memory_fragmentation_ratio,
                    redis_connected_clients,
                    redis_evicted_keys_total
                )
                
                if info_memory.get("used_memory"):
                    redis_memory_used.set(info_memory.get("used_memory", 0))
                    redis_memory_peak.set(info_memory.get("used_memory_peak", 0))
                    redis_memory_fragmentation_ratio.set(info_memory.get("mem_fragmentation_ratio", 0))
                
                if info_server.get("connected_clients"):
                    redis_connected_clients.set(info_server.get("connected_clients", 0))
                
                if info_stats.get("evicted_keys"):
                    # Nota: Esta métrica es acumulativa, pero Redis solo da el total
                    # Para tracking preciso, necesitaríamos trackear cambios
                    pass
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

