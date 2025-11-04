"""
Competitive Pricing Service - Servicio de precios competitivos basado en mercado P2P

Estrategia:
1. Analizar precios P2P de Binance en tiempo real
2. Calcular "TRM de mercado" (precio promedio ponderado)
3. Posicionar precios competitivos que sean mejores que el mercado
4. Considerar TODAS las comisiones de Binance
5. Maximizar volumen manteniendo rentabilidad
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import statistics
from app.services.binance_service import BinanceService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CompetitivePricingService:
    """
    Servicio para determinar precios competitivos basados en el mercado P2P real
    """

    def __init__(self):
        self.p2p_service = BinanceService()

        # Comisiones de Binance (todas las que aplican)
        self.BINANCE_FEES = {
            "p2p": 0.0,           # P2P es GRATIS
            "spot": 0.001,         # 0.1% en Spot
            "withdrawal_usdt_trc20": 1.0,   # $1 USDT en TRC20
            "withdrawal_usdt_erc20": 10.0,  # $10 USDT en ERC20 (más caro)
        }

        # Margen mínimo de ganancia deseado (configurable)
        self.MIN_PROFIT_MARGIN_PCT = 0.5  # 0.5% mínimo
        self.IDEAL_PROFIT_MARGIN_PCT = 1.5  # 1.5% ideal

    async def calculate_market_trm(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        sample_size: int = 20
    ) -> Dict:
        """
        Calcula la "TRM de mercado" basada en precios P2P reales de Binance

        En lugar de usar TRM oficial, usamos el precio REAL del mercado P2P
        como referencia, ya que refleja la oferta/demanda actual.

        Métodos de cálculo:
        1. Precio medio simple
        2. Precio medio ponderado por volumen (VWAP)
        3. Percentiles (P25, P50-mediana, P75)
        """

        try:
            # Obtener órdenes de compra (lo que pagan por USDT)
            buy_orders = await self.p2p_service.get_p2p_ads(
                asset=asset, fiat=fiat, trade_type="BUY", rows=sample_size
            )

            # Obtener órdenes de venta (lo que cobran por USDT)
            sell_orders = await self.p2p_service.get_p2p_ads(
                asset=asset, fiat=fiat, trade_type="SELL", rows=sample_size
            )

            if not buy_orders or not sell_orders:
                return {
                    "success": False,
                    "error": "No market data available"
                }

            # Extraer precios y volúmenes
            buy_prices = []
            buy_volumes = []
            for order in buy_orders:
                try:
                    price = float(order["adv"]["price"])
                    volume = float(order["adv"].get("tradableQuantity", 0))
                    buy_prices.append(price)
                    buy_volumes.append(volume)
                except (KeyError, ValueError):
                    continue

            sell_prices = []
            sell_volumes = []
            for order in sell_orders:
                try:
                    price = float(order["adv"]["price"])
                    volume = float(order["adv"].get("tradableQuantity", 0))
                    sell_prices.append(price)
                    sell_volumes.append(volume)
                except (KeyError, ValueError):
                    continue

            # Calcular métricas de BUY (lo que pagan)
            buy_mean = statistics.mean(buy_prices) if buy_prices else 0
            buy_median = statistics.median(buy_prices) if buy_prices else 0
            buy_vwap = self._calculate_vwap(buy_prices, buy_volumes)

            # Calcular métricas de SELL (lo que cobran)
            sell_mean = statistics.mean(sell_prices) if sell_prices else 0
            sell_median = statistics.median(sell_prices) if sell_prices else 0
            sell_vwap = self._calculate_vwap(sell_prices, sell_volumes)

            # TRM de mercado = punto medio entre compra y venta
            market_trm_mean = (buy_mean + sell_mean) / 2
            market_trm_median = (buy_median + sell_median) / 2
            market_trm_vwap = (buy_vwap + sell_vwap) / 2

            # Spread del mercado
            market_spread = sell_mean - buy_mean
            market_spread_pct = (market_spread / buy_mean * 100) if buy_mean > 0 else 0

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "market_trm": {
                    "simple_average": market_trm_mean,
                    "mean": market_trm_mean,
                    "median": market_trm_median,
                    "vwap": market_trm_vwap,
                    "recommended": market_trm_vwap,  # VWAP es el más preciso
                    "p25": statistics.quantiles(buy_prices + sell_prices, n=4)[0] if len(buy_prices + sell_prices) >= 4 else (market_trm_median if market_trm_median > 0 else 0),
                    "p75": statistics.quantiles(buy_prices + sell_prices, n=4)[2] if len(buy_prices + sell_prices) >= 4 else (market_trm_median if market_trm_median > 0 else 0),
                },
                "buy_side": {
                    "average_price": buy_mean,
                    "mean": buy_mean,
                    "median": buy_median,
                    "vwap": buy_vwap,
                    "best": max(buy_prices) if buy_prices else 0,  # Mejor precio para vender a ellos
                    "worst": min(buy_prices) if buy_prices else 0,
                    "total_volume": sum(buy_volumes),
                    "num_orders": len(buy_prices),
                },
                "sell_side": {
                    "average_price": sell_mean,
                    "mean": sell_mean,
                    "median": sell_median,
                    "vwap": sell_vwap,
                    "best": min(sell_prices) if sell_prices else 0,  # Mejor precio para comprar de ellos
                    "worst": max(sell_prices) if sell_prices else 0,
                    "total_volume": sum(sell_volumes),
                    "num_orders": len(sell_prices),
                },
                "market_spread": {
                    "absolute": market_spread,
                    "percentage": market_spread_pct,
                },
                "sample_size": {
                    "buy_orders": len(buy_prices),
                    "sell_orders": len(sell_prices),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating market TRM: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calculate_vwap(self, prices: List[float], volumes: List[float]) -> float:
        """
        Calcula Volume-Weighted Average Price (VWAP)

        VWAP = Σ(precio * volumen) / Σ(volumen)
        Es más preciso que el promedio simple porque considera el volumen
        """
        if not prices or not volumes or len(prices) != len(volumes):
            return 0

        total_value = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        return total_value / total_volume if total_volume > 0 else 0

    async def calculate_competitive_prices(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        our_margin_pct: Optional[float] = None
    ) -> Dict:
        """
        Calcula precios competitivos para NUESTRAS operaciones

        Estrategia:
        1. Analizar precios del mercado P2P
        2. Posicionarnos MEJOR que el promedio (para ganar volumen)
        3. Mantener margen de ganancia suficiente
        4. Considerar TODAS las comisiones

        Returns:
            - our_buy_price: Precio al que NOSOTROS compramos USDT (pagar más que el mercado)
            - our_sell_price: Precio al que NOSOTROS vendemos USDT (cobrar menos que el mercado)
        """

        try:
            # 1. Obtener TRM de mercado
            market_data = await self.calculate_market_trm(asset, fiat)

            if not market_data.get("success"):
                return market_data

            market_buy_vwap = market_data["buy_side"]["vwap"]
            market_sell_vwap = market_data["sell_side"]["vwap"]
            market_spread_pct = market_data["market_spread"]["percentage"]

            # 2. Determinar nuestro margen de ganancia
            our_margin = our_margin_pct if our_margin_pct is not None else self.IDEAL_PROFIT_MARGIN_PCT

            # 3. Calcular precios competitivos

            # Para COMPRAR USDT (nosotros pagamos):
            # Queremos pagar MÁS que el mercado para ser atractivos
            # Pero no tanto que perdamos rentabilidad
            competitiveness_factor = 0.003  # 0.3% mejor que el mercado

            our_buy_price = market_buy_vwap * (1 + competitiveness_factor)

            # Para VENDER USDT (nosotros cobramos):
            # Queremos cobrar MENOS que el mercado para ser atractivos
            # Pero mantener margen suficiente
            our_sell_price = market_sell_vwap * (1 - competitiveness_factor)

            # 4. Verificar que el spread sea suficiente para rentabilidad
            our_spread = our_sell_price - our_buy_price
            our_spread_pct = (our_spread / our_buy_price * 100) if our_buy_price > 0 else 0

            # 5. Calcular profit real considerando comisiones
            profit_analysis = self._analyze_profit_with_fees(
                buy_price=our_buy_price,
                sell_price=our_sell_price,
                fiat=fiat
            )

            # 6. Ajustar si el profit es insuficiente
            if profit_analysis["net_profit_pct"] < self.MIN_PROFIT_MARGIN_PCT:
                logger.warning(
                    f"Profit insuficiente ({profit_analysis['net_profit_pct']:.2f}%), ajustando precios"
                )

                # Ajustar precios para alcanzar margen mínimo
                required_spread_pct = self.MIN_PROFIT_MARGIN_PCT + (
                    self.BINANCE_FEES["spot"] * 100 * 2  # Spot fees ida y vuelta
                ) + 0.5  # Buffer adicional

                # Recalcular precios
                market_mid = (market_buy_vwap + market_sell_vwap) / 2
                half_spread = (market_mid * required_spread_pct / 100) / 2

                our_buy_price = market_mid - half_spread
                our_sell_price = market_mid + half_spread

                # Recalcular profit
                profit_analysis = self._analyze_profit_with_fees(
                    buy_price=our_buy_price,
                    sell_price=our_sell_price,
                    fiat=fiat
                )

            # 7. Comparar con competencia
            competitiveness = self._assess_competitiveness(
                our_buy=our_buy_price,
                our_sell=our_sell_price,
                market_buy=market_buy_vwap,
                market_sell=market_sell_vwap
            )

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "our_prices": {
                    "buy_price": round(our_buy_price, 2),  # Lo que NOSOTROS pagamos por USDT
                    "sell_price": round(our_sell_price, 2),  # Lo que NOSOTROS cobramos por USDT
                    "spread_absolute": round(our_spread, 2),
                    "spread_percentage": round(our_spread_pct, 2),
                },
                "market_reference": {
                    "buy_vwap": round(market_buy_vwap, 2),
                    "sell_vwap": round(market_sell_vwap, 2),
                    "spread_percentage": round(market_spread_pct, 2),
                },
                "profit_analysis": profit_analysis,
                "competitiveness": competitiveness,
                "recommendation": self._generate_pricing_recommendation(
                    competitiveness,
                    profit_analysis
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating competitive prices: {str(e)}")
            return {"success": False, "error": str(e)}

    def _analyze_profit_with_fees(
        self,
        buy_price: float,
        sell_price: float,
        fiat: str,
        amount_usd: float = 1000.0
    ) -> Dict:
        """
        Analiza el profit REAL considerando TODAS las comisiones de Binance

        Flujo completo:
        1. Cliente nos da fiat
        2. Compramos USDT en P2P (0% fee)
        3. (Opcional) Movemos a Spot
        4. (Opcional) Trading en Spot (0.1% fee)
        5. Vendemos USDT en P2P (0% fee)
        6. Cliente recibe fiat
        """

        # Paso 1: Comprar USDT con fiat del cliente
        fiat_received = buy_price * amount_usd
        usdt_bought = amount_usd  # Compramos en P2P (0% fee)

        # Paso 2: (Si hacemos arbitraje Spot)
        spot_fees = 0  # Si NO usamos Spot
        # spot_fees = usdt_bought * self.BINANCE_FEES["spot"]  # Si usamos Spot

        usdt_after_fees = usdt_bought - spot_fees

        # Paso 3: Vender USDT al cliente final
        fiat_paid = sell_price * usdt_after_fees

        # Profit
        gross_profit = fiat_paid - fiat_received
        gross_profit_pct = (gross_profit / fiat_received * 100) if fiat_received > 0 else 0

        # Fees totales
        total_fees = spot_fees * sell_price  # Convertir fees a fiat

        net_profit = gross_profit - total_fees
        net_profit_pct = (net_profit / fiat_received * 100) if fiat_received > 0 else 0

        return {
            "amount_usd": amount_usd,
            "fiat_currency": fiat,
            "fiat_received_from_client": round(fiat_received, 2),
            "fiat_paid_to_client": round(fiat_paid, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_profit_pct": round(gross_profit_pct, 2),
            "total_fees": round(total_fees, 2),
            "net_profit": round(net_profit, 2),
            "net_profit_pct": round(net_profit_pct, 2),
            "is_profitable": net_profit_pct >= self.MIN_PROFIT_MARGIN_PCT,
        }

    def _assess_competitiveness(
        self,
        our_buy: float,
        our_sell: float,
        market_buy: float,
        market_sell: float
    ) -> Dict:
        """
        Evalúa qué tan competitivos son nuestros precios vs el mercado

        Queremos:
        - Pagar MÁS que el mercado cuando compramos (atractivo para vendedores)
        - Cobrar MENOS que el mercado cuando vendemos (atractivo para compradores)
        """

        # ¿Cuánto mejor pagamos al comprar?
        buy_advantage_pct = ((our_buy - market_buy) / market_buy * 100) if market_buy > 0 else 0

        # ¿Cuánto mejor cobramos al vender?
        sell_advantage_pct = ((market_sell - our_sell) / market_sell * 100) if market_sell > 0 else 0

        # Score general de competitividad (0-100)
        # Basado en qué tan competitivos somos:
        # - Si pagamos 0.5% más que el mercado = +25 puntos
        # - Si cobramos 0.5% menos que el mercado = +25 puntos
        # - Máximo 100 puntos
        
        # Normalizar ventajas (0.5% = 50 puntos, 1% = 100 puntos, etc.)
        buy_score = max(0, min(50, buy_advantage_pct * 100))  # 0.5% = 50 puntos máx
        sell_score = max(0, min(50, sell_advantage_pct * 100))  # 0.5% = 50 puntos máx
        
        competitiveness_score = buy_score + sell_score
        competitiveness_score = min(100, max(0, competitiveness_score))

        rating = (
            "MUY_COMPETITIVO" if competitiveness_score >= 80 else
            "COMPETITIVO" if competitiveness_score >= 60 else
            "MODERADO" if competitiveness_score >= 40 else
            "MEJORABLE" if competitiveness_score >= 20 else
            "NO_COMPETITIVO"
        )

        return {
            "buy_advantage_pct": round(buy_advantage_pct, 2),
            "sell_advantage_pct": round(sell_advantage_pct, 2),
            "overall_score": round(competitiveness_score, 2),
            "rating": rating,
            "buy_competitive": buy_advantage_pct > 0,
            "sell_competitive": sell_advantage_pct > 0,
            "message": self._generate_competitiveness_message(
                buy_advantage_pct,
                sell_advantage_pct
            )
        }

    def _generate_competitiveness_message(
        self,
        buy_adv: float,
        sell_adv: float
    ) -> str:
        """Genera mensaje explicativo sobre competitividad"""

        if buy_adv > 0 and sell_adv > 0:
            return f"🔥 EXCELENTE: Pagamos {buy_adv:.2f}% MÁS y cobramos {sell_adv:.2f}% MENOS que el mercado"
        elif buy_adv > 0:
            return f"✅ BUENO: Pagamos {buy_adv:.2f}% más al comprar, pero nuestro precio de venta podría mejorar"
        elif sell_adv > 0:
            return f"✅ BUENO: Cobramos {sell_adv:.2f}% menos al vender, pero nuestro precio de compra podría mejorar"
        else:
            return "⚠️ ADVERTENCIA: Nuestros precios NO son competitivos vs el mercado"

    def _generate_pricing_recommendation(
        self,
        competitiveness: Dict,
        profit_analysis: Dict
    ) -> str:
        """Genera recomendación final de pricing"""

        is_profitable = profit_analysis["is_profitable"]
        is_competitive = competitiveness["overall_score"] >= 40

        if is_profitable and is_competitive:
            return "🚀 USAR ESTOS PRECIOS - Son competitivos y rentables"
        elif is_profitable and not is_competitive:
            return "⚠️ MEJORAR COMPETITIVIDAD - Son rentables pero pocos clientes elegirán estos precios"
        elif not is_profitable and is_competitive:
            return "❌ AJUSTAR MARGEN - Son atractivos pero no rentables"
        else:
            return "❌ RECALCULAR - Ni competitivos ni rentables"

    async def get_pricing_strategy_summary(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """
        Resumen completo de estrategia de precios

        Combina:
        - TRM de mercado
        - Precios competitivos recomendados
        - Análisis de rentabilidad
        - Comparación con competencia
        """

        try:
            # Calcular TRM de mercado
            market_data = await self.calculate_market_trm(asset, fiat)

            if not market_data.get("success"):
                return market_data

            # Calcular precios competitivos
            pricing_data = await self.calculate_competitive_prices(asset, fiat)

            if not pricing_data.get("success"):
                return pricing_data

            # Análisis de oportunidades
            opportunities = []

            # Oportunidad de compra
            if pricing_data["our_prices"]["buy_price"] > market_data["buy_side"]["vwap"]:
                opportunities.append({
                    "type": "buy_opportunity",
                    "message": f"Pagamos {pricing_data['our_prices']['buy_price']} vs mercado {market_data['buy_side']['vwap']:.2f}",
                    "advantage": "Atractivo para vendedores"
                })

            # Oportunidad de venta
            if pricing_data["our_prices"]["sell_price"] < market_data["sell_side"]["vwap"]:
                opportunities.append({
                    "type": "sell_opportunity",
                    "message": f"Cobramos {pricing_data['our_prices']['sell_price']} vs mercado {market_data['sell_side']['vwap']:.2f}",
                    "advantage": "Atractivo para compradores"
                })

            # Generate recommendations, risks, and action plan
            recommendations = []
            risks = []
            action_plan = []

            # Recommendations based on competitiveness
            if pricing_data["competitiveness"]["overall_score"] >= 80:
                recommendations.append("Precios muy competitivos - Maximizar volumen")
                recommendations.append("Mantener monitoreo activo del mercado")
            elif pricing_data["competitiveness"]["overall_score"] >= 60:
                recommendations.append("Precios competitivos - Buen balance profit/volumen")
            else:
                recommendations.append("Mejorar competitividad para aumentar volumen")
                recommendations.append("Considerar reducir margen de ganancia")

            if pricing_data["profit_analysis"]["net_profit_pct"] >= 1.0:
                recommendations.append(f"Margen saludable de {pricing_data['profit_analysis']['net_profit_pct']:.2f}%")

            # Risks
            if abs(market_data["market_spread"]["percentage"]) > 1.0:
                risks.append(f"Spread alto del mercado ({abs(market_data['market_spread']['percentage']):.2f}%) indica volatilidad")

            if not pricing_data["competitiveness"]["buy_competitive"]:
                risks.append("Precio de compra no competitivo - Pocos vendedores elegirán tu oferta")

            if not pricing_data["competitiveness"]["sell_competitive"]:
                risks.append("Precio de venta no competitivo - Pocos compradores elegirán tu oferta")

            if pricing_data["profit_analysis"]["net_profit_pct"] < 0.5:
                risks.append("Margen de ganancia muy ajustado - Vulnerable a fluctuaciones")

            # Action plan
            action_plan.append("Monitorear precios del mercado cada 1-5 minutos")
            action_plan.append(f"Publicar orden de COMPRA a {pricing_data['our_prices']['buy_price']:.2f} {fiat}")
            action_plan.append(f"Publicar orden de VENTA a {pricing_data['our_prices']['sell_price']:.2f} {fiat}")

            if pricing_data["competitiveness"]["overall_score"] < 60:
                action_plan.append("Ajustar precios para mejorar competitividad")

            action_plan.append("Revisar y ajustar estrategia cada 30 minutos")

            # Mapear datos al formato esperado por el frontend
            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "market_trm": {
                    "fiat": market_data["fiat"],
                    "asset": market_data["asset"],
                    "buy_side": market_data["buy_side"],
                    "sell_side": market_data["sell_side"],
                    "market_trm": market_data["market_trm"],
                    "spread": market_data["market_spread"],  # Mapear market_spread a spread
                    "timestamp": market_data["timestamp"]
                },
                "competitive_prices": {
                    "our_prices": pricing_data["our_prices"],
                    "market_prices": {  # Mapear market_reference a market_prices
                        "buy_vwap": pricing_data["market_reference"]["buy_vwap"],
                        "sell_vwap": pricing_data["market_reference"]["sell_vwap"]
                    },
                    "competitiveness": pricing_data["competitiveness"],
                    "profit_analysis": {
                        "gross_margin": pricing_data["profit_analysis"]["gross_profit_pct"],
                        "net_margin_after_fees": pricing_data["profit_analysis"]["net_profit_pct"],
                        "binance_fees_total": pricing_data["profit_analysis"]["total_fees"],
                        "is_profitable": pricing_data["profit_analysis"]["is_profitable"]
                    }
                },
                "recommendations": recommendations,
                "risks": risks,
                "action_plan": action_plan,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting pricing strategy: {str(e)}")
            return {"success": False, "error": str(e)}
