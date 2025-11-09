"""
API Endpoints para Market Making Service
"""

from fastapi import APIRouter, Query, HTTPException
from app.services.market_making_service import MarketMakingService

router = APIRouter(prefix="/market-making", tags=["market-making"])


@router.post("/start")
async def start_market_making(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    update_interval_seconds: int = Query(default=30, description="Intervalo de actualización en segundos")
):
    """
    Inicia market making para un par de activos.
    """
    service = MarketMakingService()

    result = await service.start_market_making(
        asset=asset,
        fiat=fiat,
        update_interval_seconds=update_interval_seconds
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error iniciando market making"))

    return result


@router.post("/update")
async def update_market_making(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat")
):
    """
    Actualiza órdenes de market making.
    """
    service = MarketMakingService()

    result = await service.update_market_making_orders(
        asset=asset,
        fiat=fiat
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error actualizando market making"))

    return result


@router.post("/stop")
async def stop_market_making(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat")
):
    """
    Detiene market making para un par.
    """
    service = MarketMakingService()

    result = await service.stop_market_making(
        asset=asset,
        fiat=fiat
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error deteniendo market making"))

    return result


@router.get("/status")
async def get_market_making_status(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat")
):
    """
    Obtiene estado actual de market making.
    """
    service = MarketMakingService()

    result = await service.get_market_making_status(
        asset=asset,
        fiat=fiat
    )

    return result


@router.get("/all")
async def get_all_active_market_making():
    """
    Obtiene todos los pares con market making activo.
    """
    service = MarketMakingService()

    result = await service.get_all_active_market_making()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo market making activo"))

    return result

