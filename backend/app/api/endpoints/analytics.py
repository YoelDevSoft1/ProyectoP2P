"""
Endpoints de análisis y analytics avanzados.
Incluye: Triangle Arbitrage, Liquidez, ML Predictions, Risk Management
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.models.trade import Trade, TradeStatus
from app.models.price_history import PriceHistory
from app.models.alert import Alert, AlertType

# Servicios avanzados
from app.services.triangle_arbitrage_service import TriangleArbitrageService
from app.services.liquidity_analysis_service import LiquidityAnalysisService
from app.services.ml_service import AdvancedMLService
from app.services.risk_management_service import RiskManagementService
from app.services.competitive_pricing_service import CompetitivePricingService

router = APIRouter()

# Inicializar servicios
triangle_service = TriangleArbitrageService()
liquidity_service = LiquidityAnalysisService()
ml_service = AdvancedMLService()
risk_service = RiskManagementService()
pricing_service = CompetitivePricingService()


@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Datos principales para el dashboard.
    """
    # Últimas 24 horas
    last_24h = datetime.utcnow() - timedelta(hours=24)
    last_7d = datetime.utcnow() - timedelta(days=7)

    # Trades de hoy
    trades_today = db.query(Trade).filter(
        Trade.created_at >= last_24h
    ).all()

    completed_today = [t for t in trades_today if t.status == TradeStatus.COMPLETED]

    # Profit de hoy
    profit_today = sum(t.actual_profit or 0 for t in completed_today)

    # Trades de la semana
    trades_week = db.query(Trade).filter(
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
    from app.services.notification_service import NotificationService

    notification_service = NotificationService()
    success = await notification_service.test_notification()

    if success:
        return {
            "status": "success",
            "message": "Notificación de prueba enviada exitosamente"
        }
    else:
        return {
            "status": "error",
            "message": "No se pudo enviar la notificación. Verifica que TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID estén configurados correctamente."
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
