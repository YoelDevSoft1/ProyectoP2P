"""
Endpoints para análisis y ejecución de arbitraje.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.services.arbitrage_service import ArbitrageService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/spot-to-p2p")
async def analyze_spot_to_p2p(
    asset: str = Query(default="USDT"),
    fiat: str = Query(default="COP")
):
    """
    Analizar oportunidad de arbitraje Spot -> P2P.

    Estrategia:
    1. Comprar cripto en Spot
    2. Vender cripto en P2P por fiat

    Args:
        asset: Criptomoneda (USDT, BTC)
        fiat: Moneda fiat (COP, VES)
    """
    service = ArbitrageService()
    opportunity = await service.analyze_spot_to_p2p_arbitrage(asset, fiat)

    # Si es profitable y notificaciones están habilitadas, enviar alerta
    if opportunity.get('is_profitable'):
        notif_service = NotificationService()
        await notif_service.send_arbitrage_alert(opportunity)

    return opportunity


@router.get("/cross-currency")
async def analyze_cross_currency():
    """
    Analizar arbitraje entre COP y VES en P2P.

    Estrategia:
    1. Comprar USDT con una moneda
    2. Vender USDT por otra moneda
    """
    service = ArbitrageService()
    opportunity = await service.analyze_p2p_cross_currency()

    return opportunity


@router.get("/all-opportunities")
async def get_all_opportunities():
    """
    Obtener todas las oportunidades de arbitraje disponibles.

    Returns:
        Lista de oportunidades ordenadas por profit
    """
    service = ArbitrageService()

    # Analizar todas las estrategias
    spot_to_p2p_cop = await service.analyze_spot_to_p2p_arbitrage("USDT", "COP")
    spot_to_p2p_ves = await service.analyze_spot_to_p2p_arbitrage("USDT", "VES")
    cross_currency = await service.analyze_p2p_cross_currency()

    opportunities = [
        spot_to_p2p_cop,
        spot_to_p2p_ves,
        cross_currency
    ]

    # Filtrar solo las rentables
    profitable = [o for o in opportunities if o.get('is_profitable', False)]

    # Ordenar por profit
    profitable.sort(
        key=lambda x: x.get('net_profit_percentage', x.get('profit_percentage', 0)),
        reverse=True
    )

    return {
        "total_opportunities": len(opportunities),
        "profitable_count": len(profitable),
        "opportunities": profitable
    }


@router.get("/inventory")
async def get_inventory():
    """
    Obtener estado del inventario de criptomonedas.

    Returns:
        Balances de todos los assets
    """
    service = ArbitrageService()
    inventory = await service.get_inventory_status()

    return inventory


class ExecuteSpotTradeRequest(BaseModel):
    """Request para ejecutar trade en Spot"""
    symbol: str
    side: str  # BUY o SELL
    amount_usd: float


@router.post("/execute/spot")
async def execute_spot_trade(request: ExecuteSpotTradeRequest):
    """
    Ejecutar trade en Binance Spot.

    Body:
        symbol: Par (ej: USDCUSDT)
        side: BUY o SELL
        amount_usd: Cantidad en USD
    """
    service = ArbitrageService()

    result = await service.execute_spot_trade(
        symbol=request.symbol,
        side=request.side,
        amount_usd=request.amount_usd
    )

    if not result:
        return {
            "status": "error",
            "message": "Failed to execute spot trade"
        }

    return {
        "status": "success",
        "order_id": result.get('orderId'),
        "symbol": result.get('symbol'),
        "executed_qty": result.get('executedQty'),
        "fills": result.get('fills', [])
    }


@router.get("/recommended-action")
async def get_recommended_action():
    """
    Obtener la mejor acción recomendada en este momento.

    Analiza todas las oportunidades y devuelve la más rentable
    con instrucciones de ejecución.
    """
    service = ArbitrageService()

    # Analizar oportunidades
    spot_to_p2p_cop = await service.analyze_spot_to_p2p_arbitrage("USDT", "COP")
    spot_to_p2p_ves = await service.analyze_spot_to_p2p_arbitrage("USDT", "VES")
    cross_currency = await service.analyze_p2p_cross_currency()

    opportunities = [spot_to_p2p_cop, spot_to_p2p_ves, cross_currency]

    # Filtrar rentables
    profitable = [o for o in opportunities if o.get('is_profitable', False)]

    if not profitable:
        return {
            "recommendation": "HOLD",
            "message": "No hay oportunidades rentables en este momento",
            "wait_time_seconds": 60
        }

    # Mejor oportunidad
    best = max(
        profitable,
        key=lambda x: x.get('net_profit_percentage', x.get('profit_percentage', 0))
    )

    # Generar instrucciones
    instructions = []

    if best.get('strategy') == 'spot_to_p2p':
        instructions = [
            f"1. Comprar {best['recommended_amount']} USD de {best['asset']} en Binance Spot",
            f"2. Transferir a cuenta P2P",
            f"3. Vender en P2P por {best['fiat']} a precio ~${best['p2p_price']:,.2f}",
            f"4. Profit esperado: {best['net_profit_percentage']}%"
        ]
    elif best.get('strategy') == 'cross_currency':
        instructions = [
            f"1. Comprar USDT en P2P con {best.get('direction', '').split('->')[0].strip()}",
            f"2. Vender USDT en P2P por {best.get('direction', '').split('->')[1].strip()}",
            f"3. Profit esperado: {best['profit_percentage']}%"
        ]

    return {
        "recommendation": "EXECUTE",
        "opportunity": best,
        "instructions": instructions,
        "urgency": "HIGH" if best.get('net_profit_percentage', best.get('profit_percentage', 0)) >= 3 else "MEDIUM"
    }
