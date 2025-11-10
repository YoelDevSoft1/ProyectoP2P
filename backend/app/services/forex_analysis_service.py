"""
Servicio experto de análisis técnico Forex.
Implementa análisis avanzado con indicadores técnicos, generación de señales
y cálculo de métricas de rendimiento.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

import structlog

from app.services.alpha_vantage_service import AlphaVantageService

logger = structlog.get_logger()


@dataclass
class TechnicalIndicators:
    """Indicadores técnicos calculados"""
    rsi: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    sma_50: float
    sma_200: float
    atr: float
    trend_4h: str  # 'ALCISTA', 'BAJISTA', 'LATERAL'
    trend_d1: str
    support1: float
    support2: float
    resistance1: float
    resistance2: float


@dataclass
class TradingSignal:
    """Señal de trading generada"""
    type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: int  # 0-100
    confluence: List[str]  # Razones de la señal
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    risk_percent: float
    lot_size: float
    expected_duration_hours: int
    success_probability: float


@dataclass
class ForexAnalysis:
    """Análisis completo de un par Forex"""
    pair: str
    current_price: float
    bid: float
    ask: float
    datetime: str
    range_24h: Dict[str, float]
    volatility_atr: float
    trend_4h: str
    volume: str
    technical: TechnicalIndicators
    signal: TradingSignal
    recommendation: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    plan_b: Optional[Dict[str, Any]] = None


class ForexAnalysisService:
    """
    Servicio experto para análisis técnico Forex.
    Implementa las 5 capas del sistema experto de trading.
    """
    
    # Pares Forex principales
    FOREX_PAIRS = [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", 
        "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP"
    ]
    
    # Configuración de riesgo
    MAX_RISK_PER_TRADE = 0.01  # 1% del capital
    MAX_POSITIONS = 5
    MIN_STOP_LOSS_PIPS = 20
    MAX_STOP_LOSS_PIPS = 100
    MIN_RISK_REWARD = 1.5
    MAX_DRAWDOWN_PERCENT = 0.05  # 5%
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageService()
    
    def calculate_pip_value(self, pair: str, price: float) -> float:
        """Calcular valor de un pip para el par (método público)"""
        # Para pares con JPY, 1 pip = 0.01
        if "JPY" in pair:
            return 0.01
        # Para otros pares, 1 pip = 0.0001
        return 0.0001
    
    def _calculate_pip_value(self, pair: str, price: float) -> float:
        """Calcular valor de un pip para el par (método privado, alias)"""
        return self.calculate_pip_value(pair, price)
    
    def _calculate_atr(self, prices: List[Dict[str, float]], period: int = 20) -> float:
        """Calcular ATR (Average True Range)"""
        if len(prices) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(prices)):
            high = prices[i].get("high", 0)
            low = prices[i].get("low", 0)
            prev_close = prices[i-1].get("close", 0)
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if not true_ranges:
            return 0.0
        
        # Calcular ATR como media móvil simple
        atr = sum(true_ranges[-period:]) / min(period, len(true_ranges))
        return atr
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calcular Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return sum(prices[-period:]) / period
    
    def _detect_trend(self, prices: List[float], sma_short: float, sma_long: float) -> str:
        """Detectar tendencia basada en medias móviles"""
        if not prices:
            return "LATERAL"
        
        current_price = prices[-1]
        
        # Tendencia alcista: precio > SMA corta > SMA larga
        if current_price > sma_short > sma_long:
            return "ALCISTA"
        # Tendencia bajista: precio < SMA corta < SMA larga
        elif current_price < sma_short < sma_long:
            return "BAJISTA"
        else:
            return "LATERAL"
    
    def _calculate_support_resistance(
        self, 
        prices: List[Dict[str, float]], 
        current_price: float
    ) -> Tuple[float, float, float, float]:
        """Calcular niveles de soporte y resistencia"""
        if not prices:
            return current_price * 0.985, current_price * 0.97, current_price * 1.015, current_price * 1.03
        
        highs = [p.get("high", current_price) for p in prices[-20:]]
        lows = [p.get("low", current_price) for p in prices[-20:]]
        
        resistance1 = max(highs) if highs else current_price * 1.015
        resistance2 = current_price * 1.03
        support1 = min(lows) if lows else current_price * 0.985
        support2 = current_price * 0.97
        
        return support1, support2, resistance1, resistance2
    
    async def analyze_pair(
        self,
        pair: str,
        timeframe: str = "daily"
    ) -> ForexAnalysis:
        """
        Analizar un par Forex completo.
        
        Args:
            pair: Par Forex (ej: "EUR/USD")
            timeframe: Timeframe ("daily", "60min", "15min")
        
        Returns:
            Análisis completo del par
        """
        try:
            # Parsear par
            base, quote = pair.split("/")
            
            # Obtener datos históricos
            historical_data = await self.alpha_vantage.get_forex_daily(
                base, quote, "compact"
            )
            
            if not historical_data:
                # Si no hay datos, usar valores simulados
                logger.warning(f"No historical data for {pair}, using simulated values")
                return self._create_simulated_analysis(pair)
            
            # Obtener precio actual
            current_rate = await self.alpha_vantage.get_forex_realtime(base, quote)
            if not current_rate:
                # Usar último precio histórico
                latest_date = max(historical_data.keys())
                current_rate = historical_data[latest_date]["close"]
            
            # Convertir datos históricos a lista ordenada
            sorted_dates = sorted(historical_data.keys(), reverse=True)
            prices_list = [historical_data[date] for date in sorted_dates[:100]]
            close_prices = [p["close"] for p in prices_list]
            
            # Calcular indicadores
            rsi_data = await self.alpha_vantage.get_rsi(f"{base}{quote}", timeframe, 14)
            macd_data = await self.alpha_vantage.get_macd(f"{base}{quote}", timeframe)
            bb_data = await self.alpha_vantage.get_bollinger_bands(f"{base}{quote}", timeframe, 20)
            
            # Obtener valores más recientes
            latest_date = sorted_dates[0] if sorted_dates else None
            rsi = 50.0
            if rsi_data and latest_date:
                # Buscar el RSI más cercano
                for date in sorted_dates:
                    if date in rsi_data:
                        rsi = rsi_data[date]
                        break
            
            macd_line = 0.0
            macd_signal = 0.0
            macd_hist = 0.0
            if macd_data and latest_date:
                for date in sorted_dates:
                    if date in macd_data:
                        macd_line = macd_data[date].get("MACD", 0)
                        macd_signal = macd_data[date].get("Signal", 0)
                        macd_hist = macd_data[date].get("Hist", 0)
                        break
            
            bb_upper = current_rate * 1.02
            bb_middle = current_rate
            bb_lower = current_rate * 0.98
            if bb_data and latest_date:
                for date in sorted_dates:
                    if date in bb_data:
                        bb_upper = bb_data[date].get("Upper", bb_upper)
                        bb_middle = bb_data[date].get("Middle", bb_middle)
                        bb_lower = bb_data[date].get("Lower", bb_lower)
                        break
            
            # Calcular SMAs
            sma_50 = self._calculate_sma(close_prices, 50) if len(close_prices) >= 50 else current_rate
            sma_200 = self._calculate_sma(close_prices, 200) if len(close_prices) >= 200 else current_rate
            
            # Calcular ATR
            atr = self._calculate_atr(prices_list, 20)
            pip_value = self._calculate_pip_value(pair, current_rate)
            atr_pips = atr / pip_value if pip_value > 0 else 0
            
            # Detectar tendencias
            trend_4h = self._detect_trend(close_prices, sma_50, sma_200)
            trend_d1 = trend_4h  # Para simplificar, usar misma tendencia
            
            # Calcular soportes y resistencias
            support1, support2, resistance1, resistance2 = self._calculate_support_resistance(
                prices_list, current_rate
            )
            
            # Crear objeto de indicadores
            indicators = TechnicalIndicators(
                rsi=rsi,
                macd_line=macd_line,
                macd_signal=macd_signal,
                macd_hist=macd_hist,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                sma_50=sma_50,
                sma_200=sma_200,
                atr=atr_pips,
                trend_4h=trend_4h,
                trend_d1=trend_d1,
                support1=support1,
                support2=support2,
                resistance1=resistance1,
                resistance2=resistance2
            )
            
            # Generar señal
            signal = self._generate_signal(
                pair, current_rate, indicators, pip_value
            )
            
            # Calcular rango 24h
            if prices_list:
                highs_24h = [p.get("high", current_rate) for p in prices_list[:1]]
                lows_24h = [p.get("low", current_rate) for p in prices_list[:1]]
                range_24h = {
                    "high": max(highs_24h) if highs_24h else current_rate * 1.01,
                    "low": min(lows_24h) if lows_24h else current_rate * 0.99
                }
            else:
                range_24h = {
                    "high": current_rate * 1.01,
                    "low": current_rate * 0.99
                }
            
            # Crear análisis completo
            analysis = ForexAnalysis(
                pair=pair,
                current_price=current_rate,
                bid=current_rate * 0.9998,  # Simular spread
                ask=current_rate * 1.0002,
                datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                range_24h=range_24h,
                volatility_atr=atr_pips,
                trend_4h=trend_4h,
                volume="NORMAL",
                technical=indicators,
                signal=signal,
                recommendation={
                    "entry": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "risk_pips": abs(signal.entry_price - signal.stop_loss) / pip_value,
                    "reward_pips": abs(signal.take_profit - signal.entry_price) / pip_value,
                    "risk_reward_ratio": signal.risk_reward_ratio,
                    "risk_percent": signal.risk_percent,
                    "lot_size": signal.lot_size,
                    "duration_hours": signal.expected_duration_hours,
                    "success_probability": signal.success_probability
                },
                exit_conditions={
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "trailing_stop": "Activar +30 pips de ganancia, mover a breakeven +5 pips",
                    "time_stop": "Cerrar si sin movimiento después de 4H",
                    "news_exit": "Salida inmediata si evento impactante dentro 15 minutos"
                }
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing pair {pair}", error=str(e))
            return self._create_simulated_analysis(pair)
    
    def _generate_signal(
        self,
        pair: str,
        current_price: float,
        indicators: TechnicalIndicators,
        pip_value: float
    ) -> TradingSignal:
        """Generar señal de trading basada en indicadores"""
        score = 50  # Punto de partida neutral
        confluence = []
        
        # Análisis RSI
        if indicators.rsi < 35:
            score += 8
            confluence.append("RSI en zona de sobreventa")
        elif indicators.rsi > 65:
            score -= 8
            confluence.append("RSI en zona de sobrecompra")
        elif 40 < indicators.rsi < 60:
            score += 2
            confluence.append("RSI en zona neutral-alcista")
        
        # Análisis MACD
        if indicators.macd_hist > 0 and indicators.macd_line > indicators.macd_signal:
            score += 10
            confluence.append("MACD: Línea cruzó sobre señal (alcista)")
        elif indicators.macd_hist < 0 and indicators.macd_line < indicators.macd_signal:
            score -= 10
            confluence.append("MACD: Línea cruzó bajo señal (bajista)")
        
        # Análisis Bollinger Bands
        if current_price < indicators.bollinger_lower:
            score += 6
            confluence.append("Precio en banda inferior (sobreventa)")
        elif current_price > indicators.bollinger_upper:
            score -= 6
            confluence.append("Precio en banda superior (sobrecompra)")
        elif indicators.bollinger_lower < current_price < indicators.bollinger_middle:
            score += 4
            confluence.append("Precio en banda media, espacio al alza")
        
        # Análisis de medias móviles
        if current_price > indicators.sma_50 > indicators.sma_200:
            score += 12
            confluence.append("SMA: Precio > SMA50 > SMA200 (alcista)")
        elif current_price < indicators.sma_50 < indicators.sma_200:
            score -= 12
            confluence.append("SMA: Precio < SMA50 < SMA200 (bajista)")
        
        # Análisis de tendencia
        if indicators.trend_4h == "ALCISTA" and indicators.trend_d1 == "ALCISTA":
            score += 12
            confluence.append("Tendencia sincronizada en 4H y D1 (alcista)")
        elif indicators.trend_4h == "BAJISTA" and indicators.trend_d1 == "BAJISTA":
            score -= 12
            confluence.append("Tendencia sincronizada en 4H y D1 (bajista)")
        
        # Análisis de soportes/resistencias
        if indicators.support1 < current_price < indicators.support1 * 1.005:
            score += 6
            confluence.append("Precio sobre soporte validado")
        elif indicators.resistance1 > current_price > indicators.resistance1 * 0.995:
            score -= 6
            confluence.append("Precio cerca de resistencia clave")
        
        # Análisis de volatilidad
        if indicators.atr > 100:
            score -= 5
            confluence.append("Volatilidad elevada - riesgo de latigazos")
        
        # Normalizar score
        score = max(15, min(90, score))
        
        # Determinar tipo de señal
        signal_type = "HOLD"
        if score >= 65:
            signal_type = "BUY"
        elif score <= 40:
            signal_type = "SELL"
        
        # Calcular niveles de entrada, SL y TP
        if signal_type == "BUY":
            entry_price = current_price * 1.0002  # Ask price
            stop_loss_pips = max(self.MIN_STOP_LOSS_PIPS, min(self.MAX_STOP_LOSS_PIPS, int(indicators.atr * 0.8)))
            take_profit_pips = int(stop_loss_pips * 1.5)  # R:R mínimo 1:1.5
            stop_loss = entry_price - (stop_loss_pips * pip_value)
            take_profit = entry_price + (take_profit_pips * pip_value)
        elif signal_type == "SELL":
            entry_price = current_price * 0.9998  # Bid price
            stop_loss_pips = max(self.MIN_STOP_LOSS_PIPS, min(self.MAX_STOP_LOSS_PIPS, int(indicators.atr * 0.8)))
            take_profit_pips = int(stop_loss_pips * 1.5)
            stop_loss = entry_price + (stop_loss_pips * pip_value)
            take_profit = entry_price - (take_profit_pips * pip_value)
        else:
            entry_price = current_price
            stop_loss = current_price
            take_profit = current_price
            stop_loss_pips = 0
            take_profit_pips = 0
        
        # Calcular lot size (asumiendo capital virtual de $10,000)
        virtual_capital = 10000
        risk_amount = virtual_capital * self.MAX_RISK_PER_TRADE
        lot_size = risk_amount / (stop_loss_pips * 10) if stop_loss_pips > 0 else 0.1
        
        # Calcular relación riesgo-recompensa
        risk_reward = take_profit_pips / stop_loss_pips if stop_loss_pips > 0 else 0
        
        # Probabilidad de éxito basada en score
        success_probability = score / 100.0
        
        return TradingSignal(
            type=signal_type,
            confidence=score,
            confluence=confluence[:3],  # Top 3 razones
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            risk_percent=self.MAX_RISK_PER_TRADE * 100,
            lot_size=round(lot_size, 2),
            expected_duration_hours=2 if signal_type != "HOLD" else 0,
            success_probability=success_probability
        )
    
    def _create_simulated_analysis(self, pair: str) -> ForexAnalysis:
        """Crear análisis simulado cuando no hay datos disponibles"""
        current_price = 1.0850 if "EUR" in pair else 1.2750 if "GBP" in pair else 145.50
        
        indicators = TechnicalIndicators(
            rsi=62.0,
            macd_line=0.50,
            macd_signal=0.45,
            macd_hist=0.05,
            bollinger_upper=current_price * 1.02,
            bollinger_middle=current_price,
            bollinger_lower=current_price * 0.98,
            sma_50=current_price * 0.998,
            sma_200=current_price * 0.99,
            atr=45.0,
            trend_4h="ALCISTA",
            trend_d1="ALCISTA",
            support1=current_price * 0.985,
            support2=current_price * 0.97,
            resistance1=current_price * 1.015,
            resistance2=current_price * 1.03
        )
        
        pip_value = self._calculate_pip_value(pair, current_price)
        signal = self._generate_signal(pair, current_price, indicators, pip_value)
        
        return ForexAnalysis(
            pair=pair,
            current_price=current_price,
            bid=current_price * 0.9998,
            ask=current_price * 1.0002,
            datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            range_24h={"high": current_price * 1.01, "low": current_price * 0.99},
            volatility_atr=45.0,
            trend_4h="ALCISTA",
            volume="NORMAL",
            technical=indicators,
            signal=signal,
            recommendation={
                "entry": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "risk_pips": 40,
                "reward_pips": 60,
                "risk_reward_ratio": 1.5,
                "risk_percent": 1.0,
                "lot_size": 0.25,
                "duration_hours": 2,
                "success_probability": 0.75
            },
            exit_conditions={
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "trailing_stop": "Activar +30 pips de ganancia",
                "time_stop": "Cerrar si sin movimiento después de 4H",
                "news_exit": "Salida inmediata si evento impactante"
            }
        )
    
    async def scan_all_pairs(self, min_confidence: int = 70) -> List[ForexAnalysis]:
        """Escanear todos los pares y generar señales con score > min_confidence"""
        analyses = []
        for pair in self.FOREX_PAIRS:
            try:
                analysis = await self.analyze_pair(pair)
                if analysis.signal.confidence >= min_confidence:
                    analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error scanning pair {pair}", error=str(e))
                continue
        
        # Ordenar por confianza descendente
        analyses.sort(key=lambda x: x.signal.confidence, reverse=True)
        return analyses

