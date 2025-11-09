"""
Dynamic Pricing Service - Sistema de precios dinámicos inteligente

Características:
1. Ajuste por volatilidad
2. Ajuste por volumen
3. Ajuste por hora del día
4. Ajuste por competencia
5. Ajuste por inventario
6. Predicción de demanda
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import numpy as np
from app.services.binance_service import BinanceService
from app.services.competitive_pricing_service import CompetitivePricingService
from app.services.liquidity_analysis_service import LiquidityAnalysisService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DynamicPricingService:
    """
    Servicio de precios dinámicos que ajusta precios en tiempo real
    basado en múltiples factores del mercado.
    """

    def __init__(self):
        self.p2p_service = BinanceService()
        self.competitive_service = CompetitivePricingService()
        self.liquidity_service = LiquidityAnalysisService()

        # Configuración de márgenes base
        self.BASE_MARGIN_COP = settings.PROFIT_MARGIN_COP
        self.BASE_MARGIN_VES = settings.PROFIT_MARGIN_VES

        # Factores de ajuste
        self.VOLATILITY_ADJUSTMENT = {
            "low": 0.8,      # Volatilidad < 1%: margen reducido
            "medium": 1.0,   # Volatilidad 1-2%: margen estándar
            "high": 1.5,     # Volatilidad > 2%: margen aumentado
        }

        self.VOLUME_DISCOUNTS = {
            (0, 1000): 0.0,           # Sin descuento
            (1000, 5000): -0.1,       # -0.1% margen
            (5000, 10000): -0.2,      # -0.2% margen
            (10000, float('inf')): -0.3,  # -0.3% margen
        }

        # Historial de precios para cálculo de volatilidad
        self.price_history: Dict[str, List[float]] = {}
        self.max_history_size = 100

    async def calculate_dynamic_price(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        trade_type: str = "SELL",
        amount_usd: float = 1000.0,
        base_margin: Optional[float] = None
    ) -> Dict:
        """
        Calcula precio dinámico considerando múltiples factores.

        Args:
            asset: Criptomoneda (USDT, BTC, etc.)
            fiat: Moneda fiat (COP, VES, etc.)
            trade_type: BUY o SELL
            amount_usd: Cantidad en USD
            base_margin: Margen base (opcional)

        Returns:
            Precio dinámico con justificación
        """

        try:
            # 1. Obtener precio base competitivo
            competitive_prices = await self.competitive_service.calculate_competitive_prices(
                asset=asset,
                fiat=fiat
            )

            if not competitive_prices.get("success"):
                return {"success": False, "error": "No se pudo obtener precio base"}

            base_price = (
                competitive_prices["our_prices"]["buy_price"]
                if trade_type == "BUY"
                else competitive_prices["our_prices"]["sell_price"]
            )

            base_margin_pct = base_margin or (
                self.BASE_MARGIN_COP if fiat == "COP" else self.BASE_MARGIN_VES
            )

            # 2. Calcular factores de ajuste
            adjustments = await self._calculate_all_adjustments(
                asset=asset,
                fiat=fiat,
                amount_usd=amount_usd,
                base_margin_pct=base_margin_pct
            )

            # 3. Aplicar ajustes
            final_margin_pct = base_margin_pct
            adjustment_details = []

            # Ajuste por volatilidad
            if adjustments["volatility"]["adjustment"] != 0:
                final_margin_pct += adjustments["volatility"]["adjustment"]
                adjustment_details.append({
                    "factor": "volatilidad",
                    "value": adjustments["volatility"]["value"],
                    "adjustment": adjustments["volatility"]["adjustment"],
                    "reason": adjustments["volatility"]["reason"]
                })

            # Ajuste por volumen
            if adjustments["volume"]["adjustment"] != 0:
                final_margin_pct += adjustments["volume"]["adjustment"]
                adjustment_details.append({
                    "factor": "volumen",
                    "value": amount_usd,
                    "adjustment": adjustments["volume"]["adjustment"],
                    "reason": adjustments["volume"]["reason"]
                })

            # Ajuste por hora del día
            if adjustments["time"]["adjustment"] != 0:
                final_margin_pct += adjustments["time"]["adjustment"]
                adjustment_details.append({
                    "factor": "hora_del_dia",
                    "value": adjustments["time"]["hour"],
                    "adjustment": adjustments["time"]["adjustment"],
                    "reason": adjustments["time"]["reason"]
                })

            # Ajuste por competencia
            if adjustments["competition"]["adjustment"] != 0:
                final_margin_pct += adjustments["competition"]["adjustment"]
                adjustment_details.append({
                    "factor": "competencia",
                    "value": adjustments["competition"]["market_price"],
                    "adjustment": adjustments["competition"]["adjustment"],
                    "reason": adjustments["competition"]["reason"]
                })

            # Ajuste por inventario
            if adjustments["inventory"]["adjustment"] != 0:
                final_margin_pct += adjustments["inventory"]["adjustment"]
                adjustment_details.append({
                    "factor": "inventario",
                    "value": adjustments["inventory"]["ratio"],
                    "adjustment": adjustments["inventory"]["adjustment"],
                    "reason": adjustments["inventory"]["reason"]
                })

            # Limitar margen entre 0.3% y 5%
            final_margin_pct = max(0.3, min(5.0, final_margin_pct))

            # 4. Calcular precio final
            market_price = (
                competitive_prices["market_reference"]["buy_vwap"]
                if trade_type == "BUY"
                else competitive_prices["market_reference"]["sell_vwap"]
            )

            if trade_type == "BUY":
                # Para comprar: pagamos más que el mercado
                final_price = market_price * (1 + final_margin_pct / 100)
            else:
                # Para vender: cobramos menos que el mercado
                final_price = market_price * (1 - final_margin_pct / 100)

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "trade_type": trade_type,
                "amount_usd": amount_usd,
                "base_price": round(base_price, 2),
                "final_price": round(final_price, 2),
                "base_margin_pct": round(base_margin_pct, 2),
                "final_margin_pct": round(final_margin_pct, 2),
                "market_price": round(market_price, 2),
                "adjustments": adjustment_details,
                "total_adjustment_pct": round(final_margin_pct - base_margin_pct, 2),
                "competitiveness": self._assess_competitiveness(
                    final_price,
                    market_price,
                    trade_type
                ),
                "recommendation": self._generate_recommendation(
                    final_margin_pct,
                    adjustments
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating dynamic price: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _calculate_all_adjustments(
        self,
        asset: str,
        fiat: str,
        amount_usd: float,
        base_margin_pct: float
    ) -> Dict:
        """Calcula todos los ajustes de precio"""

        adjustments = {
            "volatility": await self._calculate_volatility_adjustment(asset, fiat),
            "volume": self._calculate_volume_adjustment(amount_usd),
            "time": self._calculate_time_adjustment(),
            "competition": await self._calculate_competition_adjustment(asset, fiat),
            "inventory": await self._calculate_inventory_adjustment(asset, fiat),
        }

        return adjustments

    async def _calculate_volatility_adjustment(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """Calcula ajuste por volatilidad"""

        try:
            # Obtener histórico de precios
            prices = await self._get_price_history(asset, fiat)

            if len(prices) < 10:
                return {
                    "value": 0.0,
                    "level": "unknown",
                    "adjustment": 0.0,
                    "reason": "Datos insuficientes para calcular volatilidad"
                }

            # Calcular volatilidad (desviación estándar de retornos)
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1] * 100
                    returns.append(ret)

            if not returns:
                return {
                    "value": 0.0,
                    "level": "unknown",
                    "adjustment": 0.0,
                    "reason": "No se pudieron calcular retornos"
                }

            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0

            # Obtener margen base para cálculo
            base_margin = self.BASE_MARGIN_COP if fiat == "COP" else self.BASE_MARGIN_VES

            # Clasificar volatilidad
            if volatility < 1.0:
                level = "low"
                adjustment = base_margin * (self.VOLATILITY_ADJUSTMENT["low"] - 1.0)
                reason = f"Volatilidad baja ({volatility:.2f}%) - Margen competitivo"
            elif volatility < 2.0:
                level = "medium"
                adjustment = 0.0
                reason = f"Volatilidad media ({volatility:.2f}%) - Margen estándar"
            else:
                level = "high"
                adjustment = base_margin * (self.VOLATILITY_ADJUSTMENT["high"] - 1.0)
                reason = f"Volatilidad alta ({volatility:.2f}%) - Margen protector"

            return {
                "value": round(volatility, 2),
                "level": level,
                "adjustment": round(adjustment, 2),
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Error calculating volatility adjustment: {str(e)}")
            return {
                "value": 0.0,
                "level": "unknown",
                "adjustment": 0.0,
                "reason": f"Error: {str(e)}"
            }

    def _calculate_volume_adjustment(self, amount_usd: float) -> Dict:
        """Calcula descuento por volumen"""

        discount = 0.0
        reason = "Sin descuento por volumen"

        for (min_vol, max_vol), disc in self.VOLUME_DISCOUNTS.items():
            if min_vol <= amount_usd < max_vol:
                discount = disc
                if disc < 0:
                    reason = f"Descuento de {abs(disc):.1f}% por volumen de ${amount_usd:,.0f}"
                break

        return {
            "value": amount_usd,
            "adjustment": discount,
            "reason": reason
        }

    def _calculate_time_adjustment(self) -> Dict:
        """Calcula ajuste por hora del día"""

        now = datetime.utcnow()
        hour = now.hour

        # Horas pico: 14:00-22:00 UTC (horario América Latina)
        if 14 <= hour <= 22:
            adjustment = 0.0
            reason = "Hora pico - Margen competitivo"
        # Horas bajas: 00:00-08:00 UTC
        elif 0 <= hour < 8:
            adjustment = 0.2  # Aumentar margen 0.2%
            reason = "Hora baja - Margen aumentado por menor liquidez"
        else:
            adjustment = 0.1  # Aumentar margen 0.1%
            reason = "Hora intermedia - Margen ligeramente aumentado"

        return {
            "hour": hour,
            "adjustment": adjustment,
            "reason": reason
        }

    async def _calculate_competition_adjustment(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """Calcula ajuste basado en competencia"""

        try:
            # Obtener mejor precio del mercado
            market_data = await self.competitive_service.calculate_market_trm(
                asset=asset,
                fiat=fiat,
                sample_size=10
            )

            if not market_data.get("success"):
                return {
                    "market_price": 0.0,
                    "adjustment": 0.0,
                    "reason": "No se pudo obtener datos de mercado"
                }

            best_buy = market_data["buy_side"]["best"]
            best_sell = market_data["sell_side"]["best"]

            # Si la competencia tiene precios muy competitivos, ajustar
            market_spread = market_data["market_spread"]["percentage"]

            if market_spread < 1.0:
                # Mercado muy competitivo, reducir margen ligeramente
                adjustment = -0.1
                reason = "Mercado muy competitivo - Reducir margen ligeramente"
            elif market_spread > 3.0:
                # Mercado con spread alto, podemos aumentar margen
                adjustment = 0.2
                reason = "Mercado con spread alto - Aumentar margen"
            else:
                adjustment = 0.0
                reason = "Competencia normal - Sin ajuste"

            return {
                "market_price": (best_buy + best_sell) / 2,
                "market_spread": market_spread,
                "adjustment": adjustment,
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Error calculating competition adjustment: {str(e)}")
            return {
                "market_price": 0.0,
                "adjustment": 0.0,
                "reason": f"Error: {str(e)}"
            }

    async def _calculate_inventory_adjustment(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """
        Calcula ajuste basado en inventario.
        
        Si inventario bajo en un lado, aumentar margen en ese lado
        para desincentivar operaciones.
        """

        try:
            # TODO: Implementar cuando tengamos sistema de inventario
            # Por ahora, retornar sin ajuste
            return {
                "ratio": 1.0,
                "adjustment": 0.0,
                "reason": "Sistema de inventario no implementado aún"
            }

        except Exception as e:
            logger.error(f"Error calculating inventory adjustment: {str(e)}")
            return {
                "ratio": 1.0,
                "adjustment": 0.0,
                "reason": f"Error: {str(e)}"
            }

    async def _get_price_history(
        self,
        asset: str,
        fiat: str,
        limit: int = 100
    ) -> List[float]:
        """Obtiene histórico de precios"""

        key = f"{asset}_{fiat}"

        if key not in self.price_history:
            self.price_history[key] = []

        # Si no hay historial, obtener precios actuales
        if len(self.price_history[key]) < 10:
            try:
                best_price = await self.p2p_service.get_best_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type="SELL"
                )
                if best_price:
                    self.price_history[key].append(best_price)
            except Exception:
                pass

        # Mantener solo últimos N precios
        if len(self.price_history[key]) > self.max_history_size:
            self.price_history[key] = self.price_history[key][-self.max_history_size:]

        return self.price_history[key]

    def _assess_competitiveness(
        self,
        our_price: float,
        market_price: float,
        trade_type: str
    ) -> Dict:
        """Evalúa qué tan competitivo es nuestro precio"""

        if trade_type == "BUY":
            # Para comprar: queremos pagar más (precio más alto)
            advantage = ((our_price - market_price) / market_price) * 100
            is_competitive = advantage > 0
        else:
            # Para vender: queremos cobrar menos (precio más bajo)
            advantage = ((market_price - our_price) / market_price) * 100
            is_competitive = advantage > 0

        if advantage > 0.5:
            rating = "MUY_COMPETITIVO"
        elif advantage > 0.2:
            rating = "COMPETITIVO"
        elif advantage > 0:
            rating = "MODERADO"
        else:
            rating = "NO_COMPETITIVO"

        return {
            "advantage_pct": round(advantage, 2),
            "is_competitive": is_competitive,
            "rating": rating
        }

    def _generate_recommendation(
        self,
        final_margin_pct: float,
        adjustments: Dict
    ) -> str:
        """Genera recomendación basada en precio final"""

        total_adjustment = sum(
            adj.get("adjustment", 0) for adj in adjustments.values()
        )

        if final_margin_pct < 0.5:
            return "⚠️ MARGEN MUY BAJO - Riesgo de no rentabilidad"
        elif final_margin_pct > 3.0:
            return "⚠️ MARGEN ALTO - Puede reducir volumen"
        elif total_adjustment > 0.5:
            return "✅ PRECIO OPTIMIZADO - Buena competitividad con rentabilidad"
        else:
            return "✅ PRECIO ESTÁNDAR - Balance adecuado"

    async def update_price_history(
        self,
        asset: str,
        fiat: str,
        price: float
    ):
        """Actualiza historial de precios"""

        key = f"{asset}_{fiat}"
        if key not in self.price_history:
            self.price_history[key] = []

        self.price_history[key].append(price)

        # Mantener solo últimos N precios
        if len(self.price_history[key]) > self.max_history_size:
            self.price_history[key] = self.price_history[key][-self.max_history_size:]

    async def get_pricing_summary(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """Obtiene resumen completo de pricing dinámico"""

        try:
            # Precios para diferentes volúmenes
            volumes = [500, 1000, 5000, 10000]
            prices_by_volume = []

            for vol in volumes:
                buy_price = await self.calculate_dynamic_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type="BUY",
                    amount_usd=vol
                )
                sell_price = await self.calculate_dynamic_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type="SELL",
                    amount_usd=vol
                )

                if buy_price.get("success") and sell_price.get("success"):
                    prices_by_volume.append({
                        "volume_usd": vol,
                        "buy_price": buy_price["final_price"],
                        "sell_price": sell_price["final_price"],
                        "spread": sell_price["final_price"] - buy_price["final_price"],
                        "spread_pct": (
                            (sell_price["final_price"] - buy_price["final_price"]) /
                            buy_price["final_price"] * 100
                        )
                    })

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "prices_by_volume": prices_by_volume,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting pricing summary: {str(e)}")
            return {"success": False, "error": str(e)}

