"""
Servicio para obtener datos históricos de Yahoo Finance.
Usa yfinance para obtener datos de criptomonedas, forex, y acciones.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import time
import random

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Servicio para obtener datos históricos de Yahoo Finance."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)
    
    def get_crypto_data(self, symbol: str, period: str = "1y", 
                       interval: str = "1d", max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de criptomonedas.
        
        Args:
            symbol: Símbolo de la criptomoneda (ej: "BTC-USD", "ETH-USD")
            period: Período ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Intervalo ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")
            max_retries: Número máximo de intentos
        
        Returns:
            DataFrame con datos históricos (OHLCV)
        """
        for attempt in range(max_retries):
            try:
                # Agregar delay aleatorio para evitar rate limiting
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    logger.info(f"Retry {attempt + 1}/{max_retries} for {symbol} after {delay:.2f}s delay")
                    time.sleep(delay)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval)
                
                if data.empty:
                    if attempt < max_retries - 1:
                        logger.warning(f"No data found for {symbol}, retrying...")
                        continue
                    logger.warning(f"No data found for {symbol} after {max_retries} attempts")
                    return None
                
                # Limpiar datos
                data = data.dropna()
                if len(data) == 0:
                    if attempt < max_retries - 1:
                        continue
                    return None
                
                data.columns = [col.lower() for col in data.columns]
                
                logger.info(f"Retrieved {len(data)} data points for {symbol}")
                return data
                
            except Exception as e:
                error_msg = str(e).lower()
                # Detectar rate limiting (429, "too many requests", "rate limit")
                is_rate_limit = (
                    "429" in error_msg or 
                    "too many requests" in error_msg or 
                    "rate limit" in error_msg or
                    "crumb" in error_msg  # Yahoo Finance a veces falla con crumb
                )
                
                if is_rate_limit:
                    if attempt < max_retries - 1:
                        # Delay exponencial con jitter: 10-20s, 20-40s, 40-80s
                        base_delay = 10 * (2 ** attempt)
                        delay = random.uniform(base_delay, base_delay * 2)
                        logger.warning(
                            f"Rate limit hit for {symbol} (intento {attempt + 1}/{max_retries}), "
                            f"esperando {delay:.1f}s antes de reintentar..."
                        )
                        time.sleep(delay)
                        
                        # Limpiar caché de cookies de yfinance para forzar nuevo crumb
                        try:
                            import yfinance as yf
                            # Forzar limpieza de caché
                            ticker = yf.Ticker(symbol)
                            if hasattr(ticker, 'history'):
                                # Crear nuevo ticker para limpiar estado
                                del ticker
                        except:
                            pass
                        
                        continue
                    else:
                        logger.error(
                            f"Rate limit exceeded for {symbol} after {max_retries} attempts. "
                            f"Espera unos minutos antes de intentar nuevamente."
                        )
                        return None
                else:
                    logger.error(f"Error fetching crypto data for {symbol}: {e}", exc_info=True)
                    if attempt < max_retries - 1:
                        # Para otros errores, esperar menos tiempo
                        delay = random.uniform(2, 5)
                        time.sleep(delay)
                        continue
                    return None
        
        return None
    
    def get_forex_data(self, from_currency: str, to_currency: str,
                      period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de Forex.
        
        Args:
            from_currency: Moneda base (ej: "USD")
            to_currency: Moneda destino (ej: "COP")
            period: Período
            interval: Intervalo
        
        Returns:
            DataFrame con datos históricos
        """
        try:
            # Yahoo Finance usa formato "FROMTO=X" para Forex
            symbol = f"{from_currency}{to_currency}=X"
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for {from_currency}/{to_currency}")
                return None
            
            # Limpiar datos
            data = data.dropna()
            data.columns = [col.lower() for col in data.columns]
            
            logger.info(f"Retrieved {len(data)} data points for {from_currency}/{to_currency}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching forex data for {from_currency}/{to_currency}: {e}", exc_info=True)
            return None
    
    def get_stock_data(self, symbol: str, period: str = "1y",
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de acciones.
        
        Args:
            symbol: Símbolo de la acción (ej: "AAPL", "MSFT")
            period: Período
            interval: Intervalo
        
        Returns:
            DataFrame con datos históricos
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Limpiar datos
            data = data.dropna()
            data.columns = [col.lower() for col in data.columns]
            
            logger.info(f"Retrieved {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}", exc_info=True)
            return None
    
    def prepare_data_for_training(self, data: pd.DataFrame,
                                  target_col: str = "close") -> pd.DataFrame:
        """
        Preparar datos para entrenamiento de modelos de ML.
        Yahoo Finance ya viene con OHLCV completo, así que aprovechamos eso.
        
        Args:
            data: DataFrame con datos históricos de Yahoo Finance
            target_col: Columna objetivo (default: "close")
        
        Returns:
            DataFrame preparado para entrenamiento
        """
        try:
            df = data.copy()
            
            # Yahoo Finance usa close, high, low, open, volume
            # Asegurar que tenemos las columnas necesarias
            if target_col not in df.columns:
                if "close" in df.columns:
                    target_col = "close"
                elif "Close" in df.columns:
                    target_col = "Close"
                else:
                    raise ValueError(f"Target column '{target_col}' not found in data. Available columns: {list(df.columns)}")
            
            # Normalizar nombres de columnas a minúsculas
            df.columns = [col.lower() for col in df.columns]
            target_col = target_col.lower()
            
            # Renombrar close a price para consistencia
            if "price" not in df.columns:
                if target_col in df.columns:
                    df["price"] = df[target_col]
                elif "close" in df.columns:
                    df["price"] = df["close"]
                else:
                    raise ValueError(f"No se encontró columna de precio. Columnas disponibles: {list(df.columns)}")
            
            # Asegurar que tenemos volumen
            if "volume" not in df.columns:
                df["volume"] = 0.0
                logger.warning("No se encontró columna 'volume', usando 0.0")
            
            # Calcular spread basado en high/low
            if "high" in df.columns and "low" in df.columns and "price" in df.columns:
                df["spread"] = ((df["high"] - df["low"]) / df["price"]) * 100
            else:
                df["spread"] = 0.0
                logger.warning("No se encontraron columnas high/low, usando spread=0.0")
            
            # Añadir timestamp
            if isinstance(df.index, pd.DatetimeIndex):
                df["timestamp"] = df.index
                df = df.reset_index(drop=True)
            elif "timestamp" not in df.columns:
                # Intentar usar el índice como fecha
                try:
                    df["timestamp"] = pd.to_datetime(df.index)
                except:
                    df["timestamp"] = pd.date_range(start='2020-01-01', periods=len(df), freq='D')
                    logger.warning("No se pudo convertir índice a fecha, usando fechas generadas")
            
            # Ordenar por timestamp
            df = df.sort_values("timestamp").reset_index(drop=True)
            
            # Limpiar datos inválidos
            df = df[df['price'] > 0]
            df = df.dropna(subset=['price'])
            
            logger.info(f"✅ Prepared {len(df)} data points for training")
            logger.info(f"   Price range: {df['price'].min():.2f} - {df['price'].max():.2f}")
            logger.info(f"   Date range: {df['timestamp'].min()} - {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing data for training: {e}", exc_info=True)
            raise
    
    def get_multiple_symbols(self, symbols: List[str], period: str = "1y",
                            interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Obtener datos de múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
            period: Período
            interval: Intervalo
        
        Returns:
            Diccionario con datos de cada símbolo
        """
        results = {}
        for symbol in symbols:
            try:
                data = self.get_crypto_data(symbol, period=period, interval=interval)
                if data is not None:
                    results[symbol] = data
            except Exception as e:
                logger.warning(f"Error fetching {symbol}: {e}")
                continue
        
        return results
    
    def get_usdt_cop_data(self, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de USDT/COP (simulado como USD/COP).
        Yahoo Finance no tiene USDT directamente, usamos USD/COP.
        """
        try:
            # Obtener USD/COP de Yahoo Finance
            data = self.get_forex_data("USD", "COP", period=period, interval=interval)
            if data is not None:
                # Preparar para entrenamiento
                data = self.prepare_data_for_training(data, target_col="close")
            return data
        except Exception as e:
            logger.error(f"Error fetching USDT/COP data: {e}", exc_info=True)
            return None
    
    def get_crypto_usdt_data(self, crypto: str, period: str = "1y",
                            interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de criptomonedas vs USDT.
        
        Args:
            crypto: Criptomoneda (ej: "BTC", "ETH")
            period: Período
            interval: Intervalo
        
        Returns:
            DataFrame con datos históricos
        """
        try:
            symbol = f"{crypto}-USD"  # Yahoo Finance usa USD, no USDT
            data = self.get_crypto_data(symbol, period=period, interval=interval)
            if data is not None:
                data = self.prepare_data_for_training(data, target_col="close")
            return data
        except Exception as e:
            logger.error(f"Error fetching {crypto}/USDT data: {e}", exc_info=True)
            return None

