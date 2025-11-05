"""
Binance Service con Cache - Versión optimizada con Redis
Extiende BinanceService agregando cache inteligente con Redis
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import structlog

from app.services.binance_service import BinanceService
from app.services.cache_service import get_cache_service, CacheService
from app.core.config import settings

logger = structlog.get_logger()


class BinanceServiceCached(BinanceService):
    """
    Servicio de Binance P2P con cache Redis inteligente

    Mejoras:
    - Cache distribuido con Redis
    - Fallback a cache en memoria
    - Invalidación inteligente
    - Métricas de performance
    """

    def __init__(self) -> None:
        super().__init__()
        self.cache: Optional[CacheService] = None
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0

    async def _ensure_cache(self) -> CacheService:
        """Asegurar que el servicio de cache está disponible"""
        if self.cache is None:
            self.cache = await get_cache_service()
        return self.cache

    async def get_best_price(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        trade_type: str = "BUY",
        pay_types: Optional[List[str]] = None,
        return_details: bool = False,
        rows: int = 10,
    ) -> Any:
        """
        Obtener el mejor precio con cache Redis inteligente

        Flujo:
        1. Intentar obtener de Redis cache
        2. Si no está, intentar cache en memoria (fallback)
        3. Si no está, consultar API
        4. Guardar en ambos caches
        """
        self._total_requests += 1

        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        trade_type_upper = trade_type.upper()

        # Intentar Redis cache primero
        cache = await self._ensure_cache()

        cached_data = await cache.get_price(asset_upper, fiat_upper, trade_type_upper)

        if cached_data is not None:
            self._cache_hits += 1
            logger.debug(
                "Redis cache HIT",
                asset=asset_upper,
                fiat=fiat_upper,
                trade_type=trade_type_upper,
                hit_rate=self.get_cache_hit_rate()
            )

            if return_details:
                return cached_data
            else:
                return cached_data.get("price", 0.0) if isinstance(cached_data, dict) else cached_data

        # Cache miss - consultar API
        self._cache_misses += 1
        logger.debug(
            "Redis cache MISS - consulting API",
            asset=asset_upper,
            fiat=fiat_upper,
            trade_type=trade_type_upper
        )

        # Usar método del padre (que tiene su propio cache en memoria como fallback)
        result = await super().get_best_price(
            asset=asset,
            fiat=fiat,
            trade_type=trade_type,
            pay_types=pay_types,
            return_details=True,  # Siempre obtener detalles para cachear
            rows=rows
        )

        if result:
            # Guardar en Redis cache
            await cache.set_price(
                asset_upper,
                fiat_upper,
                trade_type_upper,
                result,
                ttl=cache.TTL_PRICE
            )

            logger.debug(
                "Price cached in Redis",
                asset=asset_upper,
                fiat=fiat_upper,
                trade_type=trade_type_upper,
                price=result.get("price") if isinstance(result, dict) else result
            )

        # Retornar en el formato solicitado
        if return_details:
            return result
        else:
            return result.get("price", 0.0) if isinstance(result, dict) else result

    async def get_market_depth(
        self,
        asset: str,
        fiat: str,
        trade_type: str = "BUY",
        limit: int = 20
    ) -> List[Dict]:
        """
        Obtener profundidad de mercado con cache
        """
        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        trade_type_upper = trade_type.upper()

        # Intentar obtener de cache
        cache = await self._ensure_cache()
        cached_depth = await cache.get_market_depth(asset_upper, fiat_upper, trade_type_upper)

        if cached_depth:
            logger.debug(
                "Market depth cache HIT",
                asset=asset_upper,
                fiat=fiat_upper,
                trade_type=trade_type_upper
            )
            return cached_depth

        # Cache miss - consultar API
        ads = await self.get_p2p_ads(
            asset=asset,
            fiat=fiat,
            trade_type=trade_type,
            rows=limit
        )

        # Guardar en cache
        if ads:
            await cache.set_market_depth(
                asset_upper,
                fiat_upper,
                trade_type_upper,
                ads,
                ttl=cache.TTL_MARKET_DEPTH
            )

        return ads

    async def invalidate_cache(
        self,
        asset: Optional[str] = None,
        fiat: Optional[str] = None
    ) -> int:
        """
        Invalidar cache de precios

        Args:
            asset: Si se especifica, invalida solo ese asset
            fiat: Si se especifica, invalida solo ese fiat

        Returns:
            Número de claves invalidadas
        """
        cache = await self._ensure_cache()

        if asset:
            count = await cache.invalidate_prices(asset.upper())
            logger.info(f"Invalidated {count} cached prices for {asset}")
            return count
        else:
            count = await cache.invalidate_prices()
            logger.info(f"Invalidated {count} cached prices (all)")
            return count

    def get_cache_hit_rate(self) -> float:
        """Calcular tasa de aciertos del cache"""
        if self._total_requests == 0:
            return 0.0
        return round((self._cache_hits / self._total_requests) * 100, 2)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        cache = await self._ensure_cache()
        redis_stats = await cache.get_stats()

        return {
            "redis": redis_stats,
            "service": {
                "total_requests": self._total_requests,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate_percentage": self.get_cache_hit_rate()
            }
        }

    async def aclose(self) -> None:
        """Cerrar conexiones"""
        await super().aclose()

        if self.cache:
            await self.cache.close()
            logger.info("Cache service closed")


# Helper function para crear instancia cacheada
async def get_binance_service_cached() -> BinanceServiceCached:
    """Obtener instancia del servicio con cache"""
    service = BinanceServiceCached()
    await service._ensure_cache()
    return service
