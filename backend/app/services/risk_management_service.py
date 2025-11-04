"""
Risk Management Service - Gestión profesional de riesgo

Métricas implementadas:
1. Value at Risk (VaR) - 95% y 99%
2. Sharpe Ratio
3. Sortino Ratio
4. Maximum Drawdown
5. Calmar Ratio
6. Win Rate y Profit Factor
7. Risk-Adjusted Return
8. Position Sizing óptimo (Kelly Criterion)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import statistics
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RiskManagementService:
    """Servicio profesional de gestión de riesgo para trading P2P"""

    def __init__(self):
        # Límites de riesgo configurables
        self.MAX_POSITION_SIZE_PCT = 10.0  # % del capital
        self.MAX_DAILY_LOSS_PCT = 5.0  # % pérdida máxima diaria
        self.MAX_DRAWDOWN_PCT = 15.0  # % drawdown máximo permitido
        self.MIN_SHARPE_RATIO = 1.0  # Sharpe mínimo aceptable

        # Risk-free rate (treasury bonds Colombia)
        self.RISK_FREE_RATE = 0.12  # 12% anual

    def calculate_var(
        self,
        returns: List[float],
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> Dict:
        """
        Calcula Value at Risk (VaR)

        VaR es la pérdida máxima esperada con un nivel de confianza dado

        Args:
            returns: Lista de retornos históricos (en %)
            confidence_level: Nivel de confianza (0.95 = 95%, 0.99 = 99%)
            time_horizon_days: Horizonte temporal en días
        """

        if not returns or len(returns) < 30:
            return {
                "success": False,
                "error": "Insufficient returns data (minimum 30 samples)"
            }

        try:
            returns_array = np.array(returns)

            # Método histórico: percentil
            var_percentile = np.percentile(returns_array, (1 - confidence_level) * 100)

            # Método paramétrico (asumiendo distribución normal)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)

            # Z-score para nivel de confianza
            z_scores = {0.95: 1.645, 0.99: 2.326}
            z_score = z_scores.get(confidence_level, 1.645)

            var_parametric = mean_return - (z_score * std_return)

            # Ajustar por horizonte temporal (si es > 1 día)
            if time_horizon_days > 1:
                var_percentile *= np.sqrt(time_horizon_days)
                var_parametric *= np.sqrt(time_horizon_days)

            # Conditional VaR (CVaR) - pérdida promedio cuando se excede el VaR
            cvar = np.mean(returns_array[returns_array <= var_percentile])

            return {
                "success": True,
                "confidence_level": confidence_level,
                "time_horizon_days": time_horizon_days,
                "var_historical": var_percentile,
                "var_parametric": var_parametric,
                "cvar": cvar,
                "interpretation": self._interpret_var(var_parametric, confidence_level),
                "samples": len(returns),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: Optional[float] = None
    ) -> Dict:
        """
        Calcula Sharpe Ratio - medida de retorno ajustado por riesgo

        Sharpe = (Retorno promedio - Tasa libre de riesgo) / Desviación estándar

        Un Sharpe > 1 es bueno, > 2 es muy bueno, > 3 es excelente
        """

        if not returns or len(returns) < 30:
            return {
                "success": False,
                "error": "Insufficient returns data (minimum 30 samples)"
            }

        try:
            returns_array = np.array(returns)

            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array, ddof=1)

            if std_return == 0:
                return {
                    "success": False,
                    "error": "Zero volatility - cannot calculate Sharpe Ratio"
                }

            rfr = risk_free_rate if risk_free_rate is not None else self.RISK_FREE_RATE
            # Convertir tasa anual a tasa por período
            rfr_period = rfr / 252  # Asumiendo 252 días de trading

            sharpe = (mean_return - rfr_period) / std_return

            # Anualizar el Sharpe Ratio (multiplicar por sqrt(252))
            sharpe_annualized = sharpe * np.sqrt(252)

            return {
                "success": True,
                "sharpe_ratio": sharpe,
                "sharpe_ratio_annualized": sharpe_annualized,
                "mean_return": mean_return,
                "std_return": std_return,
                "risk_free_rate": rfr,
                "rating": self._rate_sharpe_ratio(sharpe_annualized),
                "interpretation": self._interpret_sharpe_ratio(sharpe_annualized),
                "samples": len(returns),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Sharpe Ratio: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        risk_free_rate: Optional[float] = None,
        target_return: float = 0.0
    ) -> Dict:
        """
        Calcula Sortino Ratio - similar al Sharpe pero solo penaliza volatilidad negativa

        Sortino = (Retorno promedio - Target) / Desviación estándar de retornos negativos

        Mejor que Sharpe porque no penaliza volatilidad positiva
        """

        if not returns or len(returns) < 30:
            return {
                "success": False,
                "error": "Insufficient returns data (minimum 30 samples)"
            }

        try:
            returns_array = np.array(returns)

            mean_return = np.mean(returns_array)

            # Downside deviation: solo considera retornos por debajo del target
            downside_returns = returns_array[returns_array < target_return]

            if len(downside_returns) == 0:
                downside_deviation = 0.001  # Evitar división por cero
            else:
                downside_deviation = np.std(downside_returns, ddof=1)

            rfr = risk_free_rate if risk_free_rate is not None else self.RISK_FREE_RATE
            rfr_period = rfr / 252

            sortino = (mean_return - rfr_period) / downside_deviation

            # Anualizar
            sortino_annualized = sortino * np.sqrt(252)

            return {
                "success": True,
                "sortino_ratio": sortino,
                "sortino_ratio_annualized": sortino_annualized,
                "downside_deviation": downside_deviation,
                "downside_periods": len(downside_returns),
                "downside_percentage": len(downside_returns) / len(returns) * 100,
                "rating": self._rate_sortino_ratio(sortino_annualized),
                "interpretation": self._interpret_sortino_ratio(sortino_annualized),
                "samples": len(returns),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Sortino Ratio: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_maximum_drawdown(self, equity_curve: List[float]) -> Dict:
        """
        Calcula Maximum Drawdown - pérdida máxima desde un pico

        MDD mide la mayor caída de capital desde un máximo histórico

        Args:
            equity_curve: Lista de valores de capital a lo largo del tiempo
        """

        if not equity_curve or len(equity_curve) < 2:
            return {
                "success": False,
                "error": "Insufficient equity data (minimum 2 points)"
            }

        try:
            equity_array = np.array(equity_curve)

            # Calcular running maximum
            running_max = np.maximum.accumulate(equity_array)

            # Calcular drawdown en cada punto
            drawdown = (equity_array - running_max) / running_max * 100

            # Maximum drawdown
            mdd = np.min(drawdown)
            mdd_index = np.argmin(drawdown)

            # Encontrar el pico desde donde comenzó el MDD
            peak_index = np.argmax(equity_array[:mdd_index + 1])

            # Calcular duración del drawdown
            duration_days = mdd_index - peak_index

            # Calcular recovery (si hay)
            recovered = False
            recovery_days = None

            if mdd_index < len(equity_array) - 1:
                peak_value = equity_array[peak_index]
                for i in range(mdd_index + 1, len(equity_array)):
                    if equity_array[i] >= peak_value:
                        recovered = True
                        recovery_days = i - mdd_index
                        break

            # Drawdown actual (desde último pico)
            current_drawdown = drawdown[-1]

            return {
                "success": True,
                "maximum_drawdown_pct": mdd,
                "current_drawdown_pct": current_drawdown,
                "mdd_peak_index": int(peak_index),
                "mdd_valley_index": int(mdd_index),
                "duration_days": int(duration_days),
                "recovered": recovered,
                "recovery_days": recovery_days,
                "risk_level": self._classify_drawdown_risk(mdd),
                "interpretation": self._interpret_drawdown(mdd),
                "samples": len(equity_curve),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating maximum drawdown: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        maximum_drawdown_pct: float
    ) -> Dict:
        """
        Calcula Calmar Ratio - retorno anual / maximum drawdown

        Mide retorno ajustado por peor caída posible

        Calmar > 1 es bueno, > 2 es muy bueno, > 3 es excelente
        """

        try:
            if maximum_drawdown_pct >= 0:
                return {
                    "success": False,
                    "error": "Maximum drawdown must be negative"
                }

            # MDD es negativo, así que dividimos por valor absoluto
            calmar = annual_return / abs(maximum_drawdown_pct)

            return {
                "success": True,
                "calmar_ratio": calmar,
                "annual_return": annual_return,
                "maximum_drawdown": maximum_drawdown_pct,
                "rating": self._rate_calmar_ratio(calmar),
                "interpretation": self._interpret_calmar_ratio(calmar),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Calmar Ratio: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_trading_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calcula métricas de trading comprehensivas

        Args:
            trades: Lista de trades con 'profit', 'is_win', etc.
        """

        if not trades or len(trades) < 10:
            return {
                "success": False,
                "error": "Insufficient trades (minimum 10)"
            }

        try:
            wins = [t for t in trades if t.get("is_win", False)]
            losses = [t for t in trades if not t.get("is_win", False)]

            total_trades = len(trades)
            num_wins = len(wins)
            num_losses = len(losses)

            # Win Rate
            win_rate = (num_wins / total_trades) * 100

            # Average Win/Loss
            avg_win = statistics.mean([t["profit"] for t in wins]) if wins else 0
            avg_loss = statistics.mean([t["profit"] for t in losses]) if losses else 0

            # Profit Factor
            total_wins = sum([t["profit"] for t in wins])
            total_losses = abs(sum([t["profit"] for t in losses]))

            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

            # Expectancy
            expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

            # Average R:R (Risk:Reward)
            avg_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

            # Longest winning/losing streak
            current_streak = 0
            max_win_streak = 0
            max_loss_streak = 0
            current_streak_type = None

            for trade in trades:
                is_win = trade.get("is_win", False)

                if current_streak_type == is_win:
                    current_streak += 1
                else:
                    current_streak = 1
                    current_streak_type = is_win

                if is_win:
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_loss_streak = max(max_loss_streak, current_streak)

            return {
                "success": True,
                "total_trades": total_trades,
                "winning_trades": num_wins,
                "losing_trades": num_losses,
                "win_rate_pct": win_rate,
                "average_win": avg_win,
                "average_loss": avg_loss,
                "risk_reward_ratio": avg_rr,
                "profit_factor": profit_factor,
                "expectancy": expectancy,
                "max_win_streak": max_win_streak,
                "max_loss_streak": max_loss_streak,
                "rating": self._rate_trading_performance(win_rate, profit_factor, expectancy),
                "interpretation": self._interpret_trading_metrics(
                    win_rate, profit_factor, avg_rr
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating trading metrics: {str(e)}")
            return {"success": False, "error": str(e)}

    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict:
        """
        Calcula Kelly Criterion para position sizing óptimo

        Kelly = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win

        Indica el % óptimo del capital a arriesgar por trade
        """

        try:
            loss_rate = 1 - win_rate

            # Kelly formula
            kelly = (win_rate * avg_win - loss_rate * abs(avg_loss)) / avg_win if avg_win > 0 else 0

            # Kelly conservador (50% Kelly para reducir riesgo)
            kelly_conservative = kelly * 0.5

            # Clamp entre 0 y max position size
            kelly = max(0, min(kelly, self.MAX_POSITION_SIZE_PCT / 100))
            kelly_conservative = max(0, min(kelly_conservative, self.MAX_POSITION_SIZE_PCT / 100))

            return {
                "success": True,
                "kelly_percentage": kelly * 100,
                "kelly_conservative_percentage": kelly_conservative * 100,
                "recommended_position_size": kelly_conservative * 100,
                "interpretation": self._interpret_kelly(kelly_conservative * 100),
                "warning": "Use Kelly conservador para reducir volatilidad" if kelly > 0.1 else None,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Kelly Criterion: {str(e)}")
            return {"success": False, "error": str(e)}

    def comprehensive_risk_assessment(
        self,
        returns: List[float],
        equity_curve: List[float],
        trades: List[Dict],
        current_position_size: float,
        total_capital: float
    ) -> Dict:
        """
        Evaluación comprehensiva de riesgo combinando todas las métricas
        """

        try:
            # Calcular todas las métricas
            var_result = self.calculate_var(returns, confidence_level=0.95)
            sharpe_result = self.calculate_sharpe_ratio(returns)
            sortino_result = self.calculate_sortino_ratio(returns)
            mdd_result = self.calculate_maximum_drawdown(equity_curve)
            trading_metrics = self.calculate_trading_metrics(trades)

            # Risk Score (0-100, donde 100 es mínimo riesgo)
            risk_score = self._calculate_overall_risk_score(
                var_result, sharpe_result, mdd_result, trading_metrics
            )

            # Position size actual vs óptimo
            position_size_pct = (current_position_size / total_capital) * 100

            # Recomendaciones
            recommendations = self._generate_risk_recommendations(
                risk_score,
                var_result,
                sharpe_result,
                mdd_result,
                trading_metrics,
                position_size_pct
            )

            return {
                "success": True,
                "risk_score": risk_score,
                "risk_level": self._classify_risk_level(risk_score),
                "metrics": {
                    "var": var_result,
                    "sharpe_ratio": sharpe_result,
                    "sortino_ratio": sortino_result,
                    "maximum_drawdown": mdd_result,
                    "trading_metrics": trading_metrics,
                },
                "position_sizing": {
                    "current_position_pct": position_size_pct,
                    "is_oversized": position_size_pct > self.MAX_POSITION_SIZE_PCT,
                },
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in comprehensive risk assessment: {str(e)}")
            return {"success": False, "error": str(e)}

    # Helper methods para interpretación

    def _interpret_var(self, var: float, confidence: float) -> str:
        """Interpreta VaR"""
        return f"Con {confidence*100}% de confianza, la pérdida máxima esperada es {abs(var):.2f}%"

    def _rate_sharpe_ratio(self, sharpe: float) -> str:
        """Rating de Sharpe Ratio"""
        if sharpe > 3:
            return "EXCELENTE"
        elif sharpe > 2:
            return "MUY BUENO"
        elif sharpe > 1:
            return "BUENO"
        elif sharpe > 0:
            return "ACEPTABLE"
        else:
            return "POBRE"

    def _interpret_sharpe_ratio(self, sharpe: float) -> str:
        """Interpreta Sharpe Ratio"""
        if sharpe > 2:
            return "Excelente retorno ajustado por riesgo - Estrategia muy eficiente"
        elif sharpe > 1:
            return "Buen retorno ajustado por riesgo - Estrategia sólida"
        elif sharpe > 0:
            return "Retorno positivo pero con alto riesgo relativo"
        else:
            return "Retorno inferior a la tasa libre de riesgo - Revisar estrategia"

    def _rate_sortino_ratio(self, sortino: float) -> str:
        """Rating de Sortino Ratio"""
        if sortino > 2:
            return "EXCELENTE"
        elif sortino > 1.5:
            return "MUY BUENO"
        elif sortino > 1:
            return "BUENO"
        else:
            return "ACEPTABLE"

    def _interpret_sortino_ratio(self, sortino: float) -> str:
        """Interpreta Sortino Ratio"""
        if sortino > 2:
            return "Excelente manejo de downside risk - Volatilidad negativa muy controlada"
        elif sortino > 1:
            return "Buen control de pérdidas - Drawdowns manejables"
        else:
            return "Necesita mejorar control de pérdidas"

    def _classify_drawdown_risk(self, mdd: float) -> str:
        """Clasifica riesgo por drawdown"""
        mdd_abs = abs(mdd)
        if mdd_abs > 30:
            return "MUY ALTO"
        elif mdd_abs > 20:
            return "ALTO"
        elif mdd_abs > 10:
            return "MODERADO"
        else:
            return "BAJO"

    def _interpret_drawdown(self, mdd: float) -> str:
        """Interpreta drawdown"""
        mdd_abs = abs(mdd)
        if mdd_abs > 20:
            return f"Drawdown de {mdd_abs:.1f}% es muy alto - Riesgo significativo de capital"
        elif mdd_abs > 10:
            return f"Drawdown de {mdd_abs:.1f}% es moderado - Aceptable pero vigilar"
        else:
            return f"Drawdown de {mdd_abs:.1f}% es bajo - Buen control de riesgo"

    def _rate_calmar_ratio(self, calmar: float) -> str:
        """Rating de Calmar Ratio"""
        if calmar > 3:
            return "EXCELENTE"
        elif calmar > 2:
            return "MUY BUENO"
        elif calmar > 1:
            return "BUENO"
        else:
            return "POBRE"

    def _interpret_calmar_ratio(self, calmar: float) -> str:
        """Interpreta Calmar Ratio"""
        if calmar > 2:
            return "Excelente relación retorno/drawdown - Estrategia muy eficiente"
        elif calmar > 1:
            return "Buena relación retorno/drawdown"
        else:
            return "Retorno no justifica el drawdown máximo - Revisar estrategia"

    def _rate_trading_performance(
        self,
        win_rate: float,
        profit_factor: float,
        expectancy: float
    ) -> str:
        """Rating general de performance"""
        if win_rate > 60 and profit_factor > 2 and expectancy > 0:
            return "EXCELENTE"
        elif win_rate > 50 and profit_factor > 1.5 and expectancy > 0:
            return "BUENO"
        elif profit_factor > 1 and expectancy > 0:
            return "ACEPTABLE"
        else:
            return "POBRE"

    def _interpret_trading_metrics(
        self,
        win_rate: float,
        profit_factor: float,
        avg_rr: float
    ) -> str:
        """Interpreta métricas de trading"""
        if win_rate > 60 and profit_factor > 2:
            return "Estrategia muy rentable con alta tasa de éxito"
        elif profit_factor > 1.5:
            return "Estrategia rentable - Continuar monitoreando"
        elif profit_factor > 1:
            return "Estrategia marginalmente rentable - Buscar optimizaciones"
        else:
            return "Estrategia no rentable - Requiere cambios significativos"

    def _interpret_kelly(self, kelly_pct: float) -> str:
        """Interpreta Kelly percentage"""
        if kelly_pct > 10:
            return f"Kelly sugiere {kelly_pct:.1f}% pero considerar limitar a {self.MAX_POSITION_SIZE_PCT}% por gestión de riesgo"
        elif kelly_pct > 5:
            return f"Tamaño de posición recomendado: {kelly_pct:.1f}% del capital"
        elif kelly_pct > 0:
            return f"Tamaño de posición conservador: {kelly_pct:.1f}% del capital"
        else:
            return "Kelly negativo o cero - No operar hasta mejorar win rate o R:R"

    def _calculate_overall_risk_score(
        self,
        var_result: Dict,
        sharpe_result: Dict,
        mdd_result: Dict,
        trading_metrics: Dict
    ) -> float:
        """Calcula score de riesgo overall (0-100)"""

        score = 100  # Empezar en 100 (mínimo riesgo)

        # Penalizar por VaR alto
        if var_result.get("success"):
            var_val = abs(var_result.get("var_parametric", 0))
            score -= min(30, var_val * 3)

        # Bonus/penalización por Sharpe
        if sharpe_result.get("success"):
            sharpe = sharpe_result.get("sharpe_ratio_annualized", 0)
            if sharpe > 2:
                score += 10
            elif sharpe < 1:
                score -= 15

        # Penalizar por drawdown
        if mdd_result.get("success"):
            mdd = abs(mdd_result.get("maximum_drawdown_pct", 0))
            score -= min(25, mdd * 1.5)

        # Penalizar por métricas de trading pobres
        if trading_metrics.get("success"):
            win_rate = trading_metrics.get("win_rate_pct", 0)
            profit_factor = trading_metrics.get("profit_factor", 0)

            if win_rate < 40 or profit_factor < 1:
                score -= 20

        return max(0, min(100, score))

    def _classify_risk_level(self, risk_score: float) -> str:
        """Clasifica nivel de riesgo"""
        if risk_score >= 80:
            return "BAJO"
        elif risk_score >= 60:
            return "MODERADO"
        elif risk_score >= 40:
            return "ALTO"
        else:
            return "MUY ALTO"

    def _generate_risk_recommendations(
        self,
        risk_score: float,
        var_result: Dict,
        sharpe_result: Dict,
        mdd_result: Dict,
        trading_metrics: Dict,
        position_size_pct: float
    ) -> List[str]:
        """Genera recomendaciones basadas en análisis de riesgo"""

        recommendations = []

        if risk_score < 60:
            recommendations.append("⚠️ Nivel de riesgo elevado - Considerar reducir exposición")

        if position_size_pct > self.MAX_POSITION_SIZE_PCT:
            recommendations.append(
                f"📉 Tamaño de posición ({position_size_pct:.1f}%) excede el máximo recomendado ({self.MAX_POSITION_SIZE_PCT}%)"
            )

        if mdd_result.get("success"):
            mdd = abs(mdd_result.get("maximum_drawdown_pct", 0))
            if mdd > 15:
                recommendations.append(
                    f"⚠️ Drawdown máximo ({mdd:.1f}%) es alto - Implementar stop loss más estrictos"
                )

        if sharpe_result.get("success"):
            sharpe = sharpe_result.get("sharpe_ratio_annualized", 0)
            if sharpe < 1:
                recommendations.append(
                    "📊 Sharpe Ratio bajo - Considerar estrategias alternativas o reducir riesgo"
                )

        if trading_metrics.get("success"):
            win_rate = trading_metrics.get("win_rate_pct", 0)
            profit_factor = trading_metrics.get("profit_factor", 0)

            if win_rate < 50 and profit_factor < 1.5:
                recommendations.append(
                    "📈 Mejorar win rate o risk:reward ratio para rentabilidad sostenible"
                )

        if not recommendations:
            recommendations.append("✅ Gestión de riesgo sólida - Mantener disciplina actual")

        return recommendations
