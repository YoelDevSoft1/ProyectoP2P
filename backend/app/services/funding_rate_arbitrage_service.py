"""
Servicio de Funding Rate Arbitrage.

Estrategia delta-neutral que aprovecha los funding rates de perpetual futures
para generar ganancias sin exposición direccional al precio.

Estrategia:
- Funding Rate Positivo (longs pagan a shorts):
  → Comprar en Spot + Short en Futures = Recibir funding

- Funding Rate Negativo (shorts pagan a longs):
  → Long en Futures = Recibir funding (sin necesidad de spot)

Esta es una estrategia de bajo riesgo con retornos consistentes.
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
class FundingRateOpportunity:
    """Oportunidad de arbitraje de funding rate."""

    symbol: str
    funding_rate: float  # Rate por período (ej: 0.0001 = 0.01%)
    funding_rate_pct: float  # Rate en porcentaje
    apy: float  # Anualizado
    next_funding_time: datetime
    hours_until_funding: float

    # Precios
    spot_price: float
    futures_price: float
    basis: float  # Diferencia spot - futures
    basis_pct: float  # Basis en porcentaje

    # Tipo de estrategia
    strategy_type: str  # "LONG_FUNDING" o "SHORT_FUNDING"
    direction: str  # Descripción de la estrategia

    # Profit estimation
    expected_profit_per_period: float  # $ por período
    expected_daily_profit: float  # $ por día
    net_apy: float  # APY después de fees

    # Risk metrics
    liquidation_price: Optional[float]
    required_margin: float
    leverage_used: int

    # Ratings
    opportunity_score: float  # 0-100
    risk_level: str  # BAJO, MODERADO, ALTO
    recommendation: str  # BUY, HOLD, AVOID


class FundingRateArbitrageService:
    """
    Servicio para detectar y analizar oportunidades de funding rate arbitrage.
    """

    # Configuración
    MIN_FUNDING_RATE_PCT = 0.01  # 0.01% mínimo para considerar oportunidad
    MIN_APY = 5.0  # 5% APY mínimo
    MAX_LEVERAGE = 3  # Leverage máximo recomendado para safety
    SPOT_FEE = 0.001  # 0.1% spot trading fee
    FUTURES_FEE = 0.0004  # 0.04% futures trading fee (maker)
    FUNDING_PERIODS_PER_DAY = 3  # Binance cobra funding 3 veces al día

    def __init__(self) -> None:
        """Inicializar servicios de Binance."""
        self.spot_service = BinanceSpotService()
        self.futures_service = BinanceFuturesService()

    async def find_all_opportunities(
        self,
        min_apy: float = MIN_APY,
        max_leverage: int = MAX_LEVERAGE,
    ) -> List[FundingRateOpportunity]:
        """
        Escanear todos los perpetuals en busca de oportunidades de funding rate arbitrage.

        Args:
            min_apy: APY mínimo para considerar oportunidad
            max_leverage: Leverage máximo a usar

        Returns:
            Lista de oportunidades ordenadas por net_apy descendente
        """
        try:
            # Get all funding rates
            all_funding_rates = await self.futures_service.get_all_funding_rates()

            if not all_funding_rates:
                logger.warning("No funding rates available")
                return []

            opportunities = []

            # Analyze each perpetual
            for funding_data in all_funding_rates:
                symbol = funding_data["symbol"]
                funding_rate = funding_data["funding_rate"]

                # Skip if funding rate too small
                if abs(funding_rate) * 100 < self.MIN_FUNDING_RATE_PCT:
                    continue

                # Analyze opportunity
                opportunity = await self.analyze_opportunity(
                    symbol=symbol,
                    max_leverage=max_leverage,
                )

                if opportunity and opportunity.net_apy >= min_apy:
                    opportunities.append(opportunity)

            # Sort by net APY (highest first)
            opportunities.sort(key=lambda x: x.net_apy, reverse=True)

            logger.info(
                "Funding rate arbitrage scan completed",
                total_scanned=len(all_funding_rates),
                opportunities_found=len(opportunities),
            )

            return opportunities

        except Exception as exc:  # noqa: BLE001
            logger.error("Error finding funding rate opportunities", error=str(exc))
            return []

    async def analyze_opportunity(
        self,
        symbol: str,
        max_leverage: int = MAX_LEVERAGE,
        position_size_usd: float = 10000.0,
    ) -> Optional[FundingRateOpportunity]:
        """
        Analizar una oportunidad específica de funding rate arbitrage.

        Args:
            symbol: Par de trading (ej: BTCUSDT)
            max_leverage: Leverage máximo
            position_size_usd: Tamaño de posición en USD

        Returns:
            FundingRateOpportunity con análisis completo
        """
        try:
            # Get funding rate data
            funding_data = await self.futures_service.get_funding_rate(symbol)
            if not funding_data:
                return None

            funding_rate = funding_data["funding_rate"]
            next_funding_time = funding_data["funding_time"]

            # Skip if funding rate too small
            if abs(funding_rate) * 100 < self.MIN_FUNDING_RATE_PCT:
                return None

            # Get prices
            spot_price = await self.spot_service.get_spot_price(symbol)
            futures_price = funding_data["mark_price"]

            if spot_price == 0 or futures_price == 0:
                return None

            # Calculate basis
            basis = spot_price - futures_price
            basis_pct = (basis / spot_price) * 100

            # Determine strategy type
            if funding_rate > 0:
                # Positive funding: Longs pay shorts
                # Strategy: Buy Spot + Short Futures
                strategy_type = "SHORT_FUNDING"
                direction = "Buy Spot + Short Futures (collect funding from longs)"
            else:
                # Negative funding: Shorts pay longs
                # Strategy: Long Futures only (no spot needed)
                strategy_type = "LONG_FUNDING"
                direction = "Long Futures (collect funding from shorts)"

            # Calculate APY
            apy = await self._calculate_apy(funding_rate)

            # Calculate expected profits
            expected_profit_per_period = abs(funding_rate) * position_size_usd
            expected_daily_profit = expected_profit_per_period * self.FUNDING_PERIODS_PER_DAY

            # Calculate fees (entry + exit)
            if strategy_type == "SHORT_FUNDING":
                # Need to buy spot and short futures
                entry_fees = (self.SPOT_FEE + self.FUTURES_FEE) * position_size_usd
                exit_fees = (self.SPOT_FEE + self.FUTURES_FEE) * position_size_usd
                total_fees = entry_fees + exit_fees
            else:
                # Only need to long futures
                entry_fees = self.FUTURES_FEE * position_size_usd
                exit_fees = self.FUTURES_FEE * position_size_usd
                total_fees = entry_fees + exit_fees

            # Calculate break-even time (days to recover fees)
            if expected_daily_profit > 0:
                days_to_breakeven = total_fees / expected_daily_profit
            else:
                days_to_breakeven = float('inf')

            # Calculate net APY after fees
            annual_fees = total_fees * (365 / 30)  # Assume monthly rebalancing
            annual_profit = expected_daily_profit * 365
            net_annual_profit = annual_profit - annual_fees
            net_apy = (net_annual_profit / position_size_usd) * 100

            # Calculate liquidation price (if using leverage)
            leverage_used = 1  # Default to 1x (no leverage for spot+futures)
            liquidation_price = None
            required_margin = position_size_usd

            if strategy_type == "LONG_FUNDING":
                # For long futures only, can use leverage
                leverage_used = min(max_leverage, 3)  # Conservative leverage
                required_margin = position_size_usd / leverage_used

                # Liquidation price for long position
                # Liq price = Entry price * (1 - 1/leverage + fees)
                liquidation_price = futures_price * (1 - (1 / leverage_used) + 0.01)

            # Calculate opportunity score (0-100)
            opportunity_score = await self._calculate_opportunity_score(
                apy=net_apy,
                funding_rate=abs(funding_rate),
                basis_pct=abs(basis_pct),
                days_to_breakeven=days_to_breakeven,
            )

            # Assess risk level
            risk_level = await self._assess_risk_level(
                leverage=leverage_used,
                basis_pct=abs(basis_pct),
                days_to_breakeven=days_to_breakeven,
            )

            # Generate recommendation
            recommendation = await self._generate_recommendation(
                net_apy=net_apy,
                opportunity_score=opportunity_score,
                risk_level=risk_level,
                days_to_breakeven=days_to_breakeven,
            )

            # Calculate hours until next funding
            now_ts = datetime.now().timestamp() * 1000
            hours_until_funding = (next_funding_time - now_ts) / (1000 * 3600)

            return FundingRateOpportunity(
                symbol=symbol,
                funding_rate=funding_rate,
                funding_rate_pct=funding_rate * 100,
                apy=apy,
                next_funding_time=datetime.fromtimestamp(next_funding_time / 1000),
                hours_until_funding=hours_until_funding,
                spot_price=spot_price,
                futures_price=futures_price,
                basis=basis,
                basis_pct=basis_pct,
                strategy_type=strategy_type,
                direction=direction,
                expected_profit_per_period=expected_profit_per_period,
                expected_daily_profit=expected_daily_profit,
                net_apy=net_apy,
                liquidation_price=liquidation_price,
                required_margin=required_margin,
                leverage_used=leverage_used,
                opportunity_score=opportunity_score,
                risk_level=risk_level,
                recommendation=recommendation,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing funding rate opportunity", symbol=symbol, error=str(exc))
            return None

    async def get_best_opportunity(
        self,
        min_apy: float = MIN_APY,
        max_leverage: int = MAX_LEVERAGE,
    ) -> Optional[FundingRateOpportunity]:
        """
        Obtener la mejor oportunidad de funding rate arbitrage.

        Returns:
            La oportunidad con mayor net_apy
        """
        opportunities = await self.find_all_opportunities(
            min_apy=min_apy,
            max_leverage=max_leverage,
        )

        if opportunities:
            return opportunities[0]  # Already sorted by net_apy

        return None

    async def analyze_historical_performance(
        self,
        symbol: str,
        days: int = 30,
    ) -> Dict[str, any]:
        """
        Analizar el rendimiento histórico del funding rate de un símbolo.

        Args:
            symbol: Par de trading
            days: Días de historial a analizar

        Returns:
            Estadísticas históricas y proyecciones
        """
        try:
            # Get historical funding rates (8 periods per day)
            periods = days * self.FUNDING_PERIODS_PER_DAY
            history = await self.futures_service.get_historical_funding_rates(
                symbol=symbol,
                limit=min(periods, 1000),  # API limit
            )

            if not history:
                return {}

            # Calculate statistics
            rates = [h["funding_rate"] for h in history]

            avg_funding_rate = sum(rates) / len(rates)
            max_funding_rate = max(rates)
            min_funding_rate = min(rates)

            # Calculate positive vs negative periods
            positive_periods = sum(1 for r in rates if r > 0)
            negative_periods = sum(1 for r in rates if r < 0)

            positive_pct = (positive_periods / len(rates)) * 100
            negative_pct = (negative_periods / len(rates)) * 100

            # Calculate average APY
            avg_apy = await self._calculate_apy(avg_funding_rate)

            # Calculate volatility (standard deviation)
            mean = avg_funding_rate
            variance = sum((r - mean) ** 2 for r in rates) / len(rates)
            std_dev = variance ** 0.5

            # Annualized volatility
            annualized_volatility = std_dev * (365 ** 0.5) * 100

            # Calculate Sharpe ratio (assuming 0 risk-free rate)
            if std_dev > 0:
                sharpe_ratio = (avg_funding_rate * 365 * self.FUNDING_PERIODS_PER_DAY) / std_dev
            else:
                sharpe_ratio = 0

            return {
                "symbol": symbol,
                "analysis_period_days": days,
                "data_points": len(history),
                "avg_funding_rate": avg_funding_rate,
                "avg_funding_rate_pct": avg_funding_rate * 100,
                "max_funding_rate": max_funding_rate,
                "min_funding_rate": min_funding_rate,
                "positive_periods": positive_periods,
                "negative_periods": negative_periods,
                "positive_pct": positive_pct,
                "negative_pct": negative_pct,
                "avg_apy": avg_apy,
                "volatility": std_dev,
                "annualized_volatility_pct": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "consistency_score": await self._calculate_consistency_score(rates),
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing historical performance", symbol=symbol, error=str(exc))
            return {}

    # ==================== HELPER METHODS ====================

    async def _calculate_apy(self, funding_rate: float) -> float:
        """Calcular APY basado en funding rate."""
        return await self.futures_service.calculate_funding_rate_apy(
            funding_rate=funding_rate,
            periods_per_day=self.FUNDING_PERIODS_PER_DAY,
        )

    async def _calculate_opportunity_score(
        self,
        apy: float,
        funding_rate: float,
        basis_pct: float,
        days_to_breakeven: float,
    ) -> float:
        """
        Calcular score de oportunidad (0-100).

        Factores:
        - APY: Mayor es mejor (50% weight)
        - Funding rate absoluto: Mayor es mejor (20% weight)
        - Basis risk: Menor es mejor (15% weight)
        - Tiempo a breakeven: Menor es mejor (15% weight)
        """
        # APY score (0-50 points)
        # 20%+ APY = 50 points, 5% = 10 points
        apy_score = min((apy / 20) * 50, 50)

        # Funding rate score (0-20 points)
        # 0.1%+ per period = 20 points
        funding_score = min((abs(funding_rate) * 100 / 0.1) * 20, 20)

        # Basis risk score (0-15 points)
        # Lower basis = better (less convergence risk)
        # 0% basis = 15 points, 5%+ basis = 0 points
        basis_score = max(15 - (abs(basis_pct) / 5) * 15, 0)

        # Breakeven score (0-15 points)
        # 1 day breakeven = 15 points, 30+ days = 0 points
        if days_to_breakeven < float('inf'):
            breakeven_score = max(15 - (days_to_breakeven / 30) * 15, 0)
        else:
            breakeven_score = 0

        total_score = apy_score + funding_score + basis_score + breakeven_score

        return round(total_score, 2)

    async def _assess_risk_level(
        self,
        leverage: int,
        basis_pct: float,
        days_to_breakeven: float,
    ) -> str:
        """Evaluar nivel de riesgo."""
        risk_points = 0

        # Leverage risk
        if leverage > 5:
            risk_points += 3
        elif leverage > 3:
            risk_points += 2
        elif leverage > 1:
            risk_points += 1

        # Basis risk
        if abs(basis_pct) > 5:
            risk_points += 3
        elif abs(basis_pct) > 2:
            risk_points += 2
        elif abs(basis_pct) > 1:
            risk_points += 1

        # Breakeven risk
        if days_to_breakeven > 30:
            risk_points += 3
        elif days_to_breakeven > 14:
            risk_points += 2
        elif days_to_breakeven > 7:
            risk_points += 1

        if risk_points >= 7:
            return "ALTO"
        elif risk_points >= 4:
            return "MODERADO"
        else:
            return "BAJO"

    async def _generate_recommendation(
        self,
        net_apy: float,
        opportunity_score: float,
        risk_level: str,
        days_to_breakeven: float,
    ) -> str:
        """Generar recomendación de trading."""
        if net_apy < 5:
            return "AVOID"

        if risk_level == "ALTO":
            return "AVOID"

        if days_to_breakeven > 30:
            return "AVOID"

        if opportunity_score >= 70:
            return "BUY"

        if opportunity_score >= 50:
            return "HOLD"

        return "AVOID"

    async def _calculate_consistency_score(self, rates: List[float]) -> float:
        """
        Calcular score de consistencia (0-100).

        Mide qué tan consistentemente el funding rate se mantiene en una dirección.
        Mayor consistencia = menos volatilidad = menor riesgo.
        """
        if not rates:
            return 0

        # Check direction consistency
        positive_count = sum(1 for r in rates if r > 0)
        negative_count = sum(1 for r in rates if r < 0)

        # Percentage in dominant direction
        dominant_pct = max(positive_count, negative_count) / len(rates)

        # Volatility penalty
        mean = sum(rates) / len(rates)
        variance = sum((r - mean) ** 2 for r in rates) / len(rates)
        std_dev = variance ** 0.5

        # Coefficient of variation (CV)
        if abs(mean) > 0:
            cv = abs(std_dev / mean)
        else:
            cv = float('inf')

        # Score calculation
        consistency_score = dominant_pct * 100

        # Reduce score if too volatile
        if cv > 1:
            consistency_score *= 0.5
        elif cv > 0.5:
            consistency_score *= 0.75

        return round(consistency_score, 2)
