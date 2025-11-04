"""
Endpoints de precios y tasas.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import redis.asyncio as aioredis

from app.core.database import get_db, get_redis
from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.trm_service import TRMService

router = APIRouter()


@router.get("/current")
async def get_current_prices(
    asset: str = Query(default="USDT", description="Criptomoneda"),
    fiat: Optional[str] = Query(default=None, description="Moneda fiat (COP, VES, o ambas)"),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Obtener precios actuales de Binance P2P con margen de ganancia.

    Returns:
        Precios actuales para compra y venta con el margen aplicado
    """
    binance_service = BinanceService()

    # Si no se especifica fiat, traer ambas
    fiats = [fiat] if fiat else ["COP", "VES"]
    results = {}

    for currency in fiats:
        # Intentar obtener de cache
        cache_key = f"price:{asset}:{currency}"
        cached = await redis.get(cache_key)

        if cached:
            import json
            results[currency] = json.loads(cached)
        else:
            # Obtener precios de Binance
            buy_price = await binance_service.get_best_price(
                asset=asset,
                fiat=currency,
                trade_type="BUY"
            )

            sell_price = await binance_service.get_best_price(
                asset=asset,
                fiat=currency,
                trade_type="SELL"
            )

            # Aplicar margen de ganancia
            margin = settings.PROFIT_MARGIN_COP if currency == "COP" else settings.PROFIT_MARGIN_VES

            # Nuestro precio de venta (el usuario nos compra)
            our_sell_price = buy_price * (1 + margin / 100)

            # Nuestro precio de compra (el usuario nos vende)
            our_buy_price = sell_price * (1 - margin / 100)

            price_data = {
                "asset": asset,
                "fiat": currency,
                "buy_price": round(our_buy_price, 2),  # Precio al que compramos
                "sell_price": round(our_sell_price, 2),  # Precio al que vendemos
                "market_buy": round(buy_price, 2),
                "market_sell": round(sell_price, 2),
                "spread": round(((our_sell_price - our_buy_price) / our_buy_price) * 100, 2),
                "margin": margin,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Si es COP, incluir TRM
            if currency == "COP":
                trm_service = TRMService()
                trm = await trm_service.get_current_trm()
                price_data["trm"] = trm

            results[currency] = price_data

            # Guardar en cache
            import json
            await redis.setex(
                cache_key,
                settings.UPDATE_PRICE_INTERVAL,
                json.dumps(price_data)
            )

    return results


@router.get("/history")
async def get_price_history(
    asset: str = Query(default="USDT"),
    fiat: str = Query(default="COP"),
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de precios.

    Args:
        asset: Criptomoneda
        fiat: Moneda fiat
        hours: Horas hacia atrás (máximo 1 semana)
    """
    from app.models.price_history import PriceHistory

    since = datetime.utcnow() - timedelta(hours=hours)

    history = db.query(PriceHistory).filter(
        PriceHistory.asset == asset,
        PriceHistory.fiat == fiat,
        PriceHistory.timestamp >= since
    ).order_by(PriceHistory.timestamp.asc()).all()

    return {
        "asset": asset,
        "fiat": fiat,
        "period_hours": hours,
        "data_points": len(history),
        "history": [
            {
                "timestamp": h.timestamp.isoformat(),
                "bid": h.bid_price,
                "ask": h.ask_price,
                "avg": h.avg_price,
                "spread": h.spread
            }
            for h in history
        ]
    }


@router.get("/trm")
async def get_trm(redis: aioredis.Redis = Depends(get_redis)):
    """
    Obtener TRM (Tasa Representativa del Mercado) actual de Colombia.
    """
    trm_service = TRMService()
    trm_data = await trm_service.get_trm_with_history()

    return trm_data


@router.get("/spread-analysis")
async def analyze_spread(
    asset: str = Query(default="USDT"),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Análisis de spread entre COP y VES para detectar oportunidades de arbitraje.
    """
    binance_service = BinanceService()

    # Obtener precios de ambas monedas
    cop_buy = await binance_service.get_best_price(asset, "COP", "BUY")
    cop_sell = await binance_service.get_best_price(asset, "COP", "SELL")
    ves_buy = await binance_service.get_best_price(asset, "VES", "BUY")
    ves_sell = await binance_service.get_best_price(asset, "VES", "SELL")

    # Calcular spread
    cop_spread = ((cop_sell - cop_buy) / cop_buy) * 100
    ves_spread = ((ves_sell - ves_buy) / ves_buy) * 100

    # Detectar oportunidad de arbitraje
    arbitrage_opportunity = False
    arbitrage_profit = 0

    # Ejemplo: Comprar en COP, vender en VES
    # (Necesitaríamos tasa de cambio COP/VES para cálculo exacto)

    return {
        "asset": asset,
        "cop": {
            "buy": cop_buy,
            "sell": cop_sell,
            "spread_percent": round(cop_spread, 2)
        },
        "ves": {
            "buy": ves_buy,
            "sell": ves_sell,
            "spread_percent": round(ves_spread, 2)
        },
        "arbitrage_opportunity": arbitrage_opportunity,
        "potential_profit_percent": round(arbitrage_profit, 2),
        "timestamp": datetime.utcnow().isoformat()
    }
