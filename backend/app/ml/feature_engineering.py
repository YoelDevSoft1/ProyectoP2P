"""
Feature Engineering Avanzado para Trading.
Incluye indicadores técnicos, features de mercado, y transformaciones.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedFeatureEngineer:
    """Ingeniería de features avanzada para trading."""
    
    def __init__(self):
        self.feature_cache = {}
    
    def calculate_technical_indicators(self, df: pd.DataFrame, 
                                      price_col: str = 'price') -> pd.DataFrame:
        """
        Calcular indicadores técnicos avanzados.
        """
        df = df.copy()
        
        # Moving Averages
        df['ma_5'] = df[price_col].rolling(window=5, min_periods=1).mean()
        df['ma_10'] = df[price_col].rolling(window=10, min_periods=1).mean()
        df['ma_20'] = df[price_col].rolling(window=20, min_periods=1).mean()
        df['ma_50'] = df[price_col].rolling(window=50, min_periods=1).mean()
        df['ma_200'] = df[price_col].rolling(window=200, min_periods=1).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df[price_col].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df[price_col].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI (Relative Strength Index)
        delta = df[price_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df[price_col].rolling(window=20, min_periods=1).mean()
        bb_std = df[price_col].rolling(window=20, min_periods=1).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df[price_col] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR (Average True Range)
        high = df.get('high', df[price_col] * 1.01)
        low = df.get('low', df[price_col] * 0.99)
        tr1 = high - low
        tr2 = abs(high - df[price_col].shift())
        tr3 = abs(low - df[price_col].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14, min_periods=1).mean()
        
        # Stochastic Oscillator
        low_14 = low.rolling(window=14, min_periods=1).min()
        high_14 = high.rolling(window=14, min_periods=1).max()
        df['stoch_k'] = 100 * ((df[price_col] - low_14) / (high_14 - low_14))
        df['stoch_d'] = df['stoch_k'].rolling(window=3, min_periods=1).mean()
        
        # ADX (Average Directional Index) - simplificado
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr_smooth = tr.rolling(window=14, min_periods=1).mean()
        plus_di = 100 * (plus_dm.rolling(window=14, min_periods=1).mean() / tr_smooth)
        minus_di = 100 * (minus_dm.rolling(window=14, min_periods=1).mean() / tr_smooth)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14, min_periods=1).mean()
        
        # Volume indicators (si hay volumen)
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=20, min_periods=1).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            df['volume_price_trend'] = (df['volume'] * df[price_col].pct_change()).cumsum()
        
        # Momentum indicators
        df['momentum'] = df[price_col].pct_change(periods=10)
        df['roc'] = ((df[price_col] - df[price_col].shift(10)) / df[price_col].shift(10)) * 100
        df['cci'] = self._calculate_cci(df[price_col], high, low, period=20)
        
        # Volatility
        df['volatility'] = df[price_col].rolling(window=10, min_periods=1).std()
        df['volatility_ratio'] = df['volatility'] / df[price_col]
        df['price_change'] = df[price_col].pct_change()
        df['price_change_abs'] = df['price_change'].abs()
        
        # Price patterns
        df['higher_high'] = (df[price_col] > df[price_col].shift(1)) & (df[price_col].shift(1) > df[price_col].shift(2))
        df['lower_low'] = (df[price_col] < df[price_col].shift(1)) & (df[price_col].shift(1) < df[price_col].shift(2))
        
        # Fill NaN values
        df = df.bfill().fillna(0)
        
        return df
    
    def _calculate_cci(self, price: pd.Series, high: pd.Series, low: pd.Series, period: int = 20) -> pd.Series:
        """Calcular Commodity Channel Index."""
        tp = (high + low + price) / 3
        sma = tp.rolling(window=period, min_periods=1).mean()
        mad = tp.rolling(window=period, min_periods=1).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - sma) / (0.015 * mad)
        return cci
    
    def calculate_market_features(self, df: pd.DataFrame, 
                                 spread_col: str = 'spread',
                                 volume_col: str = 'volume') -> pd.DataFrame:
        """
        Calcular features de mercado (spread, liquidez, etc.).
        """
        df = df.copy()
        
        # Spread features
        if spread_col in df.columns:
            df['spread_ma'] = df[spread_col].rolling(window=5, min_periods=1).mean()
            df['spread_std'] = df[spread_col].rolling(window=10, min_periods=1).std()
            df['spread_change'] = df[spread_col].pct_change()
            df['spread_ratio'] = df[spread_col] / df.get('price', 1)
        
        # Volume features
        if volume_col in df.columns:
            df['volume_ma'] = df[volume_col].rolling(window=20, min_periods=1).mean()
            df['volume_std'] = df[volume_col].rolling(window=20, min_periods=1).std()
            df['volume_change'] = df[volume_col].pct_change()
            df['volume_trend'] = df[volume_col].rolling(window=5, min_periods=1).apply(
                lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1 if x.iloc[-1] < x.iloc[0] else 0
            )
        
        # Liquidity features (spread * volume)
        if spread_col in df.columns and volume_col in df.columns:
            df['liquidity'] = df[volume_col] / (df[spread_col] + 1e-6)
            df['liquidity_ma'] = df['liquidity'].rolling(window=10, min_periods=1).mean()
        
        # Market depth (simulado)
        if 'volume' in df.columns:
            df['market_depth'] = df['volume'].rolling(window=10, min_periods=1).sum()
        
        # Fill NaN
        df = df.fillna(method='bfill').fillna(0)
        
        return df
    
    def calculate_time_features(self, df: pd.DataFrame, 
                               timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Calcular features temporales.
        """
        df = df.copy()
        
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df['hour'] = df[timestamp_col].dt.hour
            df['day_of_week'] = df[timestamp_col].dt.dayofweek
            df['day_of_month'] = df[timestamp_col].dt.day
            df['month'] = df[timestamp_col].dt.month
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_market_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17)).astype(int)
            
            # Cyclical encoding
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
    
    def calculate_profit_features(self, df: pd.DataFrame,
                                 price_col: str = 'price',
                                 buy_price: Optional[float] = None) -> pd.DataFrame:
        """
        Calcular features relacionadas con profit potencial.
        """
        df = df.copy()
        
        # Profit potencial si compramos a precio anterior
        if buy_price is None:
            buy_price = df[price_col].shift(1)
        else:
            buy_price = pd.Series([buy_price] * len(df), index=df.index)
        
        df['potential_profit'] = df[price_col] - buy_price
        df['potential_profit_pct'] = (df['potential_profit'] / buy_price) * 100
        
        # Profit real si vendemos ahora
        df['profit_if_sell'] = df[price_col] - buy_price
        df['profit_pct'] = (df['profit_if_sell'] / buy_price) * 100
        
        # Risk metrics
        df['max_drawdown'] = self._calculate_max_drawdown(df[price_col])
        df['sharpe_ratio'] = self._calculate_sharpe_ratio(df[price_col])
        
        return df
    
    def _calculate_max_drawdown(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Calcular máximo drawdown."""
        rolling_max = prices.rolling(window=window, min_periods=1).max()
        drawdown = (prices - rolling_max) / rolling_max
        return drawdown
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, window: int = 20, risk_free_rate: float = 0.0) -> pd.Series:
        """Calcular Sharpe ratio."""
        returns_pct = returns.pct_change()
        mean_return = returns_pct.rolling(window=window, min_periods=1).mean()
        std_return = returns_pct.rolling(window=window, min_periods=1).std()
        sharpe = (mean_return - risk_free_rate) / (std_return + 1e-6)
        return sharpe
    
    def create_all_features(self, df: pd.DataFrame,
                           price_col: str = 'price',
                           spread_col: str = 'spread',
                           volume_col: str = 'volume',
                           timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Crear todas las features avanzadas.
        """
        logger.info("Creating advanced features")
        
        # Technical indicators
        df = self.calculate_technical_indicators(df, price_col=price_col)
        
        # Market features
        df = self.calculate_market_features(df, spread_col=spread_col, volume_col=volume_col)
        
        # Time features
        df = self.calculate_time_features(df, timestamp_col=timestamp_col)
        
        # Profit features
        df = self.calculate_profit_features(df, price_col=price_col)
        
        # Fill NaN
        df = df.bfill().fillna(0)
        
        logger.info(f"Created {len(df.columns)} features")
        
        return df
    
    def get_feature_list(self, include_profit: bool = True) -> List[str]:
        """
        Obtener lista de features disponibles.
        """
        base_features = [
            'price', 'spread', 'volume',
            'ma_5', 'ma_10', 'ma_20', 'ma_50', 'ma_200',
            'ema_12', 'ema_26', 'macd', 'macd_signal', 'macd_histogram',
            'rsi', 'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position',
            'atr', 'stoch_k', 'stoch_d', 'adx',
            'momentum', 'roc', 'cci',
            'volatility', 'volatility_ratio', 'price_change', 'price_change_abs',
            'spread_ma', 'spread_std', 'spread_change', 'spread_ratio',
            'volume_ma', 'volume_std', 'volume_change', 'volume_trend',
            'liquidity', 'liquidity_ma', 'market_depth',
            'hour', 'day_of_week', 'day_of_month', 'month',
            'is_weekend', 'is_market_hours',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
        ]
        
        if include_profit:
            base_features.extend([
                'potential_profit', 'potential_profit_pct',
                'profit_if_sell', 'profit_pct',
                'max_drawdown', 'sharpe_ratio'
            ])
        
        return base_features

