"""
Servicio de Statistical Arbitrage (Pairs Trading).

Estrategia cuantitativa que aprovecha las relaciones estadísticas entre pares de activos
para generar ganancias mediante mean reversion.

Estrategia:
- Identificar pares de activos cointegrados (relación de largo plazo)
- Calcular spread normalizado entre los pares
- Cuando el spread se desvía significativamente de la media:
  → Short el activo sobrevalorado + Long el infravalorado
- Cuando el spread revierte a la media → Cerrar posiciones

Esta es una estrategia market-neutral de bajo riesgo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import structlog

from app.core.config import settings
from app.services.binance_spot_service import BinanceSpotService

logger = structlog.get_logger()

# Try to import statsmodels (for cointegration test)
try:
    from statsmodels.tsa.stattools import coint

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logger.warning("statsmodels not installed. Cointegration tests disabled. Install with: pip install statsmodels")


@dataclass
class PairSignal:
    """Señal de trading para un par de activos."""

    pair_name: str
    asset_1: str  # First asset (e.g., BTC)
    asset_2: str  # Second asset (e.g., ETH)

    # Prices
    price_1: float
    price_2: float

    # Spread analysis
    current_spread: float
    mean_spread: float
    std_spread: float
    z_score: float  # Z-score del spread

    # Correlation & cointegration
    correlation: float
    is_cointegrated: bool
    cointegration_pvalue: float

    # Trading signal
    signal_type: str  # "LONG_SPREAD", "SHORT_SPREAD", "NEUTRAL"
    confidence: float  # 0-100
    entry_threshold: float  # Z-score threshold used

    # Position sizing
    asset_1_quantity: float
    asset_2_quantity: float
    hedge_ratio: float  # Ratio for hedging

    # Expected profit
    expected_return_pct: float
    expected_profit_usd: float

    # Risk metrics
    risk_level: str  # BAJO, MODERADO, ALTO
    max_spread_deviation: float
    lookback_days: int

    # Recommendation
    recommendation: str  # BUY, HOLD, AVOID
    reason: str


@dataclass
class PairStatistics:
    """Estadísticas históricas de un par."""

    pair_name: str
    correlation: float
    cointegration_pvalue: float
    is_cointegrated: bool
    mean_spread: float
    std_spread: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    avg_holding_period_hours: float


class StatisticalArbitrageService:
    """
    Servicio para detectar oportunidades de statistical arbitrage (pairs trading).
    """

    # Configuración
    DEFAULT_LOOKBACK_DAYS = 30
    MIN_CORRELATION = 0.7  # Correlación mínima para considerar par
    MAX_COINTEGRATION_PVALUE = 0.05  # p-value máximo para cointegración (95% confianza)
    ENTRY_Z_SCORE = 2.0  # Z-score para entrada (2 desviaciones estándar)
    EXIT_Z_SCORE = 0.5  # Z-score para salida
    MIN_EXPECTED_RETURN = 0.5  # 0.5% retorno mínimo esperado

    # Pares de crypto populares para analizar
    CRYPTO_PAIRS = [
        ("BTCUSDT", "ETHUSDT"),  # BTC vs ETH
        ("BTCUSDT", "BNBUSDT"),  # BTC vs BNB
        ("ETHUSDT", "BNBUSDT"),  # ETH vs BNB
        ("BTCUSDT", "SOLUSDT"),  # BTC vs SOL
        ("ETHUSDT", "SOLUSDT"),  # ETH vs SOL
        ("BTCUSDT", "ADAUSDT"),  # BTC vs ADA
        ("ETHUSDT", "MATICUSDT"),  # ETH vs MATIC
        ("BNBUSDT", "SOLUSDT"),  # BNB vs SOL
    ]

    def __init__(self) -> None:
        """Inicializar servicio de Binance."""
        self.spot_service = BinanceSpotService()

    async def find_all_opportunities(
        self,
        min_z_score: float = ENTRY_Z_SCORE,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[PairSignal]:
        """
        Escanear todos los pares en busca de oportunidades de statistical arbitrage.

        Args:
            min_z_score: Z-score mínimo para generar señal
            lookback_days: Días de historial para análisis

        Returns:
            Lista de señales ordenadas por confidence descendente
        """
        try:
            signals = []

            for symbol_1, symbol_2 in self.CRYPTO_PAIRS:
                signal = await self.analyze_pair(
                    symbol_1=symbol_1,
                    symbol_2=symbol_2,
                    lookback_days=lookback_days,
                    entry_z_score=min_z_score,
                )

                if signal and signal.signal_type != "NEUTRAL":
                    signals.append(signal)

            # Sort by confidence (highest first)
            signals.sort(key=lambda x: x.confidence, reverse=True)

            logger.info(
                "Statistical arbitrage scan completed",
                pairs_analyzed=len(self.CRYPTO_PAIRS),
                signals_found=len(signals),
            )

            return signals

        except Exception as exc:  # noqa: BLE001
            logger.error("Error finding statistical arbitrage opportunities", error=str(exc))
            return []

    async def analyze_pair(
        self,
        symbol_1: str,
        symbol_2: str,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        entry_z_score: float = ENTRY_Z_SCORE,
        position_size_usd: float = 10000.0,
    ) -> Optional[PairSignal]:
        """
        Analizar un par de activos para statistical arbitrage.

        Args:
            symbol_1: Primer símbolo (ej: BTCUSDT)
            symbol_2: Segundo símbolo (ej: ETHUSDT)
            lookback_days: Días de historial para análisis
            entry_z_score: Z-score threshold para entrada
            position_size_usd: Tamaño de posición en USD

        Returns:
            PairSignal con análisis completo
        """
        try:
            # Get historical prices
            prices_1 = await self._get_historical_prices(symbol_1, lookback_days)
            prices_2 = await self._get_historical_prices(symbol_2, lookback_days)

            if not prices_1 or not prices_2 or len(prices_1) < 10 or len(prices_2) < 10:
                logger.warning("Insufficient price data", symbol_1=symbol_1, symbol_2=symbol_2)
                return None

            # Ensure same length
            min_len = min(len(prices_1), len(prices_2))
            prices_1 = prices_1[-min_len:]
            prices_2 = prices_2[-min_len:]

            # Convert to numpy arrays
            prices_1_arr = np.array(prices_1)
            prices_2_arr = np.array(prices_2)

            # Calculate correlation
            correlation = np.corrcoef(prices_1_arr, prices_2_arr)[0, 1]

            # Skip if correlation too low
            if abs(correlation) < self.MIN_CORRELATION:
                return None

            # Test for cointegration
            is_cointegrated = False
            cointegration_pvalue = 1.0

            if HAS_STATSMODELS:
                try:
                    _, pvalue, _ = coint(prices_1_arr, prices_2_arr)
                    cointegration_pvalue = pvalue
                    is_cointegrated = pvalue < self.MAX_COINTEGRATION_PVALUE
                except Exception as e:
                    logger.warning("Cointegration test failed", error=str(e))

            # Skip if not cointegrated (not a good pair for mean reversion)
            if HAS_STATSMODELS and not is_cointegrated:
                return None

            # Calculate hedge ratio (beta)
            # hedge_ratio = Cov(X, Y) / Var(X)
            covariance = np.cov(prices_1_arr, prices_2_arr)[0, 1]
            variance_1 = np.var(prices_1_arr)
            hedge_ratio = covariance / variance_1 if variance_1 > 0 else 1.0

            # Calculate spread: spread = price_2 - hedge_ratio * price_1
            spread = prices_2_arr - hedge_ratio * prices_1_arr

            # Calculate spread statistics
            mean_spread = np.mean(spread)
            std_spread = np.std(spread)

            # Current values
            current_price_1 = prices_1[-1]
            current_price_2 = prices_2[-1]
            current_spread = current_price_2 - hedge_ratio * current_price_1

            # Calculate z-score
            if std_spread > 0:
                z_score = (current_spread - mean_spread) / std_spread
            else:
                z_score = 0

            # Determine signal
            signal_type = "NEUTRAL"
            if z_score > entry_z_score:
                # Spread is high → SHORT the spread
                # SHORT asset_2, LONG asset_1
                signal_type = "SHORT_SPREAD"
            elif z_score < -entry_z_score:
                # Spread is low → LONG the spread
                # LONG asset_2, SHORT asset_1
                signal_type = "LONG_SPREAD"

            # Calculate position sizes
            # Split position_size between both assets based on hedge ratio
            asset_1_value = position_size_usd / (1 + abs(hedge_ratio))
            asset_2_value = position_size_usd - asset_1_value

            asset_1_quantity = asset_1_value / current_price_1
            asset_2_quantity = asset_2_value / current_price_2

            # Adjust quantities based on hedge ratio
            if signal_type == "SHORT_SPREAD":
                # SHORT asset_2, LONG asset_1
                asset_2_quantity = -asset_2_quantity
            elif signal_type == "LONG_SPREAD":
                # LONG asset_2, SHORT asset_1
                asset_1_quantity = -asset_1_quantity

            # Calculate expected return
            # Expected return when spread reverts to mean
            expected_spread_change = mean_spread - current_spread
            expected_return_pct = (abs(z_score) / 2) * (std_spread / current_price_2) * 100

            # Expected profit in USD
            expected_profit_usd = (expected_return_pct / 100) * position_size_usd

            # Calculate confidence
            confidence = await self._calculate_confidence(
                z_score=abs(z_score),
                correlation=abs(correlation),
                is_cointegrated=is_cointegrated,
                cointegration_pvalue=cointegration_pvalue,
            )

            # Assess risk level
            risk_level = await self._assess_risk_level(
                z_score=abs(z_score),
                correlation=abs(correlation),
                std_spread=std_spread,
            )

            # Generate recommendation
            recommendation = await self._generate_recommendation(
                signal_type=signal_type,
                confidence=confidence,
                risk_level=risk_level,
                expected_return_pct=expected_return_pct,
            )

            # Generate reason
            reason = await self._generate_reason(
                signal_type=signal_type,
                z_score=z_score,
                expected_return_pct=expected_return_pct,
            )

            # Extract asset names
            asset_1 = symbol_1.replace("USDT", "")
            asset_2 = symbol_2.replace("USDT", "")
            pair_name = f"{asset_1}/{asset_2}"

            # Calculate max spread deviation
            max_spread_deviation = np.max(np.abs(spread - mean_spread))

            return PairSignal(
                pair_name=pair_name,
                asset_1=asset_1,
                asset_2=asset_2,
                price_1=current_price_1,
                price_2=current_price_2,
                current_spread=current_spread,
                mean_spread=mean_spread,
                std_spread=std_spread,
                z_score=z_score,
                correlation=correlation,
                is_cointegrated=is_cointegrated,
                cointegration_pvalue=cointegration_pvalue,
                signal_type=signal_type,
                confidence=confidence,
                entry_threshold=entry_z_score,
                asset_1_quantity=asset_1_quantity,
                asset_2_quantity=asset_2_quantity,
                hedge_ratio=hedge_ratio,
                expected_return_pct=expected_return_pct,
                expected_profit_usd=expected_profit_usd,
                risk_level=risk_level,
                max_spread_deviation=max_spread_deviation,
                lookback_days=lookback_days,
                recommendation=recommendation,
                reason=reason,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing pair", symbol_1=symbol_1, symbol_2=symbol_2, error=str(exc))
            return None

    async def get_pair_statistics(
        self,
        symbol_1: str,
        symbol_2: str,
        lookback_days: int = 90,
    ) -> Optional[PairStatistics]:
        """
        Obtener estadísticas históricas de un par para backtesting.

        Args:
            symbol_1: Primer símbolo
            symbol_2: Segundo símbolo
            lookback_days: Días de historial

        Returns:
            PairStatistics con métricas históricas
        """
        try:
            # Get historical prices
            prices_1 = await self._get_historical_prices(symbol_1, lookback_days)
            prices_2 = await self._get_historical_prices(symbol_2, lookback_days)

            if not prices_1 or not prices_2 or len(prices_1) < 30:
                return None

            # Ensure same length
            min_len = min(len(prices_1), len(prices_2))
            prices_1 = prices_1[-min_len:]
            prices_2 = prices_2[-min_len:]

            prices_1_arr = np.array(prices_1)
            prices_2_arr = np.array(prices_2)

            # Calculate correlation
            correlation = np.corrcoef(prices_1_arr, prices_2_arr)[0, 1]

            # Test cointegration
            is_cointegrated = False
            cointegration_pvalue = 1.0

            if HAS_STATSMODELS:
                try:
                    _, pvalue, _ = coint(prices_1_arr, prices_2_arr)
                    cointegration_pvalue = pvalue
                    is_cointegrated = pvalue < self.MAX_COINTEGRATION_PVALUE
                except:
                    pass

            # Calculate hedge ratio
            covariance = np.cov(prices_1_arr, prices_2_arr)[0, 1]
            variance_1 = np.var(prices_1_arr)
            hedge_ratio = covariance / variance_1 if variance_1 > 0 else 1.0

            # Calculate spread
            spread = prices_2_arr - hedge_ratio * prices_1_arr
            mean_spread = np.mean(spread)
            std_spread = np.std(spread)

            # Simulate trading strategy
            returns = []
            positions = []  # Track open positions

            for i in range(len(spread)):
                if std_spread > 0:
                    z_score = (spread[i] - mean_spread) / std_spread
                else:
                    z_score = 0

                # Entry signals
                if z_score > self.ENTRY_Z_SCORE and len(positions) == 0:
                    # SHORT spread
                    positions.append({
                        "type": "SHORT_SPREAD",
                        "entry_z": z_score,
                        "entry_idx": i,
                    })
                elif z_score < -self.ENTRY_Z_SCORE and len(positions) == 0:
                    # LONG spread
                    positions.append({
                        "type": "LONG_SPREAD",
                        "entry_z": z_score,
                        "entry_idx": i,
                    })

                # Exit signals
                if len(positions) > 0:
                    pos = positions[0]
                    if abs(z_score) < self.EXIT_Z_SCORE:
                        # Close position
                        holding_period = i - pos["entry_idx"]
                        return_pct = abs(pos["entry_z"] - z_score)
                        returns.append(return_pct)
                        positions.pop(0)

            # Calculate statistics
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
                win_rate_pct = (sum(1 for r in returns if r > 0) / len(returns)) * 100
            else:
                sharpe_ratio = 0
                win_rate_pct = 0

            # Calculate max drawdown
            cumulative_returns = np.cumsum(returns) if returns else [0]
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / (running_max + 1e-10)
            max_drawdown_pct = abs(np.min(drawdown)) * 100

            # Average holding period
            if returns:
                avg_holding_period_hours = (lookback_days * 24) / len(returns)
            else:
                avg_holding_period_hours = 0

            asset_1 = symbol_1.replace("USDT", "")
            asset_2 = symbol_2.replace("USDT", "")
            pair_name = f"{asset_1}/{asset_2}"

            return PairStatistics(
                pair_name=pair_name,
                correlation=correlation,
                cointegration_pvalue=cointegration_pvalue,
                is_cointegrated=is_cointegrated,
                mean_spread=mean_spread,
                std_spread=std_spread,
                sharpe_ratio=sharpe_ratio,
                max_drawdown_pct=max_drawdown_pct,
                win_rate_pct=win_rate_pct,
                avg_holding_period_hours=avg_holding_period_hours,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Error calculating pair statistics", error=str(exc))
            return None

    # ==================== HELPER METHODS ====================

    async def _get_historical_prices(
        self,
        symbol: str,
        days: int,
    ) -> List[float]:
        """
        Obtener precios históricos (simulado).

        En producción, esto debería obtener datos reales de:
        - Database de price_history
        - Binance Klines API
        - External data provider

        Por ahora, retorna una lista vacía para indicar que se necesita implementar.
        """
        # TODO: Implementar obtención de precios históricos
        # Opciones:
        # 1. Desde database (PriceHistory model)
        # 2. Desde Binance Klines API
        # 3. Cache local

        try:
            # Simulate getting data from Binance (usar client real aquí)
            # For now return empty - need to implement with actual API
            logger.debug("Historical price fetch not implemented", symbol=symbol)
            return []

        except Exception as exc:
            logger.error("Error getting historical prices", symbol=symbol, error=str(exc))
            return []

    async def _calculate_confidence(
        self,
        z_score: float,
        correlation: float,
        is_cointegrated: bool,
        cointegration_pvalue: float,
    ) -> float:
        """
        Calcular confidence score (0-100).

        Factores:
        - Z-score: Mayor desviación = mayor confidence (40% weight)
        - Correlation: Mayor correlación = mayor confidence (30% weight)
        - Cointegration: Cointegrado = mayor confidence (30% weight)
        """
        # Z-score component (0-40 points)
        # Z >= 3 = 40 points, Z = 2 = 26 points, Z = 1 = 13 points
        z_score_component = min((z_score / 3) * 40, 40)

        # Correlation component (0-30 points)
        # Correlation = 1 = 30 points, 0.7 = 21 points
        correlation_component = ((correlation - 0.7) / 0.3) * 30
        correlation_component = max(0, min(correlation_component, 30))

        # Cointegration component (0-30 points)
        if is_cointegrated:
            # Lower p-value = higher confidence
            # p = 0.01 = 30 points, p = 0.05 = 15 points
            cointegration_component = (1 - (cointegration_pvalue / 0.05)) * 30
            cointegration_component = max(0, min(cointegration_component, 30))
        else:
            cointegration_component = 0

        total_confidence = z_score_component + correlation_component + cointegration_component

        return round(total_confidence, 2)

    async def _assess_risk_level(
        self,
        z_score: float,
        correlation: float,
        std_spread: float,
    ) -> str:
        """Evaluar nivel de riesgo."""
        risk_points = 0

        # Z-score risk (too extreme might not revert)
        if z_score > 4:
            risk_points += 2
        elif z_score > 3:
            risk_points += 1

        # Correlation risk
        if correlation < 0.8:
            risk_points += 2
        elif correlation < 0.9:
            risk_points += 1

        # Volatility risk (high spread volatility = higher risk)
        # This is relative - would need benchmarking
        if std_spread > 100:  # Arbitrary threshold
            risk_points += 2

        if risk_points >= 5:
            return "ALTO"
        elif risk_points >= 3:
            return "MODERADO"
        else:
            return "BAJO"

    async def _generate_recommendation(
        self,
        signal_type: str,
        confidence: float,
        risk_level: str,
        expected_return_pct: float,
    ) -> str:
        """Generar recomendación."""
        if signal_type == "NEUTRAL":
            return "HOLD"

        if risk_level == "ALTO":
            return "AVOID"

        if expected_return_pct < self.MIN_EXPECTED_RETURN:
            return "AVOID"

        if confidence >= 70:
            return "BUY"

        if confidence >= 50:
            return "HOLD"

        return "AVOID"

    async def _generate_reason(
        self,
        signal_type: str,
        z_score: float,
        expected_return_pct: float,
    ) -> str:
        """Generar razón de la recomendación."""
        if signal_type == "SHORT_SPREAD":
            return f"Spread {z_score:.2f} std devs above mean. Expected {expected_return_pct:.2f}% return on reversion."
        elif signal_type == "LONG_SPREAD":
            return f"Spread {abs(z_score):.2f} std devs below mean. Expected {expected_return_pct:.2f}% return on reversion."
        else:
            return "Spread within normal range. No signal."
