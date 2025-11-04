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
import httpx
from typing import Optional, Dict, List
import structlog
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger()


class BinanceService:
    """
    Servicio para obtener datos de Binance.

    Nota: P2P no tiene API oficial completa.
    Este servicio usa endpoints públicos disponibles.
    """

    def __init__(self):
        self.base_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

    async def get_p2p_ads(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        trade_type: str = "BUY",
        pay_types: Optional[List[str]] = None,
        rows: int = 10
    ) -> List[Dict]:
        """
        Obtener anuncios P2P de Binance.

        Args:
            asset: Criptomoneda (USDT, BTC, etc.)
            fiat: Moneda fiat (COP, VES, etc.)
            trade_type: BUY o SELL
            pay_types: Métodos de pago
            rows: Número de resultados

        Returns:
            Lista de anuncios P2P
        """
        endpoint = f"{self.base_url}/adv/search"

        payload = {
            "asset": asset,
            "fiat": fiat,
            "merchantCheck": False,
            "page": 1,
            "payTypes": pay_types or [],
            "publisherType": None,
            "rows": rows,
            "tradeType": trade_type,
            "transAmount": ""
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    return data.get("data", [])
                else:
                    logger.error("Binance P2P API error", response=data)
                    return []

        except Exception as e:
            logger.error("Error fetching P2P ads", error=str(e))
            return []

    async def get_best_price(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        trade_type: str = "BUY"
    ) -> float:
        """
        Obtener el mejor precio disponible en P2P.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY (nosotros compramos) o SELL (nosotros vendemos)

        Returns:
            Mejor precio disponible
        """
        ads = await self.get_p2p_ads(asset, fiat, trade_type, rows=5)

        if not ads:
            logger.warning("No P2P ads found", asset=asset, fiat=fiat, trade_type=trade_type)
            return 0.0

        # Obtener precios válidos
        prices = []
        for ad in ads:
            try:
                adv = ad.get("adv", {})
                price = float(adv.get("price", 0))
                if price > 0:
                    prices.append(price)
            except (ValueError, TypeError):
                continue

        if not prices:
            return 0.0

        # Para BUY (compramos), queremos el precio más bajo
        # Para SELL (vendemos), queremos el precio más alto
        if trade_type == "BUY":
            return min(prices)
        else:
            return max(prices)

    async def get_market_depth(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """
        Obtener profundidad del mercado P2P.

        Returns:
            Dict con mejores precios de compra y venta, y spread
        """
        buy_ads = await self.get_p2p_ads(asset, fiat, "BUY", rows=10)
        sell_ads = await self.get_p2p_ads(asset, fiat, "SELL", rows=10)

        buy_prices = []
        sell_prices = []

        for ad in buy_ads:
            try:
                price = float(ad.get("adv", {}).get("price", 0))
                available = float(ad.get("adv", {}).get("surplusAmount", 0))
                if price > 0:
                    buy_prices.append({
                        "price": price,
                        "available": available,
                        "merchant": ad.get("advertiser", {}).get("nickName", "")
                    })
            except (ValueError, TypeError):
                continue

        for ad in sell_ads:
            try:
                price = float(ad.get("adv", {}).get("price", 0))
                available = float(ad.get("adv", {}).get("surplusAmount", 0))
                if price > 0:
                    sell_prices.append({
                        "price": price,
                        "available": available,
                        "merchant": ad.get("advertiser", {}).get("nickName", "")
                    })
            except (ValueError, TypeError):
                continue

        best_buy = min(buy_prices, key=lambda x: x["price"]) if buy_prices else None
        best_sell = max(sell_prices, key=lambda x: x["price"]) if sell_prices else None

        spread = 0
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
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_payment_methods(self, fiat: str = "COP") -> List[str]:
        """
        Obtener métodos de pago disponibles para una moneda.

        Args:
            fiat: Moneda fiat

        Returns:
            Lista de métodos de pago
        """
        # Métodos de pago comunes por país
        payment_methods = {
            "COP": ["Nequi", "Bancolombia", "DaviPlata", "BankTransfer", "PSE"],
            "VES": ["Banesco", "Mercantil", "BDV", "BankTransfer", "Zelle"]
        }

        return payment_methods.get(fiat, ["BankTransfer"])

    async def check_api_status(self) -> bool:
        """
        Verificar si la API de Binance está disponible.

        Returns:
            True si la API responde correctamente
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.binance.com/api/v3/ping",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("Binance API health check failed", error=str(e))
            return False
