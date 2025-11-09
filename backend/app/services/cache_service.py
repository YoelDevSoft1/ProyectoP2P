"""
Cache Service - Servicio de caché con Redis para optimizar consultas
Reduce llamadas a APIs externas y mejora el rendimiento del sistema
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import logging

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis_pool import redis_pool
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


class CacheService:
    """
    Servicio de caché con Redis

    Funcionalidades:
    - Cache con TTL configurable
    - Cache de precios de mercado
    - Cache de análisis de arbitraje
    - Cache de liquidez
    - Invalidación automática
    - Fallback si Redis no está disponible
    """

    # TTL defaults (segundos)
    TTL_PRICE = 5  # Precios: 5 segundos
    TTL_MARKET_DEPTH = 10  # Profundidad de mercado: 10 segundos
    TTL_ARBITRAGE = 15  # Oportunidades de arbitraje: 15 segundos
    TTL_TRM = 300  # TRM: 5 minutos
    TTL_LIQUIDITY = 20  # Análisis de liquidez: 20 segundos
    TTL_ML_PREDICTION = 60  # Predicciones ML: 1 minuto

    def __init__(self):
        """Inicializar servicio de cache usando el pool compartido de Redis"""
        self.redis: Optional[aioredis.Redis] = None
        self._redis_available = False
        self._last_health_check = datetime.utcnow()
        self._health_check_interval = timedelta(seconds=30)

    async def connect(self) -> bool:
        """Conectar a Redis usando el pool compartido"""
        try:
            # Usar el pool compartido de Redis en lugar de crear una nueva conexión
            self.redis = await redis_pool.get_client()
            
            if self.redis is None:
                self._redis_available = False
                logger.warning("Redis pool not available for cache service")
                return False

            # Verificar conexión
            await self.redis.ping()
            self._redis_available = True
            self._last_health_check = datetime.utcnow()
            logger.info("Redis cache connected successfully using shared pool")
            return True

        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Running without cache.")
            self._redis_available = False
            return False

    async def _ensure_connected(self) -> bool:
        """Asegurar que hay conexión a Redis"""
        # Si no tenemos cliente, intentar obtenerlo del pool
        if self.redis is None:
            try:
                self.redis = await redis_pool.get_client()
                if self.redis is None:
                    self._redis_available = False
                    return False
            except Exception:
                self._redis_available = False
                return False
        
        # Health check periódico
        if datetime.utcnow() - self._last_health_check > self._health_check_interval:
            try:
                await self.redis.ping()
                self._redis_available = True
                self._last_health_check = datetime.utcnow()
            except Exception:
                self._redis_available = False
                # Intentar reconectar
                self.redis = await redis_pool.get_client()
                if self.redis:
                    try:
                        await self.redis.ping()
                        self._redis_available = True
                        self._last_health_check = datetime.utcnow()
                    except Exception:
                        self._redis_available = False
                        return False
                else:
                    return False

        return self._redis_available

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del cache

        Args:
            key: Clave del cache

        Returns:
            Valor cacheado o None si no existe
        """
        if not await self._ensure_connected():
            metrics.track_cache_miss(key.split(':')[0] if ':' in key else "unknown")
            return None

        import time
        start_time = time.time()
        
        try:
            value = await self.redis.get(key)
            duration = time.time() - start_time
            metrics.track_redis_operation("get", duration, "success")

            if value is None:
                logger.debug(f"Cache MISS: {key}")
                metrics.track_cache_miss(key.split(':')[0] if ':' in key else "unknown")
                return None

            logger.debug(f"Cache HIT: {key}")
            metrics.track_cache_hit(key.split(':')[0] if ':' in key else "unknown")

            # Deserializar JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Si no es JSON, devolver como string
                return value

        except RedisError as e:
            duration = time.time() - start_time
            metrics.track_redis_operation("get", duration, "error")
            logger.warning(f"Redis GET error for key {key}: {str(e)}")
            self._redis_available = False
            metrics.track_cache_miss(key.split(':')[0] if ':' in key else "unknown")
            return None
        except Exception as e:
            duration = time.time() - start_time
            metrics.track_redis_operation("get", duration, "error")
            logger.error(f"Unexpected cache GET error: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guardar valor en cache

        Args:
            key: Clave del cache
            value: Valor a guardar
            ttl: Time to live en segundos (opcional)

        Returns:
            True si se guardó exitosamente
        """
        if not await self._ensure_connected():
            return False

        import time
        start_time = time.time()
        
        try:
            # Serializar a JSON si no es string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)

            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)

            duration = time.time() - start_time
            metrics.track_redis_operation("set", duration, "success")
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except RedisError as e:
            duration = time.time() - start_time
            metrics.track_redis_operation("set", duration, "error")
            logger.warning(f"Redis SET error for key {key}: {str(e)}")
            self._redis_available = False
            return False
        except Exception as e:
            duration = time.time() - start_time
            metrics.track_redis_operation("set", duration, "error")
            logger.error(f"Unexpected cache SET error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Eliminar valor del cache

        Args:
            key: Clave a eliminar

        Returns:
            True si se eliminó
        """
        if not await self._ensure_connected():
            return False

        try:
            await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Eliminar todas las claves que coincidan con un patrón

        Args:
            pattern: Patrón de claves (ej: "price:USDT:*")

        Returns:
            Número de claves eliminadas
        """
        if not await self._ensure_connected():
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache DELETE pattern {pattern}: {deleted} keys")
                return deleted

            return 0
        except Exception as e:
            logger.warning(f"Cache DELETE pattern error: {str(e)}")
            return 0

    # === MÉTODOS ESPECÍFICOS PARA EL DOMINIO ===

    async def get_price(
        self,
        asset: str,
        fiat: str,
        trade_type: str
    ) -> Optional[float]:
        """Obtener precio cacheado"""
        key = f"price:{asset}:{fiat}:{trade_type}"
        return await self.get(key)

    async def set_price(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        price: float,
        ttl: Optional[int] = None
    ) -> bool:
        """Guardar precio en cache"""
        key = f"price:{asset}:{fiat}:{trade_type}"
        ttl = ttl or self.TTL_PRICE
        return await self.set(key, price, ttl)

    async def get_market_depth(
        self,
        asset: str,
        fiat: str,
        trade_type: str
    ) -> Optional[Dict]:
        """Obtener profundidad de mercado cacheada"""
        key = f"depth:{asset}:{fiat}:{trade_type}"
        return await self.get(key)

    async def set_market_depth(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        depth_data: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Guardar profundidad de mercado en cache"""
        key = f"depth:{asset}:{fiat}:{trade_type}"
        ttl = ttl or self.TTL_MARKET_DEPTH
        return await self.set(key, depth_data, ttl)

    async def get_arbitrage_opportunity(
        self,
        strategy: str,
        asset: str,
        fiat: str
    ) -> Optional[Dict]:
        """Obtener oportunidad de arbitraje cacheada"""
        key = f"arb:{strategy}:{asset}:{fiat}"
        return await self.get(key)

    async def set_arbitrage_opportunity(
        self,
        strategy: str,
        asset: str,
        fiat: str,
        opportunity: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Guardar oportunidad de arbitraje en cache"""
        key = f"arb:{strategy}:{asset}:{fiat}"
        ttl = ttl or self.TTL_ARBITRAGE
        return await self.set(key, opportunity, ttl)

    async def invalidate_prices(self, asset: Optional[str] = None) -> int:
        """Invalidar todos los precios cacheados (o de un asset específico)"""
        pattern = f"price:{asset or '*'}:*"
        return await self.delete_pattern(pattern)

    async def invalidate_arbitrage(self) -> int:
        """Invalidar todas las oportunidades de arbitraje cacheadas"""
        return await self.delete_pattern("arb:*")

    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        if not await self._ensure_connected():
            return {
                "available": False,
                "error": "Redis not available"
            }

        try:
            info = await self.redis.info("stats")
            keyspace = await self.redis.info("keyspace")

            total_keys = 0
            if keyspace:
                for db_info in keyspace.values():
                    total_keys += db_info.get("keys", 0)

            return {
                "available": True,
                "total_keys": total_keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "total_connections": info.get("total_connections_received", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calcular tasa de aciertos del cache"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    async def close(self):
        """Cerrar conexión a Redis"""
        # No cerramos el cliente ya que es compartido por el pool
        # El pool se encargará de cerrar las conexiones cuando sea necesario
        self.redis = None
        self._redis_available = False
        logger.info("Redis cache service closed (using shared pool)")


# Singleton global
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Obtener instancia singleton del servicio de cache"""
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()

    return _cache_service
