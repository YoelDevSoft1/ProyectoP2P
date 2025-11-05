"""
Servicio de tasas de cambio con cache y fuentes combinadas.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

import structlog

from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.trm_service import TRMService

logger = structlog.get_logger()


class FXService:
    """Obtiene tasas de cambio USD/fiat usando TRM, mercado y valores de respaldo."""

    def __init__(
        self,
        p2p_service: Optional[BinanceService] = None,
        spot_service: Optional[BinanceSpotService] = None,
        trm_service: Optional[TRMService] = None,
        cache_ttl_seconds: Optional[int] = None,
    ) -> None:
        self.p2p_service = p2p_service or BinanceService()
        self.spot_service = spot_service or BinanceSpotService()
        self.trm_service = trm_service or TRMService()

        ttl_seconds = cache_ttl_seconds or settings.FX_CACHE_TTL_SECONDS
        self._cache_ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, Dict[str, float]] = {}

    async def get_rate(self, fiat: str) -> float:
        """
        Obtener tasa USD -> fiat.

        Args:
            fiat: moneda (COP, VES, etc.)
        """
        fiat_code = fiat.upper()
        now = datetime.utcnow()

        cached = self._cache.get(fiat_code)
        if cached:
            cached_ts = cached.get("ts")
            if isinstance(cached_ts, datetime) and now - cached_ts < self._cache_ttl:
                return cached["value"]

        if fiat_code == "USD":
            rate = 1.0
        elif fiat_code == "COP":
            rate = await self.trm_service.get_current_trm()
        else:
            rate = await self._get_rate_from_market(fiat_code)

        if rate <= 0:
            rate = settings.FX_FALLBACK_RATES.get(fiat_code, 1.0)
            logger.warning(
                "Using fallback FX rate",
                fiat=fiat_code,
                rate=rate,
            )

        self._cache[fiat_code] = {"value": rate, "ts": now}
        return rate

    async def _get_rate_from_market(self, fiat: str) -> float:
        """
        Derivar tasa desde Binance P2P vs Spot.
        """
        try:
            sell_quote = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat=fiat,
                trade_type="SELL",
                return_details=True,
            )
            if not sell_quote:
                return settings.FX_FALLBACK_RATES.get(fiat, 1.0)

            spot_price = await self.spot_service.get_spot_price("USDCUSDT")
            if spot_price <= 0:
                spot_price = 1.0

            implicit_rate = sell_quote["price"] / spot_price
            logger.info(
                "FX rate derived from market",
                fiat=fiat,
                rate=implicit_rate,
                p2p_price=sell_quote["price"],
                spot_price=spot_price,
            )
            return implicit_rate
        except Exception as exc:
            logger.error(
                "Error deriving FX rate from market",
                fiat=fiat,
                error=str(exc),
            )
            return settings.FX_FALLBACK_RATES.get(fiat, 1.0)
