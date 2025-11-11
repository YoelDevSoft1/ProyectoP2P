"""
Endpoints de análisis y analytics avanzados.
Incluye: Triangle Arbitrage, Liquidez, ML Predictions, Risk Management
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.models.trade import Trade, TradeStatus
from app.models.price_history import PriceHistory
from app.models.alert import Alert, AlertType

# Servicios avanzados
from app.services.triangle_arbitrage_service import TriangleArbitrageService
from app.services.liquidity_analysis_service import LiquidityAnalysisService
from app.services.ml_service import AdvancedMLService
from app.services.risk_management_service import RiskManagementService
from app.services.competitive_pricing_service import CompetitivePricingService
from app.services.xpu_monitor_service import get_xpu_monitor_service
from app.ml.gpu_utils import get_gpu_info

router = APIRouter()

# Inicializar servicios
triangle_service = TriangleArbitrageService()
liquidity_service = LiquidityAnalysisService()
ml_service = AdvancedMLService()
risk_service = RiskManagementService()
pricing_service = CompetitivePricingService()


def _get_price_from_history(entry: PriceHistory) -> float:
    """
    PriceHistory almacena bid/ask/avg; este helper obtiene un valor usable.
    Prioriza avg_price, luego bid_price, luego ask_price.
    """
    candidates = [
        getattr(entry, "avg_price", None),
        getattr(entry, "bid_price", None),
        getattr(entry, "ask_price", None),
    ]
    for value in candidates:
        if value is not None and value > 0:
            return float(value)
    for value in candidates:
        if value not in (None, 0):
            return float(value)
    return 0.0


def _get_volume_from_history(entry: PriceHistory) -> float:
    """Devuelve el volumen disponible (volume_24h) o 0 si no existe."""
    volume = getattr(entry, "volume_24h", None)
    return float(volume) if volume not in (None, "") else 0.0


@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    only_real_trades: bool = Query(default=False, description="Solo mostrar trades reales (con binance_order_id)")
):
    """
    Datos principales para el dashboard.
    
    Args:
        only_real_trades: Si es True, solo muestra trades reales (con binance_order_id).
                         Si es False, muestra todos los trades (reales y simulados).
    """
    # Últimas 24 horas
    last_24h = datetime.utcnow() - timedelta(hours=24)
    last_7d = datetime.utcnow() - timedelta(days=7)

    # Base query para trades
    base_query = db.query(Trade)
    
    # Filtrar solo trades reales si se solicita
    if only_real_trades:
        base_query = base_query.filter(Trade.binance_order_id.isnot(None))

    # Trades de hoy
    trades_today = base_query.filter(
        Trade.created_at >= last_24h
    ).all()

    completed_today = [t for t in trades_today if t.status == TradeStatus.COMPLETED]

    # Profit de hoy
    profit_today = sum(t.actual_profit or 0 for t in completed_today)

    # Trades de la semana
    trades_week = base_query.filter(
        Trade.created_at >= last_7d,
        Trade.status == TradeStatus.COMPLETED
    ).all()

    profit_week = sum(t.actual_profit or 0 for t in trades_week)

    # Alertas no leídas
    unread_alerts = db.query(Alert).filter(
        Alert.is_read == False
    ).count()

    # Trade más reciente
    latest_trade = db.query(Trade).order_by(
        Trade.created_at.desc()
    ).first()

    return {
        "today": {
            "total_trades": len(trades_today),
            "completed_trades": len(completed_today),
            "total_profit": round(profit_today, 2),
            "average_profit": round(profit_today / len(completed_today), 2) if completed_today else 0
        },
        "week": {
            "total_trades": len(trades_week),
            "total_profit": round(profit_week, 2),
            "average_profit": round(profit_week / len(trades_week), 2) if trades_week else 0
        },
        "alerts": {
            "unread": unread_alerts
        },
        "latest_trade": {
            "id": latest_trade.id,
            "type": latest_trade.trade_type.value,
            "status": latest_trade.status.value,
            "fiat": latest_trade.fiat,
            "amount": latest_trade.crypto_amount,
            "created_at": latest_trade.created_at.isoformat()
        } if latest_trade else None
    }


@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Métricas de rendimiento del bot.
    """
    since = datetime.utcnow() - timedelta(days=days)

    trades = db.query(Trade).filter(
        Trade.created_at >= since
    ).all()

    completed = [t for t in trades if t.status == TradeStatus.COMPLETED]
    automated = [t for t in completed if t.is_automated]

    # Calcular métricas
    total_profit = sum(t.actual_profit or 0 for t in completed)
    total_volume = sum(t.crypto_amount for t in completed)

    # Profit por día
    daily_profit = {}
    for trade in completed:
        date = trade.created_at.date().isoformat()
        if date not in daily_profit:
            daily_profit[date] = 0
        daily_profit[date] += trade.actual_profit or 0

    # Win rate
    successful_trades = len(completed)
    total_attempts = len(trades)
    win_rate = (successful_trades / total_attempts * 100) if total_attempts > 0 else 0

    return {
        "period_days": days,
        "total_trades": len(trades),
        "completed_trades": len(completed),
        "automated_trades": len(automated),
        "total_profit": round(total_profit, 2),
        "total_volume_usd": round(total_volume, 2),
        "win_rate": round(win_rate, 2),
        "average_profit_per_trade": round(total_profit / len(completed), 2) if completed else 0,
        "automation_rate": round(len(automated) / len(completed) * 100, 2) if completed else 0,
        "daily_profit": {k: round(v, 2) for k, v in sorted(daily_profit.items())}
    }


@router.get("/alerts")
async def get_alerts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    alert_type: Optional[AlertType] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener alertas del sistema.
    """
    query = db.query(Alert)

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type.value,
                "priority": a.priority.value,
                "title": a.title,
                "message": a.message,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.post("/alerts/{alert_id}/read")
async def mark_alert_as_read(alert_id: int, db: Session = Depends(get_db)):
    """Marcar alerta como leída"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    alert.read_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "alert_id": alert_id}


