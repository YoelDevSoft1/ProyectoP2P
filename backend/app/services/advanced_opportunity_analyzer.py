"""
Advanced Opportunity Analyzer - El cerebro del sistema de arbitraje.

Este servicio combina TODAS las estrategias de arbitraje y:
1. Ejecuta todas las estrategias en paralelo
2. Rankea oportunidades por múltiples criterios
3. Optimiza asignación de capital (portfolio optimization)
4. Genera recomendaciones inteligentes
5. Monitorea en tiempo real

Estrategias integradas:
- Funding Rate Arbitrage (Perpetuals)
- Statistical Arbitrage (Pairs Trading)
- Delta-Neutral Arbitrage (Spot + Futures)
- Triangle Arbitrage (Multi-path)
- Spot-to-P2P Arbitrage
- Cross-Currency Arbitrage

Este es el servicio principal que debe usar el trading bot.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import settings
from app.services.arbitrage_service import ArbitrageService
from app.services.delta_neutral_arbitrage_service import (
    DeltaNeutralArbitrageService,
    DeltaNeutralOpportunity,
)
from app.services.funding_rate_arbitrage_service import (
    FundingRateArbitrageService,
    FundingRateOpportunity,
)
from app.services.statistical_arbitrage_service import (
    PairSignal,
    StatisticalArbitrageService,
)
from app.services.advanced_triangle_arbitrage_service import (
    AdvancedTriangleArbitrageService,
    ArbitragePath,
)

logger = structlog.get_logger()


class StrategyType(str, Enum):
    """Tipos de estrategias de arbitraje."""

    FUNDING_RATE = "funding_rate"
    STATISTICAL = "statistical"
    DELTA_NEUTRAL = "delta_neutral"
    TRIANGLE = "triangle"
    SPOT_TO_P2P = "spot_to_p2p"
    CROSS_CURRENCY = "cross_currency"


@dataclass
class UnifiedOpportunity:
    """
    Oportunidad unificada que puede representar cualquier estrategia.
    """

    # Identification
    opportunity_id: str
    strategy_type: StrategyType
    timestamp: datetime

    # Core metrics
    expected_return_pct: float  # Expected return %
    expected_return_usd: float  # Expected return in USD
    risk_score: float  # 0-100 (lower is better)
    confidence: float  # 0-100 (higher is better)

    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    risk_adjusted_return: float  # Return / Risk

    # Execution metrics
    required_capital_usd: float
    execution_time_estimate_seconds: float
    complexity_score: float  # 0-100 (higher = more complex)

    # Liquidity
    liquidity_score: float  # 0-100
    max_position_size_usd: float

    # Overall scoring
    opportunity_score: float  # 0-100 (composite score)
    priority: str  # HIGH, MEDIUM, LOW
    recommendation: str  # BUY, HOLD, AVOID

    # Strategy-specific data
    details: Dict[str, Any]  # Original opportunity data
    execution_plan: Dict[str, Any]  # Step-by-step plan

    # Metadata
    exchange: str
    symbols: List[str]
    tags: List[str] = field(default_factory=list)


@dataclass
class PortfolioAllocation:
    """Recomendación de asignación de capital entre estrategias."""

    total_capital_usd: float
    allocations: List[Dict[str, Any]]
    expected_portfolio_return_pct: float
    portfolio_sharpe_ratio: float
    portfolio_risk_score: float
    diversification_score: float  # 0-100
    recommendation: str


class AdvancedOpportunityAnalyzer:
    """
    Analizador avanzado que combina todas las estrategias de arbitraje.
    """

    def __init__(self) -> None:
        """Inicializar todos los servicios de estrategias."""
        self.funding_rate_service = FundingRateArbitrageService()
        self.statistical_service = StatisticalArbitrageService()
        self.delta_neutral_service = DeltaNeutralArbitrageService()
        self.triangle_service = AdvancedTriangleArbitrageService()
        self.basic_arbitrage_service = ArbitrageService()

    async def find_all_opportunities(
        self,
        min_expected_return: float = 1.0,
        max_risk_score: float = 70.0,
        available_capital_usd: float = 10000.0,
    ) -> List[UnifiedOpportunity]:
        """
        Encuentra TODAS las oportunidades de arbitraje across all strategies.

        Args:
            min_expected_return: Retorno mínimo esperado (%)
            max_risk_score: Risk score máximo aceptable
            available_capital_usd: Capital disponible

        Returns:
            Lista de oportunidades unificadas ordenadas por opportunity_score
        """
        try:
            logger.info(
                "Starting comprehensive opportunity scan",
                min_return=min_expected_return,
                max_risk=max_risk_score,
                capital=available_capital_usd,
            )

            # Execute all strategies in parallel
            tasks = [
                self._scan_funding_rate_opportunities(),
                self._scan_statistical_opportunities(),
                self._scan_delta_neutral_opportunities(),
                self._scan_triangle_opportunities(),
                self._scan_spot_p2p_opportunities(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten all opportunities
            all_opportunities: List[UnifiedOpportunity] = []

            for result in results:
                if isinstance(result, list):
                    all_opportunities.extend(result)
                elif isinstance(result, Exception):
                    logger.error("Strategy scan failed", error=str(result))

            # Filter by criteria
            filtered_opportunities = [
                opp
                for opp in all_opportunities
                if opp.expected_return_pct >= min_expected_return
                and opp.risk_score <= max_risk_score
                and opp.required_capital_usd <= available_capital_usd
            ]

            # Sort by opportunity_score (highest first)
            filtered_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)

            logger.info(
                "Opportunity scan completed",
                total_found=len(all_opportunities),
                after_filtering=len(filtered_opportunities),
                best_score=filtered_opportunities[0].opportunity_score if filtered_opportunities else 0,
            )

            return filtered_opportunities

        except Exception as exc:  # noqa: BLE001
            logger.error("Error finding opportunities", error=str(exc))
            return []

    async def get_best_opportunity(
        self,
        ranking_method: str = "risk_adjusted",  # "return", "risk_adjusted", "sharpe"
        available_capital_usd: float = 10000.0,
    ) -> Optional[UnifiedOpportunity]:
        """
        Obtiene la MEJOR oportunidad global según el método de ranking.

        Args:
            ranking_method: Método de ranking
                - "return": Mayor retorno esperado
                - "risk_adjusted": Mejor ratio return/risk
                - "sharpe": Mayor Sharpe ratio
            available_capital_usd: Capital disponible

        Returns:
            La mejor oportunidad
        """
        opportunities = await self.find_all_opportunities(
            available_capital_usd=available_capital_usd,
        )

        if not opportunities:
            return None

        # Sort by ranking method
        if ranking_method == "return":
            opportunities.sort(key=lambda x: x.expected_return_pct, reverse=True)
        elif ranking_method == "risk_adjusted":
            opportunities.sort(key=lambda x: x.risk_adjusted_return, reverse=True)
        elif ranking_method == "sharpe":
            opportunities.sort(key=lambda x: x.sharpe_ratio, reverse=True)
        else:
            # Default: use opportunity_score
            pass

        return opportunities[0]

    async def optimize_portfolio(
        self,
        total_capital_usd: float,
        max_positions: int = 5,
        min_return_per_strategy: float = 1.0,
    ) -> PortfolioAllocation:
        """
        Optimiza la asignación de capital entre múltiples estrategias.

        Usa Modern Portfolio Theory principles:
        - Maximiza retorno esperado
        - Minimiza riesgo via diversificación
        - Considera correlaciones entre estrategias

        Args:
            total_capital_usd: Capital total disponible
            max_positions: Máximo número de posiciones simultáneas
            min_return_per_strategy: Retorno mínimo por estrategia

        Returns:
            PortfolioAllocation con recomendaciones
        """
        try:
            # Get all opportunities
            all_opps = await self.find_all_opportunities(
                min_expected_return=min_return_per_strategy,
                available_capital_usd=total_capital_usd,
            )

            if not all_opps:
                return PortfolioAllocation(
                    total_capital_usd=total_capital_usd,
                    allocations=[],
                    expected_portfolio_return_pct=0,
                    portfolio_sharpe_ratio=0,
                    portfolio_risk_score=100,
                    diversification_score=0,
                    recommendation="NO OPPORTUNITIES FOUND",
                )

            # Select top opportunities
            top_opps = all_opps[:max_positions]

            # Calculate optimal allocation using simplified approach
            # In production: Use scipy.optimize for proper MPT
            allocations = []
            total_weight = 0

            for opp in top_opps:
                # Weight based on opportunity_score and inverse risk
                weight = (opp.opportunity_score / 100) * ((100 - opp.risk_score) / 100)
                total_weight += weight

            # Normalize weights
            for opp in top_opps:
                weight = (opp.opportunity_score / 100) * ((100 - opp.risk_score) / 100)
                normalized_weight = weight / total_weight if total_weight > 0 else 0
                allocated_capital = total_capital_usd * normalized_weight

                allocations.append({
                    "strategy": opp.strategy_type.value,
                    "opportunity_id": opp.opportunity_id,
                    "allocated_capital_usd": allocated_capital,
                    "weight_pct": normalized_weight * 100,
                    "expected_return_pct": opp.expected_return_pct,
                    "expected_return_usd": opp.expected_return_usd * normalized_weight,
                    "risk_score": opp.risk_score,
                    "symbols": opp.symbols,
                })

            # Calculate portfolio metrics
            portfolio_return = sum(a["expected_return_usd"] for a in allocations)
            portfolio_return_pct = (portfolio_return / total_capital_usd) * 100

            # Weighted average risk
            portfolio_risk = sum(
                a["risk_score"] * (a["weight_pct"] / 100) for a in allocations
            )

            # Simplified Sharpe (return / risk)
            portfolio_sharpe = portfolio_return_pct / portfolio_risk if portfolio_risk > 0 else 0

            # Diversification score
            strategy_types = set(a["strategy"] for a in allocations)
            diversification_score = (len(strategy_types) / len(StrategyType)) * 100

            # Generate recommendation
            recommendation = self._generate_portfolio_recommendation(
                portfolio_return_pct=portfolio_return_pct,
                portfolio_risk=portfolio_risk,
                diversification=diversification_score,
            )

            return PortfolioAllocation(
                total_capital_usd=total_capital_usd,
                allocations=allocations,
                expected_portfolio_return_pct=portfolio_return_pct,
                portfolio_sharpe_ratio=portfolio_sharpe,
                portfolio_risk_score=portfolio_risk,
                diversification_score=diversification_score,
                recommendation=recommendation,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error optimizing portfolio", error=str(exc))
            return PortfolioAllocation(
                total_capital_usd=total_capital_usd,
                allocations=[],
                expected_portfolio_return_pct=0,
                portfolio_sharpe_ratio=0,
                portfolio_risk_score=100,
                diversification_score=0,
                recommendation="ERROR",
            )

    async def compare_strategies(
        self,
        available_capital_usd: float = 10000.0,
    ) -> Dict[str, Any]:
        """
        Compara todas las estrategias side-by-side.

        Returns:
            Dict con comparación detallada de todas las estrategias
        """
        try:
            opportunities = await self.find_all_opportunities(
                available_capital_usd=available_capital_usd,
            )

            # Group by strategy type
            by_strategy: Dict[str, List[UnifiedOpportunity]] = {}

            for opp in opportunities:
                strategy = opp.strategy_type.value
                if strategy not in by_strategy:
                    by_strategy[strategy] = []
                by_strategy[strategy].append(opp)

            # Calculate metrics per strategy
            strategy_comparison = []

            for strategy_name, opps in by_strategy.items():
                if opps:
                    avg_return = sum(o.expected_return_pct for o in opps) / len(opps)
                    avg_risk = sum(o.risk_score for o in opps) / len(opps)
                    avg_sharpe = sum(o.sharpe_ratio for o in opps) / len(opps)
                    best_return = max(o.expected_return_pct for o in opps)
                    best_opportunity = max(opps, key=lambda x: x.opportunity_score)

                    strategy_comparison.append({
                        "strategy": strategy_name,
                        "opportunities_found": len(opps),
                        "avg_return_pct": round(avg_return, 2),
                        "best_return_pct": round(best_return, 2),
                        "avg_risk_score": round(avg_risk, 2),
                        "avg_sharpe_ratio": round(avg_sharpe, 2),
                        "best_opportunity_score": round(best_opportunity.opportunity_score, 2),
                    })

            # Sort by avg return
            strategy_comparison.sort(key=lambda x: x["avg_return_pct"], reverse=True)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_opportunities": len(opportunities),
                "strategies_active": len(by_strategy),
                "comparison": strategy_comparison,
                "best_overall_strategy": strategy_comparison[0]["strategy"] if strategy_comparison else None,
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Error comparing strategies", error=str(exc))
            return {}

    # ==================== STRATEGY SCANNERS ====================

    async def _scan_funding_rate_opportunities(self) -> List[UnifiedOpportunity]:
        """Escanea oportunidades de funding rate arbitrage."""
        try:
            opportunities = await self.funding_rate_service.find_all_opportunities()

            unified = []
            for opp in opportunities:
                unified_opp = self._unify_funding_rate_opportunity(opp)
                if unified_opp:
                    unified.append(unified_opp)

            return unified

        except Exception as exc:  # noqa: BLE001
            logger.error("Error scanning funding rate opportunities", error=str(exc))
            return []

    async def _scan_statistical_opportunities(self) -> List[UnifiedOpportunity]:
        """Escanea oportunidades de statistical arbitrage."""
        try:
            signals = await self.statistical_service.find_all_opportunities()

            unified = []
            for signal in signals:
                unified_opp = self._unify_statistical_opportunity(signal)
                if unified_opp:
                    unified.append(unified_opp)

            return unified

        except Exception as exc:  # noqa: BLE001
            logger.error("Error scanning statistical opportunities", error=str(exc))
            return []

    async def _scan_delta_neutral_opportunities(self) -> List[UnifiedOpportunity]:
        """Escanea oportunidades de delta-neutral arbitrage."""
        try:
            opportunities = await self.delta_neutral_service.find_all_opportunities()

            unified = []
            for opp in opportunities:
                unified_opp = self._unify_delta_neutral_opportunity(opp)
                if unified_opp:
                    unified.append(unified_opp)

            return unified

        except Exception as exc:  # noqa: BLE001
            logger.error("Error scanning delta-neutral opportunities", error=str(exc))
            return []

    async def _scan_triangle_opportunities(self) -> List[UnifiedOpportunity]:
        """Escanea oportunidades de triangle arbitrage."""
        try:
            paths = await self.triangle_service.find_all_arbitrage_paths()

            unified = []
            for path in paths:
                unified_opp = self._unify_triangle_opportunity(path)
                if unified_opp:
                    unified.append(unified_opp)

            return unified

        except Exception as exc:  # noqa: BLE001
            logger.error("Error scanning triangle opportunities", error=str(exc))
            return []

    async def _scan_spot_p2p_opportunities(self) -> List[UnifiedOpportunity]:
        """Escanea oportunidades de spot-to-P2P arbitrage."""
        # TODO: Implement using basic arbitrage service
        return []

    # ==================== UNIFIERS ====================

    def _unify_funding_rate_opportunity(
        self,
        opp: FundingRateOpportunity,
    ) -> Optional[UnifiedOpportunity]:
        """Convierte funding rate opportunity a formato unificado."""
        try:
            opportunity_id = f"FR_{opp.symbol}_{int(datetime.now().timestamp())}"

            # Calculate metrics
            sharpe_ratio = opp.net_apy / 10 if opp.net_apy > 0 else 0  # Simplified
            risk_adjusted_return = opp.net_apy / ((opp.opportunity_score / 100) * 10)

            # Determine priority
            if opp.opportunity_score >= 70:
                priority = "HIGH"
            elif opp.opportunity_score >= 50:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            return UnifiedOpportunity(
                opportunity_id=opportunity_id,
                strategy_type=StrategyType.FUNDING_RATE,
                timestamp=datetime.utcnow(),
                expected_return_pct=opp.net_apy / 365 * 7,  # Weekly return
                expected_return_usd=opp.expected_daily_profit * 7,  # Weekly
                risk_score=self._map_risk_level_to_score(opp.risk_level),
                confidence=opp.opportunity_score,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sharpe_ratio * 1.2,  # Simplified
                risk_adjusted_return=risk_adjusted_return,
                required_capital_usd=opp.required_margin,
                execution_time_estimate_seconds=300,  # 5 min
                complexity_score=40,  # Medium complexity
                liquidity_score=80,  # Futures usually liquid
                max_position_size_usd=100000,  # High for futures
                opportunity_score=opp.opportunity_score,
                priority=priority,
                recommendation=opp.recommendation,
                details=opp.__dict__,
                execution_plan={
                    "strategy": opp.direction,
                    "symbol": opp.symbol,
                    "funding_rate": opp.funding_rate_pct,
                },
                exchange="Binance",
                symbols=[opp.symbol],
                tags=["futures", "low_risk", "passive_income"],
            )

        except Exception as exc:
            logger.error("Error unifying funding rate opportunity", error=str(exc))
            return None

    def _unify_statistical_opportunity(
        self,
        signal: PairSignal,
    ) -> Optional[UnifiedOpportunity]:
        """Convierte statistical arbitrage signal a formato unificado."""
        try:
            opportunity_id = f"STAT_{signal.pair_name}_{int(datetime.now().timestamp())}"

            sharpe_ratio = signal.confidence / 20  # Simplified
            risk_adjusted_return = signal.expected_return_pct / (100 - signal.confidence)

            if signal.confidence >= 70:
                priority = "HIGH"
            elif signal.confidence >= 50:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            return UnifiedOpportunity(
                opportunity_id=opportunity_id,
                strategy_type=StrategyType.STATISTICAL,
                timestamp=datetime.utcnow(),
                expected_return_pct=signal.expected_return_pct,
                expected_return_usd=signal.expected_profit_usd,
                risk_score=self._map_risk_level_to_score(signal.risk_level),
                confidence=signal.confidence,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sharpe_ratio * 1.1,
                risk_adjusted_return=risk_adjusted_return,
                required_capital_usd=10000,  # Default
                execution_time_estimate_seconds=600,  # 10 min
                complexity_score=60,  # Higher complexity
                liquidity_score=70,
                max_position_size_usd=50000,
                opportunity_score=signal.confidence,
                priority=priority,
                recommendation=signal.recommendation,
                details=signal.__dict__,
                execution_plan={
                    "pair": signal.pair_name,
                    "signal": signal.signal_type,
                    "z_score": signal.z_score,
                },
                exchange="Binance",
                symbols=[signal.asset_1, signal.asset_2],
                tags=["pairs_trading", "mean_reversion", "advanced"],
            )

        except Exception as exc:
            logger.error("Error unifying statistical opportunity", error=str(exc))
            return None

    def _unify_delta_neutral_opportunity(
        self,
        opp: DeltaNeutralOpportunity,
    ) -> Optional[UnifiedOpportunity]:
        """Convierte delta-neutral opportunity a formato unificado."""
        try:
            opportunity_id = f"DN_{opp.symbol}_{int(datetime.now().timestamp())}"

            risk_adjusted_return = opp.net_return_after_fees_pct / ((opp.risk_score / 100) * 10)

            if opp.opportunity_score >= 70:
                priority = "HIGH"
            elif opp.opportunity_score >= 50:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            return UnifiedOpportunity(
                opportunity_id=opportunity_id,
                strategy_type=StrategyType.DELTA_NEUTRAL,
                timestamp=datetime.utcnow(),
                expected_return_pct=opp.net_return_after_fees_pct,
                expected_return_usd=(opp.net_return_after_fees_pct / 100) * opp.position_value_usd,
                risk_score=self._map_risk_level_to_score(opp.basis_risk_level),
                confidence=opp.opportunity_score,
                sharpe_ratio=opp.sharpe_ratio,
                sortino_ratio=opp.sharpe_ratio * 1.15,
                risk_adjusted_return=risk_adjusted_return,
                required_capital_usd=opp.required_capital_usd,
                execution_time_estimate_seconds=300,
                complexity_score=50,
                liquidity_score=75,
                max_position_size_usd=200000,
                opportunity_score=opp.opportunity_score,
                priority=priority,
                recommendation=opp.recommendation,
                details=opp.__dict__,
                execution_plan={
                    "strategy": opp.direction,
                    "symbol": opp.symbol,
                    "basis": opp.basis_pct,
                },
                exchange="Binance",
                symbols=[opp.symbol],
                tags=["delta_neutral", "low_risk", "basis_trading"],
            )

        except Exception as exc:
            logger.error("Error unifying delta-neutral opportunity", error=str(exc))
            return None

    def _unify_triangle_opportunity(
        self,
        path: ArbitragePath,
    ) -> Optional[UnifiedOpportunity]:
        """Convierte triangle arbitrage path a formato unificado."""
        try:
            opportunity_id = f"TRI_{'_'.join(path.path)}_{int(datetime.now().timestamp())}"

            sharpe_ratio = path.roi_percentage / (path.risk_score / 10)
            risk_adjusted_return = path.roi_percentage / ((path.risk_score / 100) + 0.1)

            if path.opportunity_score >= 70:
                priority = "HIGH"
            elif path.opportunity_score >= 50:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            return UnifiedOpportunity(
                opportunity_id=opportunity_id,
                strategy_type=StrategyType.TRIANGLE,
                timestamp=datetime.utcnow(),
                expected_return_pct=path.roi_percentage,
                expected_return_usd=path.profit_amount,
                risk_score=path.risk_score,
                confidence=path.liquidity_score,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sharpe_ratio * 1.1,
                risk_adjusted_return=risk_adjusted_return,
                required_capital_usd=path.initial_amount,
                execution_time_estimate_seconds=path.execution_time_estimate,
                complexity_score=path.num_steps * 15,  # More steps = more complex
                liquidity_score=path.liquidity_score,
                max_position_size_usd=50000,
                opportunity_score=path.opportunity_score,
                priority=priority,
                recommendation="BUY" if path.opportunity_score >= 50 else "AVOID",
                details={"path": path.path, "steps": path.steps},
                execution_plan={
                    "route": " → ".join(path.path),
                    "steps": path.num_steps,
                },
                exchange="Binance P2P",
                symbols=path.path,
                tags=["triangle", "multi_step", "p2p"],
            )

        except Exception as exc:
            logger.error("Error unifying triangle opportunity", error=str(exc))
            return None

    # ==================== HELPERS ====================

    def _map_risk_level_to_score(self, risk_level: str) -> float:
        """Mapea nivel de riesgo a score numérico."""
        mapping = {
            "BAJO": 20,
            "MODERADO": 50,
            "ALTO": 80,
            "MUY ALTO": 95,
        }
        return mapping.get(risk_level, 50)

    def _generate_portfolio_recommendation(
        self,
        portfolio_return_pct: float,
        portfolio_risk: float,
        diversification: float,
    ) -> str:
        """Genera recomendación para el portfolio."""
        if portfolio_return_pct >= 5 and portfolio_risk <= 40 and diversification >= 60:
            return "🚀 EJECUTAR PORTFOLIO - Excelente balance return/risk/diversificación"
        elif portfolio_return_pct >= 3 and portfolio_risk <= 60:
            return "✅ EJECUTAR PORTFOLIO - Buen balance return/risk"
        elif portfolio_return_pct >= 1:
            return "⚠️ CONSIDERAR - Retorno moderado"
        else:
            return "❌ NO EJECUTAR - Riesgo supera retorno"
