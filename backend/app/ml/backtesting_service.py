"""
Servicio de Backtesting para evaluar estrategias de trading.
Incluye walk-forward analysis, monte carlo simulation, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
import logging
from datetime import datetime, timedelta

from app.ml.profit_metrics import ProfitMetricsCalculator

logger = logging.getLogger(__name__)


class BacktestingService:
    """Servicio de backtesting para estrategias de trading."""
    
    def __init__(self):
        self.profit_calculator = ProfitMetricsCalculator()
    
    def backtest_strategy(self, predictions: pd.Series,
                         actual_prices: pd.Series,
                         initial_capital: float = 10000.0,
                         buy_threshold: float = 0.02,
                         sell_threshold: float = 0.02,
                         stop_loss: float = 0.05,
                         take_profit: float = 0.10,
                         commission: float = 0.001) -> Dict:
        """
        Backtest de una estrategia de trading.
        
        Args:
            predictions: Precios predichos
            actual_prices: Precios reales
            initial_capital: Capital inicial
            buy_threshold: Umbral para comprar (cambio porcentual)
            sell_threshold: Umbral para vender
            stop_loss: Stop loss porcentual
            take_profit: Take profit porcentual
            commission: Comisión por trade
        """
        if len(predictions) != len(actual_prices):
            raise ValueError("Predictions and actual prices must have same length")
        
        # Calcular señales
        price_changes = actual_prices.pct_change()
        predicted_changes = predictions.pct_change()
        
        # Estado del backtest
        capital = initial_capital
        position = None
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(1, len(actual_prices)):
            current_price = actual_prices.iloc[i]
            predicted_change = predicted_changes.iloc[i]
            current_capital = capital
            
            # Si no hay posición, buscar señal de compra
            if position is None:
                if predicted_change > buy_threshold:
                    # Comprar
                    shares = capital / current_price
                    cost = shares * current_price * (1 + commission)
                    if cost <= capital:
                        position = {
                            'entry_price': current_price,
                            'shares': shares,
                            'entry_index': i,
                            'entry_capital': capital,
                            'stop_loss_price': current_price * (1 - stop_loss),
                            'take_profit_price': current_price * (1 + take_profit)
                        }
                        capital -= cost
            else:
                # Si hay posición, verificar stop loss, take profit, o señal de venta
                should_sell = False
                sell_reason = None
                
                # Stop Loss
                if current_price <= position['stop_loss_price']:
                    should_sell = True
                    sell_reason = 'stop_loss'
                
                # Take Profit
                elif current_price >= position['take_profit_price']:
                    should_sell = True
                    sell_reason = 'take_profit'
                
                # Señal de venta
                elif predicted_change < -sell_threshold:
                    should_sell = True
                    sell_reason = 'signal'
                
                if should_sell:
                    # Vender
                    revenue = position['shares'] * current_price * (1 - commission)
                    capital += revenue
                    
                    profit = revenue - position['entry_capital']
                    profit_pct = (profit / position['entry_capital']) * 100
                    
                    trade = {
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'shares': position['shares'],
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'entry_index': position['entry_index'],
                        'exit_index': i,
                        'duration': i - position['entry_index'],
                        'reason': sell_reason
                    }
                    trades.append(trade)
                    position = None
            
            # Actualizar equity curve
            if position is not None:
                # Capital actual + valor de la posición
                current_equity = capital + (position['shares'] * current_price)
            else:
                current_equity = capital
            equity_curve.append(current_equity)
        
        # Calcular métricas
        if len(trades) > 0:
            profits = pd.Series([t['profit'] for t in trades])
            equity_series = pd.Series(equity_curve)
            returns = equity_series.pct_change().dropna()
            
            metrics = self.profit_calculator.calculate_all_metrics(
                prices=equity_series,
                profits=profits,
                returns=returns,
                period='daily'
            )
            
            # Métricas adicionales
            total_return = ((equity_series.iloc[-1] - initial_capital) / initial_capital) * 100
            max_equity = equity_series.max()
            min_equity_after_max = equity_series[equity_series.idxmax():].min()
            max_drawdown_pct = ((max_equity - min_equity_after_max) / max_equity) * 100
            
            metrics.update({
                'initial_capital': initial_capital,
                'final_capital': float(equity_series.iloc[-1]),
                'total_return_pct': float(total_return),
                'max_equity': float(max_equity),
                'max_drawdown_pct': float(max_drawdown_pct),
                'total_trades': len(trades),
                'winning_trades': len([t for t in trades if t['profit'] > 0]),
                'losing_trades': len([t for t in trades if t['profit'] < 0]),
                'avg_trade_duration': np.mean([t['duration'] for t in trades]) if trades else 0
            })
        else:
            metrics = {
                'initial_capital': initial_capital,
                'final_capital': initial_capital,
                'total_return_pct': 0.0,
                'total_trades': 0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'win_rate': 0.0
            }
        
        return {
            'metrics': metrics,
            'trades': trades,
            'equity_curve': equity_curve,
            'final_capital': equity_curve[-1] if equity_curve else initial_capital
        }
    
    def walk_forward_analysis(self, predictions: pd.Series,
                             actual_prices: pd.Series,
                             train_window: int = 100,
                             test_window: int = 20,
                             initial_capital: float = 10000.0) -> Dict:
        """
        Walk-forward analysis para validar estrategia.
        """
        results = []
        
        for i in range(0, len(predictions) - test_window, test_window):
            train_end = i + train_window
            test_start = train_end
            test_end = test_start + test_window
            
            if test_end > len(predictions):
                break
            
            # Datos de test
            test_predictions = predictions.iloc[test_start:test_end]
            test_prices = actual_prices.iloc[test_start:test_end]
            
            # Backtest
            result = self.backtest_strategy(
                predictions=test_predictions,
                actual_prices=test_prices,
                initial_capital=initial_capital
            )
            
            result['period'] = {
                'start': test_start,
                'end': test_end
            }
            results.append(result)
        
        # Agregar resultados
        if results:
            total_return = sum([r['metrics'].get('total_return_pct', 0) for r in results])
            avg_sharpe = np.mean([r['metrics'].get('sharpe_ratio', 0) for r in results])
            total_trades = sum([r['metrics'].get('total_trades', 0) for r in results])
            
            return {
                'periods': len(results),
                'total_return_pct': total_return,
                'avg_sharpe_ratio': float(avg_sharpe),
                'total_trades': total_trades,
                'period_results': results
            }
        else:
            return {
                'periods': 0,
                'total_return_pct': 0.0,
                'avg_sharpe_ratio': 0.0,
                'total_trades': 0,
                'period_results': []
            }
    
    def monte_carlo_simulation(self, returns: pd.Series,
                              n_simulations: int = 1000,
                              n_periods: int = 252,
                              initial_capital: float = 10000.0) -> Dict:
        """
        Simulación Monte Carlo para evaluar riesgo.
        """
        if len(returns) == 0:
            return {'simulations': [], 'metrics': {}}
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        simulations = []
        
        for _ in range(n_simulations):
            # Generar retornos aleatorios
            random_returns = np.random.normal(mean_return, std_return, n_periods)
            
            # Calcular equity curve
            equity = initial_capital
            equity_curve = [equity]
            
            for ret in random_returns:
                equity *= (1 + ret)
                equity_curve.append(equity)
            
            simulations.append(equity_curve)
        
        # Calcular métricas
        final_values = [sim[-1] for sim in simulations]
        final_values = np.array(final_values)
        
        metrics = {
            'mean_final_value': float(np.mean(final_values)),
            'std_final_value': float(np.std(final_values)),
            'min_final_value': float(np.min(final_values)),
            'max_final_value': float(np.max(final_values)),
            'percentile_5': float(np.percentile(final_values, 5)),
            'percentile_95': float(np.percentile(final_values, 95)),
            'probability_profit': float(np.mean(final_values > initial_capital) * 100),
            'expected_return_pct': float(((np.mean(final_values) - initial_capital) / initial_capital) * 100)
        }
        
        return {
            'simulations': simulations[:10],  # Solo devolver primeras 10 para no sobrecargar
            'metrics': metrics,
            'n_simulations': n_simulations
        }

