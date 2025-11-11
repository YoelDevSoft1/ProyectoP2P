"""
Endpoints para Forex y Alpha Vantage API.
Proporciona acceso a tasas de cambio, datos históricos e indicadores técnicos.
Incluye sistema experto de trading con análisis técnico avanzado.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/forex", tags=["forex"])


def get_alpha_vantage_service():
    """Dependency para obtener servicio Alpha Vantage"""
    try:
        from app.services.alpha_vantage_service import AlphaVantageService
        service = AlphaVantageService()
        # No lanzar excepción aquí, permitir que el servicio se use aunque no esté habilitado
        # Los métodos individuales manejarán el caso cuando no esté habilitado
        return service
    except ImportError:
        # Si no se puede importar, crear un servicio dummy
        class DummyService:
            enabled = False
            async def get_forex_realtime(self, *args, **kwargs):
                return None
            async def get_forex_daily(self, *args, **kwargs):
                return {}
            async def get_rsi(self, *args, **kwargs):
                return {}
            async def get_macd(self, *args, **kwargs):
                return {}
            async def get_bollinger_bands(self, *args, **kwargs):
                return {}
            async def get_technical_indicator(self, *args, **kwargs):
                return {}
        return DummyService()


@router.get("/realtime/{from_currency}/{to_currency}")
async def get_forex_realtime(
    from_currency: str,
    to_currency: str,
    service: Any = Depends(get_alpha_vantage_service)
) -> Dict[str, Any]:
    """
    Obtener tasa de cambio Forex en tiempo real.
    
    Args:
        from_currency: Moneda base (ej: "USD")
        to_currency: Moneda destino (ej: "COP")
    
    Returns:
        Tasa de cambio en tiempo real
    """
    try:
        # Verificar si el servicio está habilitado
        if not service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Alpha Vantage service is not enabled. Please configure ALPHA_VANTAGE_API_KEY in your .env file. Your API key: A828MZ96KHX5QJRF"
            )
        
        rate = await service.get_forex_realtime(from_currency.upper(), to_currency.upper())
        
        if rate is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch exchange rate for {from_currency}/{to_currency}. This may be due to rate limiting or API issues."
            )
        
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "exchange_rate": rate,
            "source": "alpha_vantage",
            "timestamp": None  # Alpha Vantage no siempre proporciona timestamp
        }
    
    except ValueError as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Alpha Vantage rate limit exceeded. Please try again later."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forex rate: {str(e)}")


@router.get("/historical/{from_currency}/{to_currency}")
async def get_forex_historical(
    from_currency: str,
    to_currency: str,
    outputsize: str = Query(default="compact", description="compact (100 días) o full (20 años)"),
    service: Any = Depends(get_alpha_vantage_service)
) -> Dict[str, Any]:
    """
    Obtener datos históricos diarios de Forex.
    
    Args:
        from_currency: Moneda base (ej: "USD")
        to_currency: Moneda destino (ej: "COP")
        outputsize: "compact" (100 días) o "full" (20 años)
    
    Returns:
        Datos históricos diarios (OHLC)
    """
    try:
        if outputsize not in ["compact", "full"]:
            raise HTTPException(
                status_code=400,
                detail="outputsize must be 'compact' or 'full'"
            )
        
        data = await service.get_forex_daily(
            from_currency.upper(),
            to_currency.upper(),
            outputsize
        )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch historical data for {from_currency}/{to_currency}"
            )
        
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "outputsize": outputsize,
            "data_points": len(data),
            "time_series": data,
            "source": "alpha_vantage"
        }
    
    except ValueError as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Alpha Vantage rate limit exceeded. Please try again later."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")


@router.get("/indicators/{symbol}/{indicator}")
async def get_forex_indicator(
    symbol: str,
    indicator: str,
    interval: str = Query(default="daily", description="daily, weekly, monthly"),
    time_period: int = Query(default=14, description="Período de tiempo"),
    service: Any = Depends(get_alpha_vantage_service)
) -> Dict[str, Any]:
    """
    Obtener indicador técnico para par Forex.
    
    Args:
        symbol: Par Forex (ej: "USD/COP" o formato Alpha Vantage)
        indicator: Indicador técnico ("RSI", "MACD", "BBANDS", "SMA", "EMA")
        interval: Intervalo ("daily", "weekly", "monthly")
        time_period: Período de tiempo (default: 14)
    
    Returns:
        Datos del indicador técnico
    """
    try:
        # Verificar si el servicio está habilitado
        if not service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Alpha Vantage service is not enabled. Please configure ALPHA_VANTAGE_API_KEY in your .env file. Your API key: A828MZ96KHX5QJRF"
            )
        
        # Validar intervalo
        valid_intervals = ["daily", "weekly", "monthly", "1min", "5min", "15min", "30min", "60min"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"interval must be one of: {', '.join(valid_intervals)}"
            )
        
        # Validar indicador
        valid_indicators = ["RSI", "MACD", "BBANDS", "SMA", "EMA", "STOCH", "ADX", "CCI"]
        if indicator.upper() not in valid_indicators:
            raise HTTPException(
                status_code=400,
                detail=f"indicator must be one of: {', '.join(valid_indicators)}"
            )
        
        # Obtener datos según el indicador
        if indicator.upper() == "RSI":
            data = await service.get_rsi(symbol, interval, time_period)
        elif indicator.upper() == "MACD":
            data = await service.get_macd(symbol, interval)
        elif indicator.upper() == "BBANDS":
            data = await service.get_bollinger_bands(symbol, interval, time_period)
        else:
            # Para otros indicadores, usar el método genérico
            data = await service.get_technical_indicator(
                symbol,
                indicator.upper(),
                interval,
                time_period,
                series_type="close"
            )
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch {indicator} data for {symbol}"
            )
        
        return {
            "symbol": symbol,
            "indicator": indicator.upper(),
            "interval": interval,
            "time_period": time_period,
            "data_points": len(data),
            "data": data,
            "source": "alpha_vantage"
        }
    
    except ValueError as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="Alpha Vantage rate limit exceeded. Please try again later."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching indicator: {str(e)}")


@router.get("/validate/{fiat}")
async def validate_fx_rate(
    fiat: str,
    service: Any = Depends(get_alpha_vantage_service)
) -> Dict[str, Any]:
    """
    Validar tasa de cambio comparando múltiples fuentes.
    
    Args:
        fiat: Moneda fiat (ej: "COP", "VES", "BRL")
    
    Returns:
        Comparación de tasas de cambio de diferentes fuentes
    """
    try:
        from app.services.fx_service import FXService
        from app.services.trm_service import TRMService
        
        fiat_code = fiat.upper()
        results = {
            "fiat": fiat_code,
            "sources": {},
            "discrepancies": [],
            "alpha_vantage_enabled": service.enabled if hasattr(service, 'enabled') else False
        }
        
        # 1. Alpha Vantage
        if service.enabled:
            try:
                av_rate = await service.get_forex_realtime("USD", fiat_code)
                if av_rate:
                    results["sources"]["alpha_vantage"] = {
                        "rate": av_rate,
                        "status": "available"
                    }
                else:
                    results["sources"]["alpha_vantage"] = {
                        "rate": None,
                        "status": "unavailable",
                        "error": "Rate limit or API error"
                    }
            except Exception as e:
                results["sources"]["alpha_vantage"] = {
                    "rate": None,
                    "status": "error",
                    "error": str(e)
                }
        else:
            results["sources"]["alpha_vantage"] = {
                "rate": None,
                "status": "disabled",
                "error": "Alpha Vantage service is not enabled. Configure ALPHA_VANTAGE_API_KEY in .env",
                "api_key_hint": "A828MZ96KHX5QJRF"
            }
        
        # 2. TRM (solo para COP)
        if fiat_code == "COP":
            try:
                trm_service = TRMService()
                trm_rate = await trm_service.get_current_trm()
                results["sources"]["trm"] = {
                    "rate": trm_rate,
                    "status": "available"
                }
                
                # Comparar con Alpha Vantage
                if "alpha_vantage" in results["sources"] and results["sources"]["alpha_vantage"]["rate"]:
                    av_rate = results["sources"]["alpha_vantage"]["rate"]
                    diff_percent = abs(trm_rate - av_rate) / trm_rate * 100
                    results["discrepancies"].append({
                        "source1": "trm",
                        "source2": "alpha_vantage",
                        "difference_percent": round(diff_percent, 2),
                        "status": "warning" if diff_percent > 2.0 else "ok"
                    })
            except Exception as e:
                results["sources"]["trm"] = {
                    "rate": None,
                    "status": "error",
                    "error": str(e)
                }
        
        # 3. FX Service (usa múltiples fuentes)
        try:
            fx_service = FXService()
            fx_rate = await fx_service.get_rate(fiat_code)
            results["sources"]["fx_service"] = {
                "rate": fx_rate,
                "status": "available"
            }
        except Exception as e:
            results["sources"]["fx_service"] = {
                "rate": None,
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating FX rate: {str(e)}")


# ============================================================================
# SISTEMA EXPERTO DE TRADING FOREX
# ============================================================================

class VirtualOrderRequest(BaseModel):
    """Request para crear orden virtual"""
    pair: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    risk_percent: float = 1.0
    signal_confidence: int = 50


class VirtualOrderResponse(BaseModel):
    """Response de orden virtual"""
    order_id: int
    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    risk_amount: float
    potential_profit: float
    risk_reward_ratio: float
    status: str
    opened_at: str


def get_forex_analysis_service():
    """Dependency para obtener servicio de análisis Forex"""
    try:
        from app.services.forex_analysis_service import ForexAnalysisService
        service = ForexAnalysisService()
        # Verificar si Alpha Vantage está habilitado
        if not service.alpha_vantage.enabled:
            raise HTTPException(
                status_code=503,
                detail="Forex analysis service requires Alpha Vantage API. Please configure ALPHA_VANTAGE_API_KEY in your .env file."
            )
        return service
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Forex analysis service not available: {str(e)}"
        )
    except HTTPException:
        raise  # Re-lanzar HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing Forex analysis service: {str(e)}"
        )


@router.get("/expert/analyze/{pair}")
async def analyze_forex_pair(
    pair: str,
    timeframe: str = Query(default="daily", description="Timeframe: daily, 60min, 15min"),
    service: Any = Depends(get_forex_analysis_service)
) -> Dict[str, Any]:
    """
    Análisis técnico completo de un par Forex.
    Retorna análisis estructurado con indicadores, señales y recomendaciones.
    
    Formato de respuesta según especificación del sistema experto.
    
    Args:
        pair: Par de divisas (ej: "EUR/USD", "EURUSD", "EUR_USD")
        timeframe: Timeframe para el análisis (daily, 60min, 15min)
    """
    try:
        # Normalizar el par (aceptar EUR/USD, EURUSD, EUR_USD)
        normalized_pair = pair.replace("_", "/").replace("-", "/").upper()
        if "/" not in normalized_pair and len(normalized_pair) == 6:
            # Si es EURUSD, convertirlo a EUR/USD
            normalized_pair = f"{normalized_pair[:3]}/{normalized_pair[3:]}"
        
        analysis = await service.analyze_pair(normalized_pair, timeframe)
        
        # Formatear respuesta según especificación
        return {
            "ANÁLISIS_FOREX": {
                "DATETIME": analysis.datetime,
                "PAR_ACTUAL": analysis.pair,
                "DATOS_ACTUALES": {
                    "Precio Actual": analysis.current_price,
                    "Bid": analysis.bid,
                    "Ask": analysis.ask,
                    "Rango 24H": f"{analysis.range_24h['low']:.4f} - {analysis.range_24h['high']:.4f}",
                    "Volatilidad (ATR-20)": f"{analysis.volatility_atr:.1f} pips",
                    "Tendencia 4H": analysis.trend_4h,
                    "Volumen": analysis.volume
                },
                "ANÁLISIS_TÉCNICO": {
                    "RSI(14)": f"{analysis.technical.rsi:.1f}",
                    "RSI_Interpretation": "NEUTRAL-ALCISTA" if 40 < analysis.technical.rsi < 60 else "SOBREVENTA" if analysis.technical.rsi < 35 else "SOBRECOMPRA",
                    "MACD": {
                        "Línea": analysis.technical.macd_line,
                        "Señal": analysis.technical.macd_signal,
                        "Histograma": analysis.technical.macd_hist,
                        "Interpretation": "ALCISTA" if analysis.technical.macd_hist > 0 else "BAJISTA"
                    },
                    "Bandas Bollinger": {
                        "Superior": analysis.technical.bollinger_upper,
                        "Media": analysis.technical.bollinger_middle,
                        "Inferior": analysis.technical.bollinger_lower,
                        "Precio Posición": "Banda media" if analysis.technical.bollinger_lower < analysis.current_price < analysis.technical.bollinger_upper else "Fuera de bandas"
                    },
                    "Soportes": {
                        "Soporte 1": analysis.technical.support1,
                        "Soporte 2": analysis.technical.support2
                    },
                    "Resistencias": {
                        "Resistencia 1": analysis.technical.resistance1,
                        "Resistencia 2": analysis.technical.resistance2
                    },
                    "Medias Móviles": {
                        "SMA 50": analysis.technical.sma_50,
                        "SMA 200": analysis.technical.sma_200,
                        "Tendencia": analysis.technical.trend_4h
                    }
                },
                "SEÑAL_GENERADA": {
                    "TIPO": analysis.signal.type,
                    "CONFIANZA": f"{analysis.signal.confidence}/100",
                    "CONFLUENCIA": analysis.signal.confluence
                },
                "RECOMENDACIÓN_OPERACIÓN": {
                    "Entrada": analysis.signal.entry_price,
                    "Stop Loss": analysis.signal.stop_loss,
                    "Take Profit": analysis.signal.take_profit,
                    "Relación R:R": f"1:{analysis.signal.risk_reward_ratio:.2f}",
                    "Riesgo": f"{analysis.signal.risk_percent}% del capital = ${10000 * analysis.signal.risk_percent / 100:.2f} (en cuenta virtual de $10,000)",
                    "Tamaño de Lote": f"{analysis.signal.lot_size} micro lotes = {analysis.signal.lot_size * 10000:.0f} unidades",
                    "Duración Esperada": f"{analysis.signal.expected_duration_hours}-{analysis.signal.expected_duration_hours * 2} horas",
                    "Probabilidad Éxito": f"{analysis.signal.success_probability * 100:.0f}% (histórico)"
                },
                "CONDICIONES_DE_SALIDA": analysis.exit_conditions
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing forex pair: {str(e)}"
        )


@router.get("/expert/signals")
async def get_trading_signals(
    min_confidence: int = Query(default=70, ge=0, le=100, description="Confianza mínima de señal"),
    service: Any = Depends(get_forex_analysis_service)
) -> Dict[str, Any]:
    """
    Escanear todos los pares principales y generar señales con score > min_confidence.
    Equivalente al comando /SEÑAL_NUEVA del sistema experto.
    """
    try:
        analyses = await service.scan_all_pairs(min_confidence)
        
        signals = []
        for analysis in analyses:
            signals.append({
                "pair": analysis.pair,
                "signal_type": analysis.signal.type,
                "confidence": analysis.signal.confidence,
                "confluence": analysis.signal.confluence,
                "entry_price": analysis.signal.entry_price,
                "stop_loss": analysis.signal.stop_loss,
                "take_profit": analysis.signal.take_profit,
                "risk_reward_ratio": analysis.signal.risk_reward_ratio,
                "current_price": analysis.current_price
            })
        
        return {
            "total_signals": len(signals),
            "min_confidence": min_confidence,
            "signals": signals
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scanning signals: {str(e)}"
        )


@router.post("/expert/virtual-order")
async def create_virtual_order(
    request: VirtualOrderRequest,
    service: Any = Depends(get_forex_analysis_service)
) -> VirtualOrderResponse:
    """
    Crear orden virtual de trading (simulación sin liquidez real).
    Equivalente al comando /EJECUTAR_ORDEN del sistema experto.
    """
    try:
        # Validar dirección
        if request.direction not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="direction must be BUY or SELL")
        
        # Calcular valores
        pip_value = service.calculate_pip_value(request.pair, request.entry_price)
        risk_pips = abs(request.entry_price - request.stop_loss) / pip_value if pip_value > 0 else 0
        reward_pips = abs(request.take_profit - request.entry_price) / pip_value if pip_value > 0 else 0
        
        virtual_capital = 10000
        risk_amount = virtual_capital * (request.risk_percent / 100)
        potential_profit = reward_pips * 10 * request.lot_size
        risk_reward_ratio = reward_pips / risk_pips if risk_pips > 0 else 0
        
        # Validar límites de riesgo
        if request.risk_percent > 2.0:
            raise HTTPException(status_code=400, detail="Risk per trade cannot exceed 2%")
        
        if risk_reward_ratio < 1.5:
            raise HTTPException(status_code=400, detail="Risk:Reward ratio must be at least 1:1.5")
        
        # Generar ID de orden (simulado)
        import time
        order_id = int(time.time() * 1000)
        
        return VirtualOrderResponse(
            order_id=order_id,
            pair=request.pair,
            direction=request.direction,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            lot_size=request.lot_size,
            risk_amount=risk_amount,
            potential_profit=potential_profit,
            risk_reward_ratio=risk_reward_ratio,
            status="OPEN",
            opened_at=time.strftime("%Y-%m-%d %H:%M:%S UTC")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating virtual order: {str(e)}"
        )


@router.get("/expert/session-stats")
async def get_session_stats() -> Dict[str, Any]:
    """
    Obtener estadísticas de sesión de trading.
    Equivalente al comando /REPORTE_DIARIO del sistema experto.
    
    Nota: En una implementación real, esto consultaría la base de datos.
    Por ahora retorna estructura de ejemplo.
    """
    # TODO: Implementar consulta real a base de datos
    return {
        "session_stats": {
            "fecha": "2025-11-09",
            "duracion_minutos": 480,
            "operaciones_totales": 12,
            "operaciones_ganadoras": 8,
            "operaciones_perdedoras": 4,
            "win_rate": 0.667,
            "profit_factor": 2.45,
            "pip_totales": 185,
            "pips_promedio_por_trade": 15.42,
            "mayor_ganancia": 65,
            "mayor_pérdida": -35,
            "sharpe_ratio": 1.82,
            "drawdown_máximo": 3.2,
            "capital_inicial": 10000,
            "capital_final": 10185,
            "rentabilidad_diaria": 1.85
        },
        "próximos_eventos_económicos": [
            {"hora": "13:30 UTC", "impacto": "ALTO", "evento": "NFP USA"}
        ]
    }

