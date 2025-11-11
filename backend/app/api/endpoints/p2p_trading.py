"""Endpoints para exponer trading P2P real."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.p2p_trading_service import P2PTradingService

router = APIRouter(prefix="/p2p-trading", tags=["p2p-trading"])


class ExecuteTradeRequest(BaseModel):
    asset: str = Field(..., description="Activo a operar (USDT, BTC, etc.)")
    fiat: str = Field(..., description="Moneda fiat (COP, VES, etc.)")
    trade_type: str = Field(..., description="Tipo de operación BUY o SELL")
    amount: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    payment_methods: List[str] = Field(default_factory=list)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    @field_validator("trade_type")
    @classmethod
    def validate_trade_type(cls, value: str) -> str:
        normalized = (value or "").upper()
        if normalized not in {"BUY", "SELL"}:
            raise ValueError("trade_type debe ser BUY o SELL")
        return normalized


class CancelTradeRequest(BaseModel):
    trade_id: int = Field(..., gt=0)


@router.post("/execute")
async def execute_trade(request: ExecuteTradeRequest):
    service = P2PTradingService()
    try:
        result = await service.execute_trade(
            asset=request.asset,
            fiat=request.fiat,
            trade_type=request.trade_type,
            amount=request.amount,
            price=request.price,
            payment_methods=request.payment_methods,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - integra con Binance
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await service.close()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "No se pudo ejecutar el trade"))

    return result


@router.post("/cancel")
async def cancel_trade(request: CancelTradeRequest):
    service = P2PTradingService()
    try:
        result = await service.cancel_trade(request.trade_id)
    except Exception as exc:  # pragma: no cover - integra con Binance
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await service.close()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "No se pudo cancelar el trade"))

    return result


@router.get("/orders")
async def get_active_orders():
    """
    Obtener órdenes P2P activas.
    
    Nota: Este endpoint requiere que el servicio de automatización de navegador
    esté configurado correctamente (BINANCE_EMAIL, BINANCE_PASSWORD).
    Si no está configurado o hay un error, retorna una lista vacía.
    """
    service = P2PTradingService()
    try:
        orders = await service.get_active_orders()
        return {
            "orders": orders,
            "total": len(orders) if orders else 0
        }
    except Exception as exc:  # pragma: no cover - integra con Binance
        # Log del error pero no fallar completamente
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error obteniendo órdenes P2P: {exc}", exc_info=True)
        
        # Retornar lista vacía en lugar de error 500
        # Esto permite que el frontend continúe funcionando
        return {
            "orders": [],
            "total": 0,
            "error": "No se pudieron obtener las órdenes. Verifica la configuración del servicio de automatización.",
            "details": str(exc) if str(exc) else None
        }
    finally:
        try:
            await service.close()
        except Exception:
            pass  # Ignorar errores al cerrar
