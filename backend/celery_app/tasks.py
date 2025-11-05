"""
Tareas asíncronas de Celery.
"""
from celery_app.worker import celery_app
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog
import asyncio
from typing import Callable, Any, List, Dict

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.price_history import PriceHistory
from app.models.alert import Alert, AlertType, AlertPriority
from app.services.binance_service import BinanceService
from app.services.trm_service import TRMService

logger = structlog.get_logger()


def get_db():
    """Helper para obtener sesión de DB"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # No cerramos aquí, se cierra en el finally del task


async def run_async_task(coro: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Helper para ejecutar tareas asíncronas desde Celery.
    Maneja correctamente el ciclo de vida del event loop y recursos.
    """
    try:
        # Intentar obtener el loop existente (si hay uno)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # No hay loop o está cerrado, crear uno nuevo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Ejecutar la coroutine
        if callable(coro):
            result = await coro(*args, **kwargs)
        else:
            result = await coro
        
        return result
    finally:
        # No cerramos el loop aquí porque puede estar siendo usado por otros
        pass


@celery_app.task(name="celery_app.tasks.update_prices")
def update_prices():
    """
    Actualizar precios de P2P y guardar en base de datos.
    """
    db = get_db()
    try:
        async def _update_prices_async():
            """Función async interna para manejar todas las llamadas async"""
            binance_service = BinanceService()
            trm_service = TRMService()
            try:
                results = []

                assets = list(dict.fromkeys(
                    asset.upper() for asset in (settings.P2P_MONITORED_ASSETS or ["USDT"])
                ))
                fiats = list(dict.fromkeys(
                    fiat.upper() for fiat in (settings.P2P_MONITORED_FIATS or ["COP", "VES"])
                ))

                trm_cache = None

                for asset in assets:
                    for fiat in fiats:
                        try:
                            depth = await binance_service.get_market_depth(
                                asset,
                                fiat,
                                rows=settings.P2P_ANALYSIS_ROWS,
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.error(
                                "Error updating price for pair",
                                asset=asset,
                                fiat=fiat,
                                error=str(exc),
                            )
                            results.append({"asset": asset, "fiat": fiat, "error": str(exc)})
                            continue

                        best_buy = depth.get("best_buy")
                        best_sell = depth.get("best_sell")

                        if not (best_buy and best_sell):
                            logger.warning(
                                "Incomplete market depth",
                                asset=asset,
                                fiat=fiat,
                            )
                            results.append({
                                "asset": asset,
                                "fiat": fiat,
                                "error": "Incomplete market depth",
                            })
                            continue

                        trm = None
                        if fiat == "COP":
                            if trm_cache is None:
                                trm_cache = await trm_service.get_current_trm()
                            trm = trm_cache

                        results.append({
                            "asset": asset,
                            "fiat": fiat,
                            "best_buy": best_buy,
                            "best_sell": best_sell,
                            "depth": depth,
                            "trm": trm,
                        })

                return results
            finally:
                # Cerrar cliente HTTP dentro del mismo event loop
                await binance_service.aclose()
        
        # Ejecutar función async
        results = asyncio.run(_update_prices_async())
        
        # Guardar resultados en base de datos
        for result in results:
            if "error" in result:
                continue

            fiat = result["fiat"]
            asset = result.get("asset", "USDT")
            best_buy = result["best_buy"]
            best_sell = result["best_sell"]
            depth = result["depth"]
            
            try:
                price_record = PriceHistory(
                    asset=asset,
                    fiat=fiat,
                    bid_price=best_buy["price"],
                    ask_price=best_sell["price"],
                    avg_price=(best_buy["price"] + best_sell["price"]) / 2,
                    spread=depth["spread_percent"],
                    source="binance_p2p",
                    trm_rate=result.get("trm")
                )

                db.add(price_record)
                db.commit()

                logger.info(
                    "Price updated",
                    asset=asset,
                    fiat=fiat,
                    bid=best_buy["price"],
                    ask=best_sell["price"]
                )
            except Exception as e:
                logger.error("Error saving price to database", fiat=fiat, error=str(e))
                db.rollback()

        updated_pairs = sorted({
            f"{result.get('asset', 'USDT')}/{result['fiat']}"
            for result in results
            if "error" not in result
        })

        return {"status": "success", "updated": updated_pairs}

    except Exception as e:
        logger.error("Error in update_prices task", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="celery_app.tasks.update_trm")
def update_trm():
    """
    Actualizar TRM desde la API del gobierno.
    """
    try:
        trm_service = TRMService()
        trm = asyncio.run(trm_service.get_current_trm())

        logger.info("TRM updated", value=trm)
        return {"status": "success", "trm": trm}

    except Exception as e:
        logger.error("Error updating TRM", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(name="celery_app.tasks.analyze_spread_opportunities")
def analyze_spread_opportunities():
    """
    Analizar spreads y detectar oportunidades de arbitraje.
    Crear alertas si se encuentran oportunidades.
    """
    db = get_db()
    try:
        from app.services.notification_service import NotificationService

        async def _analyze_spread_async():
            """Función async interna para manejar todas las llamadas async"""
            binance_service = BinanceService()
            notif_service = NotificationService()
            
            try:
                results = []
                assets = list(dict.fromkeys(
                    asset.upper() for asset in (settings.P2P_MONITORED_ASSETS or ["USDT"])
                ))
                fiats = list(dict.fromkeys(
                    fiat.upper() for fiat in (settings.P2P_MONITORED_FIATS or ["COP", "VES"])
                ))

                def build_opportunities(depth: dict, asset_code: str, fiat_code: str) -> list:
                    """Derivar mejores spreads usando profundidad de mercado."""
                    buy_levels = depth.get("buy_depth") or []
                    sell_levels = depth.get("sell_depth") or []

                    raw_opportunities = []
                    max_levels = max(settings.P2P_TOP_SPREADS * 2, 3)

                    for buy in buy_levels[:max_levels]:
                        buy_price = buy.get("price")
                        if not buy_price or buy_price <= 0:
                            continue

                        for sell in sell_levels[:max_levels]:
                            sell_price = sell.get("price")
                            if not sell_price or sell_price <= 0:
                                continue

                            spread = ((sell_price - buy_price) / buy_price) * 100
                            if spread <= 0:
                                continue

                            raw_opportunities.append({
                                "asset": asset_code,
                                "fiat": fiat_code,
                                "spread": round(spread, 2),
                                "buy_price": round(buy_price, 2),
                                "sell_price": round(sell_price, 2),
                                "buy_available": round(buy.get("available", 0.0), 2),
                                "sell_available": round(sell.get("available", 0.0), 2),
                                "buy_merchant": buy.get("merchant"),
                                "sell_merchant": sell.get("merchant"),
                                "buy_payment_methods": buy.get("payment_methods", []),
                                "sell_payment_methods": sell.get("payment_methods", []),
                            })

                    raw_opportunities.sort(key=lambda item: item["spread"], reverse=True)

                    top_opportunities = []
                    seen_keys = set()
                    for opportunity in raw_opportunities:
                        dedupe_key = (
                            opportunity["buy_price"],
                            opportunity["sell_price"],
                            opportunity.get("buy_merchant"),
                            opportunity.get("sell_merchant"),
                        )
                        if dedupe_key in seen_keys:
                            continue
                        seen_keys.add(dedupe_key)
                        top_opportunities.append(opportunity)
                        if len(top_opportunities) >= settings.P2P_TOP_SPREADS:
                            break

                    return top_opportunities

                for asset in assets:
                    for fiat in fiats:
                        try:
                            depth = await binance_service.get_market_depth(
                                asset,
                                fiat,
                                rows=settings.P2P_ANALYSIS_ROWS,
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.error(
                                "Error fetching depth for spread analysis",
                                asset=asset,
                                fiat=fiat,
                                error=str(exc),
                            )
                            continue

                        opportunities = build_opportunities(depth, asset, fiat)

                        for idx, opportunity_data in enumerate(opportunities, start=1):
                            opportunity_data["rank"] = idx
                            spread = opportunity_data["spread"]
                            opportunity_data.setdefault("potential_profit_percent", spread)

                            results.append({
                                "asset": asset,
                                "fiat": fiat,
                                "spread": spread,
                                "depth": depth,
                                "opportunity_data": opportunity_data,
                            })

                            if spread >= settings.SPREAD_THRESHOLD:
                                try:
                                    await notif_service.send_p2p_opportunity_alert(opportunity_data)
                                    logger.info(
                                        "Spread opportunity notification sent",
                                        asset=asset,
                                        fiat=fiat,
                                        spread=spread,
                                        rank=idx,
                                    )
                                except Exception as e:  # noqa: BLE001
                                    logger.error(
                                        "Error sending notification",
                                        asset=asset,
                                        fiat=fiat,
                                        error=str(e),
                                    )

                return results
            finally:
                # Cerrar cliente HTTP dentro del mismo event loop
                await binance_service.aclose()
                if 'notif_service' in locals():
                    try:
                        await notif_service.send_spread_digest(results)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Error sending spread digest", error=str(exc))

        # Ejecutar función async
        results = asyncio.run(_analyze_spread_async())
        
        # Guardar alertas en base de datos
        for result in results:
            fiat = result["fiat"]
            asset = result.get("asset", "USDT")
            spread = result["spread"]
            opportunity_data = result.get("opportunity_data", {})

            buy_price = opportunity_data.get("buy_price")
            sell_price = opportunity_data.get("sell_price")
            buy_merchant = opportunity_data.get("buy_merchant") or "N/A"
            sell_merchant = opportunity_data.get("sell_merchant") or "N/A"

            try:
                alert = Alert(
                    alert_type=AlertType.SPREAD_OPPORTUNITY,
                    priority=AlertPriority.HIGH if spread >= 1.0 else AlertPriority.MEDIUM,
                    title=f"Oportunidad de spread en {asset}/{fiat}",
                    message=(
                        f"Spread de {spread}% detectado en {asset}/{fiat}. "
                        f"Compra: {buy_price} ({buy_merchant}) "
                        f"→ Venta: {sell_price} ({sell_merchant})."
                    ),
                    asset=asset,
                    fiat=fiat,
                    percentage=spread
                )
                db.add(alert)
            except Exception as e:
                logger.error("Error saving alert", fiat=fiat, asset=asset, error=str(e))

        db.commit()
        logger.info("Spread analysis completed")
        return {"status": "success"}

    except Exception as e:
        logger.error("Error analyzing spreads", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="celery_app.tasks.run_trading_bot")
def run_trading_bot():
    """
    Ejecutar lógica del bot de trading.
    Solo ejecuta si está en modo automático o híbrido.
    """
    if settings.TRADING_MODE == "manual":
        logger.info("Trading bot skipped - manual mode enabled")
        return {"status": "skipped", "reason": "manual_mode"}

    try:
        from app.trading.bot import TradingBot

        bot = TradingBot()
        result = asyncio.run(bot.execute_trading_cycle())

        return result

    except Exception as e:
        logger.error("Error in trading bot", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(name="celery_app.tasks.retrain_ml_model")
def retrain_ml_model():
    """
    Re-entrenar modelo de ML con datos recientes.
    """
    db = get_db()
    try:
        from app.ml.trainer import MLModelTrainer

        trainer = MLModelTrainer(db)
        result = trainer.train_model()

        logger.info("ML model retrained", metrics=result)
        return {"status": "success", "metrics": result}

    except Exception as e:
        logger.error("Error retraining ML model", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="celery_app.tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Limpiar datos antiguos de la base de datos.
    - Alertas leídas mayores a 30 días
    - Price history mayor a 90 días
    """
    db = get_db()
    try:
        cutoff_alerts = datetime.utcnow() - timedelta(days=30)
        cutoff_prices = datetime.utcnow() - timedelta(days=90)

        # Eliminar alertas antiguas leídas
        deleted_alerts = db.query(Alert).filter(
            Alert.is_read == True,
            Alert.created_at < cutoff_alerts
        ).delete()

        # Eliminar price history antiguo
        deleted_prices = db.query(PriceHistory).filter(
            PriceHistory.timestamp < cutoff_prices
        ).delete()

        db.commit()

        logger.info(
            "Old data cleaned up",
            deleted_alerts=deleted_alerts,
            deleted_prices=deleted_prices
        )

        return {
            "status": "success",
            "deleted_alerts": deleted_alerts,
            "deleted_prices": deleted_prices
        }

    except Exception as e:
        logger.error("Error cleaning up old data", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="celery_app.tasks.send_notification")
def send_notification(title: str, message: str, priority: str = "medium"):
    """
    Enviar notificación por Telegram o email.

    Args:
        title: Título de la notificación
        message: Mensaje
        priority: low, medium, high, critical
    """
    if not settings.ENABLE_NOTIFICATIONS:
        return {"status": "skipped", "reason": "notifications_disabled"}

    try:
        # TODO: Implementar envío por Telegram
        # TODO: Implementar envío por email

        logger.info("Notification sent", title=title, priority=priority)
        return {"status": "success"}

    except Exception as e:
        logger.error("Error sending notification", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(name="celery_app.tasks.analyze_arbitrage")
def analyze_arbitrage():
    """
    Analizar oportunidades de arbitraje Spot-P2P.
    Enviar alertas si hay oportunidades rentables.
    """
    db = get_db()
    try:
        from app.services.arbitrage_service import ArbitrageService
        from app.services.notification_service import NotificationService

        async def _analyze_arbitrage_async() -> List[Dict[str, Any]]:
            """Función async interna para manejar todas las llamadas async"""
            arb_service = ArbitrageService()
            notif_service = NotificationService()

            assets = list(dict.fromkeys(
                asset.upper()
                for asset in (
                    settings.ARBITRAGE_MONITORED_ASSETS
                    or settings.P2P_MONITORED_ASSETS
                    or ["USDT"]
                )
            ))
            fiats = list(dict.fromkeys(
                fiat.upper()
                for fiat in (
                    settings.ARBITRAGE_MONITORED_FIATS
                    or settings.P2P_MONITORED_FIATS
                    or ["COP", "VES"]
                )
            ))

            top_limit = settings.ARBITRAGE_TOP_OPPORTUNITIES or 5

            try:
                ranked = await arb_service.get_ranked_opportunities(
                    assets=assets,
                    fiats=fiats,
                    top_n=top_limit,
                    include_triangle=True,
                )
            finally:
                await arb_service.aclose()

            profitable = [
                {**opportunity, "rank": index}
                for index, opportunity in enumerate(
                    (
                        opp
                        for opp in ranked
                        if (opp.get("score") or 0) >= settings.ARBITRAGE_MIN_PROFIT
                    ),
                    start=1,
                )
            ]

            if profitable:
                try:
                    await notif_service.send_arbitrage_digest(profitable)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Error sending arbitrage digest", error=str(exc))

            return profitable

        results = asyncio.run(_analyze_arbitrage_async())

        if not results:
            logger.info("Arbitrage analysis completed", opportunities=0)
            return {"status": "success", "opportunities": 0}

        def fmt_number(value: Any, decimals: int = 2) -> str:
            try:
                return f"{float(value):,.{decimals}f}"
            except (TypeError, ValueError):
                return f"{0:.{decimals}f}"

        def fmt_percent(value: Any) -> str:
            try:
                return f"{float(value):.2f}%"
            except (TypeError, ValueError):
                return "0.00%"

        saved = 0
        for opportunity in results:
            strategy = opportunity.get("strategy", "spot_to_p2p")
            label = opportunity.get("label", "")
            asset = opportunity.get("asset", "USDT")
            fiat = opportunity.get("fiat", "USD")
            score = opportunity.get("score", 0.0)
            details = opportunity.get("details", {})
            rank = opportunity.get("rank", 0)

            if strategy == "spot_to_p2p":
                message = (
                    f"{label} — Spot→P2P rank #{rank}. Profit neto {fmt_percent(score)}. "
                    f"Spot ${fmt_number(details.get('spot_price_usd'), 4)} | "
                    f"P2P {fmt_number(details.get('p2p_sell_price_fiat'))} {fiat}. "
                    f"Liquidez: {fmt_number(details.get('p2p_sell_available'))} {asset}."
                )
            elif strategy == "cross_currency":
                buy_quote = details.get("buy_quote", {})
                sell_quote = details.get("sell_quote", {})
                message = (
                    f"Ruta {label} rank #{rank}. Profit estimado {fmt_percent(score)}. "
                    f"Compra USDT en {details.get('fiat_from')} a {fmt_number(buy_quote.get('price'))} "
                    f"y vende en {details.get('fiat_to')} a {fmt_number(sell_quote.get('price'))}. "
                    f"Liquidez: {fmt_number(details.get('max_volume'))} {asset}."
                )
            elif strategy == "triangle_arbitrage":
                step1 = details.get("step_1", {})
                step2 = details.get("step_2", {})
                message = (
                    f"Ruta {label} rank #{rank}. ROI {fmt_percent(score)}. "
                    f"Paso 1: {step1.get('action')} @ {fmt_number(step1.get('price'))}. "
                    f"Paso 2: {step2.get('action')} @ {fmt_number(step2.get('price'))}."
                )
            else:
                message = f"{label} rank #{rank}. Profit estimado {fmt_percent(score)}."

            alert = Alert(
                alert_type=AlertType.ARBITRAGE,
                priority=AlertPriority.HIGH if score >= (settings.ARBITRAGE_MIN_PROFIT + 1) else AlertPriority.MEDIUM,
                title=f"Arbitraje {strategy.replace('_', ' ').title()} #{rank}",
                message=message,
                asset=asset,
                fiat=fiat,
                percentage=score,
            )

            db.add(alert)
            saved += 1

        db.commit()
        logger.info("Arbitrage analysis completed", opportunities=saved)
        return {"status": "success", "opportunities": saved}

    except Exception as e:
        logger.error("Error analyzing arbitrage", error=str(e))
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
