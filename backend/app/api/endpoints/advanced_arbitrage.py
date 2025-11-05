"""
Advanced Arbitrage API Endpoints.

Endpoints para todas las estrategias avanzadas de arbitraje.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query
import structlog

from app.services.advanced_opportunity_analyzer import AdvancedOpportunityAnalyzer
from app.services.funding_rate_arbitrage_service import FundingRateArbitrageService
from app.services.statistical_arbitrage_service import StatisticalArbitrageService
from app.services.delta_neutral_arbitrage_service import DeltaNeutralArbitrageService
from app.services.advanced_triangle_arbitrage_service import AdvancedTriangleArbitrageService

logger = structlog.get_logger()

router = APIRouter()

# Initialize services
opportunity_analyzer = AdvancedOpportunityAnalyzer()
funding_rate_service = FundingRateArbitrageService()
statistical_service = StatisticalArbitrageService()
delta_neutral_service = DeltaNeutralArbitrageService()
triangle_service = AdvancedTriangleArbitrageService()


# ==================== ADVANCED OPPORTUNITY ANALYZER ====================


@router.get("/scan")
async def scan_all_opportunities(
    min_return: float = Query(1.0, description="Retorno mínimo esperado (%)"),
    max_risk: float = Query(70.0, description="Risk score máximo aceptable"),
    capital: float = Query(10000.0, description="Capital disponible (USD)"),
):
    """
    Escanea TODAS las estrategias de arbitraje y retorna las mejores oportunidades.

    Este endpoint combina:
    - Funding Rate Arbitrage
    - Statistical Arbitrage
    - Delta-Neutral Arbitrage
    - Triangle Arbitrage
    - Spot-to-P2P Arbitrage

    Returns:
        Lista de oportunidades unificadas ordenadas por opportunity_score
    """
    try:
        opportunities = await opportunity_analyzer.find_all_opportunities(
            min_expected_return=min_return,
            max_risk_score=max_risk,
            available_capital_usd=capital,
        )

        return {
            "success": True,
            "total_opportunities": len(opportunities),
            "capital_available": capital,
            "filters": {
                "min_return_pct": min_return,
                "max_risk_score": max_risk,
            },
            "opportunities": [
                {
                    "id": opp.opportunity_id,
                    "strategy": opp.strategy_type.value,
                    "expected_return_pct": round(opp.expected_return_pct, 2),
                    "expected_return_usd": round(opp.expected_return_usd, 2),
                    "risk_score": round(opp.risk_score, 2),
                    "confidence": round(opp.confidence, 2),
                    "sharpe_ratio": round(opp.sharpe_ratio, 2),
                    "opportunity_score": round(opp.opportunity_score, 2),
                    "priority": opp.priority,
                    "recommendation": opp.recommendation,
                    "required_capital": round(opp.required_capital_usd, 2),
                    "execution_time_seconds": opp.execution_time_estimate_seconds,
                    "liquidity_score": round(opp.liquidity_score, 2),
                    "symbols": opp.symbols,
                    "exchange": opp.exchange,
                    "tags": opp.tags,
                }
                for opp in opportunities
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error scanning opportunities", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/best")
async def get_best_opportunity(
    ranking_method: str = Query(
        "risk_adjusted",
        description="Método de ranking: 'return', 'risk_adjusted', 'sharpe'",
    ),
    capital: float = Query(10000.0, description="Capital disponible (USD)"),
):
    """
    Obtiene la MEJOR oportunidad global según el método de ranking.

    Métodos de ranking:
    - return: Mayor retorno esperado
    - risk_adjusted: Mejor ratio return/risk
    - sharpe: Mayor Sharpe ratio
    """
    try:
        best = await opportunity_analyzer.get_best_opportunity(
            ranking_method=ranking_method,
            available_capital_usd=capital,
        )

        if not best:
            return {
                "success": False,
                "message": "No se encontraron oportunidades",
            }

        return {
            "success": True,
            "ranking_method": ranking_method,
            "opportunity": {
                "id": best.opportunity_id,
                "strategy": best.strategy_type.value,
                "expected_return_pct": round(best.expected_return_pct, 2),
                "expected_return_usd": round(best.expected_return_usd, 2),
                "risk_score": round(best.risk_score, 2),
                "confidence": round(best.confidence, 2),
                "sharpe_ratio": round(best.sharpe_ratio, 2),
                "risk_adjusted_return": round(best.risk_adjusted_return, 2),
                "opportunity_score": round(best.opportunity_score, 2),
                "priority": best.priority,
                "recommendation": best.recommendation,
                "required_capital": round(best.required_capital_usd, 2),
                "execution_time_seconds": best.execution_time_estimate_seconds,
                "liquidity_score": round(best.liquidity_score, 2),
                "symbols": best.symbols,
                "exchange": best.exchange,
                "execution_plan": best.execution_plan,
                "tags": best.tags,
            },
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting best opportunity", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/portfolio")
async def optimize_portfolio(
    capital: float = Query(10000.0, description="Capital total disponible (USD)"),
    max_positions: int = Query(5, description="Máximo número de posiciones simultáneas"),
    min_return: float = Query(1.0, description="Retorno mínimo por estrategia (%)"),
):
    """
    Optimiza la asignación de capital entre múltiples estrategias.

    Usa Modern Portfolio Theory para:
    - Maximizar retorno esperado
    - Minimizar riesgo via diversificación
    - Balancear entre estrategias

    Returns:
        Recomendación de asignación de capital
    """
    try:
        allocation = await opportunity_analyzer.optimize_portfolio(
            total_capital_usd=capital,
            max_positions=max_positions,
            min_return_per_strategy=min_return,
        )

        return {
            "success": True,
            "total_capital_usd": allocation.total_capital_usd,
            "expected_portfolio_return_pct": round(allocation.expected_portfolio_return_pct, 2),
            "portfolio_sharpe_ratio": round(allocation.portfolio_sharpe_ratio, 2),
            "portfolio_risk_score": round(allocation.portfolio_risk_score, 2),
            "diversification_score": round(allocation.diversification_score, 2),
            "recommendation": allocation.recommendation,
            "allocations": [
                {
                    "strategy": a["strategy"],
                    "allocated_capital_usd": round(a["allocated_capital_usd"], 2),
                    "weight_pct": round(a["weight_pct"], 2),
                    "expected_return_pct": round(a["expected_return_pct"], 2),
                    "expected_return_usd": round(a["expected_return_usd"], 2),
                    "risk_score": round(a["risk_score"], 2),
                    "symbols": a["symbols"],
                }
                for a in allocation.allocations
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error optimizing portfolio", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/compare-strategies")
async def compare_strategies(
    capital: float = Query(10000.0, description="Capital disponible (USD)"),
):
    """
    Compara todas las estrategias side-by-side.

    Returns:
        Comparación detallada con métricas por estrategia
    """
    try:
        comparison = await opportunity_analyzer.compare_strategies(
            available_capital_usd=capital,
        )

        return {
            "success": True,
            **comparison,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error comparing strategies", error=str(exc))
        return {"success": False, "error": str(exc)}


# ==================== FUNDING RATE ARBITRAGE ====================


@router.get("/funding-rate/opportunities")
async def get_funding_rate_opportunities(
    min_apy: float = Query(5.0, description="APY mínimo (%)"),
    max_leverage: int = Query(3, description="Leverage máximo"),
):
    """
    Encuentra todas las oportunidades de funding rate arbitrage.

    Estrategia:
    - Funding positivo: Buy Spot + Short Futures (recibir funding)
    - Funding negativo: Long Futures (recibir funding)
    """
    try:
        opportunities = await funding_rate_service.find_all_opportunities(
            min_apy=min_apy,
            max_leverage=max_leverage,
        )

        return {
            "success": True,
            "total_opportunities": len(opportunities),
            "opportunities": [
                {
                    "symbol": opp.symbol,
                    "funding_rate_pct": round(opp.funding_rate_pct, 4),
                    "apy": round(opp.apy, 2),
                    "net_apy": round(opp.net_apy, 2),
                    "strategy": opp.strategy_type,
                    "direction": opp.direction,
                    "expected_daily_profit": round(opp.expected_daily_profit, 2),
                    "next_funding_hours": round(opp.hours_until_funding, 2),
                    "spot_price": opp.spot_price,
                    "futures_price": opp.futures_price,
                    "basis_pct": round(opp.basis_pct, 2),
                    "opportunity_score": round(opp.opportunity_score, 2),
                    "risk_level": opp.risk_level,
                    "recommendation": opp.recommendation,
                }
                for opp in opportunities
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting funding rate opportunities", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/funding-rate/best")
async def get_best_funding_rate_opportunity(
    min_apy: float = Query(5.0, description="APY mínimo (%)"),
):
    """Obtiene la mejor oportunidad de funding rate arbitrage."""
    try:
        best = await funding_rate_service.get_best_opportunity(min_apy=min_apy)

        if not best:
            return {"success": False, "message": "No se encontraron oportunidades"}

        return {
            "success": True,
            "opportunity": {
                "symbol": best.symbol,
                "funding_rate_pct": round(best.funding_rate_pct, 4),
                "apy": round(best.apy, 2),
                "net_apy": round(best.net_apy, 2),
                "strategy": best.strategy_type,
                "direction": best.direction,
                "expected_daily_profit": round(best.expected_daily_profit, 2),
                "required_margin": round(best.required_margin, 2),
                "leverage_used": best.leverage_used,
                "liquidation_price": best.liquidation_price,
                "opportunity_score": round(best.opportunity_score, 2),
                "risk_level": best.risk_level,
                "recommendation": best.recommendation,
            },
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting best funding rate opportunity", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/funding-rate/historical/{symbol}")
async def get_funding_rate_historical(
    symbol: str,
    days: int = Query(30, description="Días de historial"),
):
    """Analiza el rendimiento histórico del funding rate de un símbolo."""
    try:
        historical = await funding_rate_service.analyze_historical_performance(
            symbol=symbol,
            days=days,
        )

        if not historical:
            return {"success": False, "message": "No hay datos históricos disponibles"}

        return {
            "success": True,
            **historical,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting historical funding rate", error=str(exc))
        return {"success": False, "error": str(exc)}


# ==================== STATISTICAL ARBITRAGE ====================


@router.get("/statistical/signals")
async def get_statistical_signals(
    min_z_score: float = Query(2.0, description="Z-score mínimo para señal"),
    lookback_days: int = Query(30, description="Días de historial para análisis"),
):
    """
    Encuentra señales de statistical arbitrage (pairs trading).

    Analiza pares de crypto cointegrados y genera señales basadas en
    desviaciones del spread (mean reversion).
    """
    try:
        signals = await statistical_service.find_all_opportunities(
            min_z_score=min_z_score,
            lookback_days=lookback_days,
        )

        return {
            "success": True,
            "total_signals": len(signals),
            "signals": [
                {
                    "pair": signal.pair_name,
                    "signal_type": signal.signal_type,
                    "z_score": round(signal.z_score, 2),
                    "correlation": round(signal.correlation, 3),
                    "is_cointegrated": signal.is_cointegrated,
                    "expected_return_pct": round(signal.expected_return_pct, 2),
                    "confidence": round(signal.confidence, 2),
                    "risk_level": signal.risk_level,
                    "recommendation": signal.recommendation,
                    "reason": signal.reason,
                    "asset_1": signal.asset_1,
                    "asset_2": signal.asset_2,
                    "price_1": signal.price_1,
                    "price_2": signal.price_2,
                }
                for signal in signals
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting statistical signals", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/statistical/pair/{symbol1}/{symbol2}")
async def analyze_specific_pair(
    symbol1: str,
    symbol2: str,
    lookback_days: int = Query(30, description="Días de historial"),
):
    """Analiza un par específico de activos para statistical arbitrage."""
    try:
        signal = await statistical_service.analyze_pair(
            symbol_1=symbol1,
            symbol_2=symbol2,
            lookback_days=lookback_days,
        )

        if not signal:
            return {"success": False, "message": "No se pudo analizar el par"}

        return {
            "success": True,
            "pair": signal.pair_name,
            "signal_type": signal.signal_type,
            "z_score": round(signal.z_score, 2),
            "correlation": round(signal.correlation, 3),
            "is_cointegrated": signal.is_cointegrated,
            "cointegration_pvalue": round(signal.cointegration_pvalue, 4),
            "current_spread": round(signal.current_spread, 2),
            "mean_spread": round(signal.mean_spread, 2),
            "std_spread": round(signal.std_spread, 2),
            "expected_return_pct": round(signal.expected_return_pct, 2),
            "hedge_ratio": round(signal.hedge_ratio, 3),
            "confidence": round(signal.confidence, 2),
            "risk_level": signal.risk_level,
            "recommendation": signal.recommendation,
            "reason": signal.reason,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error analyzing pair", error=str(exc))
        return {"success": False, "error": str(exc)}


# ==================== DELTA-NEUTRAL ARBITRAGE ====================


@router.get("/delta-neutral/opportunities")
async def get_delta_neutral_opportunities(
    min_return: float = Query(1.0, description="Retorno mínimo (%)"),
    holding_days: int = Query(7, description="Período de holding (días)"),
):
    """
    Encuentra oportunidades de delta-neutral arbitrage (Spot + Futures).

    Estrategia market-neutral que captura basis + funding sin exposición direccional.
    """
    try:
        opportunities = await delta_neutral_service.find_all_opportunities(
            min_total_return=min_return,
            holding_period_days=holding_days,
        )

        return {
            "success": True,
            "total_opportunities": len(opportunities),
            "opportunities": [
                {
                    "symbol": opp.symbol,
                    "strategy": opp.strategy_type,
                    "spot_price": opp.spot_price,
                    "futures_price": opp.futures_price,
                    "basis_pct": round(opp.basis_pct, 2),
                    "funding_rate_pct": round(opp.funding_rate_pct, 4),
                    "funding_apy": round(opp.funding_apy, 2),
                    "net_return_pct": round(opp.net_return_after_fees_pct, 2),
                    "holding_period_days": opp.holding_period_days,
                    "required_capital": round(opp.required_capital_usd, 2),
                    "opportunity_score": round(opp.opportunity_score, 2),
                    "risk_level": opp.basis_risk_level,
                    "recommendation": opp.recommendation,
                    "reason": opp.reason,
                }
                for opp in opportunities
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting delta-neutral opportunities", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/delta-neutral/optimal-holding/{symbol}")
async def get_optimal_holding_period(
    symbol: str,
    target_return: float = Query(5.0, description="Retorno objetivo (%)"),
):
    """Calcula el período de holding óptimo para alcanzar un retorno objetivo."""
    try:
        result = await delta_neutral_service.calculate_optimal_holding_period(
            symbol=symbol,
            target_return_pct=target_return,
        )

        if not result:
            return {"success": False, "message": "No se pudo calcular período óptimo"}

        return {
            "success": True,
            **result,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error calculating optimal holding period", error=str(exc))
        return {"success": False, "error": str(exc)}


# ==================== TRIANGLE ARBITRAGE ====================


@router.get("/triangle/paths")
async def find_triangle_paths(
    start_currency: str = Query("COP", description="Moneda de inicio"),
    min_roi: float = Query(1.0, description="ROI mínimo (%)"),
    max_steps: int = Query(5, description="Máximo número de pasos"),
    initial_amount: float = Query(200000.0, description="Cantidad inicial"),
):
    """
    Encuentra todas las rutas de triangle arbitrage usando graph exploration.

    Analiza rutas de 3, 4, 5+ pasos para encontrar ciclos rentables.
    """
    try:
        paths = await triangle_service.find_all_arbitrage_paths(
            start_currency=start_currency,
            min_roi=min_roi,
            max_steps=max_steps,
            initial_amount=initial_amount,
        )

        return {
            "success": True,
            "total_paths": len(paths),
            "start_currency": start_currency,
            "paths": [
                {
                    "route": " → ".join(path.path),
                    "roi_pct": round(path.roi_percentage, 2),
                    "profit_amount": round(path.profit_amount, 2),
                    "num_steps": path.num_steps,
                    "liquidity_score": round(path.liquidity_score, 2),
                    "risk_score": round(path.risk_score, 2),
                    "opportunity_score": round(path.opportunity_score, 2),
                    "execution_time_seconds": path.execution_time_estimate,
                }
                for path in paths
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error finding triangle paths", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.get("/triangle/optimal")
async def get_optimal_triangle_path(
    start_currency: str = Query("COP", description="Moneda de inicio"),
    min_roi: float = Query(1.0, description="ROI mínimo (%)"),
):
    """Encuentra la ruta óptima de triangle arbitrage."""
    try:
        optimal = await triangle_service.find_optimal_path(
            start_currency=start_currency,
            min_roi=min_roi,
        )

        if not optimal:
            return {"success": False, "message": "No se encontraron rutas rentables"}

        execution_plan = await triangle_service.get_path_execution_plan(optimal)

        return {
            "success": True,
            "path": execution_plan,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting optimal triangle path", error=str(exc))
        return {"success": False, "error": str(exc)}


@router.post("/triangle/compare")
async def compare_triangle_routes(
    routes: List[List[str]],
    initial_amount: float = Query(200000.0, description="Cantidad inicial"),
):
    """
    Compara múltiples rutas específicas de triangle arbitrage.

    Body:
        routes: Lista de rutas, ej: [["COP", "USDT", "VES", "COP"], ...]
    """
    try:
        compared = await triangle_service.compare_routes(
            routes=routes,
            initial_amount=initial_amount,
        )

        return {
            "success": True,
            "total_routes": len(compared),
            "routes": [
                {
                    "route": " → ".join(path.path),
                    "roi_pct": round(path.roi_percentage, 2),
                    "profit_amount": round(path.profit_amount, 2),
                    "opportunity_score": round(path.opportunity_score, 2),
                }
                for path in compared
            ],
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Error comparing triangle routes", error=str(exc))
        return {"success": False, "error": str(exc)}
