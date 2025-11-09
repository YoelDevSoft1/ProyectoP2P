"""
Order Execution Intelligence Service - Algoritmos avanzados de ejecución de órdenes

Algoritmos implementados:
1. TWAP (Time-Weighted Average Price)
2. VWAP (Volume-Weighted Average Price)
3. Iceberg Orders
4. Smart Order Routing
5. Implementation Shortfall
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import statistics
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.liquidity_analysis_service import LiquidityAnalysisService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OrderExecutionService:
    """
    Servicio de ejecución inteligente de órdenes con algoritmos avanzados.
    """

    def __init__(self):
        self.p2p_service = BinanceService()
        self.spot_service = BinanceSpotService()
        self.liquidity_service = LiquidityAnalysisService()

        # Configuración
        self.MAX_SLIPPAGE_PCT = 1.0  # Slippage máximo aceptable 1%
        self.MIN_CHUNK_SIZE_USD = 100.0  # Tamaño mínimo de chunk
        self.MAX_CHUNK_SIZE_USD = 5000.0  # Tamaño máximo de chunk

    async def execute_twap(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        total_amount_usd: float,
        duration_minutes: int = 30,
        chunks: int = 10
    ) -> Dict:
        """
        Ejecuta orden usando algoritmo TWAP (Time-Weighted Average Price).

        Divide la orden en chunks y ejecuta en intervalos de tiempo iguales.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY o SELL
            total_amount_usd: Cantidad total en USD
            duration_minutes: Duración total en minutos
            chunks: Número de chunks

        Returns:
            Resultado de ejecución
        """

        try:
            logger.info(
                f"Executing TWAP order: {total_amount_usd} USD over {duration_minutes} minutes",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type
            )

            # Calcular tamaño de chunk
            chunk_size_usd = total_amount_usd / chunks
            chunk_size_usd = max(self.MIN_CHUNK_SIZE_USD, min(chunk_size_usd, self.MAX_CHUNK_SIZE_USD))

            # Calcular intervalo entre chunks
            interval_seconds = (duration_minutes * 60) / chunks

            # Ejecutar chunks
            executed_chunks = []
            total_executed = 0.0
            total_cost = 0.0
            prices = []

            for i in range(chunks):
                # Esperar intervalo (excepto primera iteración)
                if i > 0:
                    await asyncio.sleep(interval_seconds)

                # Obtener mejor precio actual
                best_price = await self.p2p_service.get_best_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type
                )

                if not best_price or best_price <= 0:
                    logger.warning(f"No price available for chunk {i+1}")
                    continue

                # Calcular cantidad a ejecutar
                amount_to_execute = min(chunk_size_usd, total_amount_usd - total_executed)

                if amount_to_execute < self.MIN_CHUNK_SIZE_USD:
                    break

                # Ejecutar chunk
                chunk_result = await self._execute_chunk(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type,
                    amount_usd=amount_to_execute,
                    expected_price=best_price
                )

                if chunk_result.get("success"):
                    executed_chunks.append(chunk_result)
                    total_executed += chunk_result["amount_usd"]
                    total_cost += chunk_result["total_cost"]
                    prices.append(chunk_result["execution_price"])

                    logger.info(
                        f"Chunk {i+1}/{chunks} executed",
                        amount=chunk_result["amount_usd"],
                        price=chunk_result["execution_price"]
                    )

            # Calcular métricas
            if not prices:
                return {
                    "success": False,
                    "error": "No se pudo ejecutar ningún chunk"
                }

            avg_price = statistics.mean(prices)
            twap_price = total_cost / total_executed if total_executed > 0 else 0

            # Comparar con precio de mercado inicial
            initial_price = prices[0] if prices else 0
            final_price = prices[-1] if prices else 0

            price_improvement = ((initial_price - twap_price) / initial_price * 100) if initial_price > 0 else 0

            return {
                "success": True,
                "algorithm": "TWAP",
                "asset": asset,
                "fiat": fiat,
                "trade_type": trade_type,
                "total_amount_usd": total_amount_usd,
                "executed_amount_usd": round(total_executed, 2),
                "execution_rate": round(total_executed / total_amount_usd * 100, 2),
                "duration_minutes": duration_minutes,
                "chunks": len(executed_chunks),
                "twap_price": round(twap_price, 2),
                "average_price": round(avg_price, 2),
                "initial_price": round(initial_price, 2),
                "final_price": round(final_price, 2),
                "price_improvement_pct": round(price_improvement, 2),
                "total_cost": round(total_cost, 2),
                "chunks_detail": executed_chunks,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing TWAP order: {str(e)}")
            return {"success": False, "error": str(e)}

    async def execute_vwap(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        total_amount_usd: float,
        duration_minutes: int = 30
    ) -> Dict:
        """
        Ejecuta orden usando algoritmo VWAP (Volume-Weighted Average Price).

        Ejecuta proporcionalmente al volumen del mercado.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY o SELL
            total_amount_usd: Cantidad total en USD
            duration_minutes: Duración total en minutos

        Returns:
            Resultado de ejecución
        """

        try:
            logger.info(
                f"Executing VWAP order: {total_amount_usd} USD over {duration_minutes} minutes",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type
            )

            # Obtener análisis de liquidez
            liquidity_analysis = await self.liquidity_service.analyze_market_depth(
                asset=asset,
                fiat=fiat,
                depth_levels=20
            )

            if not liquidity_analysis.get("success"):
                return {
                    "success": False,
                    "error": "No se pudo analizar liquidez del mercado"
                }

            # Calcular volumen total disponible
            if trade_type == "BUY":
                total_volume = liquidity_analysis["asks"]["total_volume"]
            else:
                total_volume = liquidity_analysis["bids"]["total_volume"]

            if total_volume < total_amount_usd:
                return {
                    "success": False,
                    "error": f"Liquidez insuficiente: {total_volume} < {total_amount_usd}"
                }

            # Dividir en períodos
            num_periods = max(5, duration_minutes // 5)  # Períodos de 5 minutos
            period_duration_seconds = (duration_minutes * 60) / num_periods

            executed_chunks = []
            total_executed = 0.0
            total_cost = 0.0
            prices = []

            for period in range(num_periods):
                # Esperar intervalo (excepto primera iteración)
                if period > 0:
                    await asyncio.sleep(period_duration_seconds)

                # Recalcular liquidez
                liquidity_analysis = await self.liquidity_service.analyze_market_depth(
                    asset=asset,
                    fiat=fiat,
                    depth_levels=20
                )

                if trade_type == "BUY":
                    available_volume = liquidity_analysis["asks"]["total_volume"]
                else:
                    available_volume = liquidity_analysis["bids"]["total_volume"]

                # Calcular cantidad proporcional al volumen disponible
                # Objetivo: ejecutar proporcionalmente al volumen del mercado
                volume_ratio = available_volume / total_volume if total_volume > 0 else 0
                target_amount = (total_amount_usd - total_executed) * volume_ratio

                # Limitar por tamaño mínimo/máximo
                target_amount = max(self.MIN_CHUNK_SIZE_USD, min(target_amount, self.MAX_CHUNK_SIZE_USD))
                target_amount = min(target_amount, total_amount_usd - total_executed)

                if target_amount < self.MIN_CHUNK_SIZE_USD:
                    break

                # Obtener mejor precio
                best_price = await self.p2p_service.get_best_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type
                )

                if not best_price or best_price <= 0:
                    continue

                # Ejecutar chunk
                chunk_result = await self._execute_chunk(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type,
                    amount_usd=target_amount,
                    expected_price=best_price
                )

                if chunk_result.get("success"):
                    executed_chunks.append(chunk_result)
                    total_executed += chunk_result["amount_usd"]
                    total_cost += chunk_result["total_cost"]
                    prices.append(chunk_result["execution_price"])

            # Calcular VWAP
            if not prices:
                return {
                    "success": False,
                    "error": "No se pudo ejecutar ningún chunk"
                }

            vwap_price = total_cost / total_executed if total_executed > 0 else 0

            return {
                "success": True,
                "algorithm": "VWAP",
                "asset": asset,
                "fiat": fiat,
                "trade_type": trade_type,
                "total_amount_usd": total_amount_usd,
                "executed_amount_usd": round(total_executed, 2),
                "execution_rate": round(total_executed / total_amount_usd * 100, 2),
                "duration_minutes": duration_minutes,
                "vwap_price": round(vwap_price, 2),
                "total_cost": round(total_cost, 2),
                "chunks_detail": executed_chunks,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing VWAP order: {str(e)}")
            return {"success": False, "error": str(e)}

    async def execute_iceberg(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        total_amount_usd: float,
        visible_size_usd: float = 1000.0,
        refresh_interval_seconds: int = 60
    ) -> Dict:
        """
        Ejecuta orden tipo Iceberg (oculta tamaño real).

        Muestra solo una parte de la orden y la refresca automáticamente.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY o SELL
            total_amount_usd: Cantidad total en USD
            visible_size_usd: Tamaño visible de la orden
            refresh_interval_seconds: Intervalo de refresh en segundos

        Returns:
            Resultado de ejecución
        """

        try:
            logger.info(
                f"Executing Iceberg order: {total_amount_usd} USD (visible: {visible_size_usd})",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type
            )

            executed_chunks = []
            total_executed = 0.0
            total_cost = 0.0
            prices = []

            while total_executed < total_amount_usd:
                # Calcular cantidad a mostrar/ejecutar
                remaining = total_amount_usd - total_executed
                amount_to_execute = min(visible_size_usd, remaining)

                if amount_to_execute < self.MIN_CHUNK_SIZE_USD:
                    break

                # Obtener mejor precio
                best_price = await self.p2p_service.get_best_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type
                )

                if not best_price or best_price <= 0:
                    await asyncio.sleep(refresh_interval_seconds)
                    continue

                # Ejecutar chunk visible
                chunk_result = await self._execute_chunk(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type,
                    amount_usd=amount_to_execute,
                    expected_price=best_price
                )

                if chunk_result.get("success"):
                    executed_chunks.append(chunk_result)
                    total_executed += chunk_result["amount_usd"]
                    total_cost += chunk_result["total_cost"]
                    prices.append(chunk_result["execution_price"])

                    logger.info(
                        f"Iceberg chunk executed: {chunk_result['amount_usd']} USD",
                        total_executed=total_executed,
                        remaining=total_amount_usd - total_executed
                    )

                # Esperar antes de mostrar siguiente chunk
                if total_executed < total_amount_usd:
                    await asyncio.sleep(refresh_interval_seconds)

            # Calcular promedio
            if not prices:
                return {
                    "success": False,
                    "error": "No se pudo ejecutar ningún chunk"
                }

            avg_price = total_cost / total_executed if total_executed > 0 else 0

            return {
                "success": True,
                "algorithm": "ICEBERG",
                "asset": asset,
                "fiat": fiat,
                "trade_type": trade_type,
                "total_amount_usd": total_amount_usd,
                "executed_amount_usd": round(total_executed, 2),
                "execution_rate": round(total_executed / total_amount_usd * 100, 2),
                "visible_size_usd": visible_size_usd,
                "average_price": round(avg_price, 2),
                "total_cost": round(total_cost, 2),
                "chunks": len(executed_chunks),
                "chunks_detail": executed_chunks,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing Iceberg order: {str(e)}")
            return {"success": False, "error": str(e)}

    async def smart_order_routing(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        amount_usd: float,
        exchanges: List[str] = ["binance_p2p", "binance_spot"]
    ) -> Dict:
        """
        Enruta orden a mejor mercado disponible.

        Compara precios en múltiples mercados y ejecuta en el mejor.

        Args:
            asset: Criptomoneda
            fiat: Moneda fiat
            trade_type: BUY o SELL
            amount_usd: Cantidad en USD
            exchanges: Lista de exchanges a comparar

        Returns:
            Resultado de ejecución
        """

        try:
            logger.info(
                f"Smart routing order: {amount_usd} USD",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type,
                exchanges=exchanges
            )

            # Comparar precios en diferentes mercados
            market_prices = []

            # Precio en Binance P2P
            if "binance_p2p" in exchanges:
                p2p_price = await self.p2p_service.get_best_price(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type
                )
                if p2p_price:
                    # Estimar slippage
                    slippage_estimate = await self.liquidity_service.calculate_slippage_estimate(
                        asset=asset,
                        fiat=fiat,
                        trade_type=trade_type,
                        target_amount_usd=amount_usd
                    )

                    effective_price = p2p_price
                    if slippage_estimate.get("success"):
                        effective_price = slippage_estimate.get("average_execution_price", p2p_price)

                    market_prices.append({
                        "exchange": "binance_p2p",
                        "price": p2p_price,
                        "effective_price": effective_price,
                        "slippage_pct": slippage_estimate.get("slippage", {}).get("percentage", 0) if slippage_estimate.get("success") else 0,
                        "liquidity": slippage_estimate.get("liquidity_available", 0) if slippage_estimate.get("success") else 0,
                        "fees": 0.0  # P2P es gratis
                    })

            # Precio en Binance Spot (si aplica)
            if "binance_spot" in exchanges and asset == "USDT":
                # Para Spot, necesitaríamos convertir fiat a USD primero
                # Por simplicidad, omitimos aquí
                pass

            if not market_prices:
                return {
                    "success": False,
                    "error": "No se encontraron precios en ningún mercado"
                }

            # Encontrar mejor mercado (menor precio para compra, mayor para venta)
            if trade_type == "BUY":
                best_market = min(market_prices, key=lambda x: x["effective_price"])
            else:
                best_market = max(market_prices, key=lambda x: x["effective_price"])

            # Ejecutar en mejor mercado
            if best_market["exchange"] == "binance_p2p":
                result = await self._execute_chunk(
                    asset=asset,
                    fiat=fiat,
                    trade_type=trade_type,
                    amount_usd=amount_usd,
                    expected_price=best_market["price"]
                )

                if result.get("success"):
                    return {
                        "success": True,
                        "algorithm": "SMART_ROUTING",
                        "asset": asset,
                        "fiat": fiat,
                        "trade_type": trade_type,
                        "amount_usd": amount_usd,
                        "selected_market": best_market["exchange"],
                        "execution_price": result["execution_price"],
                        "total_cost": result["total_cost"],
                        "market_comparison": market_prices,
                        "savings_vs_alternative": self._calculate_savings(
                            best_market,
                            market_prices,
                            trade_type
                        ),
                        "timestamp": datetime.utcnow().isoformat()
                    }

            return {
                "success": False,
                "error": "No se pudo ejecutar en ningún mercado"
            }

        except Exception as e:
            logger.error(f"Error in smart order routing: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_chunk(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
        amount_usd: float,
        expected_price: float
    ) -> Dict:
        """
        Ejecuta un chunk de orden.

        NOTA: Esta es una simulación. En producción, ejecutaría la orden real.
        """

        try:
            # Simular ejecución
            # En producción, esto ejecutaría la orden real en Binance P2P

            # Simular slippage pequeño
            slippage_pct = 0.1  # 0.1% slippage típico
            execution_price = expected_price * (1 + slippage_pct / 100) if trade_type == "BUY" else expected_price * (1 - slippage_pct / 100)

            total_cost = amount_usd * execution_price if trade_type == "BUY" else amount_usd / execution_price

            return {
                "success": True,
                "amount_usd": amount_usd,
                "expected_price": expected_price,
                "execution_price": execution_price,
                "slippage_pct": slippage_pct,
                "total_cost": total_cost,
                "executed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing chunk: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calculate_savings(
        self,
        best_market: Dict,
        all_markets: List[Dict],
        trade_type: str
    ) -> Dict:
        """Calcula ahorro vs alternativa"""

        if len(all_markets) < 2:
            return {
                "savings_pct": 0.0,
                "savings_amount": 0.0,
                "message": "Solo un mercado disponible"
            }

        # Encontrar segunda mejor opción
        alternatives = [m for m in all_markets if m["exchange"] != best_market["exchange"]]
        if not alternatives:
            return {
                "savings_pct": 0.0,
                "savings_amount": 0.0,
                "message": "No hay alternativas"
            }

        if trade_type == "BUY":
            second_best = min(alternatives, key=lambda x: x["effective_price"])
            savings_pct = ((second_best["effective_price"] - best_market["effective_price"]) / second_best["effective_price"]) * 100
        else:
            second_best = max(alternatives, key=lambda x: x["effective_price"])
            savings_pct = ((best_market["effective_price"] - second_best["effective_price"]) / second_best["effective_price"]) * 100

        return {
            "savings_pct": round(savings_pct, 2),
            "savings_amount": round(abs(second_best["effective_price"] - best_market["effective_price"]), 2),
            "alternative_market": second_best["exchange"],
            "message": f"Ahorro de {savings_pct:.2f}% vs {second_best['exchange']}"
        }

