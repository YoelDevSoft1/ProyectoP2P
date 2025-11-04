"""
Endpoints de operaciones de trading.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.models.trade import Trade, TradeStatus, TradeType

router = APIRouter()


@router.get("/")
async def get_trades(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[TradeStatus] = None,
    fiat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener lista de operaciones.

    Args:
        skip: Número de registros a saltar
        limit: Número máximo de registros a devolver
        status: Filtrar por estado
        fiat: Filtrar por moneda fiat
    """
    query = db.query(Trade)

    if status:
        query = query.filter(Trade.status == status)
    if fiat:
        query = query.filter(Trade.fiat == fiat)

    total = query.count()
    trades = query.order_by(Trade.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "trades": [
            {
                "id": t.id,
                "binance_order_id": t.binance_order_id,
                "type": t.trade_type.value,
                "status": t.status.value,
                "asset": t.asset,
                "fiat": t.fiat,
                "crypto_amount": t.crypto_amount,
                "fiat_amount": t.fiat_amount,
                "price": t.price,
                "profit_margin": t.profit_margin,
                "actual_profit": t.actual_profit,
                "is_automated": t.is_automated,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in trades
        ]
    }


@router.get("/{trade_id}")
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Obtener detalles de una operación específica"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return {
        "id": trade.id,
        "binance_order_id": trade.binance_order_id,
        "type": trade.trade_type.value,
        "status": trade.status.value,
        "asset": trade.asset,
        "fiat": trade.fiat,
        "crypto_amount": trade.crypto_amount,
        "fiat_amount": trade.fiat_amount,
        "price": trade.price,
        "fee": trade.fee,
        "profit_margin": trade.profit_margin,
        "actual_profit": trade.actual_profit,
        "payment_method": trade.payment_method,
        "is_automated": trade.is_automated,
        "counterparty": trade.counterparty,
        "notes": trade.notes,
        "error_message": trade.error_message,
        "created_at": trade.created_at.isoformat(),
        "updated_at": trade.updated_at.isoformat() if trade.updated_at else None,
        "completed_at": trade.completed_at.isoformat() if trade.completed_at else None,
        "duration_seconds": trade.duration_seconds
    }


@router.get("/stats/summary")
async def get_trade_stats(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de operaciones.

    Args:
        days: Número de días a analizar
    """
    since = datetime.utcnow() - timedelta(days=days)

    trades = db.query(Trade).filter(Trade.created_at >= since).all()

    completed_trades = [t for t in trades if t.status == TradeStatus.COMPLETED]
    failed_trades = [t for t in trades if t.status == TradeStatus.FAILED]

    total_profit = sum(t.actual_profit or 0 for t in completed_trades)
    total_volume_usd = sum(t.crypto_amount for t in completed_trades)

    # Separar por moneda
    cop_trades = [t for t in completed_trades if t.fiat == "COP"]
    ves_trades = [t for t in completed_trades if t.fiat == "VES"]

    return {
        "period_days": days,
        "total_trades": len(trades),
        "completed": len(completed_trades),
        "pending": len([t for t in trades if t.status in [TradeStatus.PENDING, TradeStatus.IN_PROGRESS]]),
        "failed": len(failed_trades),
        "automated_trades": len([t for t in trades if t.is_automated]),
        "manual_trades": len([t for t in trades if not t.is_automated]),
        "total_profit": round(total_profit, 2),
        "total_volume_usd": round(total_volume_usd, 2),
        "average_profit_per_trade": round(total_profit / len(completed_trades), 2) if completed_trades else 0,
        "success_rate": round((len(completed_trades) / len(trades)) * 100, 2) if trades else 0,
        "by_currency": {
            "COP": {
                "count": len(cop_trades),
                "volume": sum(t.crypto_amount for t in cop_trades),
                "profit": sum(t.actual_profit or 0 for t in cop_trades)
            },
            "VES": {
                "count": len(ves_trades),
                "volume": sum(t.crypto_amount for t in ves_trades),
                "profit": sum(t.actual_profit or 0 for t in ves_trades)
            }
        }
    }
