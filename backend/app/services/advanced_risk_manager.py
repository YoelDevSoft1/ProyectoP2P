"""
Advanced Risk Manager - Gestión de riesgo para estrategias avanzadas de arbitraje.

Capacidades:
1. Strategy-specific risk metrics
2. Portfolio correlation analysis
3. Dynamic position sizing
4. Stress testing & scenario analysis
5. Real-time risk monitoring
6. Multi-strategy risk aggregation
7. Drawdown protection
8. Volatility targeting
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import structlog

from app.core.config import settings
from app.services.advanced_opportunity_analyzer import (
    StrategyType,
    UnifiedOpportunity,
)

logger = structlog.get_logger()


@dataclass
class StrategyRiskProfile:
    """Perfil de riesgo para una estrategia específica."""

    strategy_type: StrategyType
    expected_return_pct: float
    volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    var_95_pct: float  # Value at Risk 95%
    var_99_pct: float  # Value at Risk 99%
    correlation_with_market: float
    liquidity_score: float  # 0-100
    complexity_score: float  # 0-100
    recommended_allocation_pct: float  # % of portfolio
    max_position_size_usd: float
    risk_rating: str  # A, B, C, D, F


@dataclass
class PortfolioRiskMetrics:
    """Métricas de riesgo para el portfolio completo."""

    total_exposure_usd: float
    portfolio_var_95_pct: float
    portfolio_var_99_pct: float
    portfolio_volatility_pct: float
    portfolio_sharpe: float
    portfolio_max_drawdown_pct: float
    concentration_risk_score: float  # 0-100 (higher = more concentrated)
    diversification_ratio: float  # >1 = benefits from diversification
    correlation_matrix: Dict[str, Dict[str, float]]
    risk_parity_score: float  # 0-100 (higher = better risk balance)
    stress_test_results: Dict[str, float]


class AdvancedRiskManager:
    """
    Gestor avanzado de riesgo para múltiples estrategias de arbitraje.
    """

    # Risk limits
    MAX_PORTFOLIO_VAR_PCT = 10.0  # Max portfolio VaR
    MAX_STRATEGY_ALLOCATION_PCT = 40.0  # Max allocation to single strategy
    MIN_DIVERSIFICATION_RATIO = 1.2  # Minimum diversification benefit
    MAX_CONCENTRATION_SCORE = 60.0  # Max concentration risk
    TARGET_VOLATILITY_PCT = 15.0  # Annual volatility target

    # Strategy-specific risk parameters
    STRATEGY_RISK_PARAMS = {
        StrategyType.FUNDING_RATE: {
            "base_volatility": 5.0,  # Low volatility
            "max_leverage": 3,
            "liquidity_weight": 0.9,
            "market_correlation": 0.1,  # Low correlation
        },
        StrategyType.STATISTICAL: {
            "base_volatility": 12.0,  # Medium volatility
            "max_leverage": 1,
            "liquidity_weight": 0.7,
            "market_correlation": 0.3,
        },
        StrategyType.DELTA_NEUTRAL: {
            "base_volatility": 6.0,  # Low volatility
            "max_leverage": 2,
            "liquidity_weight": 0.85,
            "market_correlation": 0.05,  # Very low
        },
        StrategyType.TRIANGLE: {
            "base_volatility": 8.0,  # Low-medium volatility
            "max_leverage": 1,
            "liquidity_weight": 0.75,
            "market_correlation": 0.15,
        },
        StrategyType.SPOT_TO_P2P: {
            "base_volatility": 10.0,  # Medium volatility
            "max_leverage": 1,
            "liquidity_weight": 0.8,
            "market_correlation": 0.25,
        },
    }

    def __init__(self) -> None:
        """Inicializar risk manager."""
        self.risk_free_rate = 0.12  # 12% anual (Colombia)

    async def analyze_strategy_risk(
        self,
        opportunity: UnifiedOpportunity,
        historical_returns: Optional[List[float]] = None,
    ) -> StrategyRiskProfile:
        """
        Analiza el perfil de riesgo de una estrategia específica.

        Args:
            opportunity: Oportunidad a analizar
            historical_returns: Retornos históricos si disponibles

        Returns:
            StrategyRiskProfile con métricas completas
        """
        try:
            strategy_type = opportunity.strategy_type
            params = self.STRATEGY_RISK_PARAMS.get(strategy_type, {})

            # Calculate or estimate volatility
            if historical_returns and len(historical_returns) >= 30:
                volatility_pct = np.std(historical_returns) * np.sqrt(252)  # Annualize
                max_drawdown_pct = self._calculate_max_drawdown(historical_returns)
            else:
                # Use base volatility from parameters
                volatility_pct = params.get("base_volatility", 10.0)
                # Estimate drawdown from volatility
                max_drawdown_pct = volatility_pct * 2.0

            # Calculate Sharpe ratio
            sharpe_ratio = opportunity.sharpe_ratio

            # Calculate Sortino ratio (only downside volatility)
            sortino_ratio = opportunity.sortino_ratio

            # Calculate VaR (Value at Risk)
            var_95_pct = self._calculate_var(
                expected_return=opportunity.expected_return_pct,
                volatility=volatility_pct,
                confidence_level=0.95,
            )
            var_99_pct = self._calculate_var(
                expected_return=opportunity.expected_return_pct,
                volatility=volatility_pct,
                confidence_level=0.99,
            )

            # Market correlation
            market_correlation = params.get("market_correlation", 0.2)

            # Liquidity score
            liquidity_score = opportunity.liquidity_score

            # Complexity score
            complexity_score = opportunity.complexity_score

            # Calculate recommended allocation
            recommended_allocation_pct = self._calculate_optimal_allocation(
                sharpe_ratio=sharpe_ratio,
                volatility=volatility_pct,
                liquidity_score=liquidity_score,
            )

            # Max position size
            max_position_size_usd = opportunity.max_position_size_usd

            # Risk rating (A-F scale)
            risk_rating = self._calculate_risk_rating(
                sharpe_ratio=sharpe_ratio,
                max_drawdown_pct=max_drawdown_pct,
                volatility_pct=volatility_pct,
            )

            return StrategyRiskProfile(
                strategy_type=strategy_type,
                expected_return_pct=opportunity.expected_return_pct,
                volatility_pct=volatility_pct,
                max_drawdown_pct=max_drawdown_pct,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                var_95_pct=var_95_pct,
                var_99_pct=var_99_pct,
                correlation_with_market=market_correlation,
                liquidity_score=liquidity_score,
                complexity_score=complexity_score,
                recommended_allocation_pct=recommended_allocation_pct,
                max_position_size_usd=max_position_size_usd,
                risk_rating=risk_rating,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing strategy risk", error=str(exc))
            raise

    async def analyze_portfolio_risk(
        self,
        opportunities: List[UnifiedOpportunity],
        allocations: Dict[str, float],  # opportunity_id -> allocated_capital
    ) -> PortfolioRiskMetrics:
        """
        Analiza el riesgo del portfolio completo considerando correlaciones.

        Args:
            opportunities: Lista de oportunidades en el portfolio
            allocations: Dict mapeando opportunity_id a capital asignado

        Returns:
            PortfolioRiskMetrics con análisis completo
        """
        try:
            # Calculate total exposure
            total_exposure = sum(allocations.values())

            # Build correlation matrix between strategies
            correlation_matrix = await self._build_correlation_matrix(opportunities)

            # Calculate portfolio variance (considering correlations)
            portfolio_variance = await self._calculate_portfolio_variance(
                opportunities=opportunities,
                allocations=allocations,
                correlation_matrix=correlation_matrix,
            )

            portfolio_volatility_pct = np.sqrt(portfolio_variance) * 100

            # Calculate portfolio Sharpe
            weighted_returns = []
            for opp in opportunities:
                if opp.opportunity_id in allocations:
                    weight = allocations[opp.opportunity_id] / total_exposure
                    weighted_returns.append(opp.expected_return_pct * weight)

            portfolio_return = sum(weighted_returns)
            portfolio_sharpe = (portfolio_return - self.risk_free_rate) / portfolio_volatility_pct

            # Calculate portfolio VaR
            portfolio_var_95 = self._calculate_var(
                expected_return=portfolio_return,
                volatility=portfolio_volatility_pct,
                confidence_level=0.95,
            )
            portfolio_var_99 = self._calculate_var(
                expected_return=portfolio_return,
                volatility=portfolio_volatility_pct,
                confidence_level=0.99,
            )

            # Estimate max drawdown for portfolio
            portfolio_max_drawdown_pct = portfolio_volatility_pct * 2.5

            # Calculate concentration risk
            concentration_score = self._calculate_concentration_risk(allocations, total_exposure)

            # Calculate diversification ratio
            # DR = Portfolio Volatility / Weighted Average Individual Volatilities
            individual_vols = []
            for opp in opportunities:
                if opp.opportunity_id in allocations:
                    weight = allocations[opp.opportunity_id] / total_exposure
                    # Estimate individual volatility from strategy type
                    params = self.STRATEGY_RISK_PARAMS.get(opp.strategy_type, {})
                    individual_vol = params.get("base_volatility", 10.0)
                    individual_vols.append(weight * individual_vol)

            weighted_avg_vol = sum(individual_vols)
            diversification_ratio = weighted_avg_vol / portfolio_volatility_pct if portfolio_volatility_pct > 0 else 1.0

            # Calculate risk parity score
            risk_parity_score = self._calculate_risk_parity_score(
                opportunities=opportunities,
                allocations=allocations,
                portfolio_volatility=portfolio_volatility_pct,
            )

            # Run stress tests
            stress_test_results = await self._run_stress_tests(
                opportunities=opportunities,
                allocations=allocations,
            )

            return PortfolioRiskMetrics(
                total_exposure_usd=total_exposure,
                portfolio_var_95_pct=portfolio_var_95,
                portfolio_var_99_pct=portfolio_var_99,
                portfolio_volatility_pct=portfolio_volatility_pct,
                portfolio_sharpe=portfolio_sharpe,
                portfolio_max_drawdown_pct=portfolio_max_drawdown_pct,
                concentration_risk_score=concentration_score,
                diversification_ratio=diversification_ratio,
                correlation_matrix=correlation_matrix,
                risk_parity_score=risk_parity_score,
                stress_test_results=stress_test_results,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing portfolio risk", error=str(exc))
            raise

    async def calculate_dynamic_position_size(
        self,
        opportunity: UnifiedOpportunity,
        available_capital: float,
        current_portfolio_volatility: float = 0,
    ) -> float:
        """
        Calcula el tamaño de posición óptimo usando volatility targeting.

        Args:
            opportunity: Oportunidad a analizar
            available_capital: Capital disponible
            current_portfolio_volatility: Volatilidad actual del portfolio

        Returns:
            Tamaño de posición recomendado en USD
        """
        try:
            # Get strategy parameters
            params = self.STRATEGY_RISK_PARAMS.get(opportunity.strategy_type, {})
            base_volatility = params.get("base_volatility", 10.0)

            # Calculate volatility scalar
            # If current portfolio vol is low, can increase position size
            if current_portfolio_volatility > 0:
                vol_scalar = self.TARGET_VOLATILITY_PCT / current_portfolio_volatility
            else:
                vol_scalar = 1.0

            # Constrain scalar
            vol_scalar = np.clip(vol_scalar, 0.5, 2.0)

            # Base position size (Kelly criterion approach)
            win_rate = opportunity.confidence / 100
            avg_win = opportunity.expected_return_pct
            avg_loss = opportunity.risk_score / 100 * avg_win  # Estimate loss

            if avg_win > 0:
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                # Use half-Kelly for safety
                kelly_fraction = kelly_fraction * 0.5
            else:
                kelly_fraction = 0.1

            # Apply constraints
            kelly_fraction = np.clip(kelly_fraction, 0.05, 0.25)  # 5% to 25%

            # Calculate position size
            base_position = available_capital * kelly_fraction

            # Adjust by volatility scalar
            adjusted_position = base_position * vol_scalar

            # Apply max limits
            max_from_liquidity = opportunity.max_position_size_usd
            max_from_capital = available_capital * 0.40  # Max 40% in single position

            final_position = min(adjusted_position, max_from_liquidity, max_from_capital)

            return round(final_position, 2)

        except Exception as exc:  # noqa: BLE001
            logger.error("Error calculating position size", error=str(exc))
            return available_capital * 0.10  # Conservative default

    async def check_risk_limits(
        self,
        portfolio_metrics: PortfolioRiskMetrics,
    ) -> Dict[str, any]:
        """
        Verifica si el portfolio cumple con los límites de riesgo.

        Returns:
            Dict con status y violaciones
        """
        violations = []

        # Check VaR limits
        if abs(portfolio_metrics.portfolio_var_95_pct) > self.MAX_PORTFOLIO_VAR_PCT:
            violations.append({
                "type": "VAR_LIMIT",
                "metric": "Portfolio VaR 95%",
                "value": portfolio_metrics.portfolio_var_95_pct,
                "limit": self.MAX_PORTFOLIO_VAR_PCT,
                "severity": "HIGH",
            })

        # Check concentration
        if portfolio_metrics.concentration_risk_score > self.MAX_CONCENTRATION_SCORE:
            violations.append({
                "type": "CONCENTRATION",
                "metric": "Concentration Risk Score",
                "value": portfolio_metrics.concentration_risk_score,
                "limit": self.MAX_CONCENTRATION_SCORE,
                "severity": "MEDIUM",
            })

        # Check diversification
        if portfolio_metrics.diversification_ratio < self.MIN_DIVERSIFICATION_RATIO:
            violations.append({
                "type": "DIVERSIFICATION",
                "metric": "Diversification Ratio",
                "value": portfolio_metrics.diversification_ratio,
                "limit": self.MIN_DIVERSIFICATION_RATIO,
                "severity": "MEDIUM",
            })

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "risk_score": self._calculate_overall_risk_score(portfolio_metrics),
            "recommendation": self._generate_risk_recommendation(violations, portfolio_metrics),
        }

    # ==================== HELPER METHODS ====================

    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calcula maximum drawdown de una serie de retornos."""
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown)
        return abs(max_drawdown)

    def _calculate_var(
        self,
        expected_return: float,
        volatility: float,
        confidence_level: float,
    ) -> float:
        """Calcula Value at Risk paramétrico."""
        z_scores = {0.95: 1.645, 0.99: 2.326}
        z = z_scores.get(confidence_level, 1.645)
        var = expected_return - (z * volatility)
        return var

    def _calculate_optimal_allocation(
        self,
        sharpe_ratio: float,
        volatility: float,
        liquidity_score: float,
    ) -> float:
        """Calcula asignación óptima basada en métricas."""
        # Base on Sharpe ratio
        base_allocation = min(sharpe_ratio * 10, 30)  # Max 30%

        # Adjust by volatility (prefer lower vol)
        vol_adjustment = 1 - (volatility / 50)  # Normalize
        vol_adjustment = max(vol_adjustment, 0.5)

        # Adjust by liquidity
        liquidity_adjustment = liquidity_score / 100

        final_allocation = base_allocation * vol_adjustment * liquidity_adjustment

        return min(final_allocation, self.MAX_STRATEGY_ALLOCATION_PCT)

    def _calculate_risk_rating(
        self,
        sharpe_ratio: float,
        max_drawdown_pct: float,
        volatility_pct: float,
    ) -> str:
        """Calcula rating de riesgo A-F."""
        score = 0

        # Sharpe component
        if sharpe_ratio >= 3:
            score += 40
        elif sharpe_ratio >= 2:
            score += 30
        elif sharpe_ratio >= 1:
            score += 20
        elif sharpe_ratio >= 0.5:
            score += 10

        # Drawdown component
        if max_drawdown_pct <= 10:
            score += 30
        elif max_drawdown_pct <= 20:
            score += 20
        elif max_drawdown_pct <= 30:
            score += 10

        # Volatility component
        if volatility_pct <= 10:
            score += 30
        elif volatility_pct <= 20:
            score += 20
        elif volatility_pct <= 30:
            score += 10

        # Map score to rating
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        elif score >= 20:
            return "D"
        else:
            return "F"

    async def _build_correlation_matrix(
        self,
        opportunities: List[UnifiedOpportunity],
    ) -> Dict[str, Dict[str, float]]:
        """Construye matriz de correlación entre estrategias."""
        matrix = {}

        for opp1 in opportunities:
            strategy1 = opp1.strategy_type.value
            if strategy1 not in matrix:
                matrix[strategy1] = {}

            for opp2 in opportunities:
                strategy2 = opp2.strategy_type.value

                if strategy1 == strategy2:
                    correlation = 1.0
                else:
                    # Estimated correlations between strategy types
                    correlation = self._estimate_strategy_correlation(
                        opp1.strategy_type,
                        opp2.strategy_type,
                    )

                matrix[strategy1][strategy2] = correlation

        return matrix

    def _estimate_strategy_correlation(
        self,
        strategy1: StrategyType,
        strategy2: StrategyType,
    ) -> float:
        """Estima correlación entre dos tipos de estrategias."""
        # Correlation estimates (based on typical behavior)
        correlations = {
            (StrategyType.FUNDING_RATE, StrategyType.DELTA_NEUTRAL): 0.6,
            (StrategyType.FUNDING_RATE, StrategyType.STATISTICAL): 0.2,
            (StrategyType.FUNDING_RATE, StrategyType.TRIANGLE): 0.1,
            (StrategyType.DELTA_NEUTRAL, StrategyType.STATISTICAL): 0.3,
            (StrategyType.DELTA_NEUTRAL, StrategyType.TRIANGLE): 0.15,
            (StrategyType.STATISTICAL, StrategyType.TRIANGLE): 0.25,
        }

        key = (strategy1, strategy2)
        reverse_key = (strategy2, strategy1)

        return correlations.get(key, correlations.get(reverse_key, 0.3))

    async def _calculate_portfolio_variance(
        self,
        opportunities: List[UnifiedOpportunity],
        allocations: Dict[str, float],
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        """Calcula varianza del portfolio considerando correlaciones."""
        total_capital = sum(allocations.values())

        # Get strategy volatilities and weights
        strategy_data = []
        for opp in opportunities:
            if opp.opportunity_id in allocations:
                params = self.STRATEGY_RISK_PARAMS.get(opp.strategy_type, {})
                vol = params.get("base_volatility", 10.0) / 100  # Convert to decimal
                weight = allocations[opp.opportunity_id] / total_capital
                strategy_data.append({
                    "strategy": opp.strategy_type.value,
                    "weight": weight,
                    "volatility": vol,
                })

        # Calculate portfolio variance: w'Σw
        variance = 0
        for i, data_i in enumerate(strategy_data):
            for j, data_j in enumerate(strategy_data):
                correlation = correlation_matrix.get(
                    data_i["strategy"], {}
                ).get(data_j["strategy"], 0.3)

                variance += (
                    data_i["weight"] *
                    data_j["weight"] *
                    data_i["volatility"] *
                    data_j["volatility"] *
                    correlation
                )

        return variance

    def _calculate_concentration_risk(
        self,
        allocations: Dict[str, float],
        total_exposure: float,
    ) -> float:
        """
        Calcula concentration risk score usando Herfindahl index.

        Score: 0-100 (higher = more concentrated)
        """
        if total_exposure == 0:
            return 0

        weights = [amount / total_exposure for amount in allocations.values()]
        herfindahl = sum(w ** 2 for w in weights)

        # Normalize to 0-100 scale
        # HHI ranges from 1/n (perfect diversification) to 1 (total concentration)
        n = len(allocations)
        min_hhi = 1 / n if n > 0 else 0
        max_hhi = 1

        if max_hhi > min_hhi:
            normalized_score = ((herfindahl - min_hhi) / (max_hhi - min_hhi)) * 100
        else:
            normalized_score = 0

        return normalized_score

    def _calculate_risk_parity_score(
        self,
        opportunities: List[UnifiedOpportunity],
        allocations: Dict[str, float],
        portfolio_volatility: float,
    ) -> float:
        """
        Calcula risk parity score (0-100).

        Risk parity = each position contributes equally to portfolio risk.
        Score of 100 = perfect risk parity.
        """
        # Calculate risk contribution of each position
        total_capital = sum(allocations.values())
        risk_contributions = []

        for opp in opportunities:
            if opp.opportunity_id in allocations:
                weight = allocations[opp.opportunity_id] / total_capital
                params = self.STRATEGY_RISK_PARAMS.get(opp.strategy_type, {})
                vol = params.get("base_volatility", 10.0)

                # Risk contribution = weight * volatility / portfolio_volatility
                risk_contrib = (weight * vol) / portfolio_volatility if portfolio_volatility > 0 else 0
                risk_contributions.append(risk_contrib)

        if not risk_contributions:
            return 0

        # Calculate variance of risk contributions
        # Lower variance = more equal contributions = better risk parity
        mean_contrib = np.mean(risk_contributions)
        variance_contrib = np.var(risk_contributions)

        # Normalize to score (lower variance = higher score)
        score = 100 * (1 - min(variance_contrib / (mean_contrib ** 2), 1))

        return score

    async def _run_stress_tests(
        self,
        opportunities: List[UnifiedOpportunity],
        allocations: Dict[str, float],
    ) -> Dict[str, float]:
        """Ejecuta stress tests en escenarios extremos."""
        # Scenario: Market crash (all correlations → 1)
        total_loss_crash = 0
        total_capital = sum(allocations.values())

        for opp in opportunities:
            if opp.opportunity_id in allocations:
                # Assume -20% loss in crash
                loss = allocations[opp.opportunity_id] * 0.20
                total_loss_crash += loss

        crash_loss_pct = (total_loss_crash / total_capital) * 100 if total_capital > 0 else 0

        # Scenario: Liquidity crisis (wider spreads)
        liquidity_loss = 0
        for opp in opportunities:
            if opp.opportunity_id in allocations:
                # Assume 5% slippage
                loss = allocations[opp.opportunity_id] * 0.05
                liquidity_loss += loss

        liquidity_loss_pct = (liquidity_loss / total_capital) * 100 if total_capital > 0 else 0

        # Scenario: Funding rate reversal (for funding strategies)
        funding_loss = 0
        for opp in opportunities:
            if opp.opportunity_id in allocations:
                if opp.strategy_type == StrategyType.FUNDING_RATE:
                    # Assume funding goes negative
                    loss = allocations[opp.opportunity_id] * 0.10
                    funding_loss += loss

        funding_loss_pct = (funding_loss / total_capital) * 100 if total_capital > 0 else 0

        return {
            "market_crash_loss_pct": -crash_loss_pct,
            "liquidity_crisis_loss_pct": -liquidity_loss_pct,
            "funding_reversal_loss_pct": -funding_loss_pct,
            "worst_case_loss_pct": -max(crash_loss_pct, liquidity_loss_pct, funding_loss_pct),
        }

    def _calculate_overall_risk_score(
        self,
        metrics: PortfolioRiskMetrics,
    ) -> float:
        """Calcula risk score general (0-100, lower is better)."""
        score = 0

        # VaR component (30%)
        var_component = min(abs(metrics.portfolio_var_95_pct) / self.MAX_PORTFOLIO_VAR_PCT, 1) * 30

        # Concentration component (25%)
        concentration_component = (metrics.concentration_risk_score / 100) * 25

        # Volatility component (25%)
        vol_component = min(metrics.portfolio_volatility_pct / 30, 1) * 25

        # Diversification component (20%) - inverse
        div_component = (1 - min(metrics.diversification_ratio / 2, 1)) * 20

        score = var_component + concentration_component + vol_component + div_component

        return round(score, 2)

    def _generate_risk_recommendation(
        self,
        violations: List[Dict],
        metrics: PortfolioRiskMetrics,
    ) -> str:
        """Genera recomendación basada en análisis de riesgo."""
        if not violations:
            if metrics.portfolio_sharpe >= 2.0:
                return "✅ EXCELLENT - Portfolio meets all risk limits with strong returns"
            else:
                return "✅ GOOD - Portfolio is within risk limits"

        high_severity = [v for v in violations if v["severity"] == "HIGH"]

        if high_severity:
            return "❌ CRITICAL - Immediate action required to reduce risk exposure"

        return "⚠️ WARNING - Portfolio has risk limit violations that should be addressed"
