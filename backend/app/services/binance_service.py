"""
Servicio para interactuar con Binance P2P API.

IMPORTANTE: Binance no tiene una API oficial pública para P2P.
Las operaciones P2P deben hacerse a través de la interfaz web.
Este servicio usa endpoints públicos de consulta de precios.

Para operaciones reales, se requiere:
1. Usar la API de Binance Spot para conversiones
2. O implementar web scraping (con precaución y respetando ToS)
3. O usar webhooks y automatización manual
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class BinanceService:
    """
    Servicio para obtener datos de Binance P2P.
    """

    def __init__(self) -> None:
        self.base_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(10.0),
        )
        self._price_cache: Dict[
            Tuple[str, str, str, Tuple[str, ...]],
            Dict[str, Any],
        ] = {}
        self._cache_ttl = timedelta(seconds=settings.P2P_PRICE_CACHE_SECONDS)

    async def aclose(self) -> None:
        """Cerrar el cliente HTTP reutilizable."""
        await self._client.aclose()

    def _fiat_threshold(self, fiat: str) -> float:
        """Calcular el umbral de liquidez mínimo expresado en fiat local."""
        min_notional_usd = settings.P2P_MIN_SURPLUS_USDT
        if min_notional_usd <= 0:
            return 0.0

        rate = settings.FX_FALLBACK_RATES.get(fiat.upper())
        if not rate or rate <= 0:
            # Si no tenemos tasa, asumir 1:1 para no descartar oportunidades.
            rate = 1.0

        return min_notional_usd * rate

    def _is_liquid_enough(
        self,
        *,
        asset: str,
        fiat: str,
        price: float,
        available: float,
    ) -> bool:
        """Comprobar si un anuncio cumple con el mínimo de liquidez configurado."""
        try:
            if available is None:
                return False

            available = float(available)
            if available <= 0:
                return False

            if asset.upper() == "USDT":
                return available >= settings.P2P_MIN_SURPLUS_USDT

            price = float(price)
            if price <= 0:
                return False

            threshold = self._fiat_threshold(fiat)
            if threshold <= 0:
                return True

            notional = available * price
            return notional >= threshold
        except (TypeError, ValueError):  # pragma: no cover - defensivo
            return False

    async def get_p2p_ads(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        trade_type: str = "BUY",
        pay_types: Optional[List[str]] = None,
        rows: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Obtener anuncios P2P de Binance.

        Args:
            asset: Criptomoneda (USDT, BTC, etc.)
            fiat: Moneda fiat (COP, VES, etc.)
            trade_type: BUY o SELL
            pay_types: Métodos de pago
            rows: Número de resultados
        """
        payload = {
            "asset": asset,
            "fiat": fiat,
            "merchantCheck": False,
            "page": 1,
            "payTypes": pay_types or [],
            "publisherType": None,
            "rows": rows,
            "tradeType": trade_type,
            "transAmount": "",
        }

        try:
            response = await self._client.post("/adv/search", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                return data.get("data", [])

            logger.error("Binance P2P API error", response=data)
            return []

        except Exception as exc:
            logger.error("Error fetching P2P ads", error=str(exc))
            return []

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
        Obtener el mejor precio disponible en P2P.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY (nosotros compramos) o SELL (nosotros vendemos)
            pay_types: Filtros de métodos de pago
            return_details: Retornar el anuncio completo
            rows: Número de anuncios a evaluar
        """
        cache_key = (
            asset.upper(),
            fiat.upper(),
            trade_type.upper(),
            tuple(sorted(pay_types or [])),
        )
        now = datetime.utcnow()

        cached = self._price_cache.get(cache_key)
        if cached and now - cached["ts"] < self._cache_ttl:
            quote = cached["quote"]
            return quote if return_details else quote["price"]

        ads = await self.get_p2p_ads(
            asset=asset,
            fiat=fiat,
            trade_type=trade_type,
            pay_types=pay_types,
            rows=rows,
        )

        if not ads:
            logger.warning("No P2P ads found", asset=asset, fiat=fiat, trade_type=trade_type)
            return None if return_details else 0.0

        valid_quotes: List[Dict[str, Any]] = []
        for ad in ads:
            try:
                adv = ad.get("adv", {})
                price = float(adv.get("price", 0))
                available_asset = float(adv.get("surplusAmount", 0))
                min_single_amount = float(adv.get("minSingleTransAmount", 0) or 0)
                max_single_amount = float(adv.get("maxSingleTransAmount", 0) or 0)

                if price <= 0:
                    continue

                if not self._is_liquid_enough(
                    asset=asset,
                    fiat=fiat,
                    price=price,
                    available=available_asset,
                ):
                    continue

                quote = {
                    "price": price,
                    "available": available_asset,
                    "min_single_amount": min_single_amount,
                    "max_single_amount": max_single_amount,
                    "trade_type": trade_type.upper(),
                    "asset": asset.upper(),
                    "fiat": fiat.upper(),
                    "payment_methods": [
                        method.get("identifier") or method.get("tradeMethodShortName")
                        for method in adv.get("tradeMethods", [])
                    ],
                    "merchant": ad.get("advertiser", {}).get("nickName", ""),
                }
                valid_quotes.append(quote)
            except (ValueError, TypeError):
                continue

        if not valid_quotes:
            logger.debug(
                "No valid P2P quotes after filtering",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type,
            )
            return None if return_details else 0.0

        if trade_type.upper() == "BUY":
            best_quote = min(valid_quotes, key=lambda q: q["price"])
        else:
            best_quote = max(valid_quotes, key=lambda q: q["price"])

        self._price_cache[cache_key] = {"quote": best_quote, "ts": now}
        return best_quote if return_details else best_quote["price"]

    async def get_market_depth(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        rows: int = 10,
    ) -> Dict[str, Any]:
        """
        Obtener profundidad del mercado P2P.
        """
        buy_ads = await self.get_p2p_ads(asset, fiat, "BUY", rows=rows)
        sell_ads = await self.get_p2p_ads(asset, fiat, "SELL", rows=rows)

        buy_prices = []
        sell_prices = []

        for ad in buy_ads:
            try:
                price = float(ad.get("adv", {}).get("price", 0))
                available = float(ad.get("adv", {}).get("surplusAmount", 0))
                if price > 0 and self._is_liquid_enough(
                    asset=asset,
                    fiat=fiat,
                    price=price,
                    available=available,
                ):
                    buy_prices.append({
                        "price": price,
                        "available": available,
                        "merchant": ad.get("advertiser", {}).get("nickName", ""),
                        "payment_methods": [
                            method.get("identifier") or method.get("tradeMethodShortName")
                            for method in ad.get("adv", {}).get("tradeMethods", [])
                        ],
                        "min_single_amount": float(ad.get("adv", {}).get("minSingleTransAmount", 0) or 0),
                        "max_single_amount": float(ad.get("adv", {}).get("maxSingleTransAmount", 0) or 0),
                    })
            except (ValueError, TypeError):
                continue

        for ad in sell_ads:
            try:
                price = float(ad.get("adv", {}).get("price", 0))
                available = float(ad.get("adv", {}).get("surplusAmount", 0))
                if price > 0 and self._is_liquid_enough(
                    asset=asset,
                    fiat=fiat,
                    price=price,
                    available=available,
                ):
                    sell_prices.append({
                        "price": price,
                        "available": available,
                        "merchant": ad.get("advertiser", {}).get("nickName", ""),
                        "payment_methods": [
                            method.get("identifier") or method.get("tradeMethodShortName")
                            for method in ad.get("adv", {}).get("tradeMethods", [])
                        ],
                        "min_single_amount": float(ad.get("adv", {}).get("minSingleTransAmount", 0) or 0),
                        "max_single_amount": float(ad.get("adv", {}).get("maxSingleTransAmount", 0) or 0),
                    })
            except (ValueError, TypeError):
                continue

        best_buy = min(buy_prices, key=lambda x: x["price"]) if buy_prices else None
        best_sell = max(sell_prices, key=lambda x: x["price"]) if sell_prices else None

        spread = 0.0
        if best_buy and best_sell:
            spread = ((best_sell["price"] - best_buy["price"]) / best_buy["price"]) * 100

        return {
            "asset": asset,
            "fiat": fiat,
            "best_buy": best_buy,
            "best_sell": best_sell,
            "spread_percent": round(spread, 2),
            "buy_depth": buy_prices[:5],
            "sell_depth": sell_prices[:5],
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_payment_methods(self, fiat: str = "COP") -> List[str]:
        """
        Obtener métodos de pago disponibles para una moneda.
        """
        payment_methods = {
            "COP": ["Nequi", "Bancolombia", "DaviPlata", "BankTransfer", "PSE"],
            "VES": ["Banesco", "Mercantil", "BDV", "BankTransfer", "Zelle"],
        }

        return payment_methods.get(fiat, ["BankTransfer"])

    async def check_api_status(self) -> bool:
        """
        Verificar si la API de Binance está disponible.
        """
        try:
            response = await self._client.get("https://api.binance.com/api/v3/ping")
            return response.status_code == 200
        except Exception as exc:
            logger.error("Binance API health check failed", error=str(exc))
            return False
