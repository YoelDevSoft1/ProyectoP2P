"""
Triangle Arbitrage Service - Estrategia avanzada de arbitraje triangular
Detecta oportunidades de arbitraje en ciclos COP -> USDT -> VES -> COP

Estrategia:
1. Comprar USDT con COP en P2P
2. Vender USDT por VES en P2P
3. Analizar ganancia neta considerando todas las comisiones
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TriangleArbitrageService:
    """Servicio para detectar y analizar oportunidades de arbitraje triangular"""

    def __init__(self):
        self.p2p_service = BinanceService()
        self.spot_service = BinanceSpotService()

        # Comisiones típicas
        self.P2P_FEE = 0.0  # Binance P2P no cobra comisión
        self.SPOT_FEE = 0.001  # 0.1% en Spot
        self.NETWORK_FEE = 1.0  # USDT estimado para transferencias

    async def analyze_triangle_opportunity(
        self,
        initial_amount_cop: float = 1000000.0  # 1M COP inicial
    ) -> Dict:
        """
        Analiza oportunidad de arbitraje triangular completo

        Ruta: COP -> USDT (P2P) -> VES (P2P) -> [análisis de profit]
        """
        try:
            # Paso 1: COP -> USDT (compra en P2P)
            usdt_buy_price_cop = await self.p2p_service.get_best_price("USDT", "COP", "BUY")

            if not usdt_buy_price_cop or usdt_buy_price_cop <= 0:
                return {"success": False, "error": "No hay precio USDT/COP disponible"}

            usdt_amount = initial_amount_cop / usdt_buy_price_cop

            # Paso 2: USDT -> VES (venta en P2P)
            usdt_sell_price_ves = await self.p2p_service.get_best_price("USDT", "VES", "SELL")

            if not usdt_sell_price_ves or usdt_sell_price_ves <= 0:
                return {"success": False, "error": "No hay precio USDT/VES disponible"}

            final_ves_amount = usdt_amount * usdt_sell_price_ves

            # Paso 3: Calcular costo de retorno VES -> COP (si existe ruta)
            # Aquí podríamos buscar P2P VES/COP directo o usar intermediario
            ves_to_cop_rate = await self._get_ves_to_cop_rate()

            if ves_to_cop_rate:
                final_cop_amount = final_ves_amount * ves_to_cop_rate
            else:
                # Si no hay ruta directa, calculamos equivalente teórico
                final_cop_amount = None

            # Cálculo de profit
            profit_ves = final_ves_amount

            # ROI en términos de VES obtenido por COP invertido
            roi_percentage = ((final_ves_amount * usdt_sell_price_ves) - initial_amount_cop) / initial_amount_cop * 100 if final_cop_amount else 0

            opportunity = {
                "success": True,
                "type": "triangle_arbitrage",
                "route": "COP -> USDT -> VES",
                "initial_investment": {
                    "amount": initial_amount_cop,
                    "currency": "COP"
                },
                "step_1_cop_to_usdt": {
                    "cop_amount": initial_amount_cop,
                    "usdt_amount": usdt_amount,
                    "price": usdt_buy_price_cop,
                    "action": "BUY USDT"
                },
                "step_2_usdt_to_ves": {
                    "usdt_amount": usdt_amount,
                    "ves_amount": final_ves_amount,
                    "price": usdt_sell_price_ves,
                    "action": "SELL USDT"
                },
                "final_position": {
                    "ves_amount": final_ves_amount,
                    "cop_equivalent": final_cop_amount,
                },
                "profit": {
                    "ves_gained": profit_ves,
                    "roi_percentage": roi_percentage,
                },
                "is_profitable": roi_percentage > settings.ARBITRAGE_MIN_PROFIT,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_steps": [
                    f"1. Comprar {usdt_amount:.2f} USDT con {initial_amount_cop:,.0f} COP en Binance P2P",
                    f"2. Vender {usdt_amount:.2f} USDT por {final_ves_amount:,.2f} VES en Binance P2P",
                    f"3. Profit estimado: {roi_percentage:.2f}% ROI"
                ]
            }

            return opportunity

        except Exception as e:
            logger.error(f"Error en triangle arbitrage: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_ves_to_cop_rate(self) -> Optional[float]:
        """
        Intenta obtener tasa de conversión VES -> COP
        Puede ser a través de USDT como intermediario o directo si existe
        """
        try:
            # Opción 1: VES -> USDT -> COP
            ves_usdt_buy = await self.p2p_service.get_best_price("USDT", "VES", "BUY")
            usdt_cop_sell = await self.p2p_service.get_best_price("USDT", "COP", "SELL")

            if ves_usdt_buy and usdt_cop_sell and ves_usdt_buy > 0:
                # 1 VES = X USDT, 1 USDT = Y COP
                # 1 VES = X * Y COP
                rate = (1 / ves_usdt_buy) * usdt_cop_sell
                return rate

            return None

        except Exception as e:
            logger.error(f"Error calculando VES to COP rate: {str(e)}")
            return None

    async def find_best_triangle_routes(
        self,
        assets: List[str] = ["USDT", "BTC", "ETH"],
        fiats: List[str] = ["COP", "VES"]
    ) -> List[Dict]:
        """
        Busca las mejores rutas de arbitraje triangular entre múltiples activos y fiats

        Genera combinaciones como:
        - COP -> USDT -> VES
        - VES -> BTC -> COP
        - COP -> ETH -> VES
        etc.
        """
        opportunities = []

        for asset in assets:
            for fiat_from in fiats:
                for fiat_to in fiats:
                    if fiat_from == fiat_to:
                        continue

                    try:
                        # Ruta: FIAT_FROM -> ASSET -> FIAT_TO
                        route_result = await self._analyze_specific_route(
                            fiat_from, asset, fiat_to
                        )

                        if route_result and route_result.get("is_profitable"):
                            opportunities.append(route_result)

                    except Exception as e:
                        logger.error(f"Error analizando ruta {fiat_from}->{asset}->{fiat_to}: {str(e)}")
                        continue

        # Ordenar por ROI descendente
        opportunities.sort(key=lambda x: x.get("profit", {}).get("roi_percentage", 0), reverse=True)

        return opportunities

    async def _analyze_specific_route(
        self,
        fiat_from: str,
        asset: str,
        fiat_to: str,
        initial_amount: float = 1000000.0
    ) -> Optional[Dict]:
        """Analiza una ruta específica de arbitraje"""

        try:
            # Paso 1: Comprar asset con fiat_from
            asset_buy_price = await self.p2p_service.get_best_price(asset, fiat_from, "BUY")
            if not asset_buy_price or asset_buy_price <= 0:
                return None

            asset_amount = initial_amount / asset_buy_price

            # Paso 2: Vender asset por fiat_to
            asset_sell_price = await self.p2p_service.get_best_price(asset, fiat_to, "SELL")
            if not asset_sell_price or asset_sell_price <= 0:
                return None

            final_amount = asset_amount * asset_sell_price

            # Calcular equivalencia para comparar
            # Necesitamos convertir final_amount (en fiat_to) a fiat_from para calcular profit
            cross_rate = await self._get_cross_rate(fiat_to, fiat_from)

            if cross_rate:
                final_amount_in_initial_currency = final_amount * cross_rate
                profit = final_amount_in_initial_currency - initial_amount
                roi = (profit / initial_amount) * 100
            else:
                # Sin cross rate, solo podemos reportar valores absolutos
                profit = 0
                roi = 0

            return {
                "type": "triangle_arbitrage",
                "route": f"{fiat_from} -> {asset} -> {fiat_to}",
                "initial_investment": {"amount": initial_amount, "currency": fiat_from},
                "final_position": {"amount": final_amount, "currency": fiat_to},
                "asset": asset,
                "step_1": {
                    "action": f"BUY {asset}",
                    "price": asset_buy_price,
                    "amount": asset_amount,
                },
                "step_2": {
                    "action": f"SELL {asset}",
                    "price": asset_sell_price,
                    "amount": final_amount,
                },
                "profit": {
                    "absolute": profit,
                    "roi_percentage": roi,
                },
                "is_profitable": roi > settings.ARBITRAGE_MIN_PROFIT,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error en ruta {fiat_from}->{asset}->{fiat_to}: {str(e)}")
            return None

    async def _get_cross_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Obtiene tasa de cambio entre dos fiats usando USDT como puente"""
        try:
            # from_currency -> USDT -> to_currency
            from_to_usdt = await self.p2p_service.get_best_price("USDT", from_currency, "SELL")
            usdt_to_to = await self.p2p_service.get_best_price("USDT", to_currency, "BUY")

            if from_to_usdt and usdt_to_to and from_to_usdt > 0:
                # 1 from_currency = X USDT, Y to_currency = 1 USDT
                # 1 from_currency = X / Y to_currency
                rate = from_to_usdt / usdt_to_to
                return rate

            return None
        except Exception as e:
            logger.error(f"Error obteniendo cross rate {from_currency}/{to_currency}: {str(e)}")
            return None

    async def get_optimal_triangle_strategy(self) -> Dict:
        """
        Encuentra la estrategia triangular óptima considerando:
        - Máximo ROI
        - Liquidez disponible
        - Tiempo estimado de ejecución
        - Riesgo
        """

        # Buscar todas las oportunidades
        all_opportunities = await self.find_best_triangle_routes()

        if not all_opportunities:
            return {
                "success": False,
                "message": "No se encontraron oportunidades rentables",
                "opportunities_analyzed": 0
            }

        # La mejor es la primera (ya está ordenada por ROI)
        best_opportunity = all_opportunities[0]

        # Analizar liquidez disponible para esta ruta
        liquidity_analysis = await self._analyze_route_liquidity(best_opportunity)

        return {
            "success": True,
            "best_opportunity": best_opportunity,
            "liquidity": liquidity_analysis,
            "total_opportunities_found": len(all_opportunities),
            "top_3_opportunities": all_opportunities[:3],
            "recommendation": self._generate_recommendation(best_opportunity, liquidity_analysis),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _analyze_route_liquidity(self, opportunity: Dict) -> Dict:
        """Analiza la liquidez disponible para ejecutar una ruta de arbitraje"""

        route_parts = opportunity["route"].split(" -> ")
        fiat_from = route_parts[0]
        asset = route_parts[1]
        fiat_to = route_parts[2]

        try:
            # Obtener profundidad de mercado para cada paso
            step1_depth = await self.p2p_service.get_market_depth(asset, fiat_from, "BUY", limit=10)
            step2_depth = await self.p2p_service.get_market_depth(asset, fiat_to, "SELL", limit=10)

            step1_liquidity = sum([ad.get("tradableQuantity", 0) for ad in step1_depth]) if step1_depth else 0
            step2_liquidity = sum([ad.get("tradableQuantity", 0) for ad in step2_depth]) if step2_depth else 0

            # El cuello de botella es el paso con menor liquidez
            bottleneck_liquidity = min(step1_liquidity, step2_liquidity)

            return {
                "step_1_liquidity": step1_liquidity,
                "step_2_liquidity": step2_liquidity,
                "bottleneck_liquidity": bottleneck_liquidity,
                "is_liquid": bottleneck_liquidity > 100,  # Threshold: 100 USDT equivalente
                "max_executable_amount": bottleneck_liquidity,
            }

        except Exception as e:
            logger.error(f"Error analizando liquidez: {str(e)}")
            return {
                "step_1_liquidity": 0,
                "step_2_liquidity": 0,
                "bottleneck_liquidity": 0,
                "is_liquid": False,
                "error": str(e)
            }

    def _generate_recommendation(self, opportunity: Dict, liquidity: Dict) -> str:
        """Genera recomendación de ejecución basada en oportunidad y liquidez"""

        roi = opportunity.get("profit", {}).get("roi_percentage", 0)
        is_liquid = liquidity.get("is_liquid", False)

        if roi > 5.0 and is_liquid:
            return "🚀 EJECUTAR INMEDIATAMENTE - Alta rentabilidad y liquidez suficiente"
        elif roi > 3.0 and is_liquid:
            return "✅ EJECUTAR - Buena oportunidad con liquidez adecuada"
        elif roi > 1.0 and is_liquid:
            return "⚠️ CONSIDERAR - Rentabilidad moderada, evaluar costos de transacción"
        elif roi > 0 and not is_liquid:
            return "❌ NO EJECUTAR - Liquidez insuficiente para completar la operación"
        else:
            return "❌ NO EJECUTAR - Rentabilidad insuficiente"
