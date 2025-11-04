"""
Servicio de arbitraje entre Binance Spot y P2P.
Detecta y ejecuta oportunidades de ganancia.
"""
import structlog
from typing import Dict, Optional, List
from datetime import datetime

from app.services.binance_spot_service import BinanceSpotService
from app.services.binance_service import BinanceService
from app.services.trm_service import TRMService
from app.core.config import settings

logger = structlog.get_logger()


class ArbitrageService:
    """
    Detecta oportunidades de arbitraje entre:
    1. Spot (cripto-cripto)
    2. P2P (cripto-fiat)
    3. Cross-currency (COP vs VES)
    """

    def __init__(self):
        self.spot_service = BinanceSpotService()
        self.p2p_service = BinanceService()
        self.trm_service = TRMService()

    async def _get_market_exchange_rate(self, fiat: str) -> float:
        """
        Obtiene tasa de cambio real del mercado usando precios P2P implícitos.

        Compara el precio P2P del fiat con el precio Spot para derivar
        la tasa de cambio real del mercado paralelo.
        """
        try:
            # Obtener precio P2P del fiat
            p2p_price_fiat = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat=fiat,
                trade_type="SELL"
            )

            # Obtener precio Spot USDT (en USD)
            spot_price_usd = await self.spot_service.get_spot_price("USDCUSDT")
            if spot_price_usd == 0:
                spot_price_usd = 1.0

            # La tasa implícita es: precio_fiat / precio_usd
            # Ej: Si USDT vale 309.50 VES en P2P y 1.0 USD en Spot
            # entonces 1 USD = 309.50 VES (tasa de mercado paralelo)
            implicit_rate = p2p_price_fiat / spot_price_usd

            logger.info(
                f"Market exchange rate calculated",
                fiat=fiat,
                rate=implicit_rate,
                p2p_price=p2p_price_fiat,
                spot_price=spot_price_usd
            )

            return implicit_rate

        except Exception as e:
            logger.error(f"Error calculating market rate for {fiat}", error=str(e))
            # Fallback a tasas aproximadas
            fallback_rates = {
                "COP": 4000.0,  # Aprox TRM
                "VES": 36.5,    # Tasa oficial (probablemente desactualizada)
            }
            return fallback_rates.get(fiat, 1.0)

    async def analyze_spot_to_p2p_arbitrage(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """
        Analizar arbitraje: Comprar en Spot -> Vender en P2P.

        IMPORTANTE: Este análisis ahora usa tasas de mercado REALES derivadas
        de los precios P2P, no tasas oficiales.

        Flujo:
        1. Comprar USDT en Spot con USDC (~$1.00)
        2. Vender USDT en P2P por COP/VES
        3. Calcular profit real considerando tasa de mercado

        Args:
            asset: Criptomoneda (USDT)
            fiat: Moneda fiat (COP, VES)

        Returns:
            Oportunidad de arbitraje con detalles CORREGIDOS
        """
        try:
            # 1. Precio Spot USDT/USDC (cuánto cuesta 1 USDT en USD)
            spot_price = await self.spot_service.get_spot_price("USDCUSDT")

            if spot_price == 0:
                spot_price = 1.0  # Asumir paridad si no hay datos

            # 2. Precio P2P (cuánto pagan por USDT en fiat)
            p2p_sell_price = await self.p2p_service.get_best_price(
                asset=asset,
                fiat=fiat,
                trade_type="SELL"
            )

            # 3. Obtener precio P2P de compra (para calcular spread)
            p2p_buy_price = await self.p2p_service.get_best_price(
                asset=asset,
                fiat=fiat,
                trade_type="BUY"
            )

            # 4. Obtener tasa de cambio REAL del mercado
            if fiat == "COP":
                # Usar TRM oficial para COP
                exchange_rate = await self.trm_service.get_current_trm()
                logger.info(f"Using official TRM for COP: {exchange_rate}")
            else:
                # Para VES y otras monedas, calcular tasa de mercado implícita
                exchange_rate = await self._get_market_exchange_rate(fiat)
                logger.info(f"Using market rate for {fiat}: {exchange_rate}")

            # 5. Calcular profit potencial CORREGIDO
            # Costo en USD de comprar 1 USDT en Spot
            cost_usd = spot_price

            # Ingreso en USD de vender 1 USDT en P2P
            # CORRECCIÓN: Dividir precio P2P por tasa de cambio real
            revenue_usd = p2p_sell_price / exchange_rate

            # Profit bruto
            profit_per_unit = revenue_usd - cost_usd
            profit_percentage = (profit_per_unit / cost_usd) * 100 if cost_usd > 0 else 0

            # Fees estimados
            spot_fee = 0.001  # 0.1% Binance Spot
            p2p_fee = 0.0  # P2P es sin comisión
            total_fees = spot_fee

            net_profit_percentage = profit_percentage - (total_fees * 100)

            # Calcular spread P2P
            p2p_spread = ((p2p_buy_price - p2p_sell_price) / p2p_sell_price * 100) if p2p_sell_price > 0 else 0

            opportunity = {
                "strategy": "spot_to_p2p",
                "asset": asset,
                "fiat": fiat,
                "spot_price_usd": spot_price,
                "p2p_sell_price_fiat": p2p_sell_price,
                "p2p_buy_price_fiat": p2p_buy_price,
                "p2p_spread_percentage": round(abs(p2p_spread), 2),
                "exchange_rate_used": exchange_rate,
                "cost_usd": cost_usd,
                "revenue_usd": round(revenue_usd, 4),
                "profit_per_unit_usd": round(profit_per_unit, 4),
                "profit_percentage": round(profit_percentage, 2),
                "net_profit_percentage": round(net_profit_percentage, 2),
                "fees_percentage": round(total_fees * 100, 2),
                "is_profitable": net_profit_percentage > settings.ARBITRAGE_MIN_PROFIT,
                "recommended_amount": self._calculate_recommended_amount(net_profit_percentage),
                "warning": "⚠️ Profit real puede ser menor debido a slippage y liquidez" if net_profit_percentage > 10 else None,
                "timestamp": datetime.utcnow().isoformat()
            }

            if opportunity["is_profitable"]:
                logger.info(
                    "Profitable arbitrage found (CORRECTED)",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat,
                    exchange_rate=exchange_rate
                )
            else:
                logger.debug(
                    "No profitable arbitrage",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat
                )

            return opportunity

        except Exception as e:
            logger.error("Error analyzing spot to p2p arbitrage", error=str(e))
            return {
                "strategy": "spot_to_p2p",
                "is_profitable": False,
                "error": str(e)
            }

    async def analyze_p2p_cross_currency(self) -> Dict:
        """
        Analizar arbitraje entre COP y VES en P2P.

        Flujo:
        1. Comprar USDT con COP en P2P
        2. Vender USDT por VES en P2P

        Returns:
            Oportunidad de arbitraje
        """
        try:
            # Precios de compra
            cop_buy_price = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat="COP",
                trade_type="BUY"
            )

            ves_buy_price = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat="VES",
                trade_type="BUY"
            )

            # Precios de venta
            cop_sell_price = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat="COP",
                trade_type="SELL"
            )

            ves_sell_price = await self.p2p_service.get_best_price(
                asset="USDT",
                fiat="VES",
                trade_type="SELL"
            )

            # TRM
            trm = await self.trm_service.get_current_trm()

            # Estrategia 1: Comprar en COP, vender en VES
            strategy_1_profit = self._calculate_cross_profit(
                buy_price_cop=cop_buy_price,
                sell_price_ves=ves_sell_price,
                trm=trm
            )

            # Estrategia 2: Comprar en VES, vender en COP
            strategy_2_profit = self._calculate_cross_profit(
                buy_price_ves=ves_buy_price,
                sell_price_cop=cop_sell_price,
                trm=trm
            )

            best_strategy = strategy_1_profit if strategy_1_profit["profit_percentage"] > strategy_2_profit["profit_percentage"] else strategy_2_profit

            best_strategy["is_profitable"] = best_strategy["profit_percentage"] > settings.ARBITRAGE_MIN_PROFIT

            return best_strategy

        except Exception as e:
            logger.error("Error analyzing cross currency arbitrage", error=str(e))
            return {
                "strategy": "cross_currency",
                "is_profitable": False,
                "error": str(e)
            }

    def _calculate_cross_profit(
        self,
        buy_price_cop: float = 0,
        sell_price_ves: float = 0,
        buy_price_ves: float = 0,
        sell_price_cop: float = 0,
        trm: float = 4000
    ) -> Dict:
        """Calcular profit de arbitraje cross-currency"""

        if buy_price_cop and sell_price_ves:
            # COP -> VES
            cost_usd = buy_price_cop / trm
            revenue_usd = sell_price_ves / 36.5  # Ajustar con tasa real
            direction = "COP -> VES"

        elif buy_price_ves and sell_price_cop:
            # VES -> COP
            cost_usd = buy_price_ves / 36.5
            revenue_usd = sell_price_cop / trm
            direction = "VES -> COP"

        else:
            return {"profit_percentage": 0}

        profit = revenue_usd - cost_usd
        profit_percentage = (profit / cost_usd) * 100

        return {
            "strategy": "cross_currency",
            "direction": direction,
            "cost_usd": cost_usd,
            "revenue_usd": revenue_usd,
            "profit_percentage": round(profit_percentage, 2)
        }

    def _calculate_recommended_amount(self, profit_percentage: float) -> float:
        """
        Calcular monto recomendado según profit.

        Args:
            profit_percentage: Porcentaje de ganancia

        Returns:
            Monto en USD recomendado
        """
        if profit_percentage < settings.ARBITRAGE_MIN_PROFIT:
            return 0

        # Más profit = mayor monto recomendado
        if profit_percentage >= 5.0:
            return settings.MAX_TRADE_AMOUNT
        elif profit_percentage >= 3.0:
            return settings.MAX_TRADE_AMOUNT * 0.7
        elif profit_percentage >= 2.0:
            return settings.MAX_TRADE_AMOUNT * 0.5
        else:
            return settings.MIN_TRADE_AMOUNT

    async def execute_spot_trade(
        self,
        symbol: str,
        side: str,
        amount_usd: float
    ) -> Optional[Dict]:
        """
        Ejecutar trade en Spot.

        Args:
            symbol: Par (ej: USDCUSDT)
            side: BUY o SELL
            amount_usd: Cantidad en USD

        Returns:
            Resultado de la operación
        """
        try:
            # Obtener info del símbolo
            symbol_info = await self.spot_service.get_symbol_info(symbol)

            if not symbol_info:
                logger.error("Symbol info not found", symbol=symbol)
                return None

            # Obtener precio actual
            price = await self.spot_service.get_spot_price(symbol)

            # Calcular cantidad
            quantity = self.spot_service.calculate_quantity(
                price=price,
                notional=amount_usd,
                step_size=symbol_info['step_size']
            )

            # Ejecutar orden de mercado
            order = await self.spot_service.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity
            )

            if order:
                logger.info(
                    "Spot trade executed successfully",
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_id=order['orderId']
                )

            return order

        except Exception as e:
            logger.error("Error executing spot trade", symbol=symbol, error=str(e))
            return None

    async def get_inventory_status(self) -> Dict:
        """
        Obtener estado del inventario de criptomonedas.

        Returns:
            Balance de activos principales
        """
        balances = await self.spot_service.get_all_balances()

        # Calcular valor total en USD
        total_usd = 0.0
        for asset, amount in balances.items():
            if asset == "USDT":
                total_usd += amount
            # Aquí podrías agregar conversión de otros assets a USD

        return {
            "balances": balances,
            "total_usd": round(total_usd, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
