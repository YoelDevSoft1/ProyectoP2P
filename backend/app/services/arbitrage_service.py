"""
Servicio de arbitraje entre Binance Spot y P2P.
Detecta y ejecuta oportunidades de ganancia.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import structlog

from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.fx_service import FXService
from app.services.trm_service import TRMService

logger = structlog.get_logger()


class ArbitrageService:
    """
    Detecta oportunidades de arbitraje entre:
    1. Spot (cripto-cripto)
    2. P2P (cripto-fiat)
    3. Cross-currency (COP vs VES)
    """

    def __init__(
        self,
        spot_service: Optional[BinanceSpotService] = None,
        p2p_service: Optional[BinanceService] = None,
        fx_service: Optional[FXService] = None,
        trm_service: Optional[TRMService] = None,
    ) -> None:
        self.spot_service = spot_service or BinanceSpotService()
        self.p2p_service = p2p_service or BinanceService()
        self.trm_service = trm_service or TRMService()
        self.fx_service = fx_service or FXService(
            p2p_service=self.p2p_service,
            spot_service=self.spot_service,
            trm_service=self.trm_service,
        )

    async def analyze_spot_to_p2p_arbitrage(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
    ) -> Dict[str, Any]:
        """
        Analizar arbitraje: Comprar en Spot -> Vender en P2P.

        Flujo:
        1. Comprar USDT en Spot con USDC (~1 USD)
        2. Vender USDT en P2P por COP/VES
        3. Calcular profit real considerando tasa de mercado
        """
        asset_code = asset.upper()
        fiat_code = fiat.upper()

        try:
            (
                spot_price,
                p2p_sell_quote,
                p2p_buy_quote,
                exchange_rate,
            ) = await asyncio.gather(
                self.spot_service.get_spot_price("USDCUSDT"),
                self.p2p_service.get_best_price(
                    asset=asset_code,
                    fiat=fiat_code,
                    trade_type="SELL",
                    return_details=True,
                ),
                self.p2p_service.get_best_price(
                    asset=asset_code,
                    fiat=fiat_code,
                    trade_type="BUY",
                    return_details=True,
                ),
                self.fx_service.get_rate(fiat_code),
            )

            if spot_price is None or spot_price <= 0:
                spot_price = 1.0

            if exchange_rate is None or exchange_rate <= 0:
                exchange_rate = settings.FX_FALLBACK_RATES.get(fiat_code, 1.0)

            p2p_sell_price = p2p_sell_quote["price"] if isinstance(p2p_sell_quote, dict) else 0.0
            p2p_buy_price = p2p_buy_quote["price"] if isinstance(p2p_buy_quote, dict) else 0.0
            sell_available = p2p_sell_quote.get("available") if isinstance(p2p_sell_quote, dict) else 0.0

            cost_usd = spot_price
            revenue_usd = p2p_sell_price / exchange_rate if exchange_rate else 0.0
            profit_per_unit = revenue_usd - cost_usd
            profit_percentage = (profit_per_unit / cost_usd) * 100 if cost_usd > 0 else 0.0

            spot_fee = 0.001  # 0.1% Binance Spot
            net_profit_percentage = profit_percentage - (spot_fee * 100)

            recommended_amount = self._calculate_recommended_amount(net_profit_percentage)
            liquidity_warning: Optional[str] = None

            if recommended_amount > 0:
                if not sell_available or sell_available <= 0:
                    liquidity_warning = "Sin liquidez suficiente en el mejor anuncio P2P."
                    recommended_amount = 0
                elif sell_available < recommended_amount:
                    liquidity_warning = (
                        f"Liquidez disponible limitada a {sell_available:.2f} {asset_code}. "
                        "Monto recomendado ajustado."
                    )
                    recommended_amount = sell_available

            p2p_spread = 0.0
            if p2p_sell_price > 0 and p2p_buy_price > 0:
                p2p_spread = ((p2p_buy_price - p2p_sell_price) / p2p_sell_price) * 100

            opportunity = {
                "strategy": "spot_to_p2p",
                "asset": asset_code,
                "fiat": fiat_code,
                "spot_price_usd": round(spot_price, 4),
                "p2p_sell_price_fiat": round(p2p_sell_price, 2),
                "p2p_buy_price_fiat": round(p2p_buy_price, 2),
                "p2p_sell_available": round(sell_available or 0.0, 2),
                "p2p_spread_percentage": round(abs(p2p_spread), 2),
                "exchange_rate_used": round(exchange_rate, 4),
                "cost_usd": round(cost_usd, 4),
                "revenue_usd": round(revenue_usd, 4),
                "profit_per_unit_usd": round(profit_per_unit, 4),
                "profit_percentage": round(profit_percentage, 2),
                "net_profit_percentage": round(net_profit_percentage, 2),
                "fees_percentage": round(spot_fee * 100, 2),
                "is_profitable": net_profit_percentage > settings.ARBITRAGE_MIN_PROFIT,
                "recommended_amount": round(recommended_amount, 2),
                "liquidity_warning": liquidity_warning,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if opportunity["is_profitable"]:
                logger.info(
                    "Profitable arbitrage found",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat_code,
                    exchange_rate=exchange_rate,
                )
            else:
                logger.debug(
                    "No profitable arbitrage",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat_code,
                )

            return opportunity

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing spot to p2p arbitrage", error=str(exc))
            return {
                "strategy": "spot_to_p2p",
                "is_profitable": False,
                "error": str(exc),
            }

    async def analyze_p2p_cross_currency(self) -> Dict[str, Any]:
        """
        Analizar arbitraje entre COP y VES en P2P.

        Flujo:
        1. Comprar USDT con COP en P2P
        2. Vender USDT por VES en P2P
        """
        try:
            (
                cop_buy_price,
                cop_sell_price,
                ves_buy_price,
                ves_sell_price,
                cop_rate,
                ves_rate,
            ) = await asyncio.gather(
                self.p2p_service.get_best_price("USDT", "COP", "BUY"),
                self.p2p_service.get_best_price("USDT", "COP", "SELL"),
                self.p2p_service.get_best_price("USDT", "VES", "BUY"),
                self.p2p_service.get_best_price("USDT", "VES", "SELL"),
                self.fx_service.get_rate("COP"),
                self.fx_service.get_rate("VES"),
            )

            strategy_1_profit = self._calculate_cross_profit(
                buy_price_cop=cop_buy_price,
                sell_price_ves=ves_sell_price,
                cop_rate=cop_rate,
                ves_rate=ves_rate,
            )

            strategy_2_profit = self._calculate_cross_profit(
                buy_price_ves=ves_buy_price,
                sell_price_cop=cop_sell_price,
                cop_rate=cop_rate,
                ves_rate=ves_rate,
            )

            best_strategy = (
                strategy_1_profit
                if strategy_1_profit["profit_percentage"] > strategy_2_profit["profit_percentage"]
                else strategy_2_profit
            )

            best_strategy["is_profitable"] = best_strategy["profit_percentage"] > settings.ARBITRAGE_MIN_PROFIT
            best_strategy["cop_rate"] = round(cop_rate or 0.0, 4)
            best_strategy["ves_rate"] = round(ves_rate or 0.0, 4)

            return best_strategy

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing cross currency arbitrage", error=str(exc))
            return {
                "strategy": "cross_currency",
                "is_profitable": False,
                "error": str(exc),
            }

    def _calculate_cross_profit(
        self,
        buy_price_cop: float = 0.0,
        sell_price_ves: float = 0.0,
        buy_price_ves: float = 0.0,
        sell_price_cop: float = 0.0,
        cop_rate: float = 0.0,
        ves_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calcular profit de arbitraje cross-currency."""

        if buy_price_cop and sell_price_ves and cop_rate and ves_rate:
            cost_usd = buy_price_cop / cop_rate
            revenue_usd = sell_price_ves / ves_rate
            direction = "COP -> VES"
        elif buy_price_ves and sell_price_cop and cop_rate and ves_rate:
            cost_usd = buy_price_ves / ves_rate
            revenue_usd = sell_price_cop / cop_rate
            direction = "VES -> COP"
        else:
            return {
                "strategy": "cross_currency",
                "profit_percentage": 0.0,
                "cost_usd": 0.0,
                "revenue_usd": 0.0,
                "direction": "N/A",
            }

        profit = revenue_usd - cost_usd
        profit_percentage = (profit / cost_usd) * 100 if cost_usd > 0 else 0.0

        return {
            "strategy": "cross_currency",
            "direction": direction,
            "cost_usd": round(cost_usd, 4),
            "revenue_usd": round(revenue_usd, 4),
            "profit_percentage": round(profit_percentage, 2),
        }

    def _calculate_recommended_amount(self, profit_percentage: float) -> float:
        """
        Calcular monto recomendado segun profit.
        """
        if profit_percentage < settings.ARBITRAGE_MIN_PROFIT:
            return 0.0

        if profit_percentage >= 5.0:
            return settings.MAX_TRADE_AMOUNT
        if profit_percentage >= 3.0:
            return settings.MAX_TRADE_AMOUNT * 0.7
        if profit_percentage >= 2.0:
            return settings.MAX_TRADE_AMOUNT * 0.5
        return settings.MIN_TRADE_AMOUNT

    async def execute_spot_trade(
        self,
        symbol: str,
        side: str,
        amount_usd: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Ejecutar trade en Spot.
        """
        try:
            symbol_info = await self.spot_service.get_symbol_info(symbol)

            if not symbol_info:
                logger.error("Symbol info not found", symbol=symbol)
                return None

            price = await self.spot_service.get_spot_price(symbol)

            quantity = self.spot_service.calculate_quantity(
                price=price,
                notional=amount_usd,
                step_size=symbol_info["step_size"],
            )

            order = await self.spot_service.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
            )

            if order:
                logger.info(
                    "Spot trade executed successfully",
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_id=order["orderId"],
                )

            return order

        except Exception as exc:  # noqa: BLE001
            logger.error("Error executing spot trade", symbol=symbol, error=str(exc))
            return None

    async def get_inventory_status(self) -> Dict[str, Any]:
        """
        Obtener estado del inventario de criptomonedas.
        """
        balances = await self.spot_service.get_all_balances()

        total_usd = 0.0
        for asset_code, amount in balances.items():
            if asset_code == "USDT":
                total_usd += amount
            # TODO: Agregar conversiones adicionales si se operan otros activos.

        return {
            "balances": balances,
            "total_usd": round(total_usd, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
