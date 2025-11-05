"""
Servicio para Binance Spot API.
Trading automatico oficial con API documentada.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional

import structlog
from binance.error import ClientError, ServerError
from binance.spot import Spot

from app.core.config import settings

logger = structlog.get_logger()


class BinanceSpotService:
    """
    Servicio para operar en Binance Spot usando API oficial.
    """

    def __init__(self) -> None:
        """Inicializar cliente de Binance Spot."""
        self.client = Spot(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            base_url="https://api.binance.com" if not settings.BINANCE_TESTNET else "https://testnet.binance.vision",
        )

    async def _run_client(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Ejecutar llamadas bloqueantes del cliente en un hilo."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def get_account_balance(self, asset: str = "USDT") -> float:
        """Obtener balance disponible de un activo."""
        try:
            account = await self._run_client(self.client.account)

            for balance in account["balances"]:
                if balance["asset"] == asset:
                    return float(balance["free"])

            return 0.0

        except ClientError as exc:
            logger.error("Error getting account balance", error=str(exc))
            return 0.0

    async def get_spot_price(self, symbol: str = "USDTUSDC") -> float:
        """Obtener precio actual en Spot."""
        try:
            ticker = await self._run_client(self.client.ticker_price, symbol=symbol)
            return float(ticker["price"])

        except ClientError as exc:
            logger.error("Error getting spot price", symbol=symbol, error=str(exc))
            return 0.0

    async def get_all_balances(self) -> Dict[str, float]:
        """Obtener balances de todos los activos."""
        try:
            account = await self._run_client(self.client.account)
            balances: Dict[str, float] = {}

            for balance in account["balances"]:
                free = float(balance["free"])
                if free > 0:
                    balances[balance["asset"]] = free

            return balances

        except ClientError as exc:
            logger.error("Error getting all balances", error=str(exc))
            return {}

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Optional[Dict[str, Any]]:
        """Crear orden de mercado (ejecucion inmediata)."""
        try:
            order = await self._run_client(
                self.client.new_order,
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
            )

            logger.info(
                "Market order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_id=order["orderId"],
            )

            return order

        except ClientError as exc:
            logger.error(
                "Error creating market order",
                symbol=symbol,
                side=side,
                error=str(exc),
            )
            return None

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Optional[Dict[str, Any]]:
        """Crear orden limit (Good Till Cancelled)."""
        try:
            order = await self._run_client(
                self.client.new_order,
                symbol=symbol,
                side=side,
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=price,
            )

            logger.info(
                "Limit order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_id=order["orderId"],
            )

            return order

        except ClientError as exc:
            logger.error(
                "Error creating limit order",
                symbol=symbol,
                side=side,
                error=str(exc),
            )
            return None

    async def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancelar una orden abierta."""
        try:
            await self._run_client(self.client.cancel_order, symbol=symbol, orderId=order_id)
            logger.info("Order cancelled", symbol=symbol, order_id=order_id)
            return True

        except ClientError as exc:
            logger.error("Error cancelling order", order_id=order_id, error=str(exc))
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener lista de ordenes abiertas."""
        try:
            if symbol:
                orders = await self._run_client(self.client.get_open_orders, symbol=symbol)
            else:
                orders = await self._run_client(self.client.get_open_orders)

            return orders

        except ClientError as exc:
            logger.error("Error getting open orders", error=str(exc))
            return []

    async def get_order_status(self, symbol: str, order_id: int) -> Optional[Dict[str, Any]]:
        """Consultar estado de una orden."""
        try:
            order = await self._run_client(self.client.get_order, symbol=symbol, orderId=order_id)
            return order

        except ClientError as exc:
            logger.error("Error getting order status", order_id=order_id, error=str(exc))
            return None

    async def get_24h_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtener estadisticas de 24 horas."""
        try:
            ticker = await self._run_client(self.client.ticker_24hr, symbol=symbol)
            return {
                "symbol": ticker["symbol"],
                "price_change": float(ticker["priceChange"]),
                "price_change_percent": float(ticker["priceChangePercent"]),
                "last_price": float(ticker["lastPrice"]),
                "volume": float(ticker["volume"]),
                "high": float(ticker["highPrice"]),
                "low": float(ticker["lowPrice"]),
            }

        except ClientError as exc:
            logger.error("Error getting 24h ticker", symbol=symbol, error=str(exc))
            return None

    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtener informacion del par de trading."""
        try:
            exchange_info = await self._run_client(self.client.exchange_info, symbol=symbol)

            if exchange_info["symbols"]:
                symbol_info = exchange_info["symbols"][0]
                filters = {f["filterType"]: f for f in symbol_info["filters"]}

                return {
                    "symbol": symbol_info["symbol"],
                    "status": symbol_info["status"],
                    "base_asset": symbol_info["baseAsset"],
                    "quote_asset": symbol_info["quoteAsset"],
                    "min_qty": float(filters.get("LOT_SIZE", {}).get("minQty", 0)),
                    "max_qty": float(filters.get("LOT_SIZE", {}).get("maxQty", 0)),
                    "step_size": float(filters.get("LOT_SIZE", {}).get("stepSize", 0)),
                    "min_notional": float(filters.get("MIN_NOTIONAL", {}).get("minNotional", 0)),
                }

            return None

        except ClientError as exc:
            logger.error("Error getting symbol info", symbol=symbol, error=str(exc))
            return None

    async def check_api_connection(self) -> bool:
        """Verificar conexion con la API de Binance Spot."""
        try:
            await self._run_client(self.client.ping)
            return True

        except (ClientError, ServerError, Exception) as exc:  # noqa: BLE001
            logger.error("Binance Spot API connection failed", error=str(exc))
            return False

    async def get_server_time(self) -> int:
        """Obtener tiempo del servidor de Binance."""
        try:
            time_data = await self._run_client(self.client.time)
            return time_data["serverTime"]

        except ClientError as exc:
            logger.error("Error getting server time", error=str(exc))
            return 0

    def calculate_quantity(
        self,
        price: float,
        notional: float,
        step_size: float,
    ) -> float:
        """Calcular cantidad valida segun restricciones del simbolo."""
        quantity = notional / price

        precision = len(str(step_size).split(".")[-1].rstrip("0"))
        quantity = round(quantity - (quantity % step_size), precision)

        return quantity
