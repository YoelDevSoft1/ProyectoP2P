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

import asyncio
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

    # Pares válidos soportados por Binance P2P (basado en disponibilidad real)
    # Formato: (asset, fiat) -> soportado
    # NOTA: Binance P2P no soporta todos los pares. Esta lista se basa en disponibilidad real.
    VALID_PAIRS = {
        # USDT - El más líquido y disponible en la mayoría de monedas fiat LATAM
        ("USDT", "COP"): True,
        ("USDT", "VES"): True,
        ("USDT", "BRL"): True,
        ("USDT", "ARS"): True,
        ("USDT", "PEN"): True,
        ("USDT", "MXN"): True,
        # BTC - Disponible en monedas principales LATAM (limitado)
        ("BTC", "COP"): True,
        ("BTC", "VES"): True,
        ("BTC", "BRL"): True,
        ("BTC", "ARS"): True,
        # ETH - Disponible en algunas monedas LATAM (muy limitado)
        ("ETH", "COP"): True,
        ("ETH", "VES"): True,
        ("ETH", "BRL"): True,
        # BNB - Muy limitado, principalmente en monedas principales
        ("BNB", "COP"): True,
        ("BNB", "BRL"): True,
    }
    
    # Pares conocidos como NO soportados (para evitar intentos)
    INVALID_PAIRS = {
        # ETH no está disponible en MXN, USD, PEN, ARS en muchos casos
        ("ETH", "MXN"): True,
        ("ETH", "USD"): True,
        ("ETH", "PEN"): True,
        ("ETH", "ARS"): False,  # Puede estar disponible, dejar que la API lo valide
        # BNB muy limitado
        ("BNB", "VES"): True,
        ("BNB", "ARS"): True,
        ("BNB", "PEN"): True,
        ("BNB", "MXN"): True,
        ("BNB", "CLP"): True,
        # USD no está disponible en P2P (solo stablecoins como USDT)
        ("USDT", "USD"): False,  # Puede haber confusión, pero no es común en P2P
        ("BTC", "USD"): False,
        ("ETH", "USD"): False,
        ("BNB", "USD"): False,
    }
    
    # Assets soportados en Binance P2P
    SUPPORTED_ASSETS = {"USDT", "BTC", "ETH", "BNB", "BUSD"}
    
    # Fiats soportados en Binance P2P para LATAM
    SUPPORTED_FIATS = {"COP", "VES", "BRL", "ARS", "PEN", "MXN", "CLP", "USD"}

    def __init__(self) -> None:
        self.base_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(30.0),  # Aumentado para retries
        )
        self._price_cache: Dict[
            Tuple[str, str, str, Tuple[str, ...]],
            Dict[str, Any],
        ] = {}
        self._cache_ttl = timedelta(seconds=settings.P2P_PRICE_CACHE_SECONDS)
        # Cache de pares inválidos para evitar intentos repetidos
        self._invalid_pairs_cache: set = set()
        
        # Rate limiting: Binance P2P API permite ~10-20 requests por segundo
        # Usar un semáforo para limitar solicitudes concurrentes
        self._rate_limiter = asyncio.Semaphore(5)  # Máximo 5 solicitudes concurrentes
        self._request_delay = 0.1  # 100ms entre solicitudes (10 req/s)
        self._last_request_time: Optional[datetime] = None

    async def aclose(self) -> None:
        """Cerrar el cliente HTTP reutilizable."""
        await self._client.aclose()
    
    def is_valid_pair(self, asset: str, fiat: str) -> bool:
        """
        Verificar si un par asset/fiat es válido para Binance P2P.
        
        Args:
            asset: Criptomoneda (USDT, BTC, etc.)
            fiat: Moneda fiat (COP, VES, etc.)
            
        Returns:
            True si el par es válido, False en caso contrario
        """
        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        pair_key = (asset_upper, fiat_upper)
        
        # Verificar si está en cache de pares inválidos (aprendidos dinámicamente)
        if pair_key in self._invalid_pairs_cache:
            return False
        
        # Verificar si está en la lista de pares conocidos como inválidos
        if pair_key in self.INVALID_PAIRS:
            is_invalid = self.INVALID_PAIRS[pair_key]
            if is_invalid:
                logger.debug(
                    "Pair known to be invalid",
                    asset=asset_upper,
                    fiat=fiat_upper
                )
                return False
        
        # Verificar si el asset y fiat están en las listas soportadas
        if asset_upper not in self.SUPPORTED_ASSETS:
            logger.debug(
                "Asset not supported in Binance P2P",
                asset=asset_upper,
                supported_assets=list(self.SUPPORTED_ASSETS)
            )
            return False
        
        if fiat_upper not in self.SUPPORTED_FIATS:
            logger.debug(
                "Fiat not supported in Binance P2P",
                fiat=fiat_upper,
                supported_fiats=list(self.SUPPORTED_FIATS)
            )
            return False
        
        # Verificar si el par específico está en la lista de pares válidos conocidos
        if pair_key in self.VALID_PAIRS:
            return self.VALID_PAIRS[pair_key]
        
        # Si no está en ninguna lista, permitir que se intente (para descubrimiento)
        # pero la API nos dirá si no es válido y lo marcaremos
        # Para assets menos comunes como ETH/BNB, ser más conservador
        if asset_upper in ["ETH", "BNB"]:
            # Para ETH y BNB, solo permitir si está explícitamente en VALID_PAIRS
            logger.debug(
                "Pair not in known valid pairs for less common asset",
                asset=asset_upper,
                fiat=fiat_upper
            )
            return False
        
        # Para USDT y BTC, permitir intentar (son los más líquidos)
        return True
    
    def mark_pair_as_invalid(self, asset: str, fiat: str):
        """
        Marcar un par como inválido para evitar futuros intentos.
        
        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
        """
        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        self._invalid_pairs_cache.add((asset_upper, fiat_upper))
        logger.info(
            "Pair marked as invalid",
            asset=asset_upper,
            fiat=fiat_upper
        )

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
        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        trade_type_upper = trade_type.upper()
        
        # Validar par antes de hacer la solicitud
        if not self.is_valid_pair(asset_upper, fiat_upper):
            logger.debug(
                "Skipping invalid pair",
                asset=asset_upper,
                fiat=fiat_upper,
                trade_type=trade_type_upper
            )
            return []
        
        # Validar trade_type
        if trade_type_upper not in ["BUY", "SELL"]:
            logger.warning(
                "Invalid trade_type",
                trade_type=trade_type,
                asset=asset_upper,
                fiat=fiat_upper
            )
            return []
        
        # Construir payload (asegurarse de que no haya valores None que puedan causar problemas)
        # Binance P2P API es sensible a valores None, así que los omitimos
        payload = {
            "asset": asset_upper,
            "fiat": fiat_upper,
            "merchantCheck": False,
            "page": 1,
            "payTypes": pay_types if pay_types else [],
            "rows": max(1, min(rows, 20)),  # Limitar rows entre 1 y 20
            "tradeType": trade_type_upper,
            "transAmount": "",  # Vacío es válido según la API
        }
        
        # Solo agregar publisherType si tiene un valor válido (no None)
        # La API de Binance puede rechazar None en algunos campos

        # Rate limiting global usando Redis (compartido entre todos los workers)
        from app.core.rate_limiter import binance_p2p_rate_limiter
        
        # Esperar hasta obtener un token del rate limiter global
        if not await binance_p2p_rate_limiter.wait_for_token(tokens=1, max_wait=2.0):
            logger.warning(
                "Rate limiter timeout, proceeding anyway",
                asset=asset_upper,
                fiat=fiat_upper,
                trade_type=trade_type_upper
            )
        
        # Rate limiting local adicional con semáforo para evitar demasiadas solicitudes concurrentes
        async with self._rate_limiter:
            # Asegurar delay mínimo entre solicitudes
            if self._last_request_time:
                elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
                if elapsed < self._request_delay:
                    await asyncio.sleep(self._request_delay - elapsed)
            
            # Retry logic para errores 429
            max_retries = 3
            base_delay = 2.0  # 2 segundos base (más conservador)
            
            for attempt in range(max_retries):
                try:
                    self._last_request_time = datetime.utcnow()
                    response = await self._client.post("/adv/search", json=payload)
                    
                    # Si recibimos 429, esperar y reintentar
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            # Exponential backoff: 1s, 2s, 4s
                            delay = base_delay * (2 ** attempt)
                            logger.warning(
                                "Rate limited by Binance API, retrying",
                                asset=asset_upper,
                                fiat=fiat_upper,
                                attempt=attempt + 1,
                                delay=delay
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(
                                "Rate limited by Binance API, max retries exceeded",
                                asset=asset_upper,
                                fiat=fiat_upper,
                                status_code=429
                            )
                            return []
                    
                    response.raise_for_status()
                    data = response.json()

                    if data.get("success"):
                        ads_data = data.get("data", [])
                        # Si no hay datos pero la respuesta fue exitosa, puede ser que el par no tenga liquidez
                        if not ads_data:
                            logger.debug(
                                "No ads found for pair (may be low liquidity or unavailable)",
                                asset=asset_upper,
                                fiat=fiat_upper,
                                trade_type=trade_type_upper
                            )
                        return ads_data

                    # Si la API retorna error "illegal parameter", marcar el par como inválido
                    error_code = data.get("code", "")
                    error_message = data.get("message", "")
                    
                    if error_code == "000002" or "illegal parameter" in error_message.lower():
                        logger.warning(
                            "Invalid pair detected by Binance API - marking as invalid",
                            asset=asset_upper,
                            fiat=fiat_upper,
                            trade_type=trade_type_upper,
                            error_code=error_code,
                            error_message=error_message,
                            payload={k: v for k, v in payload.items() if v is not None}  # Log sin None
                        )
                        # Marcar como inválido para evitar futuros intentos
                        self.mark_pair_as_invalid(asset_upper, fiat_upper)
                        return []
                    
                    # Otro tipo de error, solo loguear
                    logger.error(
                        "Binance P2P API error",
                        asset=asset_upper,
                        fiat=fiat_upper,
                        trade_type=trade_type_upper,
                        response=data
                    )
                    return []

                except httpx.HTTPStatusError as exc:
                    # Si es 429 y no hemos agotado los reintentos, continuar el loop
                    if exc.response.status_code == 429 and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "HTTP 429 error, retrying",
                            asset=asset_upper,
                            fiat=fiat_upper,
                            attempt=attempt + 1,
                            delay=delay
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    logger.error(
                        "HTTP error fetching P2P ads",
                        asset=asset_upper,
                        fiat=fiat_upper,
                        status_code=exc.response.status_code,
                        error=str(exc),
                        attempt=attempt + 1
                    )
                    return []
                except Exception as exc:
                    logger.error(
                        "Error fetching P2P ads",
                        asset=asset_upper,
                        fiat=fiat_upper,
                        error=str(exc),
                        attempt=attempt + 1
                    )
                    return []
            
            # Si llegamos aquí, se agotaron los reintentos
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
        asset_upper = asset.upper()
        fiat_upper = fiat.upper()
        
        # Validar par antes de hacer las solicitudes
        if not self.is_valid_pair(asset_upper, fiat_upper):
            logger.debug(
                "Skipping market depth for invalid pair",
                asset=asset_upper,
                fiat=fiat_upper
            )
            return {
                "asset": asset_upper,
                "fiat": fiat_upper,
                "best_buy": None,
                "best_sell": None,
                "spread_percent": 0.0,
                "buy_depth": [],
                "sell_depth": [],
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Invalid pair"
            }
        
        buy_ads = await self.get_p2p_ads(asset_upper, fiat_upper, "BUY", rows=rows)
        sell_ads = await self.get_p2p_ads(asset_upper, fiat_upper, "SELL", rows=rows)

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
            "asset": asset_upper,
            "fiat": fiat_upper,
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
