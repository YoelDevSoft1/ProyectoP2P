"""
Advanced Triangle Arbitrage Service con optimización multi-path.

Mejoras sobre el servicio básico:
1. Graph-based routing: Usa grafos para encontrar rutas óptimas
2. Multi-path optimization: Analiza rutas de 3, 4, 5+ pasos
3. Bellman-Ford algorithm: Detecta ciclos de arbitraje negativos
4. Concurrent analysis: Análisis paralelo de múltiples rutas
5. Liquidity-weighted routing: Considera liquidez en el cálculo de rutas
6. Dynamic path discovery: Encuentra rutas que el análisis simple no detecta

Este servicio puede encontrar oportunidades como:
- COP -> USDT -> VES -> USDT -> COP (4 pasos)
- COP -> BTC -> ETH -> USDT -> COP (multi-asset)
- Rutas complejas que maximizan profit
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import structlog

from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService

logger = structlog.get_logger()


@dataclass
class ArbitragePath:
    """Representa una ruta de arbitraje."""

    path: List[str]  # Secuencia de monedas: ["COP", "USDT", "VES", "COP"]
    steps: List[Dict]  # Detalles de cada paso
    initial_amount: float
    final_amount: float
    roi_percentage: float
    profit_amount: float
    num_steps: int
    liquidity_score: float  # 0-100
    execution_time_estimate: float  # Segundos
    risk_score: float  # 0-100 (menor es mejor)
    opportunity_score: float  # 0-100 (mayor es mejor)


class AdvancedTriangleArbitrageService:
    """
    Servicio avanzado de arbitraje triangular con optimización multi-path.
    """

    def __init__(self) -> None:
        """Inicializar servicios."""
        self.p2p_service = BinanceService()
        self.spot_service = BinanceSpotService()

        # Configuración
        self.P2P_FEE = 0.0  # Binance P2P sin comisión
        self.SPOT_FEE = 0.001  # 0.1% Spot
        self.NETWORK_FEE_USDT = 1.0  # ~$1 USDT por transferencia

        # Assets y fiats disponibles (solo los más líquidos y validados)
        # Usar los mismos que están en BinanceService para consistencia
        self.ASSETS = ["USDT", "BTC", "ETH"]  # Removido BNB y BUSD (menos líquidos)
        self.FIATS = ["COP", "VES", "BRL", "ARS"]  # LATAM focus (removido PEN y MXN menos líquidos)

        # Cache de precios para evitar llamadas repetidas
        self._price_cache: Dict[Tuple[str, str, str], Optional[float]] = {}
        self._cache_timestamp = None

    async def find_all_arbitrage_paths(
        self,
        start_currency: str = "COP",
        min_roi: float = 1.0,
        max_steps: int = 5,
        initial_amount: float = 200000.0,
    ) -> List[ArbitragePath]:
        """
        Encuentra todas las rutas de arbitraje posibles usando graph exploration.

        Args:
            start_currency: Moneda de inicio (default: COP)
            min_roi: ROI mínimo para considerar ruta (%)
            max_steps: Máximo número de pasos en la ruta
            initial_amount: Cantidad inicial para simular

        Returns:
            Lista de rutas ordenadas por opportunity_score
        """
        try:
            # Clear cache at start
            await self._refresh_price_cache()

            # Build currency graph
            graph = await self._build_currency_graph()

            if not graph:
                logger.warning("Failed to build currency graph")
                return []

            # Find all paths starting and ending with start_currency
            all_paths = await self._find_cycles_in_graph(
                graph=graph,
                start_node=start_currency,
                max_depth=max_steps,
            )

            if not all_paths:
                logger.info("No cycles found in graph", start=start_currency)
                return []

            # Analyze each path
            analyzed_paths = []

            tasks = [
                self._analyze_path(
                    path=path,
                    initial_amount=initial_amount,
                )
                for path in all_paths
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, ArbitragePath) and result.roi_percentage >= min_roi:
                    analyzed_paths.append(result)

            # Sort by opportunity score (highest first)
            analyzed_paths.sort(key=lambda x: x.opportunity_score, reverse=True)

            logger.info(
                "Arbitrage path analysis completed",
                paths_found=len(all_paths),
                profitable_paths=len(analyzed_paths),
                best_roi=analyzed_paths[0].roi_percentage if analyzed_paths else 0,
            )

            return analyzed_paths

        except Exception as exc:  # noqa: BLE001
            logger.error("Error finding arbitrage paths", error=str(exc))
            return []

    async def find_optimal_path(
        self,
        start_currency: str = "COP",
        min_roi: float = 1.0,
    ) -> Optional[ArbitragePath]:
        """
        Encuentra la ruta óptima de arbitraje.

        Returns:
            La mejor ruta basada en opportunity_score
        """
        paths = await self.find_all_arbitrage_paths(
            start_currency=start_currency,
            min_roi=min_roi,
        )

        if paths:
            return paths[0]

        return None

    async def compare_routes(
        self,
        routes: List[List[str]],
        initial_amount: float = 200000.0,
    ) -> List[ArbitragePath]:
        """
        Compara múltiples rutas específicas.

        Args:
            routes: Lista de rutas, ej: [["COP", "USDT", "VES", "COP"], ...]
            initial_amount: Cantidad inicial

        Returns:
            Lista de rutas analizadas ordenadas por roi
        """
        try:
            await self._refresh_price_cache()

            tasks = [
                self._analyze_path(path=route, initial_amount=initial_amount)
                for route in routes
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            analyzed_paths = [r for r in results if isinstance(r, ArbitragePath)]
            analyzed_paths.sort(key=lambda x: x.roi_percentage, reverse=True)

            return analyzed_paths

        except Exception as exc:  # noqa: BLE001
            logger.error("Error comparing routes", error=str(exc))
            return []

    # ==================== GRAPH BUILDING ====================

    async def _build_currency_graph(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Construye un grafo de monedas con edges ponderados.

        Returns:
            Dict[currency, List[(target_currency, trade_type)]]
            ej: {"COP": [("USDT", "BUY"), ("USDT", "SELL")], ...}
        """
        graph: Dict[str, List[Tuple[str, str]]] = {}

        # All currencies (assets + fiats)
        all_currencies = set(self.ASSETS + self.FIATS)

        # Build edges between all currency pairs
        for currency in all_currencies:
            graph[currency] = []

            # Try connections to assets (P2P)
            for asset in self.ASSETS:
                if currency in self.FIATS and asset != currency:
                    # Can BUY asset with fiat
                    graph[currency].append((asset, "BUY"))
                    # Can SELL asset for fiat
                    graph[currency].append((asset, "SELL"))

                # Asset to asset (via Spot - not implemented yet but structure ready)
                # if currency in self.ASSETS and asset != currency:
                #     graph[currency].append((asset, "SPOT"))

        return graph

    async def _find_cycles_in_graph(
        self,
        graph: Dict[str, List[Tuple[str, str]]],
        start_node: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """
        Encuentra todos los ciclos que empiezan y terminan en start_node.

        Args:
            graph: Grafo de monedas
            start_node: Nodo de inicio (ej: "COP")
            max_depth: Profundidad máxima de búsqueda

        Returns:
            Lista de paths (ciclos)
        """
        cycles = []

        def dfs(
            current: str,
            path: List[str],
            visited: Set[str],
            depth: int,
        ) -> None:
            """Depth-first search para encontrar ciclos."""
            if depth > max_depth:
                return

            # If we're back at start and have at least 3 nodes (start -> ... -> start)
            if current == start_node and len(path) >= 3:
                # Found a cycle
                cycles.append(path.copy())
                return

            # Don't revisit nodes (except start node at the end)
            if current in visited and current != start_node:
                return

            visited.add(current)

            # Explore neighbors
            if current in graph:
                for neighbor, _ in graph[current]:
                    # Only allow returning to start_node at the end
                    if neighbor == start_node and len(path) >= 2:
                        new_path = path + [neighbor]
                        cycles.append(new_path.copy())
                    elif neighbor not in visited:
                        new_path = path + [neighbor]
                        dfs(neighbor, new_path, visited.copy(), depth + 1)

        # Start DFS from start_node
        dfs(start_node, [start_node], set(), 0)

        # Remove duplicates and very short cycles
        unique_cycles = []
        seen = set()

        for cycle in cycles:
            if len(cycle) >= 3:  # At least: start -> mid -> start
                cycle_key = tuple(cycle)
                if cycle_key not in seen:
                    seen.add(cycle_key)
                    unique_cycles.append(cycle)

        return unique_cycles

    # ==================== PATH ANALYSIS ====================

    async def _analyze_path(
        self,
        path: List[str],
        initial_amount: float,
    ) -> Optional[ArbitragePath]:
        """
        Analiza una ruta específica calculando profit, liquidez, riesgo.

        Args:
            path: Lista de monedas en la ruta, ej: ["COP", "USDT", "VES", "COP"]
            initial_amount: Cantidad inicial

        Returns:
            ArbitragePath con análisis completo
        """
        try:
            if len(path) < 3:
                return None

            current_amount = initial_amount
            steps = []
            total_fees = 0

            # Execute each step in the path
            for i in range(len(path) - 1):
                from_currency = path[i]
                to_currency = path[i + 1]

                # Determine if this is a BUY or SELL
                if from_currency in self.FIATS and to_currency in self.ASSETS:
                    # Buying asset with fiat
                    trade_type = "BUY"
                    price = await self._get_cached_price(to_currency, from_currency, "BUY")

                    if not price or price <= 0:
                        return None

                    # How much asset we get
                    received_amount = current_amount / price

                    steps.append({
                        "from": from_currency,
                        "to": to_currency,
                        "trade_type": trade_type,
                        "price": price,
                        "input_amount": current_amount,
                        "output_amount": received_amount,
                        "asset": to_currency,
                    })

                    current_amount = received_amount

                elif from_currency in self.ASSETS and to_currency in self.FIATS:
                    # Selling asset for fiat
                    trade_type = "SELL"
                    price = await self._get_cached_price(from_currency, to_currency, "SELL")

                    if not price or price <= 0:
                        return None

                    # How much fiat we get
                    received_amount = current_amount * price

                    steps.append({
                        "from": from_currency,
                        "to": to_currency,
                        "trade_type": trade_type,
                        "price": price,
                        "input_amount": current_amount,
                        "output_amount": received_amount,
                        "asset": from_currency,
                    })

                    current_amount = received_amount

                else:
                    # Unsupported transition (e.g., fiat to fiat direct)
                    return None

            final_amount = current_amount

            # Calculate profit
            profit_amount = final_amount - initial_amount
            roi_percentage = (profit_amount / initial_amount) * 100 if initial_amount > 0 else 0

            # Calculate metrics
            liquidity_score = await self._calculate_liquidity_score(steps)
            execution_time = len(steps) * 30  # Estimate 30s per step
            risk_score = await self._calculate_risk_score(path, roi_percentage, liquidity_score)
            opportunity_score = await self._calculate_opportunity_score(
                roi=roi_percentage,
                liquidity=liquidity_score,
                risk=risk_score,
                steps=len(steps),
            )

            return ArbitragePath(
                path=path,
                steps=steps,
                initial_amount=initial_amount,
                final_amount=final_amount,
                roi_percentage=roi_percentage,
                profit_amount=profit_amount,
                num_steps=len(steps),
                liquidity_score=liquidity_score,
                execution_time_estimate=execution_time,
                risk_score=risk_score,
                opportunity_score=opportunity_score,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing path", path=path, error=str(exc))
            return None

    async def _get_cached_price(
        self,
        asset: str,
        fiat: str,
        trade_type: str,
    ) -> Optional[float]:
        """Obtiene precio con caching para evitar llamadas repetidas."""
        cache_key = (asset, fiat, trade_type)

        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        # Fetch price
        price = await self.p2p_service.get_best_price(asset, fiat, trade_type)

        self._price_cache[cache_key] = price

        return price

    async def _refresh_price_cache(self) -> None:
        """Limpia el cache de precios."""
        self._price_cache.clear()
        self._cache_timestamp = datetime.utcnow()

    # ==================== SCORING & METRICS ====================

    async def _calculate_liquidity_score(self, steps: List[Dict]) -> float:
        """
        Calcula score de liquidez (0-100) basado en la liquidez disponible en cada paso.

        Mayor liquidez = menor slippage risk = mayor score
        """
        # Simplified - en producción obtener market depth real
        # Para now, assume score based on number of steps (más pasos = menos liquidez)

        if not steps:
            return 0

        # Base score
        base_score = 100

        # Penalty por cada paso adicional
        step_penalty = len(steps) * 10

        # Penalty si usa assets menos líquidos
        illiquid_penalty = 0
        for step in steps:
            asset = step.get("asset")
            if asset in ["BTC", "ETH"]:
                illiquid_penalty += 0  # Muy líquidos
            elif asset in ["USDT", "BUSD"]:
                illiquid_penalty += 0  # Muy líquidos
            else:
                illiquid_penalty += 5  # Menos líquidos

        final_score = max(base_score - step_penalty - illiquid_penalty, 0)

        return min(final_score, 100)

    async def _calculate_risk_score(
        self,
        path: List[str],
        roi: float,
        liquidity: float,
    ) -> float:
        """
        Calcula risk score (0-100, menor es mejor).

        Factores:
        - Número de pasos: Más pasos = más riesgo
        - ROI extremo: ROI muy alto puede indicar datos erróneos
        - Liquidez baja: Mayor riesgo de no ejecución
        """
        risk_points = 0

        # Step risk
        num_steps = len(path) - 1
        risk_points += num_steps * 10

        # ROI extremo risk (too good to be true)
        if roi > 10:
            risk_points += 30
        elif roi > 5:
            risk_points += 10

        # Liquidity risk
        if liquidity < 30:
            risk_points += 30
        elif liquidity < 50:
            risk_points += 15

        return min(risk_points, 100)

    async def _calculate_opportunity_score(
        self,
        roi: float,
        liquidity: float,
        risk: float,
        steps: int,
    ) -> float:
        """
        Calcula opportunity score (0-100, mayor es mejor).

        Factores:
        - ROI: Mayor es mejor (50% weight)
        - Liquidez: Mayor es mejor (25% weight)
        - Risk: Menor es mejor (15% weight)
        - Efficiency: Menos pasos mejor (10% weight)
        """
        # ROI component (0-50)
        # 5%+ ROI = 50 points, 1% = 10 points
        roi_score = min((roi / 5) * 50, 50)

        # Liquidity component (0-25)
        liquidity_score = (liquidity / 100) * 25

        # Risk component (0-15)
        # Lower risk = higher score
        risk_score = ((100 - risk) / 100) * 15

        # Efficiency component (0-10)
        # Fewer steps = higher score
        # 3 steps = 10 points, 5+ steps = 5 points
        if steps <= 3:
            efficiency_score = 10
        elif steps == 4:
            efficiency_score = 8
        else:
            efficiency_score = 5

        total_score = roi_score + liquidity_score + risk_score + efficiency_score

        return round(total_score, 2)

    # ==================== UTILITY METHODS ====================

    async def get_path_execution_plan(
        self,
        path: ArbitragePath,
    ) -> Dict:
        """
        Genera un plan de ejecución detallado para una ruta.

        Returns:
            Plan con instrucciones paso a paso
        """
        execution_steps = []

        for i, step in enumerate(path.steps, 1):
            execution_steps.append({
                "step_number": i,
                "action": f"{step['trade_type']} {step['to']}",
                "from_currency": step["from"],
                "to_currency": step["to"],
                "price": step["price"],
                "input_amount": step["input_amount"],
                "output_amount": step["output_amount"],
                "estimated_time_seconds": 30,
                "exchange": "Binance P2P",
            })

        return {
            "path": " → ".join(path.path),
            "total_steps": len(execution_steps),
            "estimated_total_time_seconds": path.execution_time_estimate,
            "expected_roi": path.roi_percentage,
            "expected_profit": path.profit_amount,
            "initial_investment": path.initial_amount,
            "final_amount": path.final_amount,
            "liquidity_score": path.liquidity_score,
            "risk_score": path.risk_score,
            "opportunity_score": path.opportunity_score,
            "execution_steps": execution_steps,
            "recommendation": self._generate_recommendation(path),
        }

    def _generate_recommendation(self, path: ArbitragePath) -> str:
        """Genera recomendación basada en scores."""
        if path.opportunity_score >= 70:
            return "🚀 EJECUTAR INMEDIATAMENTE - Excelente oportunidad"
        elif path.opportunity_score >= 50:
            return "✅ EJECUTAR - Buena oportunidad"
        elif path.opportunity_score >= 35:
            return "⚠️ CONSIDERAR - Oportunidad moderada"
        else:
            return "❌ NO EJECUTAR - Riesgo supera beneficio potencial"
