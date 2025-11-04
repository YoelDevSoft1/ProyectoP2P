"""
Endpoints para Binance Spot Trading.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.binance_spot_service import BinanceSpotService
from app.services.arbitrage_service import ArbitrageService

router = APIRouter()


class MarketOrderRequest(BaseModel):
    """Esquema para orden de mercado"""
    symbol: str
    side: str  # BUY o SELL
    quantity: float


class LimitOrderRequest(BaseModel):
    """Esquema para orden limit"""
    symbol: str
    side: str
    quantity: float
    price: float


@router.get("/balance")
async def get_balance(asset: str = Query(default="USDT")):
    """
    Obtener balance de un asset específico.

    Args:
        asset: Símbolo del asset (USDT, BTC, etc.)
    """
    service = BinanceSpotService()
    balance = await service.get_account_balance(asset)

    return {
        "asset": asset,
        "balance": balance,
        "available": balance  # En una cuenta real, distinguir entre free y locked
    }


@router.get("/balances")
async def get_all_balances():
    """
    Obtener todos los balances de la cuenta.
    """
    service = BinanceSpotService()
    balances = await service.get_all_balances()

    return {
        "balances": balances,
        "total_assets": len(balances)
    }


@router.get("/price/{symbol}")
async def get_spot_price(symbol: str):
    """
    Obtener precio actual de un par en Spot.

    Args:
        symbol: Par de trading (ej: BTCUSDT, USDCUSDT)
    """
    service = BinanceSpotService()
    price = await service.get_spot_price(symbol)

    if price == 0:
        raise HTTPException(status_code=404, detail="Symbol not found or no price available")

    return {
        "symbol": symbol,
        "price": price
    }


@router.get("/ticker/{symbol}")
async def get_24h_ticker(symbol: str):
    """
    Obtener estadísticas de 24 horas de un par.

    Args:
        symbol: Par de trading
    """
    service = BinanceSpotService()
    ticker = await service.get_24h_ticker(symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    return ticker


@router.post("/order/market")
async def create_market_order(order: MarketOrderRequest):
    """
    Crear orden de mercado (ejecución inmediata).

    Body:
        symbol: Par (ej: BTCUSDT)
        side: BUY o SELL
        quantity: Cantidad
    """
    service = BinanceSpotService()

    # Validar side
    if order.side not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Side must be BUY or SELL")

    result = await service.create_market_order(
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to create market order")

    return {
        "status": "success",
        "order_id": result.get('orderId'),
        "symbol": result.get('symbol'),
        "side": result.get('side'),
        "executed_qty": result.get('executedQty'),
        "fills": result.get('fills', [])
    }


@router.post("/order/limit")
async def create_limit_order(order: LimitOrderRequest):
    """
    Crear orden limit.

    Body:
        symbol: Par
        side: BUY o SELL
        quantity: Cantidad
        price: Precio límite
    """
    service = BinanceSpotService()

    if order.side not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Side must be BUY or SELL")

    result = await service.create_limit_order(
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        price=order.price
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to create limit order")

    return {
        "status": "success",
        "order_id": result.get('orderId'),
        "symbol": result.get('symbol'),
        "side": result.get('side'),
        "price": result.get('price'),
        "quantity": result.get('origQty')
    }


@router.get("/orders/open")
async def get_open_orders(symbol: Optional[str] = None):
    """
    Obtener órdenes abiertas.

    Args:
        symbol: Par específico (opcional)
    """
    service = BinanceSpotService()
    orders = await service.get_open_orders(symbol)

    return {
        "orders": orders,
        "count": len(orders)
    }


@router.delete("/order/{symbol}/{order_id}")
async def cancel_order(symbol: str, order_id: int):
    """
    Cancelar una orden abierta.

    Args:
        symbol: Par
        order_id: ID de la orden
    """
    service = BinanceSpotService()
    success = await service.cancel_order(symbol, order_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel order")

    return {
        "status": "success",
        "message": f"Order {order_id} cancelled"
    }


@router.get("/order/{symbol}/{order_id}")
async def get_order_status(symbol: str, order_id: int):
    """
    Consultar estado de una orden.

    Args:
        symbol: Par
        order_id: ID de la orden
    """
    service = BinanceSpotService()
    order = await service.get_order_status(symbol, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.get("/symbol/{symbol}")
async def get_symbol_info(symbol: str):
    """
    Obtener información de un par de trading.

    Args:
        symbol: Par (ej: BTCUSDT)
    """
    service = BinanceSpotService()
    info = await service.get_symbol_info(symbol)

    if not info:
        raise HTTPException(status_code=404, detail="Symbol not found")

    return info


@router.get("/health")
async def check_spot_connection():
    """
    Verificar conexión con Binance Spot API.
    """
    service = BinanceSpotService()
    is_connected = await service.check_api_connection()

    return {
        "status": "connected" if is_connected else "disconnected",
        "api": "Binance Spot",
        "timestamp": await service.get_server_time()
    }
