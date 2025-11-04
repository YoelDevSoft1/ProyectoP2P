"""
Liquidity Analysis Service - Análisis avanzado de liquidez y detección de market makers

Funciones:
1. Análisis de profundidad de mercado (orderbook depth)
2. Detección de market makers por patrones
3. Análisis de volumen y spread
4. Identificación de zonas de soporte/resistencia
5. Cálculo de slippage estimado
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import statistics
from app.services.binance_service import BinanceService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LiquidityAnalysisService:
    """Servicio avanzado para análisis de liquidez y microestructura de mercado"""

    def __init__(self):
        self.p2p_service = BinanceService()

        # Thresholds para detección de market makers
        self.MARKET_MAKER_MIN_VOLUME = 10000  # USDT mínimo
        self.MARKET_MAKER_SPREAD_THRESHOLD = 0.5  # % spread máximo típico de MM
        self.LARGE_ORDER_MULTIPLIER = 3  # 3x el tamaño promedio

    async def analyze_market_depth(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        depth_levels: int = 20
    ) -> Dict:
        """
        Análisis completo de profundidad de mercado

        Retorna:
        - Distribución de liquidez por niveles de precio
        - Identificación de zonas de alta liquidez
        - Cálculo de spread efectivo
        - Detección de paredes de compra/venta
        """

        try:
            # Obtener bids (órdenes de compra) y asks (órdenes de venta)
            buy_orders = await self.p2p_service.get_market_depth(
                asset, fiat, "BUY", limit=depth_levels
            )
            sell_orders = await self.p2p_service.get_market_depth(
                asset, fiat, "SELL", limit=depth_levels
            )

            if not buy_orders or not sell_orders:
                return {"success": False, "error": "No hay datos de mercado"}

            # Procesar órdenes de compra (bids)
            bids_analysis = self._analyze_order_side(buy_orders, "BUY")

            # Procesar órdenes de venta (asks)
            asks_analysis = self._analyze_order_side(sell_orders, "SELL")

            # Calcular spread
            best_bid = float(buy_orders[0]["adv"]["price"]) if buy_orders else 0
            best_ask = float(sell_orders[0]["adv"]["price"]) if sell_orders else 0

            spread_absolute = best_ask - best_bid if best_ask and best_bid else 0
            spread_percentage = (spread_absolute / best_bid * 100) if best_bid > 0 else 0

            # Calcular mid price
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0

            # Análisis de desequilibrio (order book imbalance)
            total_bid_volume = bids_analysis["total_volume"]
            total_ask_volume = asks_analysis["total_volume"]

            imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume) if (total_bid_volume + total_ask_volume) > 0 else 0

            # Detección de "walls" (grandes órdenes que actúan como soporte/resistencia)
            bid_walls = self._detect_walls(buy_orders, "BUY")
            ask_walls = self._detect_walls(sell_orders, "SELL")

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "timestamp": datetime.utcnow().isoformat(),
                "spread": {
                    "absolute": spread_absolute,
                    "percentage": spread_percentage,
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "mid_price": mid_price,
                },
                "bids": bids_analysis,
                "asks": asks_analysis,
                "imbalance": {
                    "ratio": imbalance,
                    "interpretation": self._interpret_imbalance(imbalance),
                    "signal": "BULLISH" if imbalance > 0.2 else ("BEARISH" if imbalance < -0.2 else "NEUTRAL")
                },
                "walls": {
                    "bid_walls": bid_walls,
                    "ask_walls": ask_walls,
                    "total_walls": len(bid_walls) + len(ask_walls),
                },
                "liquidity_score": self._calculate_liquidity_score(
                    total_bid_volume,
                    total_ask_volume,
                    spread_percentage
                ),
                "market_quality": self._assess_market_quality(
                    spread_percentage,
                    total_bid_volume + total_ask_volume,
                    len(bid_walls) + len(ask_walls)
                )
            }

        except Exception as e:
            logger.error(f"Error en análisis de profundidad: {str(e)}")
            return {"success": False, "error": str(e)}

    def _analyze_order_side(self, orders: List[Dict], side: str) -> Dict:
        """Analiza un lado del orderbook (bids o asks)"""

        if not orders:
            return {
                "total_volume": 0,
                "average_order_size": 0,
                "median_order_size": 0,
                "price_levels": 0,
                "orders": []
            }

        volumes = []
        prices = []
        processed_orders = []

        for order in orders:
            try:
                price = float(order["adv"]["price"])
                quantity = float(order["adv"].get("tradableQuantity", 0))

                volumes.append(quantity)
                prices.append(price)

                processed_orders.append({
                    "price": price,
                    "quantity": quantity,
                    "total_value": price * quantity,
                })

            except (KeyError, ValueError) as e:
                continue

        total_volume = sum(volumes)
        avg_volume = statistics.mean(volumes) if volumes else 0
        median_volume = statistics.median(volumes) if volumes else 0

        # Calcular distribución acumulativa
        cumulative_distribution = []
        cumulative_vol = 0
        for order in processed_orders:
            cumulative_vol += order["quantity"]
            cumulative_distribution.append({
                "price": order["price"],
                "cumulative_volume": cumulative_vol,
                "percentage": (cumulative_vol / total_volume * 100) if total_volume > 0 else 0
            })

        return {
            "total_volume": total_volume,
            "average_order_size": avg_volume,
            "median_order_size": median_volume,
            "price_levels": len(orders),
            "orders": processed_orders[:10],  # Top 10 para no saturar
            "cumulative_distribution": cumulative_distribution[:10],
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "range": (max(prices) - min(prices)) if prices else 0
            }
        }

    def _detect_walls(self, orders: List[Dict], side: str) -> List[Dict]:
        """
        Detecta 'walls' (órdenes grandes que actúan como soporte/resistencia)

        Un wall es una orden significativamente más grande que el promedio
        """

        if not orders or len(orders) < 3:
            return []

        volumes = [float(order["adv"].get("tradableQuantity", 0)) for order in orders]
        avg_volume = statistics.mean(volumes)

        walls = []

        for order in orders:
            try:
                price = float(order["adv"]["price"])
                quantity = float(order["adv"].get("tradableQuantity", 0))

                # Es un wall si es 3x+ el volumen promedio
                if quantity >= avg_volume * self.LARGE_ORDER_MULTIPLIER:
                    walls.append({
                        "price": price,
                        "quantity": quantity,
                        "side": side,
                        "multiplier": quantity / avg_volume,
                        "type": "SUPPORT" if side == "BUY" else "RESISTANCE"
                    })

            except (KeyError, ValueError):
                continue

        return walls

    def _interpret_imbalance(self, imbalance: float) -> str:
        """Interpreta el desequilibrio del orderbook"""

        if imbalance > 0.3:
            return "Fuerte presión compradora - Más liquidez en bids que asks"
        elif imbalance > 0.1:
            return "Presión compradora moderada"
        elif imbalance < -0.3:
            return "Fuerte presión vendedora - Más liquidez en asks que bids"
        elif imbalance < -0.1:
            return "Presión vendedora moderada"
        else:
            return "Mercado equilibrado - Liquidez similar en ambos lados"

    def _calculate_liquidity_score(
        self,
        bid_volume: float,
        ask_volume: float,
        spread_pct: float
    ) -> Dict:
        """
        Calcula un score de liquidez del 0-100

        Factores:
        - Volumen total (40%)
        - Spread (40%)
        - Balance bid/ask (20%)
        """

        # Score por volumen (0-40 puntos)
        total_volume = bid_volume + ask_volume
        volume_score = min(40, (total_volume / 10000) * 40)  # 10k USDT = score perfecto

        # Score por spread (0-40 puntos)
        # Spread < 0.5% = perfecto, > 2% = malo
        if spread_pct <= 0.5:
            spread_score = 40
        elif spread_pct >= 2.0:
            spread_score = 0
        else:
            spread_score = 40 * (1 - (spread_pct - 0.5) / 1.5)

        # Score por balance (0-20 puntos)
        if total_volume > 0:
            balance = min(bid_volume, ask_volume) / max(bid_volume, ask_volume)
            balance_score = balance * 20
        else:
            balance_score = 0

        total_score = volume_score + spread_score + balance_score

        return {
            "score": round(total_score, 2),
            "components": {
                "volume_score": round(volume_score, 2),
                "spread_score": round(spread_score, 2),
                "balance_score": round(balance_score, 2),
            },
            "rating": self._get_liquidity_rating(total_score)
        }

    def _get_liquidity_rating(self, score: float) -> str:
        """Convierte score numérico en rating cualitativo"""
        if score >= 80:
            return "EXCELENTE"
        elif score >= 60:
            return "BUENA"
        elif score >= 40:
            return "MODERADA"
        elif score >= 20:
            return "BAJA"
        else:
            return "MUY BAJA"

    def _assess_market_quality(
        self,
        spread: float,
        total_volume: float,
        num_walls: int
    ) -> Dict:
        """Evalúa la calidad general del mercado"""

        issues = []
        quality_score = 100

        # Penalizar spread alto
        if spread > 2.0:
            issues.append("Spread muy alto - baja eficiencia")
            quality_score -= 30
        elif spread > 1.0:
            issues.append("Spread moderadamente alto")
            quality_score -= 15

        # Penalizar volumen bajo
        if total_volume < 1000:
            issues.append("Volumen muy bajo - alta probabilidad de slippage")
            quality_score -= 30
        elif total_volume < 5000:
            issues.append("Volumen moderadamente bajo")
            quality_score -= 15

        # Walls pueden ser positivos o negativos
        if num_walls > 5:
            issues.append("Múltiples walls detectados - posible manipulación")
            quality_score -= 10

        if not issues:
            issues.append("Mercado saludable sin issues detectados")

        return {
            "quality_score": max(0, quality_score),
            "rating": "EXCELENTE" if quality_score >= 80 else (
                "BUENA" if quality_score >= 60 else (
                    "MODERADA" if quality_score >= 40 else "POBRE"
                )
            ),
            "issues": issues,
            "recommendation": "OPERAR CON CONFIANZA" if quality_score >= 70 else (
                "OPERAR CON PRECAUCIÓN" if quality_score >= 40 else "EVITAR ÓRDENES GRANDES"
            )
        }

    async def detect_market_makers(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """
        Detecta posibles market makers analizando patrones de órdenes

        Características de market makers:
        - Órdenes grandes y consistentes en ambos lados
        - Spread tight (menor al promedio)
        - Alta frecuencia de actualización
        - Volumen significativo
        """

        try:
            depth_analysis = await self.analyze_market_depth(asset, fiat, depth_levels=20)

            if not depth_analysis.get("success"):
                return {"success": False, "error": "No se pudo analizar profundidad"}

            bids = depth_analysis["bids"]["orders"]
            asks = depth_analysis["asks"]["orders"]
            spread_pct = depth_analysis["spread"]["percentage"]

            # Analizar patrones de market making
            potential_mms = []

            # Buscar órdenes en ambos lados con spread tight
            for bid in bids[:5]:  # Top 5 bids
                for ask in asks[:5]:  # Top 5 asks
                    # Calcular spread entre esta bid y ask específicas
                    order_spread = ((ask["price"] - bid["price"]) / bid["price"] * 100)

                    # Si el spread es tight y los volúmenes son grandes
                    if (order_spread < self.MARKET_MAKER_SPREAD_THRESHOLD and
                        bid["quantity"] > 1000 and ask["quantity"] > 1000):

                        potential_mms.append({
                            "bid_price": bid["price"],
                            "ask_price": ask["price"],
                            "bid_quantity": bid["quantity"],
                            "ask_quantity": ask["quantity"],
                            "spread_percentage": order_spread,
                            "confidence": self._calculate_mm_confidence(
                                bid["quantity"],
                                ask["quantity"],
                                order_spread
                            )
                        })

            # Ordenar por confidence
            potential_mms.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "market_makers_detected": len(potential_mms),
                "potential_market_makers": potential_mms[:3],  # Top 3
                "market_spread": spread_pct,
                "interpretation": self._interpret_mm_presence(len(potential_mms), spread_pct),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error detectando market makers: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calculate_mm_confidence(
        self,
        bid_quantity: float,
        ask_quantity: float,
        spread: float
    ) -> float:
        """Calcula confidence score de que sea un market maker"""

        confidence = 0

        # Mayor volumen = mayor confidence (max 50 puntos)
        avg_quantity = (bid_quantity + ask_quantity) / 2
        confidence += min(50, (avg_quantity / 10000) * 50)

        # Menor spread = mayor confidence (max 30 puntos)
        if spread < 0.2:
            confidence += 30
        elif spread < 0.5:
            confidence += 20
        elif spread < 1.0:
            confidence += 10

        # Balance entre bid y ask (max 20 puntos)
        balance = min(bid_quantity, ask_quantity) / max(bid_quantity, ask_quantity)
        confidence += balance * 20

        return round(confidence, 2)

    def _interpret_mm_presence(self, num_mms: int, spread: float) -> str:
        """Interpreta la presencia de market makers"""

        if num_mms >= 3 and spread < 1.0:
            return "Alta actividad de market makers - Mercado muy líquido y eficiente"
        elif num_mms >= 1 and spread < 1.5:
            return "Presencia moderada de market makers - Buena liquidez"
        elif num_mms >= 1:
            return "Algunos market makers detectados pero spread amplio"
        else:
            return "Baja o nula presencia de market makers - Mercado retail"

    async def calculate_slippage_estimate(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        target_amount_usd: float
    ) -> Dict:
        """
        Estima el slippage esperado para una orden de cierto tamaño

        Slippage = diferencia entre precio esperado y precio real de ejecución
        """

        try:
            orders = await self.p2p_service.get_market_depth(
                asset, fiat, trade_type, limit=20
            )

            if not orders:
                return {"success": False, "error": "No hay órdenes disponibles"}

            best_price = float(orders[0]["adv"]["price"])
            accumulated_volume = 0
            weighted_price_sum = 0

            for order in orders:
                price = float(order["adv"]["price"])
                quantity = float(order["adv"].get("tradableQuantity", 0))

                if accumulated_volume >= target_amount_usd:
                    break

                # Cuánto de esta orden necesitamos
                needed = min(quantity, target_amount_usd - accumulated_volume)

                weighted_price_sum += price * needed
                accumulated_volume += needed

            if accumulated_volume == 0:
                return {
                    "success": False,
                    "error": "No hay suficiente liquidez para la orden"
                }

            average_execution_price = weighted_price_sum / accumulated_volume
            slippage_absolute = abs(average_execution_price - best_price)
            slippage_percentage = (slippage_absolute / best_price) * 100

            return {
                "success": True,
                "target_amount_usd": target_amount_usd,
                "best_price": best_price,
                "average_execution_price": average_execution_price,
                "slippage": {
                    "absolute": slippage_absolute,
                    "percentage": slippage_percentage,
                },
                "feasible": accumulated_volume >= target_amount_usd * 0.95,  # 95% threshold
                "liquidity_available": accumulated_volume,
                "price_impact": "BAJO" if slippage_percentage < 0.5 else (
                    "MODERADO" if slippage_percentage < 1.5 else "ALTO"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculando slippage: {str(e)}")
            return {"success": False, "error": str(e)}