@router.post("/test-notification")
async def test_notification():
    """
    Enviar notificación de prueba por Telegram.
    Útil para verificar que la configuración del bot está correcta.
    """
    from app.services.telegram_service import telegram_service

    # Probar conexión
    test_result = await telegram_service.test_connection()
    
    if test_result.get("status") == "success":
        return {
            "status": "success",
            "message": "Notificación de prueba enviada exitosamente",
            "details": test_result
        }
    else:
        return {
            "status": "error",
            "message": test_result.get("message", "Error desconocido"),
            "details": test_result
        }


# ============================================================================
# TRIANGLE ARBITRAGE ENDPOINTS
# ============================================================================

@router.get("/triangle-arbitrage/analyze")
async def analyze_triangle_arbitrage(
    initial_amount: float = Query(200000, description="Cantidad inicial en COP"),
):
    """
    Analiza oportunidad de arbitraje triangular COP -> USDT -> VES
    Este es el análisis más sofisticado que busca ganancias en ciclos de múltiples conversiones
    """
    result = await triangle_service.analyze_triangle_opportunity(initial_amount)
    return result


@router.get("/triangle-arbitrage/find-all-routes")
async def find_all_triangle_routes(
    assets: List[str] = Query(["USDT", "BTC"], description="Assets a analizar"),
    fiats: List[str] = Query(["COP", "VES"], description="Fiats a analizar"),
):
    """
    Busca TODAS las rutas de arbitraje triangular posibles
    Ejemplo: COP -> USDT -> VES, VES -> BTC -> COP, etc.
    """
    result = await triangle_service.find_best_triangle_routes(assets, fiats)
    return {
        "success": True,
        "total_opportunities": len(result),
        "opportunities": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/triangle-arbitrage/optimal-strategy")
async def get_optimal_triangle_strategy():
    """
    Retorna la MEJOR estrategia triangular considerando:
    - ROI máximo, Liquidez disponible, Riesgo, Tiempo de ejecución
    """
    result = await triangle_service.get_optimal_triangle_strategy()
    return result


# ============================================================================
# LIQUIDITY ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/liquidity/market-depth")
async def analyze_market_depth(
    asset: str = Query("USDT", description="Asset a analizar"),
    fiat: str = Query("COP", description="Fiat currency"),
    depth_levels: int = Query(20, description="Niveles de profundidad"),
):
    """
    Análisis completo de profundidad de mercado
    Retorna: Distribución de liquidez, Spread, Walls, Imbalance, Liquidity score
    """
    result = await liquidity_service.analyze_market_depth(asset, fiat, depth_levels)
    return result


@router.get("/liquidity/detect-market-makers")
async def detect_market_makers(
    asset: str = Query("USDT"),
    fiat: str = Query("COP"),
):
    """
    Detecta posibles market makers en el orderbook
    Market makers proveen liquidez constante con spreads tight
    """
    result = await liquidity_service.detect_market_makers(asset, fiat)
    return result


@router.get("/liquidity/slippage-estimate")
async def estimate_slippage(
    asset: str = Query("USDT"),
    fiat: str = Query("COP"),
    trade_type: str = Query("BUY", description="BUY or SELL"),
    target_amount_usd: float = Query(1000, description="Target amount in USD"),
):
    """
    Estima el slippage esperado para una orden de cierto tamaño
    Slippage = diferencia entre precio esperado y precio real de ejecución
    """
    result = await liquidity_service.calculate_slippage_estimate(
        asset, fiat, trade_type, target_amount_usd
    )
    return result


# ============================================================================
# MACHINE LEARNING ENDPOINTS
# ============================================================================

@router.get("/ml/predict-spread")
async def predict_future_spread(
    asset: str = Query("USDT"),
    fiat: str = Query("COP"),
    horizon_minutes: int = Query(10, description="Prediction horizon in minutes"),
):
    """
    Predice el spread futuro basado en condiciones actuales del mercado
    Usa Machine Learning para predecir cómo evolucionará el spread
    """
    # Obtener condiciones actuales del mercado
    depth = await liquidity_service.analyze_market_depth(asset, fiat)

    if not depth.get("success"):
        raise HTTPException(status_code=400, detail="Cannot analyze current market")

    current_market_data = {
        "current_spread": depth["spread"]["percentage"],
        "bid_volume": depth["bids"]["total_volume"],
        "ask_volume": depth["asks"]["total_volume"],
        "bid_ask_ratio": depth["bids"]["total_volume"] / max(depth["asks"]["total_volume"], 1),
        "volatility": 0,
        "momentum": 0,
        "num_orders_bid": depth["bids"]["price_levels"],
        "num_orders_ask": depth["asks"]["price_levels"],
    }

    result = ml_service.predict_future_spread(current_market_data, horizon_minutes)
    return result


@router.post("/ml/classify-opportunity")
async def classify_opportunity(
    opportunity_data: dict,
):
    """
    Clasifica una oportunidad de trading en: EXCELLENT, GOOD, MODERATE, POOR
    Basado en ML y análisis de factores múltiples
    """
    result = ml_service.classify_opportunity(opportunity_data)
    return result


@router.get("/ml/optimal-timing")
async def predict_optimal_timing(
    asset: str = Query("USDT"),
    fiat: str = Query("COP"),
):
    """
    Predice el timing óptimo para ejecutar una operación
    Analiza patrones históricos por hora del día y condiciones actuales
    """
    depth = await liquidity_service.analyze_market_depth(asset, fiat)

    market_conditions = {
        "current_spread": depth.get("spread", {}).get("percentage", 0),
        "liquidity": depth.get("bids", {}).get("total_volume", 0) + depth.get("asks", {}).get("total_volume", 0),
        "volatility": 0,
    }

    result = ml_service.predict_optimal_timing(market_conditions)
    return result


@router.post("/ml/train-spread-predictor")
async def train_ml_spread_predictor(
    db: Session = Depends(get_db)
):
    """
    Entrenar modelo ML (Gradient Boosting) para predicción de spreads.
    Este modelo es usado por el endpoint /ml/predict-spread.
    """
    try:
        # Obtener datos históricos
        price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se necesitan al menos 100 registros, se encontraron {len(price_history)}"
            )
        
        # Preparar datos históricos en el formato esperado por ml_service
        historical_data = []
        for ph in price_history:
            # Obtener depth data si está disponible (simulado para datos históricos)
            price = _get_price_from_history(ph)
            volume = _get_volume_from_history(ph)
            
            # Calcular spread si no está disponible
            spread = ph.spread or 0
            if spread == 0 and ph.bid_price and ph.ask_price:
                spread = ((ph.ask_price - ph.bid_price) / price) * 100 if price > 0 else 0
            
            historical_data.append({
                "spread": spread,
                "bid_volume": volume * 0.5,  # Estimación: mitad bid, mitad ask
                "ask_volume": volume * 0.5,
                "bid_ask_ratio": 1.0,  # Por defecto
                "volatility": 0,  # Se calcularía con datos históricos
                "momentum": 0,  # Se calcularía con datos históricos
                "num_orders_bid": 10,  # Valor por defecto
                "num_orders_ask": 10,  # Valor por defecto
                "timestamp": ph.timestamp,
            })
        
        # Entrenar modelo
        result = ml_service.train_spread_predictor(historical_data)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error desconocido al entrenar el modelo")
            )
        
        return {
            "status": "success",
            "message": "Modelo ML (Gradient Boosting) entrenado exitosamente",
            "model_type": result.get("model", "Gradient Boosting Regressor"),
            "train_score": result.get("train_score"),
            "test_score": result.get("test_score"),
            "samples": result.get("samples"),
            "timestamp": result.get("timestamp"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training ML spread predictor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")


# ============================================================================
# RISK MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/risk/calculate-var")
async def calculate_var(
    returns: List[float],
    confidence_level: float = Query(0.95, description="Confidence level (0.95 or 0.99)"),
    time_horizon_days: int = Query(1, description="Time horizon in days"),
):
    """
    Calcula Value at Risk (VaR)
    VaR es la pérdida máxima esperada con un nivel de confianza dado
    """
    result = risk_service.calculate_var(returns, confidence_level, time_horizon_days)
    return result


@router.post("/risk/calculate-sharpe")
async def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: Optional[float] = None,
):
    """
    Calcula Sharpe Ratio - retorno ajustado por riesgo
    Sharpe > 1 es bueno, > 2 es muy bueno, > 3 es excelente
    """
    result = risk_service.calculate_sharpe_ratio(returns, risk_free_rate)
    return result


@router.post("/risk/calculate-sortino")
async def calculate_sortino_ratio(
    returns: List[float],
    target_return: float = Query(0.0, description="Target return"),
):
    """
    Calcula Sortino Ratio
    Similar al Sharpe pero solo penaliza volatilidad negativa
    """
    result = risk_service.calculate_sortino_ratio(returns, target_return=target_return)
    return result


@router.post("/risk/calculate-drawdown")
async def calculate_maximum_drawdown(
    equity_curve: List[float],
):
    """
    Calcula Maximum Drawdown - pérdida máxima desde un pico
    """
    result = risk_service.calculate_maximum_drawdown(equity_curve)
    return result


@router.post("/risk/trading-metrics")
async def calculate_trading_metrics(
    trades: List[dict],
):
    """
    Calcula métricas comprehensivas de trading:
    Win rate, Profit factor, Average win/loss, R:R ratio, Expectancy
    """
    result = risk_service.calculate_trading_metrics(trades)
    return result


@router.get("/risk/kelly-criterion")
async def calculate_kelly_criterion(
    win_rate: float = Query(..., description="Win rate (0-1)"),
    avg_win: float = Query(..., description="Average win"),
    avg_loss: float = Query(..., description="Average loss (positive number)"),
):
    """
    Calcula Kelly Criterion para position sizing óptimo
    Kelly te dice qué % de tu capital deberías arriesgar por trade
    """
    result = risk_service.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
    return result


@router.post("/risk/comprehensive-assessment")
async def comprehensive_risk_assessment(
    returns: List[float],
    equity_curve: List[float],
    trades: List[dict],
    current_position_size: float,
    total_capital: float,
):
    """
    Evaluación COMPREHENSIVA de riesgo
    Combina TODAS las métricas de riesgo en un solo análisis
    """
    result = risk_service.comprehensive_risk_assessment(
        returns, equity_curve, trades, current_position_size, total_capital
    )
    return result


# ============================================================================
# DASHBOARD SUMMARY ENDPOINTS
# ============================================================================

@router.get("/advanced-summary")
async def get_advanced_dashboard_summary():
    """
    Retorna un resumen completo avanzado para el dashboard principal
    Combina: Triangle arbitrage, Liquidez, Predicciones ML, Métricas de riesgo
    """
    try:
        # Triangle arbitrage
        triangle_opp = await triangle_service.get_optimal_triangle_strategy()

        # Liquidez COP y VES
        liquidity_cop = await liquidity_service.analyze_market_depth("USDT", "COP", 10)
        liquidity_ves = await liquidity_service.analyze_market_depth("USDT", "VES", 10)

        # Market makers
        mm_cop = await liquidity_service.detect_market_makers("USDT", "COP")
        mm_ves = await liquidity_service.detect_market_makers("USDT", "VES")

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "triangle_arbitrage": {
                "best_opportunity": triangle_opp.get("best_opportunity"),
                "total_opportunities": triangle_opp.get("total_opportunities_found", 0),
                "recommendation": triangle_opp.get("recommendation", ""),
            },
            "liquidity": {
                "cop": {
                    "score": liquidity_cop.get("liquidity_score", {}).get("score", 0),
                    "rating": liquidity_cop.get("liquidity_score", {}).get("rating", "UNKNOWN"),
                    "spread": liquidity_cop.get("spread", {}).get("percentage", 0),
                    "market_makers": mm_cop.get("market_makers_detected", 0),
                    "market_quality": liquidity_cop.get("market_quality", {}).get("rating", "UNKNOWN"),
                },
                "ves": {
                    "score": liquidity_ves.get("liquidity_score", {}).get("score", 0),
                    "rating": liquidity_ves.get("liquidity_score", {}).get("rating", "UNKNOWN"),
                    "spread": liquidity_ves.get("spread", {}).get("percentage", 0),
                    "market_makers": mm_ves.get("market_makers_detected", 0),
                    "market_quality": liquidity_ves.get("market_quality", {}).get("rating", "UNKNOWN"),
                },
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-opportunities")
async def get_top_opportunities(
    limit: int = Query(10, description="Number of opportunities to return"),
):
    """
    Retorna las top N oportunidades ordenadas por ROI
    Combina: Triangle arbitrage, Spot to P2P, Simple P2P spread
    """
    try:
        # Triangle arbitrage
        triangle_opps = await triangle_service.find_best_triangle_routes()

        # Tomar top N
        top_opportunities = triangle_opps[:limit]

        return {
            "success": True,
            "total_opportunities": len(triangle_opps),
            "opportunities": top_opportunities,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPETITIVE PRICING ENDPOINTS
# ============================================================================

@router.get("/pricing/market-trm")
async def get_market_trm(
    asset: str = Query("USDT", description="Asset to analyze"),
    fiat: str = Query("COP", description="Fiat currency"),
    sample_size: int = Query(20, ge=5, le=50, description="Number of orders to sample"),
):
    """
    Calcula la TRM de mercado basada en precios P2P reales de Binance.

    Usa VWAP (Volume-Weighted Average Price) para obtener un precio más
    preciso que considera el volumen de cada orden.

    Returns:
        - average_price: Precio medio simple
        - vwap_price: VWAP (más preciso)
        - median_price: Precio mediano
        - p25/p75: Percentiles 25 y 75
        - spread: Diferencia entre buy y sell
        - market_depth: Análisis de liquidez
    """
    try:
        result = await pricing_service.calculate_market_trm(asset, fiat, sample_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating market TRM: {str(e)}")


@router.get("/pricing/competitive-prices")
async def get_competitive_prices(
    asset: str = Query("USDT", description="Asset to trade"),
    fiat: str = Query("COP", description="Fiat currency"),
    our_margin_pct: Optional[float] = Query(None, ge=0, le=10, description="Our margin percentage (0-10%)"),
):
    """
    Calcula precios competitivos para NUESTRAS operaciones P2P.

    Estrategia:
    1. Analizar precios del mercado P2P
    2. Posicionarnos MEJOR que el promedio (para ganar volumen)
    3. Mantener margen de ganancia suficiente
    4. Considerar TODAS las comisiones de Binance

    Returns:
        - our_buy_price: Precio al que NOSOTROS compramos USDT (pagar más = mejor)
        - our_sell_price: Precio al que NOSOTROS vendemos USDT (cobrar menos = mejor)
        - market_buy_avg: Promedio del mercado para compras
        - market_sell_avg: Promedio del mercado para ventas
        - competitiveness_score: Qué tan competitivos somos (0-100)
        - profit_analysis: Análisis de profit con todas las fees
    """
    try:
        result = await pricing_service.calculate_competitive_prices(asset, fiat, our_margin_pct)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating competitive prices: {str(e)}")


@router.get("/pricing/strategy-summary")
async def get_pricing_strategy_summary(
    asset: str = Query("USDT", description="Asset to trade"),
    fiat: str = Query("COP", description="Fiat currency"),
):
    """
    Retorna un resumen completo de la estrategia de pricing.

    Combina:
    1. Market TRM analysis
    2. Competitive pricing recommendations
    3. Fee analysis
    4. Risk assessment
    5. Actionable recommendations

    Este endpoint es ideal para el dashboard principal.
    """
    try:
        result = await pricing_service.get_pricing_strategy_summary(asset, fiat)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pricing strategy: {str(e)}")


# ============================================================================
# Deep Learning Endpoints (PyTorch - CPU)
# ============================================================================

try:
    from app.ml import DLModelTrainer, DLPredictor, get_gpu_info
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False


@router.get("/dl/model-info")
async def get_dl_model_info():
    """
    Obtener información sobre el estado de los modelos de Deep Learning.
    Incluye información de GPU/CPU disponible.
    """
    if not DL_AVAILABLE:
        return {
            "available": False,
            "error": "Deep Learning no disponible. PyTorch no está instalado."
        }
    
    try:
        gpu_info = get_gpu_info()
        return {
            "available": True,
            "device": gpu_info.get("device", "cpu"),
            "gpu_available": gpu_info.get("available", False),
            "intel_extension": gpu_info.get("intel_extension", False),
            "message": "Deep Learning disponible - usando CPU"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.post("/dl/train-price-predictor")
async def train_price_predictor(
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelo LSTM para predicción de precios.
    Usa CPU automáticamente (GPU si está disponible).
    """
    if not DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        # Obtener datos históricos
        price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se necesitan al menos 100 registros, se encontraron {len(price_history)}"
            )
        
        # Convertir a DataFrame
        import pandas as pd
        data = pd.DataFrame([
            {
                "price": _get_price_from_history(ph),
                "spread": ph.spread or 0,
                "volume": _get_volume_from_history(ph),
                "timestamp": ph.timestamp,
                "hour": ph.timestamp.hour,
                "day_of_week": ph.timestamp.weekday(),
            }
            for ph in price_history
        ])
        
        # Calcular features adicionales
        data['ma_5'] = data['price'].rolling(window=5, min_periods=1).mean()
        data['ma_20'] = data['price'].rolling(window=20, min_periods=1).mean()
        data['volatility'] = data['price'].rolling(window=10, min_periods=1).std().fillna(0)
        data['price_change'] = data['price'].diff().fillna(0)
        data['spread_ma'] = data['spread'].rolling(window=5, min_periods=1).mean().fillna(0)
        
        # Entrenar modelo
        trainer = DLModelTrainer()
        result = trainer.train_price_predictor(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")


class PredictPriceRequest(BaseModel):
    sequence: List[List[float]]


@router.post("/dl/predict-price")
async def predict_price_dl(
    request: PredictPriceRequest,
    db: Session = Depends(get_db)
):
    """
    Predecir precio usando modelo LSTM entrenado.
    
    Args:
        sequence: Lista de listas con features. Debe ser una secuencia de 10 timesteps.
                 Cada timestep debe tener las mismas features usadas en el entrenamiento.
    """
    if not DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        import numpy as np
        sequence_array = np.array(request.sequence)
        
        # Validar forma
        if len(sequence_array.shape) != 2:
            raise HTTPException(
                status_code=400,
                detail=f"Secuencia debe ser 2D (timesteps, features). Recibido: {sequence_array.shape}"
            )
        
        if sequence_array.shape[0] != 10:
            raise HTTPException(
                status_code=400,
                detail=f"Secuencia debe tener 10 timesteps. Recibido: {sequence_array.shape[0]}"
            )
        
        predictor = DLPredictor()
        prediction = predictor.predict_price(sequence_array)
        
        if prediction is None:
            raise HTTPException(
                status_code=404,
                detail="Modelo no encontrado. Entrena el modelo primero usando POST /api/v1/analytics/dl/train-price-predictor"
            )
        
        return {
            "predicted_price": prediction,
            "device": str(predictor.device),
            "sequence_shape": sequence_array.shape
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting: {str(e)}")


@router.post("/dl/train-spread-predictor")
async def train_spread_predictor(
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelo GRU para predicción de spreads.
    """
    if not DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        # Similar a train_price_predictor
        price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se necesitan al menos 100 registros."
            )
        
        import pandas as pd
        data = pd.DataFrame([
            {
                "spread": ph.spread or 0,
                "price": _get_price_from_history(ph),
                "volume": _get_volume_from_history(ph),
                "timestamp": ph.timestamp,
                "hour": ph.timestamp.hour,
                "day_of_week": ph.timestamp.weekday(),
            }
            for ph in price_history
        ])
        
        data['ma_5'] = data['price'].rolling(window=5, min_periods=1).mean()
        data['ma_20'] = data['price'].rolling(window=20, min_periods=1).mean()
        data['volatility'] = data['price'].rolling(window=10, min_periods=1).std().fillna(0)
        
        trainer = DLModelTrainer()
        result = trainer.train_spread_predictor(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")


@router.post("/dl/train-anomaly-detector")
async def train_anomaly_detector(
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar autoencoder para detección de anomalías.
    """
    if not DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se necesitan al menos 100 registros."
            )
        
        import pandas as pd
        data = pd.DataFrame([
            {
                "price": _get_price_from_history(ph),
                "spread": ph.spread or 0,
                "volume": _get_volume_from_history(ph),
                "timestamp": ph.timestamp,
                "hour": ph.timestamp.hour,
                "day_of_week": ph.timestamp.weekday(),
            }
            for ph in price_history
        ])
        
        data['ma_5'] = data['price'].rolling(window=5, min_periods=1).mean()
        data['ma_20'] = data['price'].rolling(window=20, min_periods=1).mean()
        data['volatility'] = data['price'].rolling(window=10, min_periods=1).std().fillna(0)
        data['price_change'] = data['price'].diff().fillna(0)
        data['spread_ma'] = data['spread'].rolling(window=5, min_periods=1).mean().fillna(0)
        
        trainer = DLModelTrainer()
        result = trainer.train_anomaly_detector(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")


@router.post("/dl/detect-anomalies")
async def detect_anomalies_dl(
    threshold: float = Query(default=0.1, ge=0.01, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Detectar anomalías en datos recientes usando autoencoder.
    """
    if not DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        # Obtener datos recientes
        recent_history = db.query(PriceHistory).order_by(
            PriceHistory.timestamp.desc()
        ).limit(100).all()
        
        if len(recent_history) < 10:
            raise HTTPException(
                status_code=400,
                detail="No hay suficientes datos recientes."
            )
        
        import pandas as pd
        import numpy as np
        
        data = pd.DataFrame([
            {
                "price": _get_price_from_history(ph),
                "spread": ph.spread or 0,
                "volume": _get_volume_from_history(ph),
                "hour": ph.timestamp.hour,
                "day_of_week": ph.timestamp.weekday(),
            }
            for ph in recent_history
        ])
        
        data['ma_5'] = data['price'].rolling(window=5, min_periods=1).mean()
        data['ma_20'] = data['price'].rolling(window=20, min_periods=1).mean()
        data['volatility'] = data['price'].rolling(window=10, min_periods=1).std().fillna(0)
        data['price_change'] = data['price'].diff().fillna(0)
        data['spread_ma'] = data['spread'].rolling(window=5, min_periods=1).mean().fillna(0)
        
        data_array = data[['price', 'spread', 'volume', 'ma_5', 'ma_20', 
                           'volatility', 'price_change', 'hour', 'day_of_week', 'spread_ma']].values
        
        predictor = DLPredictor()
        anomalies = predictor.detect_anomalies(data_array, threshold=threshold)
        
        # Combinar con timestamps
        results = []
        for i, (ph, is_anomaly) in enumerate(zip(recent_history, anomalies)):
            results.append({
                "timestamp": ph.timestamp.isoformat(),
                "price": _get_price_from_history(ph),
                "spread": ph.spread,
                "is_anomaly": is_anomaly
            })
        
        return {
            "anomalies_detected": sum(anomalies),
            "total_samples": len(anomalies),
            "threshold": threshold,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


# ============================================================================
# Advanced Deep Learning Endpoints (Latest Innovations)
# ============================================================================

try:
    from app.ml import AdvancedDLTrainer, AdvancedFeatureEngineer, ProfitMetricsCalculator, BacktestingService
    ADVANCED_DL_AVAILABLE = True
except ImportError:
    ADVANCED_DL_AVAILABLE = False


@router.post("/dl/advanced/train-transformer")
async def train_advanced_transformer(
    symbol: str = Query(default="BTC-USD", description="Símbolo de Yahoo Finance (ej: BTC-USD, ETH-USD, USDCOP=X)"),
    period: str = Query(default="2y", description="Período (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)"),
    interval: str = Query(default="1d", description="Intervalo (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)"),
    use_yahoo: bool = Query(default=True, description="Usar Yahoo Finance (True) o datos de BD (False)"),
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.0001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelo Transformer avanzado con las últimas técnicas.
    Usa datos históricos de Yahoo Finance por defecto.
    Incluye: Attention mechanisms, positional encoding, etc.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible. PyTorch no está instalado."
        )
    
    try:
        import pandas as pd
        from app.services.yahoo_finance_service import YahooFinanceService
        
        if use_yahoo:
            # Usar Yahoo Finance
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Fetching data from Yahoo Finance for {symbol}")
            yahoo_service = YahooFinanceService()
            
            # Determinar si es Forex o Crypto
            if "=X" in symbol or "/" in symbol:
                # Forex
                if "=X" in symbol:
                    from_curr = symbol.split("=")[0][:3]
                    to_curr = symbol.split("=")[0][3:]
                else:
                    parts = symbol.split("/")
                    from_curr = parts[0]
                    to_curr = parts[1]
                data = yahoo_service.get_forex_data(from_curr, to_curr, period=period, interval=interval)
            else:
                # Crypto o Stock
                if "-" in symbol:
                    data = yahoo_service.get_crypto_data(symbol, period=period, interval=interval)
                else:
                    data = yahoo_service.get_stock_data(symbol, period=period, interval=interval)
            
            if data is None or data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se pudieron obtener datos de Yahoo Finance para {symbol}"
                )
            
            # Preparar datos para entrenamiento
            data = yahoo_service.prepare_data_for_training(data, target_col="close")
            
        else:
            # Usar datos de la base de datos
            price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
            
            if len(price_history) < 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"No hay suficientes datos. Se necesitan al menos 200 registros, se encontraron {len(price_history)}"
                )
            
            data = pd.DataFrame([
                {
                    "price": _get_price_from_history(ph),
                    "spread": ph.spread or 0,
                    "volume": _get_volume_from_history(ph),
                    "timestamp": ph.timestamp,
                }
                for ph in price_history
            ])
        
        if len(data) < 200:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se necesitan al menos 200 registros, se encontraron {len(data)}"
            )
        
        # Entrenar modelo
        trainer = AdvancedDLTrainer()
        result = trainer.train_transformer_model(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            target_col='price'
        )
        
        result['data_source'] = 'yahoo_finance' if use_yahoo else 'database'
        result['symbol'] = symbol
        result['data_points'] = len(data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training transformer: {str(e)}")


@router.post("/dl/advanced/train-profit-aware")
async def train_profit_aware_model(
    symbol: str = Query(default="BTC-USD", description="Símbolo de Yahoo Finance"),
    period: str = Query(default="1y", description="Período"),
    interval: str = Query(default="1d", description="Intervalo"),
    use_yahoo: bool = Query(default=True, description="Usar Yahoo Finance"),
    epochs: int = Query(default=100, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelo que predice profit directamente.
    Usa datos históricos de Yahoo Finance por defecto.
    Incluye predicción de precio, profit, riesgo y confianza.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        import pandas as pd
        from app.services.yahoo_finance_service import YahooFinanceService
        
        if use_yahoo:
            # Usar Yahoo Finance
            yahoo_service = YahooFinanceService()
            
            if "=X" in symbol or "/" in symbol:
                if "=X" in symbol:
                    from_curr = symbol.split("=")[0][:3]
                    to_curr = symbol.split("=")[0][3:]
                else:
                    parts = symbol.split("/")
                    from_curr = parts[0]
                    to_curr = parts[1]
                data = yahoo_service.get_forex_data(from_curr, to_curr, period=period, interval=interval)
            else:
                if "-" in symbol:
                    data = yahoo_service.get_crypto_data(symbol, period=period, interval=interval)
                else:
                    data = yahoo_service.get_stock_data(symbol, period=period, interval=interval)
            
            if data is None or data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se pudieron obtener datos de Yahoo Finance para {symbol}"
                )
            
            data = yahoo_service.prepare_data_for_training(data, target_col="close")
        else:
            # Usar datos de BD
            price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
            
            if len(price_history) < 200:
                raise HTTPException(
                    status_code=400,
                    detail="No hay suficientes datos. Se necesitan al menos 200 registros."
                )
            
            data = pd.DataFrame([
                {
                    "price": _get_price_from_history(ph),
                    "spread": ph.spread or 0,
                    "volume": _get_volume_from_history(ph),
                    "timestamp": ph.timestamp,
                }
                for ph in price_history
            ])
        
        trainer = AdvancedDLTrainer()
        result = trainer.train_profit_aware_model(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            target_col='price'
        )
        
        result['data_source'] = 'yahoo_finance' if use_yahoo else 'database'
        result['symbol'] = symbol
        result['data_points'] = len(data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training profit-aware model: {str(e)}")


@router.post("/dl/advanced/train-ensemble")
async def train_ensemble_models(
    symbol: str = Query(default="BTC-USD", description="Símbolo de Yahoo Finance"),
    period: str = Query(default="1y", description="Período"),
    interval: str = Query(default="1d", description="Intervalo"),
    use_yahoo: bool = Query(default=True, description="Usar Yahoo Finance"),
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar ensemble de múltiples modelos avanzados.
    Usa datos históricos de Yahoo Finance por defecto.
    Combina: Transformer, Attention LSTM, Residual LSTM, Hybrid Model.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        import pandas as pd
        from app.services.yahoo_finance_service import YahooFinanceService
        
        if use_yahoo:
            # Usar Yahoo Finance
            yahoo_service = YahooFinanceService()
            
            if "=X" in symbol or "/" in symbol:
                if "=X" in symbol:
                    from_curr = symbol.split("=")[0][:3]
                    to_curr = symbol.split("=")[0][3:]
                else:
                    parts = symbol.split("/")
                    from_curr = parts[0]
                    to_curr = parts[1]
                data = yahoo_service.get_forex_data(from_curr, to_curr, period=period, interval=interval)
            else:
                if "-" in symbol:
                    data = yahoo_service.get_crypto_data(symbol, period=period, interval=interval)
                else:
                    data = yahoo_service.get_stock_data(symbol, period=period, interval=interval)
            
            if data is None or data.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se pudieron obtener datos de Yahoo Finance para {symbol}"
                )
            
            data = yahoo_service.prepare_data_for_training(data, target_col="close")
        else:
            # Usar datos de BD
            price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
            
            if len(price_history) < 200:
                raise HTTPException(
                    status_code=400,
                    detail="No hay suficientes datos. Se necesitan al menos 200 registros."
                )
            
            data = pd.DataFrame([
                {
                    "price": _get_price_from_history(ph),
                    "spread": ph.spread or 0,
                    "volume": _get_volume_from_history(ph),
                    "timestamp": ph.timestamp,
                }
                for ph in price_history
            ])
        
        trainer = AdvancedDLTrainer()
        result = trainer.train_ensemble_model(
            data=data,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            target_col='price'
        )
        
        result['data_source'] = 'yahoo_finance' if use_yahoo else 'database'
        result['symbol'] = symbol
        result['data_points'] = len(data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training ensemble: {str(e)}")


@router.post("/dl/advanced/backtest")
async def backtest_strategy(
    buy_threshold: float = Query(default=0.02, ge=0.001, le=0.1),
    sell_threshold: float = Query(default=0.02, ge=0.001, le=0.1),
    stop_loss: float = Query(default=0.05, ge=0.01, le=0.5),
    take_profit: float = Query(default=0.10, ge=0.01, le=1.0),
    initial_capital: float = Query(default=10000.0, ge=100, le=1000000),
    db: Session = Depends(get_db)
):
    """
    Backtest de estrategia de trading usando modelos entrenados.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        # Obtener datos históricos
        price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail="No hay suficientes datos para backtesting."
            )
        
        import pandas as pd
        import numpy as np
        
        # Preparar datos
        data = pd.DataFrame([
            {
                "price": _get_price_from_history(ph),
                "spread": ph.spread or 0,
                "volume": _get_volume_from_history(ph),
                "timestamp": ph.timestamp,
            }
            for ph in price_history
        ])
        
        # Por simplicidad, usar precios como predicciones
        # En producción, usarías un modelo entrenado
        predictions = data['price'].copy()
        actual_prices = data['price'].copy()
        
        # Backtest
        backtesting_service = BacktestingService()
        result = backtesting_service.backtest_strategy(
            predictions=predictions,
            actual_prices=actual_prices,
            initial_capital=initial_capital,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in backtesting: {str(e)}")


@router.get("/dl/advanced/profit-metrics")
async def get_profit_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Calcular métricas de profit y risk.
    Incluye: Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Profit Factor, etc.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        # Obtener datos históricos
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        price_history = db.query(PriceHistory).filter(
            PriceHistory.timestamp >= cutoff_date
        ).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 10:
            raise HTTPException(
                status_code=400,
                detail="No hay suficientes datos."
            )
        
        import pandas as pd
        
        # Preparar datos
        prices = pd.Series([_get_price_from_history(ph) for ph in price_history])
        returns = prices.pct_change().dropna()
        
        # Calcular métricas
        profit_calculator = ProfitMetricsCalculator()
        metrics = profit_calculator.calculate_all_metrics(
            prices=prices,
            returns=returns,
            period='daily'
        )
        
        return {
            "period_days": days,
            "data_points": len(price_history),
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


@router.post("/dl/advanced/train-with-db-data")
async def train_models_with_db_data(
    model_type: str = Query(default="transformer", description="Tipo de modelo: transformer, ensemble, profit-aware, all"),
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.0001, ge=0.0001, le=0.1),
    min_records: int = Query(default=200, ge=100, le=10000),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelos avanzados usando datos de la base de datos.
    Esta es la forma más confiable de entrenar si no tienes acceso a Yahoo Finance.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Obtener datos históricos de la BD
        cutoff_date = datetime.utcnow() - timedelta(days=min_records * 2)
        price_history = db.query(PriceHistory).filter(
            PriceHistory.timestamp >= cutoff_date
        ).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < min_records:
            # Usar todos los datos disponibles
            price_history = db.query(PriceHistory).order_by(PriceHistory.timestamp).all()
        
        if len(price_history) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"No hay suficientes datos. Se encontraron {len(price_history)} registros, se necesitan al menos 100."
            )
        
        # Convertir a DataFrame
        # PriceHistory usa avg_price, bid_price, ask_price, no 'price' directo
        data = pd.DataFrame([
            {
                "price": ph.avg_price if ph.avg_price else (ph.bid_price if ph.bid_price else (ph.ask_price if ph.ask_price else 0)),
                "spread": ph.spread if ph.spread else 0,
                "volume": ph.volume_24h if ph.volume_24h else 0,
                "timestamp": ph.timestamp,
            }
            for ph in price_history
        ])
        
        # Filtrar datos inválidos
        data = data[data['price'] > 0]
        data = data.dropna()
        
        if len(data) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Después de limpiar datos, solo quedan {len(data)} registros válidos."
            )
        
        trainer = AdvancedDLTrainer()
        results = {}
        
        # Entrenar según el tipo de modelo solicitado
        if model_type in ["transformer", "all"]:
            result = trainer.train_transformer_model(
                data=data,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['transformer'] = result
        
        if model_type in ["profit-aware", "all"]:
            result = trainer.train_profit_aware_model(
                data=data,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['profit_aware'] = result
        
        if model_type in ["ensemble", "all"]:
            result = trainer.train_ensemble_model(
                data=data,
                epochs=max(epochs // 2, 20),  # Ensemble toma más tiempo, usar menos épocas
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['ensemble'] = result
        
        return {
            "status": "success",
            "data_source": "database",
            "data_points": len(data),
            "models_trained": list(results.keys()),
            "results": results,
            "message": f"Modelos entrenados exitosamente con {len(data)} registros de la BD"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training models: {str(e)}")


@router.post("/dl/advanced/train-with-yahoo")
async def train_models_with_yahoo(
    symbol: str = Query(default="BTC-USD", description="Símbolo de Yahoo Finance (BTC-USD, ETH-USD, USDCOP=X, etc.)"),
    period: str = Query(default="2y", description="Período (1y, 2y, 5y, max)"),
    interval: str = Query(default="1d", description="Intervalo (1d, 1h, 1wk)"),
    model_type: str = Query(default="transformer", description="Tipo de modelo: transformer, ensemble, profit-aware, all"),
    epochs: int = Query(default=50, ge=1, le=500),
    batch_size: int = Query(default=32, ge=1, le=256),
    learning_rate: float = Query(default=0.0001, ge=0.0001, le=0.1),
    db: Session = Depends(get_db)
):
    """
    Entrenar modelos avanzados usando datos de Yahoo Finance.
    Recomendado: Mejor calidad de datos y más datos históricos.
    """
    if not ADVANCED_DL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Advanced Deep Learning no disponible."
        )
    
    try:
        import pandas as pd
        import logging
        logger = logging.getLogger(__name__)
        from app.services.yahoo_finance_service import YahooFinanceService
        
        logger.info(f"🎯 Entrenando con Yahoo Finance: {symbol} (período: {period}, intervalo: {interval})")
        
        # Obtener datos de Yahoo Finance
        yahoo_service = YahooFinanceService()
        
        # Determinar tipo de símbolo y obtener datos
        if "=X" in symbol or "/" in symbol:
            # Forex
            if "=X" in symbol:
                from_curr = symbol.split("=")[0][:3]
                to_curr = symbol.split("=")[0][3:]
            else:
                parts = symbol.split("/")
                from_curr = parts[0]
                to_curr = parts[1]
            logger.info(f"Obteniendo datos Forex: {from_curr}/{to_curr}")
            data = yahoo_service.get_forex_data(from_curr, to_curr, period=period, interval=interval)
        else:
            # Crypto o Stock
            if "-" in symbol:
                logger.info(f"Obteniendo datos Crypto: {symbol}")
                data = yahoo_service.get_crypto_data(symbol, period=period, interval=interval, max_retries=5)
            else:
                logger.info(f"Obteniendo datos Stock: {symbol}")
                data = yahoo_service.get_stock_data(symbol, period=period, interval=interval)
        
        if data is None or data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No se pudieron obtener datos de Yahoo Finance para {symbol}. "
                       f"Intenta con otro símbolo o verifica tu conexión a internet."
            )
        
        logger.info(f"✅ Datos obtenidos: {len(data)} registros")
        
        # Preparar datos para entrenamiento
        # Yahoo Finance ya tiene OHLCV, así que usamos close como price
        data = yahoo_service.prepare_data_for_training(data, target_col="close")
        
        # Asegurar que tenemos columnas necesarias
        if 'price' not in data.columns and 'close' in data.columns:
            data['price'] = data['close']
        elif 'price' not in data.columns:
            raise HTTPException(
                status_code=400,
                detail="No se pudo encontrar columna de precio en los datos de Yahoo Finance."
            )
        
        logger.info(f"📊 Datos preparados: {len(data)} registros, {len(data.columns)} features")
        
        if len(data) < 200:
            raise HTTPException(
                status_code=400,
                detail=f"Solo se obtuvieron {len(data)} registros. "
                       f"Intenta con un período más largo (ej: '2y' o '5y') o un intervalo más corto (ej: '1h')."
            )
        
        trainer = AdvancedDLTrainer()
        results = {}
        
        # Entrenar según el tipo de modelo solicitado
        if model_type in ["transformer", "all"]:
            logger.info("🚀 Entrenando modelo Transformer...")
            result = trainer.train_transformer_model(
                data=data,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['transformer'] = result
        
        if model_type in ["profit-aware", "all"]:
            logger.info("🚀 Entrenando modelo Profit-Aware...")
            result = trainer.train_profit_aware_model(
                data=data,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['profit_aware'] = result
        
        if model_type in ["ensemble", "all"]:
            logger.info("🚀 Entrenando Ensemble de Modelos...")
            result = trainer.train_ensemble_model(
                data=data,
                epochs=max(epochs // 2, 20),  # Ensemble toma más tiempo
                batch_size=batch_size,
                learning_rate=learning_rate,
                target_col='price'
            )
            results['ensemble'] = result
        
        return {
            "status": "success",
            "data_source": "yahoo_finance",
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data_points": len(data),
            "models_trained": list(results.keys()),
            "results": results,
            "message": f"✅ Modelos entrenados exitosamente con {len(data)} registros de Yahoo Finance para {symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error training models with Yahoo Finance: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error entrenando modelos con Yahoo Finance: {str(e)}. "
                   f"Verifica que el símbolo sea correcto y que Yahoo Finance esté accesible."
        )


@router.get("/gpu/status")
async def get_gpu_status():
    """
    Obtiene el estado de la GPU Intel Arc (si está disponible).
    Combina información de PyTorch y XPU Manager.
    """
    try:
        # Información básica de GPU desde PyTorch
        gpu_info = get_gpu_info()
        
        # Intentar obtener información de XPU Manager (si está disponible)
        xpu_monitor = get_xpu_monitor_service()
        xpu_info = None
        if xpu_monitor.available:
            try:
                xpu_info = xpu_monitor.get_gpu_info()
            except Exception as e:
                logger.warning(f"No se pudo obtener información de XPU Manager: {e}")
        
        return {
            "pytorch_gpu": gpu_info,
            "xpu_manager": xpu_info if xpu_info else {"available": False, "message": "XPU Manager no disponible"},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de GPU: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado de GPU: {str(e)}"
        )


@router.get("/gpu/metrics")
async def get_gpu_metrics(device_id: int = Query(0, description="ID del dispositivo GPU")):
    """
    Obtiene métricas detalladas de la GPU (temperatura, uso, memoria, etc.).
    Requiere que XPU Manager esté corriendo.
    """
    try:
        xpu_monitor = get_xpu_monitor_service()
        
        if not xpu_monitor.available:
            raise HTTPException(
                status_code=503,
                detail="XPU Manager no está disponible. "
                       "Asegúrate de que el servicio esté corriendo (ver docker-compose.xpu-monitor.yml)"
            )
        
        metrics = xpu_monitor.get_gpu_metrics(device_id)
        health = xpu_monitor.get_gpu_health(device_id)
        
        if not metrics and not health:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron métricas para el dispositivo GPU {device_id}"
            )
        
        return {
            "device_id": device_id,
            "health": health,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo métricas de GPU: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo métricas de GPU: {str(e)}"
        )
