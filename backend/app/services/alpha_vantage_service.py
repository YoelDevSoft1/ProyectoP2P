"""
Servicio para interactuar con Alpha Vantage API.
Proporciona datos Forex, indicadores técnicos y datos históricos.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import structlog

from app.core.config import settings
from app.core.rate_limiter import binance_p2p_rate_limiter

logger = structlog.get_logger()


class AlphaVantageService:
    """
    Servicio para obtener datos financieros de Alpha Vantage.
    
    Límites Free Tier:
    - 25 requests/day
    - 5 requests/minute
    
    Premium Tier:
    - Hasta 1200 requests/day
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "ALPHA_VANTAGE_API_KEY", None)
        self.enabled_flag = getattr(settings, "ALPHA_VANTAGE_ENABLED", True)
        
        # El servicio está habilitado solo si:
        # 1. ALPHA_VANTAGE_ENABLED es True
        # 2. Y tenemos una API key
        if not self.enabled_flag:
            logger.info("Alpha Vantage service is disabled via ALPHA_VANTAGE_ENABLED setting")
            self.enabled = False
        elif not self.api_key:
            logger.warning("Alpha Vantage API key not configured - service will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Alpha Vantage service initialized", api_key_prefix=self.api_key[:8] if self.api_key else None)
        
        # Cache para reducir requests (Alpha Vantage tiene límites estrictos)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=15)  # Cache por 15 minutos
    
    async def _make_request(
        self,
        function: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Hacer solicitud a Alpha Vantage API.
        
        Args:
            function: Función de Alpha Vantage (ej: "CURRENCY_EXCHANGE_RATE")
            params: Parámetros adicionales
            use_cache: Usar caché si está disponible
        
        Returns:
            Respuesta de la API
        """
        if not self.enabled:
            raise ValueError("Alpha Vantage API key not configured")
        
        # Verificar caché
        cache_key = f"{function}:{str(sorted((params or {}).items()))}"
        if use_cache and cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if datetime.utcnow() - cached_data["timestamp"] < self._cache_ttl:
                logger.debug("Using cached Alpha Vantage data", function=function)
                return cached_data["data"]
        
        # Usar rate limiter (compartido con Binance para control global)
        await binance_p2p_rate_limiter.wait_for_token()
        
        # Preparar parámetros
        request_params = {
            "function": function,
            "apikey": self.api_key,
            **(params or {})
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=request_params)
                response.raise_for_status()
                data = response.json()
                
                # Verificar errores de Alpha Vantage
                if "Error Message" in data:
                    error_msg = data["Error Message"]
                    logger.error("Alpha Vantage error", error=error_msg, function=function)
                    raise ValueError(f"Alpha Vantage error: {error_msg}")
                
                if "Note" in data:
                    logger.warning("Alpha Vantage rate limit", note=data["Note"])
                    raise ValueError("Alpha Vantage rate limit exceeded")
                
                # Guardar en caché
                if use_cache:
                    self._cache[cache_key] = {
                        "data": data,
                        "timestamp": datetime.utcnow()
                    }
                
                return data
        
        except httpx.HTTPError as e:
            logger.error("Alpha Vantage API HTTP error", error=str(e), function=function)
            raise
        except Exception as e:
            logger.error("Unexpected error in Alpha Vantage", error=str(e), function=function)
            raise
    
    async def get_forex_realtime(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """
        Obtener tasa de cambio Forex en tiempo real.
        
        Args:
            from_currency: Moneda base (ej: "USD")
            to_currency: Moneda destino (ej: "COP")
        
        Returns:
            Tasa de cambio como float, o None si hay error
        """
        if not self.enabled:
            return None
        
        try:
            data = await self._make_request(
                "CURRENCY_EXCHANGE_RATE",
                params={
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper()
                }
            )
            
            exchange_rate_data = data.get("Realtime Currency Exchange Rate", {})
            exchange_rate = exchange_rate_data.get("5. Exchange Rate")
            
            if exchange_rate:
                rate = float(exchange_rate)
                logger.info(
                    "Alpha Vantage forex rate fetched",
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate
                )
                return rate
            
            return None
        
        except Exception as e:
            logger.error(
                "Error fetching Alpha Vantage forex rate",
                error=str(e),
                from_currency=from_currency,
                to_currency=to_currency
            )
            return None
    
    async def get_forex_daily(
        self,
        from_symbol: str,
        to_symbol: str,
        outputsize: str = "compact"
    ) -> Dict[str, Dict[str, float]]:
        """
        Obtener datos históricos diarios de Forex.
        
        Args:
            from_symbol: Moneda base (ej: "USD")
            to_symbol: Moneda destino (ej: "COP")
            outputsize: "compact" (100 días) o "full" (20 años)
        
        Returns:
            {
                "2025-11-09": {
                    "open": 4000.00,
                    "high": 4010.00,
                    "low": 3990.00,
                    "close": 4005.00
                },
                ...
            }
        """
        if not self.enabled:
            return {}
        
        try:
            data = await self._make_request(
                "FX_DAILY",
                params={
                    "from_symbol": from_symbol.upper(),
                    "to_symbol": to_symbol.upper(),
                    "outputsize": outputsize
                },
                use_cache=True  # Cachear datos históricos por más tiempo
            )
            
            time_series = data.get("Time Series FX (Daily)", {})
            
            # Convertir a formato más usable
            result = {}
            for date, values in time_series.items():
                result[date] = {
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0))
                }
            
            logger.info(
                "Alpha Vantage forex daily data fetched",
                from_symbol=from_symbol,
                to_symbol=to_symbol,
                records=len(result)
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "Error fetching Alpha Vantage forex daily data",
                error=str(e),
                from_symbol=from_symbol,
                to_symbol=to_symbol
            )
            return {}
    
    async def get_rsi(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 14
    ) -> Dict[str, float]:
        """
        Obtener RSI (Relative Strength Index).
        
        Args:
            symbol: Par Forex (ej: "USD/COP" o usar formato Alpha Vantage)
            interval: Intervalo ("daily", "weekly", "monthly")
            time_period: Período (default: 14)
        
        Returns:
            {
                "2025-11-09": 65.50,
                "2025-11-08": 62.30,
                ...
            }
        """
        if not self.enabled:
            return {}
        
        try:
            data = await self._make_request(
                "RSI",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": time_period,
                    "series_type": "close"
                }
            )
            
            technical_data = data.get("Technical Analysis: RSI", {})
            
            # Convertir valores a float
            result = {
                date: float(value.get("RSI", 0))
                for date, value in technical_data.items()
            }
            
            logger.debug(
                "Alpha Vantage RSI fetched",
                symbol=symbol,
                records=len(result)
            )
            
            return result
        
        except Exception as e:
            logger.error("Error fetching Alpha Vantage RSI", error=str(e), symbol=symbol)
            return {}
    
    async def get_macd(
        self,
        symbol: str,
        interval: str = "daily"
    ) -> Dict[str, Dict[str, float]]:
        """
        Obtener MACD (Moving Average Convergence Divergence).
        
        Args:
            symbol: Par Forex (ej: "USD/COP")
            interval: Intervalo ("daily", "weekly", "monthly")
        
        Returns:
            {
                "2025-11-09": {
                    "MACD": 0.50,
                    "Signal": 0.45,
                    "Hist": 0.05
                },
                ...
            }
        """
        if not self.enabled:
            return {}
        
        try:
            data = await self._make_request(
                "MACD",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "series_type": "close",
                    "fastperiod": 12,
                    "slowperiod": 26,
                    "signalperiod": 9
                }
            )
            
            technical_data = data.get("Technical Analysis: MACD", {})
            
            result = {
                date: {
                    "MACD": float(value.get("MACD", 0)),
                    "Signal": float(value.get("MACD_Signal", 0)),
                    "Hist": float(value.get("MACD_Hist", 0))
                }
                for date, value in technical_data.items()
            }
            
            logger.debug(
                "Alpha Vantage MACD fetched",
                symbol=symbol,
                records=len(result)
            )
            
            return result
        
        except Exception as e:
            logger.error("Error fetching Alpha Vantage MACD", error=str(e), symbol=symbol)
            return {}
    
    async def get_bollinger_bands(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 20
    ) -> Dict[str, Dict[str, float]]:
        """
        Obtener Bollinger Bands.
        
        Args:
            symbol: Par Forex (ej: "USD/COP")
            interval: Intervalo ("daily", "weekly", "monthly")
            time_period: Período (default: 20)
        
        Returns:
            {
                "2025-11-09": {
                    "Upper": 4050.00,
                    "Middle": 4000.00,
                    "Lower": 3950.00
                },
                ...
            }
        """
        if not self.enabled:
            return {}
        
        try:
            data = await self._make_request(
                "BBANDS",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": time_period,
                    "series_type": "close",
                    "nbdevup": 2,
                    "nbdevdn": 2
                }
            )
            
            technical_data = data.get("Technical Analysis: BBANDS", {})
            
            result = {
                date: {
                    "Upper": float(value.get("Real Upper Band", 0)),
                    "Middle": float(value.get("Real Middle Band", 0)),
                    "Lower": float(value.get("Real Lower Band", 0))
                }
                for date, value in technical_data.items()
            }
            
            logger.debug(
                "Alpha Vantage Bollinger Bands fetched",
                symbol=symbol,
                records=len(result)
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "Error fetching Alpha Vantage Bollinger Bands",
                error=str(e),
                symbol=symbol
            )
            return {}
    
    async def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Obtener indicador técnico genérico.
        
        Args:
            symbol: Símbolo (ej: "USD/COP" o formato Alpha Vantage)
            indicator: Indicador ("RSI", "MACD", "BBANDS", "SMA", "EMA", etc.)
            interval: Intervalo ("daily", "weekly", "monthly")
            time_period: Período de tiempo
            series_type: Tipo de serie ("open", "high", "low", "close")
            **kwargs: Parámetros adicionales específicos del indicador
        
        Returns:
            Datos del indicador técnico
        """
        if not self.enabled:
            return {}
        
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "time_period": time_period,
                "series_type": series_type,
                **kwargs
            }
            
            data = await self._make_request(indicator.upper(), params=params)
            
            # Alpha Vantage retorna los datos con diferentes claves según el indicador
            # Buscar la clave que contiene los datos
            for key in data.keys():
                if "Technical Analysis" in key or "Indicator" in key or indicator.upper() in key:
                    return data[key]
            
            # Si no se encuentra una clave específica, retornar todos los datos
            return data
        
        except Exception as e:
            logger.error(
                "Error fetching Alpha Vantage technical indicator",
                error=str(e),
                symbol=symbol,
                indicator=indicator
            )
            return {}

