"""
API Endpoints para Dynamic Pricing Service
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.dynamic_pricing_service import DynamicPricingService

router = APIRouter(prefix="/dynamic-pricing", tags=["dynamic-pricing"])


@router.get("/calculate")
async def calculate_dynamic_price(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat"),
    trade_type: str = Query(default="SELL", description="BUY o SELL"),
    amount_usd: float = Query(default=1000.0, description="Cantidad en USD"),
    base_margin: Optional[float] = Query(default=None, description="Margen base (opcional)")
):
    """
    Calcula precio dinámico considerando múltiples factores:
    - Volatilidad
    - Volumen
    - Hora del día
    - Competencia
    - Inventario
    """
    service = DynamicPricingService()

    if trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="trade_type debe ser BUY o SELL")

    result = await service.calculate_dynamic_price(
        asset=asset,
        fiat=fiat,
        trade_type=trade_type,
        amount_usd=amount_usd,
        base_margin=base_margin
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error calculando precio dinámico"))

    return result


@router.get("/summary")
async def get_pricing_summary(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: str = Query(default="COP", description="Moneda fiat")
):
    """
    Obtiene resumen de pricing dinámico para diferentes volúmenes.
    """
    service = DynamicPricingService()

    result = await service.get_pricing_summary(
        asset=asset,
        fiat=fiat
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo resumen"))

    return result

