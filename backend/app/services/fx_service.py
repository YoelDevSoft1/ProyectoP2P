"""
Servicio de tasas de cambio con cache y fuentes combinadas.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog

from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.trm_service import TRMService

logger = structlog.get_logger()

# Importación opcional de Alpha Vantage
try:
    from app.services.alpha_vantage_service import AlphaVantageService
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False
    AlphaVantageService = None


class FXService:
    """Obtiene tasas de cambio USD/fiat usando TRM, mercado y valores de respaldo."""

    def __init__(
        self,
        p2p_service: Optional[BinanceService] = None,
        spot_service: Optional[BinanceSpotService] = None,
        trm_service: Optional[TRMService] = None,
        cache_ttl_seconds: Optional[int] = None,
        alpha_vantage_service: Optional[Any] = None,
    ) -> None:
        self.p2p_service = p2p_service or BinanceService()
        self.spot_service = spot_service or BinanceSpotService()
        self.trm_service = trm_service or TRMService()

        # Alpha Vantage (opcional)
        if ALPHA_VANTAGE_AVAILABLE and settings.ALPHA_VANTAGE_ENABLED:
            try:
                self.alpha_vantage = alpha_vantage_service or AlphaVantageService()
                if not self.alpha_vantage.enabled:
                    self.alpha_vantage = None
                    logger.debug("Alpha Vantage service disabled (no API key)")
            except Exception as e:
                logger.warning("Failed to initialize Alpha Vantage", error=str(e))
                self.alpha_vantage = None
        else:
            self.alpha_vantage = None

        ttl_seconds = cache_ttl_seconds or settings.FX_CACHE_TTL_SECONDS
        self._cache_ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, Dict[str, float]] = {}

    async def get_rate(self, fiat: str) -> float:
        """
        Obtener tasa USD -> fiat con validación cruzada.
        
        Orden de prioridad:
        1. TRM (para COP) - fuente oficial
        2. Alpha Vantage (validación/backup)
        3. Binance P2P (para otras monedas)
        4. Fallback (valores por defecto)

        Args:
            fiat: moneda (COP, VES, etc.)
        """
        fiat_code = fiat.upper()
        now = datetime.utcnow()

        # Verificar caché
        cached = self._cache.get(fiat_code)
        if cached:
            cached_ts = cached.get("ts")
            if isinstance(cached_ts, datetime) and now - cached_ts < self._cache_ttl:
                return cached["value"]

        rate = None
        source = "unknown"

        # 1. USD siempre es 1.0
        if fiat_code == "USD":
            rate = 1.0
            source = "fixed"
        
        # 2. COP: Usar TRM (fuente oficial) con validación Alpha Vantage
        elif fiat_code == "COP":
            try:
                rate = await self.trm_service.get_current_trm()
                source = "trm"
                
                # Validar con Alpha Vantage si está disponible
                if self.alpha_vantage and rate > 0:
                    try:
                        av_rate = await self.alpha_vantage.get_forex_realtime("USD", "COP")
                        if av_rate and av_rate > 0:
                            # Calcular diferencia porcentual
                            diff_percent = abs(rate - av_rate) / rate * 100
                            
                            if diff_percent > 2.0:  # Más del 2% de diferencia
                                logger.warning(
                                    "Large discrepancy between TRM and Alpha Vantage",
                                    trm_rate=rate,
                                    alpha_vantage_rate=av_rate,
                                    diff_percent=round(diff_percent, 2),
                                    fiat=fiat_code
                                )
                            else:
                                logger.debug(
                                    "TRM validated with Alpha Vantage",
                                    trm_rate=rate,
                                    alpha_vantage_rate=av_rate,
                                    diff_percent=round(diff_percent, 2)
                                )
                    except Exception as e:
                        logger.debug(
                            "Alpha Vantage validation failed (non-critical)",
                            error=str(e),
                            fiat=fiat_code
                        )
            except Exception as e:
                logger.warning("TRM service failed", error=str(e), fiat=fiat_code)
                rate = None
        
        # 3. Otras monedas: Intentar Alpha Vantage primero, luego Binance P2P
        else:
            # Intentar Alpha Vantage primero (más confiable para Forex)
            if self.alpha_vantage:
                try:
                    av_rate = await self.alpha_vantage.get_forex_realtime("USD", fiat_code)
                    if av_rate and av_rate > 0:
                        rate = av_rate
                        source = "alpha_vantage"
                        logger.debug(
                            "FX rate from Alpha Vantage",
                            fiat=fiat_code,
                            rate=rate
                        )
                except Exception as e:
                    logger.debug(
                        "Alpha Vantage failed, trying Binance P2P",
                        error=str(e),
                        fiat=fiat_code
                    )
            
            # Si Alpha Vantage falló o no está disponible, usar Binance P2P
            if rate is None or rate <= 0:
                try:
                    rate = await self._get_rate_from_market(fiat_code)
                    if rate and rate > 0:
                        source = "binance_p2p"
                except Exception as e:
                    logger.warning(
                        "Binance P2P rate failed",
                        error=str(e),
                        fiat=fiat_code
                    )
                    rate = None

        # 4. Fallback si todo falla
        if rate is None or rate <= 0:
            rate = settings.FX_FALLBACK_RATES.get(fiat_code, 1.0)
            source = "fallback"
            logger.warning(
                "Using fallback FX rate",
                fiat=fiat_code,
                rate=rate,
                source=source
            )
        else:
            logger.info(
                "FX rate obtained",
                fiat=fiat_code,
                rate=rate,
                source=source
            )

        # Guardar en caché
        self._cache[fiat_code] = {"value": rate, "ts": now, "source": source}
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
