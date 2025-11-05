"""
Servicio para Binance Futures API (Perpetual Futures).
Permite operar en futuros perpetuos y acceder a funding rates para arbitraje.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import structlog
from binance.error import ClientError, ServerError
from binance.um_futures import UMFutures

from app.core.config import settings

logger = structlog.get_logger()


class BinanceFuturesService:
    """
    Servicio para operar en Binance USD-M Futures (Perpetual Futures).
    Soporta funding rate arbitrage y delta-neutral strategies.
    """

    def __init__(self) -> None:
        """Inicializar cliente de Binance Futures."""
        base_url = (
            "https://fapi.binance.com"
            if not settings.BINANCE_TESTNET
            else "https://testnet.binancefuture.com"
        )

        self.client = UMFutures(
            key=settings.BINANCE_API_KEY,
            secret=settings.BINANCE_API_SECRET,
            base_url=base_url,
        )

    async def _run_client(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Ejecutar llamadas bloqueantes del cliente en un hilo."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    # ==================== FUNDING RATE METHODS ====================

    async def get_funding_rate(self, symbol: str = "BTCUSDT") -> Optional[Dict[str, Any]]:
        """
        Obtener el funding rate actual y próximo de un perpetual.

        Returns:
            {
                "symbol": "BTCUSDT",
                "funding_rate": 0.0001,  # 0.01%
                "funding_time": 1609459200000,  # Next funding time
                "mark_price": 50000.0,
            }
        """
        try:
            # Get current funding rate
            funding_info = await self._run_client(self.client.funding_rate, symbol=symbol, limit=1)

            if not funding_info:
                return None

            latest = funding_info[0]

            # Get mark price for additional context
            mark_price_data = await self.get_mark_price(symbol)
            mark_price = mark_price_data["mark_price"] if mark_price_data else 0.0

            return {
                "symbol": latest["symbol"],
                "funding_rate": float(latest["fundingRate"]),
                "funding_time": int(latest["fundingTime"]),
                "mark_price": mark_price,
            }

        except ClientError as exc:
            logger.error("Error getting funding rate", symbol=symbol, error=str(exc))
            return None

    async def get_historical_funding_rates(
        self,
        symbol: str = "BTCUSDT",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Obtener funding rates históricos para análisis de tendencias.

        Args:
            symbol: Par de trading (ej: BTCUSDT)
            limit: Número de registros (max 1000)

        Returns:
            Lista de funding rates con timestamps
        """
        try:
            funding_history = await self._run_client(
                self.client.funding_rate,
                symbol=symbol,
                limit=limit,
            )

            return [
                {
                    "symbol": f["symbol"],
                    "funding_rate": float(f["fundingRate"]),
                    "funding_time": int(f["fundingTime"]),
                }
                for f in funding_history
            ]

        except ClientError as exc:
            logger.error("Error getting funding rate history", symbol=symbol, error=str(exc))
            return []

    async def get_all_funding_rates(self) -> List[Dict[str, Any]]:
        """
        Obtener funding rates de todos los perpetuals activos.
        Útil para encontrar las mejores oportunidades de arbitraje.

        Returns:
            Lista de todos los funding rates ordenados por tasa absoluta
        """
        try:
            # Get all premium index (includes funding rate)
            premium_index = await self._run_client(self.client.mark_price)

            funding_rates = []
            for item in premium_index:
                if "lastFundingRate" in item:
                    funding_rates.append({
                        "symbol": item["symbol"],
                        "funding_rate": float(item["lastFundingRate"]),
                        "next_funding_time": int(item["nextFundingTime"]),
                        "mark_price": float(item["markPrice"]),
                        "index_price": float(item["indexPrice"]),
                    })

            # Sort by absolute funding rate (highest opportunities first)
            funding_rates.sort(key=lambda x: abs(x["funding_rate"]), reverse=True)

            return funding_rates

        except ClientError as exc:
            logger.error("Error getting all funding rates", error=str(exc))
            return []

    async def calculate_funding_rate_apy(
        self,
        funding_rate: float,
        periods_per_day: int = 3,
    ) -> float:
        """
        Calcular APY (Annual Percentage Yield) basado en funding rate.

        Args:
            funding_rate: Funding rate (ej: 0.0001 = 0.01%)
            periods_per_day: Número de funding periods por día (default: 3)

        Returns:
            APY anualizado en porcentaje
        """
        # APY = (1 + rate)^periods - 1
        daily_rate = funding_rate * periods_per_day
        apy = ((1 + daily_rate) ** 365 - 1) * 100

        return apy

    # ==================== PRICE METHODS ====================

    async def get_mark_price(self, symbol: str = "BTCUSDT") -> Optional[Dict[str, Any]]:
        """
        Obtener mark price (precio de marca) del perpetual.
        El mark price se usa para calcular funding y liquidaciones.
        """
        try:
            mark_price_data = await self._run_client(self.client.mark_price, symbol=symbol)

            return {
                "symbol": mark_price_data["symbol"],
                "mark_price": float(mark_price_data["markPrice"]),
                "index_price": float(mark_price_data["indexPrice"]),
                "last_funding_rate": float(mark_price_data.get("lastFundingRate", 0)),
                "next_funding_time": int(mark_price_data.get("nextFundingTime", 0)),
            }

        except ClientError as exc:
            logger.error("Error getting mark price", symbol=symbol, error=str(exc))
            return None

    async def get_futures_price(self, symbol: str = "BTCUSDT") -> float:
        """Obtener precio actual del perpetual."""
        try:
            ticker = await self._run_client(self.client.ticker_price, symbol=symbol)
            return float(ticker["price"])

        except ClientError as exc:
            logger.error("Error getting futures price", symbol=symbol, error=str(exc))
            return 0.0

    async def get_24h_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de 24 horas del perpetual."""
        try:
            ticker = await self._run_client(self.client.ticker_24hr_price_change, symbol=symbol)

            return {
                "symbol": ticker["symbol"],
                "price_change": float(ticker["priceChange"]),
                "price_change_percent": float(ticker["priceChangePercent"]),
                "last_price": float(ticker["lastPrice"]),
                "volume": float(ticker["volume"]),
                "quote_volume": float(ticker["quoteVolume"]),
                "high": float(ticker["highPrice"]),
                "low": float(ticker["lowPrice"]),
                "open_interest": float(ticker.get("openInterest", 0)),
            }

        except ClientError as exc:
            logger.error("Error getting 24h ticker", symbol=symbol, error=str(exc))
            return None

    # ==================== ACCOUNT & POSITION METHODS ====================

    async def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """
        Obtener balance de la cuenta de Futures.

        Returns:
            {
                "total_wallet_balance": 10000.0,
                "available_balance": 9500.0,
                "total_unrealized_profit": 100.0,
                "balances": [{"asset": "USDT", "balance": 10000.0}]
            }
        """
        try:
            account = await self._run_client(self.client.account)

            return {
                "total_wallet_balance": float(account.get("totalWalletBalance", 0)),
                "available_balance": float(account.get("availableBalance", 0)),
                "total_unrealized_profit": float(account.get("totalUnrealizedProfit", 0)),
                "total_margin_balance": float(account.get("totalMarginBalance", 0)),
                "balances": [
                    {
                        "asset": b["asset"],
                        "balance": float(b["balance"]),
                        "available": float(b["availableBalance"]),
                    }
                    for b in account.get("assets", [])
                    if float(b["balance"]) > 0
                ],
            }

        except ClientError as exc:
            logger.error("Error getting account balance", error=str(exc))
            return None

    async def get_positions(
        self,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtener posiciones abiertas en Futures.

        Args:
            symbol: Filtrar por símbolo específico (opcional)

        Returns:
            Lista de posiciones con detalles de P&L, leverage, etc.
        """
        try:
            if symbol:
                positions = await self._run_client(self.client.get_position_risk, symbol=symbol)
            else:
                positions = await self._run_client(self.client.get_position_risk)

            # Filter only positions with size > 0
            active_positions = []
            for pos in positions:
                position_amt = float(pos["positionAmt"])
                if abs(position_amt) > 0:
                    active_positions.append({
                        "symbol": pos["symbol"],
                        "position_amt": position_amt,
                        "entry_price": float(pos["entryPrice"]),
                        "mark_price": float(pos["markPrice"]),
                        "unrealized_profit": float(pos["unRealizedProfit"]),
                        "leverage": int(pos["leverage"]),
                        "liquidation_price": float(pos.get("liquidationPrice", 0)),
                        "margin_type": pos.get("marginType", "cross"),
                        "isolated_wallet": float(pos.get("isolatedWallet", 0)),
                    })

            return active_positions

        except ClientError as exc:
            logger.error("Error getting positions", error=str(exc))
            return []

    async def get_leverage(self, symbol: str) -> int:
        """Obtener leverage actual de un símbolo."""
        try:
            positions = await self._run_client(self.client.get_position_risk, symbol=symbol)

            if positions:
                return int(positions[0].get("leverage", 1))

            return 1

        except ClientError as exc:
            logger.error("Error getting leverage", symbol=symbol, error=str(exc))
            return 1

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Configurar leverage para un símbolo.

        Args:
            symbol: Par de trading
            leverage: Leverage (1-125 dependiendo del símbolo)
        """
        try:
            await self._run_client(self.client.change_leverage, symbol=symbol, leverage=leverage)

            logger.info("Leverage updated", symbol=symbol, leverage=leverage)
            return True

        except ClientError as exc:
            logger.error("Error setting leverage", symbol=symbol, leverage=leverage, error=str(exc))
            return False

    async def set_margin_type(self, symbol: str, margin_type: str = "CROSSED") -> bool:
        """
        Configurar tipo de margen (CROSSED o ISOLATED).

        Args:
            symbol: Par de trading
            margin_type: "CROSSED" o "ISOLATED"
        """
        try:
            await self._run_client(self.client.change_margin_type, symbol=symbol, marginType=margin_type)

            logger.info("Margin type updated", symbol=symbol, margin_type=margin_type)
            return True

        except ClientError as exc:
            # Error 4046 means margin type is already set
            if "4046" in str(exc):
                logger.debug("Margin type already set", symbol=symbol, margin_type=margin_type)
                return True

            logger.error("Error setting margin type", symbol=symbol, error=str(exc))
            return False

    # ==================== ORDER METHODS ====================

    async def create_market_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        quantity: float,
        reduce_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Crear orden de mercado en Futures.

        Args:
            symbol: Par de trading
            side: "BUY" o "SELL"
            quantity: Cantidad en unidades del activo base
            reduce_only: True para solo reducir posición existente
        """
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": quantity,
            }

            if reduce_only:
                params["reduceOnly"] = "true"

            order = await self._run_client(self.client.new_order, **params)

            logger.info(
                "Futures market order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_id=order["orderId"],
            )

            return order

        except ClientError as exc:
            logger.error(
                "Error creating futures market order",
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
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Crear orden limit en Futures."""
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "timeInForce": time_in_force,
                "quantity": quantity,
                "price": price,
            }

            if reduce_only:
                params["reduceOnly"] = "true"

            order = await self._run_client(self.client.new_order, **params)

            logger.info(
                "Futures limit order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_id=order["orderId"],
            )

            return order

        except ClientError as exc:
            logger.error(
                "Error creating futures limit order",
                symbol=symbol,
                side=side,
                error=str(exc),
            )
            return None

    async def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancelar una orden abierta en Futures."""
        try:
            await self._run_client(self.client.cancel_order, symbol=symbol, orderId=order_id)
            logger.info("Futures order cancelled", symbol=symbol, order_id=order_id)
            return True

        except ClientError as exc:
            logger.error("Error cancelling futures order", order_id=order_id, error=str(exc))
            return False

    async def cancel_all_orders(self, symbol: str) -> bool:
        """Cancelar todas las órdenes abiertas de un símbolo."""
        try:
            await self._run_client(self.client.cancel_open_orders, symbol=symbol)
            logger.info("All futures orders cancelled", symbol=symbol)
            return True

        except ClientError as exc:
            logger.error("Error cancelling all orders", symbol=symbol, error=str(exc))
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener órdenes abiertas en Futures."""
        try:
            if symbol:
                orders = await self._run_client(self.client.get_orders, symbol=symbol)
            else:
                orders = await self._run_client(self.client.get_orders)

            return [o for o in orders if o["status"] in ["NEW", "PARTIALLY_FILLED"]]

        except ClientError as exc:
            logger.error("Error getting open orders", error=str(exc))
            return []

    # ==================== UTILITY METHODS ====================

    async def get_exchange_info(self, symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtener información de los símbolos disponibles."""
        try:
            exchange_info = await self._run_client(self.client.exchange_info)

            if symbol:
                # Find specific symbol info
                for s in exchange_info["symbols"]:
                    if s["symbol"] == symbol:
                        filters = {f["filterType"]: f for f in s["filters"]}

                        return {
                            "symbol": s["symbol"],
                            "status": s["status"],
                            "base_asset": s["baseAsset"],
                            "quote_asset": s["quoteAsset"],
                            "price_precision": s["pricePrecision"],
                            "quantity_precision": s["quantityPrecision"],
                            "min_qty": float(filters.get("LOT_SIZE", {}).get("minQty", 0)),
                            "max_qty": float(filters.get("LOT_SIZE", {}).get("maxQty", 0)),
                            "step_size": float(filters.get("LOT_SIZE", {}).get("stepSize", 0)),
                            "min_notional": float(filters.get("MIN_NOTIONAL", {}).get("notional", 0)),
                        }

            return exchange_info

        except ClientError as exc:
            logger.error("Error getting exchange info", error=str(exc))
            return None

    async def check_api_connection(self) -> bool:
        """Verificar conexión con la API de Binance Futures."""
        try:
            await self._run_client(self.client.ping)
            return True

        except (ClientError, ServerError, Exception) as exc:  # noqa: BLE001
            logger.error("Binance Futures API connection failed", error=str(exc))
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
        """Calcular cantidad válida según restricciones del símbolo."""
        quantity = notional / price

        precision = len(str(step_size).split(".")[-1].rstrip("0"))
        quantity = round(quantity - (quantity % step_size), precision)

        return quantity
