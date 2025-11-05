"""
Servicio de Delta-Neutral Arbitrage (Spot-Futures).

Estrategia que combina posiciones en Spot y Futures para eliminar exposición direccional
al precio (delta = 0) mientras captura oportunidades de:
1. Basis trading (diferencia spot-futures)
2. Funding rate payments
3. Convergence trading

Estrategia:
- Futures > Spot (Contango):
  → Long Spot + Short Futures = Profit from basis convergence + funding

- Spot > Futures (Backwardation):
  → Short Spot + Long Futures = Profit from basis convergence

Esta es una estrategia market-neutral de muy bajo riesgo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog

from app.core.config import settings
from app.services.binance_futures_service import BinanceFuturesService
from app.services.binance_spot_service import BinanceSpotService

logger = structlog.get_logger()


@dataclass
class DeltaNeutralOpportunity:
    """Oportunidad de arbitraje delta-neutral."""

    symbol: str
    asset: str  # e.g., BTC

    # Prices
    spot_price: float
    futures_price: float
    basis: float  # spot - futures
    basis_pct: float  # (basis / spot) * 100

    # Funding rate
    funding_rate: float
    funding_rate_pct: float
    next_funding_time: datetime
    hours_until_funding: float

    # Strategy
    strategy_type: str  # "LONG_SPOT_SHORT_FUTURES" or "LONG_FUTURES"
    direction: str  # Human-readable description

    # Returns
    basis_return_pct: float  # Expected return from basis convergence
    funding_apy: float  # Annualized funding rate return
    total_expected_return_pct: float  # Basis + Funding
    net_return_after_fees_pct: float

    # Position sizing
    spot_quantity: float
    futures_quantity: float
    position_value_usd: float
    required_capital_usd: float

    # Risk metrics
    basis_risk_level: str  # BAJO, MODERADO, ALTO
    liquidation_price: Optional[float]
    max_loss_pct: float  # Maximum potential loss
    holding_period_days: int  # Recommended holding period

    # Scores
    opportunity_score: float  # 0-100
    sharpe_ratio: float
    recommendation: str  # BUY, HOLD, AVOID
    reason: str


class DeltaNeutralArbitrageService:
    """
    Servicio para detectar oportunidades de arbitraje delta-neutral entre Spot y Futures.
    """

    # Configuración
    MIN_BASIS_PCT = 0.2  # 0.2% mínimo de basis para considerar
    MAX_BASIS_PCT = 10.0  # 10% máximo (anomalía probable)
    MIN_TOTAL_RETURN = 1.0  # 1% retorno total mínimo
    DEFAULT_HOLDING_PERIOD_DAYS = 7  # Período de holding recomendado
    SPOT_FEE = 0.001  # 0.1% spot fee
    FUTURES_FEE = 0.0004  # 0.04% futures fee

    # Symbols to analyze
    SYMBOLS = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "MATICUSDT",
        "AVAXUSDT",
    ]

    def __init__(self) -> None:
        """Inicializar servicios."""
        self.spot_service = BinanceSpotService()
        self.futures_service = BinanceFuturesService()

    async def find_all_opportunities(
        self,
        min_total_return: float = MIN_TOTAL_RETURN,
        holding_period_days: int = DEFAULT_HOLDING_PERIOD_DAYS,
    ) -> List[DeltaNeutralOpportunity]:
        """
        Escanear todos los símbolos en busca de oportunidades delta-neutral.

        Args:
            min_total_return: Retorno total mínimo (%)
            holding_period_days: Período de holding esperado

        Returns:
            Lista de oportunidades ordenadas por total_expected_return
        """
        try:
            opportunities = []

            for symbol in self.SYMBOLS:
                opportunity = await self.analyze_opportunity(
                    symbol=symbol,
                    holding_period_days=holding_period_days,
                )

                if opportunity and opportunity.net_return_after_fees_pct >= min_total_return:
                    opportunities.append(opportunity)

            # Sort by net return (highest first)
            opportunities.sort(key=lambda x: x.net_return_after_fees_pct, reverse=True)

            logger.info(
                "Delta-neutral arbitrage scan completed",
                symbols_analyzed=len(self.SYMBOLS),
                opportunities_found=len(opportunities),
            )

            return opportunities

        except Exception as exc:  # noqa: BLE001
            logger.error("Error finding delta-neutral opportunities", error=str(exc))
            return []

    async def analyze_opportunity(
        self,
        symbol: str,
        holding_period_days: int = DEFAULT_HOLDING_PERIOD_DAYS,
        position_value_usd: float = 10000.0,
    ) -> Optional[DeltaNeutralOpportunity]:
        """
        Analizar una oportunidad específica de arbitraje delta-neutral.

        Args:
            symbol: Par de trading (e.g., BTCUSDT)
            holding_period_days: Período de holding esperado
            position_value_usd: Valor de la posición en USD

        Returns:
            DeltaNeutralOpportunity con análisis completo
        """
        try:
            # Get spot price
            spot_price = await self.spot_service.get_spot_price(symbol)
            if spot_price == 0:
                return None

            # Get futures data (mark price + funding rate)
            funding_data = await self.futures_service.get_funding_rate(symbol)
            if not funding_data:
                return None

            futures_price = funding_data["mark_price"]
            funding_rate = funding_data["funding_rate"]
            next_funding_time = funding_data["funding_time"]

            if futures_price == 0:
                return None

            # Calculate basis
            basis = spot_price - futures_price
            basis_pct = (basis / spot_price) * 100

            # Skip if basis too small or too large (anomaly)
            if abs(basis_pct) < self.MIN_BASIS_PCT:
                return None

            if abs(basis_pct) > self.MAX_BASIS_PCT:
                logger.warning("Basis too large, possible data error", symbol=symbol, basis_pct=basis_pct)
                return None

            # Determine strategy based on basis and funding rate
            if futures_price > spot_price:
                # Contango: Futures trading at premium
                # Strategy: Buy Spot + Short Futures
                strategy_type = "LONG_SPOT_SHORT_FUTURES"
                direction = "Buy Spot + Short Futures (capture basis convergence + funding)"

                # Basis return: Profit when futures converge down to spot
                basis_return_pct = basis_pct

                # Funding return: Receive funding (if positive)
                # If funding is negative, we pay
                funding_sign = 1 if funding_rate > 0 else -1

            else:
                # Backwardation: Spot trading at premium
                # Strategy: Long Futures (+ optionally short spot if possible)
                strategy_type = "LONG_FUTURES"
                direction = "Long Futures (capture basis convergence)"

                # Basis return: Profit when futures converge up to spot
                basis_return_pct = -basis_pct

                # Funding return: Pay funding if positive, receive if negative
                funding_sign = -1 if funding_rate > 0 else 1

            # Calculate funding APY
            funding_apy = await self.futures_service.calculate_funding_rate_apy(
                funding_rate=abs(funding_rate),
                periods_per_day=3,
            )

            # Adjust funding APY based on whether we pay or receive
            funding_apy = funding_apy * funding_sign

            # Calculate expected returns
            # Basis return: Expected over holding period (assume 50% convergence)
            expected_basis_convergence = 0.5  # 50% convergence assumption
            basis_return_over_period = basis_return_pct * expected_basis_convergence

            # Funding return: Over holding period
            funding_return_over_period = (funding_apy / 365) * holding_period_days

            # Total expected return
            total_expected_return_pct = basis_return_over_period + funding_return_over_period

            # Calculate fees
            if strategy_type == "LONG_SPOT_SHORT_FUTURES":
                # Entry: Buy spot + Short futures
                entry_fees = (self.SPOT_FEE + self.FUTURES_FEE) * position_value_usd
                # Exit: Sell spot + Close futures short
                exit_fees = (self.SPOT_FEE + self.FUTURES_FEE) * position_value_usd
            else:
                # Entry: Long futures only
                entry_fees = self.FUTURES_FEE * position_value_usd
                # Exit: Close futures long
                exit_fees = self.FUTURES_FEE * position_value_usd

            total_fees = entry_fees + exit_fees
            fees_pct = (total_fees / position_value_usd) * 100

            # Net return after fees
            net_return_after_fees_pct = total_expected_return_pct - fees_pct

            # Calculate position sizes
            if strategy_type == "LONG_SPOT_SHORT_FUTURES":
                # Need capital for both spot purchase and futures margin
                spot_quantity = position_value_usd / spot_price
                futures_quantity = position_value_usd / futures_price
                required_capital_usd = position_value_usd + (position_value_usd * 0.1)  # 10% futures margin
            else:
                # Only need futures margin
                spot_quantity = 0
                futures_quantity = position_value_usd / futures_price
                required_capital_usd = position_value_usd * 0.1  # 10% futures margin

            # Calculate basis risk level
            basis_risk_level = await self._assess_basis_risk(
                basis_pct=abs(basis_pct),
                funding_rate=funding_rate,
            )

            # Calculate liquidation price (for futures position)
            liquidation_price = None
            if strategy_type == "LONG_SPOT_SHORT_FUTURES":
                # Short futures position with 10x leverage
                leverage = 10
                # Liquidation = entry * (1 + 1/leverage - fees)
                liquidation_price = futures_price * (1 + (1 / leverage) - 0.01)
            else:
                # Long futures position
                leverage = 10
                # Liquidation = entry * (1 - 1/leverage + fees)
                liquidation_price = futures_price * (1 - (1 / leverage) + 0.01)

            # Calculate max loss percentage
            # Max loss = fees + potential adverse basis movement
            max_loss_pct = fees_pct + (abs(basis_pct) * 0.5)  # 50% adverse movement

            # Calculate opportunity score
            opportunity_score = await self._calculate_opportunity_score(
                total_return_pct=net_return_after_fees_pct,
                basis_pct=abs(basis_pct),
                funding_apy=abs(funding_apy),
                basis_risk=basis_risk_level,
            )

            # Calculate Sharpe ratio (simplified)
            # Assume volatility is proportional to basis volatility
            assumed_volatility = abs(basis_pct) * 0.3  # 30% of basis as volatility estimate
            if assumed_volatility > 0:
                sharpe_ratio = net_return_after_fees_pct / assumed_volatility
            else:
                sharpe_ratio = 0

            # Generate recommendation
            recommendation = await self._generate_recommendation(
                net_return_pct=net_return_after_fees_pct,
                basis_risk=basis_risk_level,
                opportunity_score=opportunity_score,
            )

            # Generate reason
            reason = await self._generate_reason(
                strategy_type=strategy_type,
                basis_return=basis_return_over_period,
                funding_return=funding_return_over_period,
                net_return=net_return_after_fees_pct,
            )

            # Calculate hours until funding
            now_ts = datetime.now().timestamp() * 1000
            hours_until_funding = (next_funding_time - now_ts) / (1000 * 3600)

            # Extract asset name
            asset = symbol.replace("USDT", "")

            return DeltaNeutralOpportunity(
                symbol=symbol,
                asset=asset,
                spot_price=spot_price,
                futures_price=futures_price,
                basis=basis,
                basis_pct=basis_pct,
                funding_rate=funding_rate,
                funding_rate_pct=funding_rate * 100,
                next_funding_time=datetime.fromtimestamp(next_funding_time / 1000),
                hours_until_funding=hours_until_funding,
                strategy_type=strategy_type,
                direction=direction,
                basis_return_pct=basis_return_over_period,
                funding_apy=funding_apy,
                total_expected_return_pct=total_expected_return_pct,
                net_return_after_fees_pct=net_return_after_fees_pct,
                spot_quantity=spot_quantity,
                futures_quantity=futures_quantity,
                position_value_usd=position_value_usd,
                required_capital_usd=required_capital_usd,
                basis_risk_level=basis_risk_level,
                liquidation_price=liquidation_price,
                max_loss_pct=max_loss_pct,
                holding_period_days=holding_period_days,
                opportunity_score=opportunity_score,
                sharpe_ratio=sharpe_ratio,
                recommendation=recommendation,
                reason=reason,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing delta-neutral opportunity", symbol=symbol, error=str(exc))
            return None

    async def get_best_opportunity(
        self,
        min_total_return: float = MIN_TOTAL_RETURN,
    ) -> Optional[DeltaNeutralOpportunity]:
        """
        Obtener la mejor oportunidad delta-neutral.

        Returns:
            La oportunidad con mayor net_return_after_fees_pct
        """
        opportunities = await self.find_all_opportunities(min_total_return=min_total_return)

        if opportunities:
            return opportunities[0]  # Already sorted

        return None

    async def calculate_optimal_holding_period(
        self,
        symbol: str,
        target_return_pct: float = 5.0,
    ) -> Dict[str, any]:
        """
        Calcular el período de holding óptimo para alcanzar un retorno objetivo.

        Args:
            symbol: Par de trading
            target_return_pct: Retorno objetivo (%)

        Returns:
            Información sobre período óptimo y retornos proyectados
        """
        try:
            # Analyze opportunity with different holding periods
            results = []

            for days in [1, 3, 7, 14, 30, 60, 90]:
                opportunity = await self.analyze_opportunity(
                    symbol=symbol,
                    holding_period_days=days,
                )

                if opportunity:
                    results.append({
                        "days": days,
                        "net_return_pct": opportunity.net_return_after_fees_pct,
                        "total_return_pct": opportunity.total_expected_return_pct,
                        "basis_return_pct": opportunity.basis_return_pct,
                        "funding_contribution_pct": opportunity.funding_apy * (days / 365),
                    })

            if not results:
                return {}

            # Find optimal period (first to exceed target or highest return)
            optimal = None
            for r in results:
                if r["net_return_pct"] >= target_return_pct:
                    optimal = r
                    break

            if not optimal:
                # Use highest return if target not reached
                optimal = max(results, key=lambda x: x["net_return_pct"])

            return {
                "symbol": symbol,
                "target_return_pct": target_return_pct,
                "optimal_holding_days": optimal["days"],
                "expected_net_return_pct": optimal["net_return_pct"],
                "all_scenarios": results,
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Error calculating optimal holding period", error=str(exc))
            return {}

    # ==================== HELPER METHODS ====================

    async def _assess_basis_risk(
        self,
        basis_pct: float,
        funding_rate: float,
    ) -> str:
        """
        Evaluar nivel de riesgo del basis.

        Factores:
        - Magnitud del basis: Mayor basis = mayor riesgo de no-convergencia
        - Funding rate: Si contradice el basis, mayor riesgo
        """
        risk_points = 0

        # Basis magnitude risk
        if abs(basis_pct) > 5:
            risk_points += 3
        elif abs(basis_pct) > 2:
            risk_points += 2
        elif abs(basis_pct) > 1:
            risk_points += 1

        # Funding rate alignment risk
        # If basis and funding don't align, higher risk
        if basis_pct > 0 and funding_rate < 0:
            # Contango but negative funding (unusual)
            risk_points += 2
        elif basis_pct < 0 and funding_rate > 0:
            # Backwardation but positive funding (unusual)
            risk_points += 2

        if risk_points >= 5:
            return "ALTO"
        elif risk_points >= 3:
            return "MODERADO"
        else:
            return "BAJO"

    async def _calculate_opportunity_score(
        self,
        total_return_pct: float,
        basis_pct: float,
        funding_apy: float,
        basis_risk: str,
    ) -> float:
        """
        Calcular opportunity score (0-100).

        Factores:
        - Total return: Mayor es mejor (50% weight)
        - Basis magnitude: Moderado es mejor (20% weight)
        - Funding APY: Mayor es mejor (20% weight)
        - Risk level: Menor es mejor (10% weight)
        """
        # Return score (0-50)
        # 5%+ return = 50 points, 1% = 10 points
        return_score = min((total_return_pct / 5) * 50, 50)

        # Basis score (0-20)
        # Optimal basis: 1-3% (sweet spot)
        if 1 <= abs(basis_pct) <= 3:
            basis_score = 20
        elif abs(basis_pct) < 1:
            basis_score = 10
        else:
            basis_score = max(20 - (abs(basis_pct) - 3) * 2, 0)

        # Funding score (0-20)
        # 20%+ APY = 20 points
        funding_score = min((abs(funding_apy) / 20) * 20, 20)

        # Risk score (0-10)
        if basis_risk == "BAJO":
            risk_score = 10
        elif basis_risk == "MODERADO":
            risk_score = 5
        else:
            risk_score = 0

        total_score = return_score + basis_score + funding_score + risk_score

        return round(total_score, 2)

    async def _generate_recommendation(
        self,
        net_return_pct: float,
        basis_risk: str,
        opportunity_score: float,
    ) -> str:
        """Generar recomendación."""
        if net_return_pct < 1:
            return "AVOID"

        if basis_risk == "ALTO":
            return "AVOID"

        if opportunity_score >= 70:
            return "BUY"

        if opportunity_score >= 50:
            return "HOLD"

        return "AVOID"

    async def _generate_reason(
        self,
        strategy_type: str,
        basis_return: float,
        funding_return: float,
        net_return: float,
    ) -> str:
        """Generar razón."""
        if strategy_type == "LONG_SPOT_SHORT_FUTURES":
            return (
                f"Contango: Futures trading at premium. "
                f"Expected {basis_return:.2f}% from basis convergence + "
                f"{funding_return:.2f}% from funding = {net_return:.2f}% net return."
            )
        else:
            return (
                f"Backwardation: Spot at premium. "
                f"Expected {basis_return:.2f}% from basis convergence + "
                f"{funding_return:.2f}% from funding = {net_return:.2f}% net return."
            )
