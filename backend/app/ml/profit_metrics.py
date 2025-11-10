"""
Métricas de Profit y Risk para Trading.
Incluye: Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Profit Factor, etc.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ProfitMetricsCalculator:
    """Calculadora de métricas de profit y risk."""
    
    def __init__(self, risk_free_rate: float = 0.0):
        self.risk_free_rate = risk_free_rate
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                              period: str = 'daily') -> float:
        """
        Calcular Sharpe Ratio.
        Mide el rendimiento ajustado por riesgo.
        """
        if len(returns) == 0:
            return 0.0
        
        # Ajustar por período
        periods_per_year = {
            'daily': 252,
            'hourly': 252 * 24,
            'minute': 252 * 24 * 60
        }.get(period, 252)
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0.0
        
        sharpe = np.sqrt(periods_per_year) * (mean_return - self.risk_free_rate) / std_return
        return float(sharpe)
    
    def calculate_sortino_ratio(self, returns: pd.Series,
                               period: str = 'daily') -> float:
        """
        Calcular Sortino Ratio.
        Similar a Sharpe pero solo considera volatilidad negativa.
        """
        if len(returns) == 0:
            return 0.0
        
        periods_per_year = {
            'daily': 252,
            'hourly': 252 * 24,
            'minute': 252 * 24 * 60
        }.get(period, 252)
        
        mean_return = returns.mean()
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0:
            downside_std = 0.0
        else:
            downside_std = negative_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        sortino = np.sqrt(periods_per_year) * (mean_return - self.risk_free_rate) / downside_std
        return float(sortino)
    
    def calculate_maximum_drawdown(self, prices: pd.Series) -> Dict:
        """
        Calcular Maximum Drawdown.
        Mide la mayor caída desde un pico.
        """
        if len(prices) == 0:
            return {'max_drawdown': 0.0, 'max_drawdown_pct': 0.0, 'duration': 0}
        
        # Calcular drawdown
        rolling_max = prices.expanding().max()
        drawdown = prices - rolling_max
        drawdown_pct = (drawdown / rolling_max) * 100
        
        # Máximo drawdown
        max_dd = drawdown.min()
        max_dd_pct = drawdown_pct.min()
        
        # Duración del drawdown
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.groupby((is_drawdown != is_drawdown.shift()).cumsum()).sum()
        max_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0
        
        return {
            'max_drawdown': float(max_dd),
            'max_drawdown_pct': float(max_dd_pct),
            'duration': int(max_duration)
        }
    
    def calculate_profit_factor(self, profits: pd.Series) -> float:
        """
        Calcular Profit Factor.
        Ratio de ganancias totales vs pérdidas totales.
        """
        if len(profits) == 0:
            return 0.0
        
        gross_profit = profits[profits > 0].sum()
        gross_loss = abs(profits[profits < 0].sum())
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        profit_factor = gross_profit / gross_loss
        return float(profit_factor)
    
    def calculate_win_rate(self, profits: pd.Series) -> Dict:
        """
        Calcular Win Rate.
        Porcentaje de trades ganadores.
        """
        if len(profits) == 0:
            return {'win_rate': 0.0, 'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0}
        
        winning_trades = (profits > 0).sum()
        losing_trades = (profits < 0).sum()
        total_trades = len(profits)
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        return {
            'win_rate': float(win_rate),
            'total_trades': int(total_trades),
            'winning_trades': int(winning_trades),
            'losing_trades': int(losing_trades)
        }
    
    def calculate_average_win_loss(self, profits: pd.Series) -> Dict:
        """
        Calcular promedio de ganancias y pérdidas.
        """
        if len(profits) == 0:
            return {'avg_win': 0.0, 'avg_loss': 0.0, 'win_loss_ratio': 0.0}
        
        wins = profits[profits > 0]
        losses = profits[profits < 0]
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
        
        return {
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'win_loss_ratio': float(win_loss_ratio)
        }
    
    def calculate_calmar_ratio(self, returns: pd.Series,
                              period: str = 'daily') -> float:
        """
        Calcular Calmar Ratio.
        Ratio de retorno anualizado vs maximum drawdown.
        """
        if len(returns) == 0:
            return 0.0
        
        periods_per_year = {
            'daily': 252,
            'hourly': 252 * 24,
            'minute': 252 * 24 * 60
        }.get(period, 252)
        
        annual_return = returns.mean() * periods_per_year
        
        # Calcular max drawdown de retornos acumulados
        cumulative_returns = (1 + returns).cumprod()
        max_dd_info = self.calculate_maximum_drawdown(cumulative_returns)
        max_dd_pct = abs(max_dd_info['max_drawdown_pct']) / 100
        
        if max_dd_pct == 0:
            return 0.0
        
        calmar = annual_return / max_dd_pct
        return float(calmar)
    
    def calculate_value_at_risk(self, returns: pd.Series, 
                               confidence_level: float = 0.95) -> float:
        """
        Calcular Value at Risk (VaR).
        Pérdida máxima esperada con un nivel de confianza.
        """
        if len(returns) == 0:
            return 0.0
        
        var = returns.quantile(1 - confidence_level)
        return float(var)
    
    def calculate_expected_shortfall(self, returns: pd.Series,
                                    confidence_level: float = 0.95) -> float:
        """
        Calcular Expected Shortfall (Conditional VaR).
        Pérdida promedio en el peor (1-confidence_level)% de casos.
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_value_at_risk(returns, confidence_level)
        es = returns[returns <= var].mean()
        return float(es)
    
    def calculate_all_metrics(self, prices: pd.Series,
                             profits: Optional[pd.Series] = None,
                             returns: Optional[pd.Series] = None,
                             period: str = 'daily') -> Dict:
        """
        Calcular todas las métricas de profit y risk.
        """
        metrics = {}
        
        # Calcular returns si no se proporcionan
        if returns is None and prices is not None:
            returns = prices.pct_change().dropna()
        
        # Métricas basadas en returns
        if returns is not None and len(returns) > 0:
            metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(returns, period)
            metrics['sortino_ratio'] = self.calculate_sortino_ratio(returns, period)
            metrics['calmar_ratio'] = self.calculate_calmar_ratio(returns, period)
            metrics['var_95'] = self.calculate_value_at_risk(returns, 0.95)
            metrics['expected_shortfall_95'] = self.calculate_expected_shortfall(returns, 0.95)
            metrics['total_return'] = float(returns.sum())
            metrics['annualized_return'] = float(returns.mean() * {
                'daily': 252,
                'hourly': 252 * 24,
                'minute': 252 * 24 * 60
            }.get(period, 252))
            metrics['volatility'] = float(returns.std())
            metrics['annualized_volatility'] = float(returns.std() * np.sqrt({
                'daily': 252,
                'hourly': 252 * 24,
                'minute': 252 * 24 * 60
            }.get(period, 252)))
        
        # Maximum Drawdown
        if prices is not None and len(prices) > 0:
            max_dd_info = self.calculate_maximum_drawdown(prices)
            metrics.update(max_dd_info)
        
        # Métricas basadas en profits
        if profits is not None and len(profits) > 0:
            metrics['profit_factor'] = self.calculate_profit_factor(profits)
            win_rate_info = self.calculate_win_rate(profits)
            metrics.update(win_rate_info)
            avg_win_loss_info = self.calculate_average_win_loss(profits)
            metrics.update(avg_win_loss_info)
            metrics['total_profit'] = float(profits.sum())
            metrics['average_profit'] = float(profits.mean())
            metrics['max_profit'] = float(profits.max())
            metrics['min_profit'] = float(profits.min())
        
        return metrics
    
    def evaluate_strategy(self, predictions: pd.Series,
                         actual_prices: pd.Series,
                         buy_threshold: float = 0.02,
                         sell_threshold: float = 0.02) -> Dict:
        """
        Evaluar estrategia de trading basada en predicciones.
        """
        if len(predictions) != len(actual_prices):
            raise ValueError("Predictions and actual prices must have same length")
        
        # Calcular señales
        price_changes = actual_prices.pct_change()
        predicted_changes = predictions.pct_change()
        
        # Señales de compra/venta
        buy_signals = predicted_changes > buy_threshold
        sell_signals = predicted_changes < -sell_threshold
        
        # Calcular profits simulados
        positions = []
        current_position = None
        
        for i in range(len(actual_prices)):
            if buy_signals.iloc[i] and current_position is None:
                # Comprar
                current_position = {
                    'entry_price': actual_prices.iloc[i],
                    'entry_index': i
                }
            elif sell_signals.iloc[i] and current_position is not None:
                # Vender
                profit = actual_prices.iloc[i] - current_position['entry_price']
                profit_pct = (profit / current_position['entry_price']) * 100
                positions.append({
                    'entry_price': current_position['entry_price'],
                    'exit_price': actual_prices.iloc[i],
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'entry_index': current_position['entry_index'],
                    'exit_index': i
                })
                current_position = None
        
        # Calcular métricas
        if len(positions) > 0:
            profits = pd.Series([p['profit'] for p in positions])
            returns = pd.Series([p['profit_pct'] for p in positions])
            metrics = self.calculate_all_metrics(
                prices=actual_prices,
                profits=profits,
                returns=returns / 100,  # Convertir a decimal
                period='daily'
            )
            metrics['total_trades'] = len(positions)
            metrics['positions'] = positions
        else:
            metrics = {
                'total_trades': 0,
                'total_profit': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'win_rate': 0.0
            }
        
        return metrics

