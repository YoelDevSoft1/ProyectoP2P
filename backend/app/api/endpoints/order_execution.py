"""
API Endpoints para Order Execution Intelligence Service
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.services.order_execution_service import OrderExecutionService

router = APIRouter(prefix="/order-execution", tags=["order-execution"])


@router.post("/twap")
async def execute_twap(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    trade_type: str = Query(default="SELL", description="BUY o SELL"),
    total_amount_usd: float = Query(..., description="Cantidad total en USD"),
    duration_minutes: int = Query(default=30, description="Duración en minutos"),
    chunks: int = Query(default=10, description="Número de chunks")
):
    """
    Ejecuta orden usando algoritmo TWAP (Time-Weighted Average Price).
    """
    service = OrderExecutionService()

    if trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="trade_type debe ser BUY o SELL")

    result = await service.execute_twap(
        asset=asset,
        fiat=fiat,
        trade_type=trade_type,
        total_amount_usd=total_amount_usd,
        duration_minutes=duration_minutes,
        chunks=chunks
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error ejecutando TWAP"))

    return result


@router.post("/vwap")
async def execute_vwap(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    trade_type: str = Query(default="SELL", description="BUY o SELL"),
    total_amount_usd: float = Query(..., description="Cantidad total en USD"),
    duration_minutes: int = Query(default=30, description="Duración en minutos")
):
    """
    Ejecuta orden usando algoritmo VWAP (Volume-Weighted Average Price).
    """
    service = OrderExecutionService()

    if trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="trade_type debe ser BUY o SELL")

    result = await service.execute_vwap(
        asset=asset,
        fiat=fiat,
        trade_type=trade_type,
        total_amount_usd=total_amount_usd,
        duration_minutes=duration_minutes
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error ejecutando VWAP"))

    return result


@router.post("/iceberg")
async def execute_iceberg(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    trade_type: str = Query(default="SELL", description="BUY o SELL"),
    total_amount_usd: float = Query(..., description="Cantidad total en USD"),
    visible_size_usd: float = Query(default=1000.0, description="Tamaño visible de la orden"),
    refresh_interval_seconds: int = Query(default=60, description="Intervalo de refresh en segundos")
):
    """
    Ejecuta orden tipo Iceberg (oculta tamaño real).
    """
    service = OrderExecutionService()

    if trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="trade_type debe ser BUY o SELL")

    result = await service.execute_iceberg(
        asset=asset,
        fiat=fiat,
        trade_type=trade_type,
        total_amount_usd=total_amount_usd,
        visible_size_usd=visible_size_usd,
        refresh_interval_seconds=refresh_interval_seconds
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error ejecutando Iceberg"))

    return result


@router.post("/smart-routing")
async def smart_order_routing(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    trade_type: str = Query(default="SELL", description="BUY o SELL"),
    amount_usd: float = Query(..., description="Cantidad en USD"),
    exchanges: Optional[str] = Query(default="binance_p2p", description="Exchanges separados por coma")
):
    """
    Enruta orden a mejor mercado disponible.
    """
    service = OrderExecutionService()

    if trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="trade_type debe ser BUY o SELL")

    exchanges_list = [e.strip() for e in exchanges.split(",")] if exchanges else ["binance_p2p"]

    result = await service.smart_order_routing(
        asset=asset,
        fiat=fiat,
        trade_type=trade_type,
        amount_usd=amount_usd,
        exchanges=exchanges_list
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error en smart routing"))

    return result

