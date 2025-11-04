"""
Tareas asíncronas de Celery.
"""
from celery_app.worker import celery_app
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog
import asyncio

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


@celery_app.task(name="celery_app.tasks.update_prices")
def update_prices():
    """
    Actualizar precios de P2P y guardar en base de datos.
    """
    db = get_db()
    try:
        binance_service = BinanceService()

        # Actualizar precios para COP y VES
        for fiat in ["COP", "VES"]:
            try:
                # Obtener market depth de manera síncrona
                depth = asyncio.run(binance_service.get_market_depth("USDT", fiat))

                best_buy = depth.get("best_buy")
                best_sell = depth.get("best_sell")

                if best_buy and best_sell:
                    # Guardar en base de datos
                    price_record = PriceHistory(
                        asset="USDT",
                        fiat=fiat,
                        bid_price=best_buy["price"],
                        ask_price=best_sell["price"],
                        avg_price=(best_buy["price"] + best_sell["price"]) / 2,
                        spread=depth["spread_percent"],
                        source="binance_p2p"
                    )

                    # Si es COP, agregar TRM
                    if fiat == "COP":
                        trm_service = TRMService()
                        trm = asyncio.run(trm_service.get_current_trm())
                        price_record.trm_rate = trm

                    db.add(price_record)
                    db.commit()

                    logger.info(
                        "Price updated",
                        asset="USDT",
                        fiat=fiat,
                        bid=best_buy["price"],
                        ask=best_sell["price"]
                    )

            except Exception as e:
                logger.error("Error updating price for fiat", fiat=fiat, error=str(e))
                db.rollback()

        return {"status": "success", "updated": ["COP", "VES"]}

    except Exception as e:
        logger.error("Error in update_prices task", error=str(e))
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
        binance_service = BinanceService()

        # Analizar para cada moneda
        for fiat in ["COP", "VES"]:
            depth = asyncio.run(binance_service.get_market_depth("USDT", fiat))
            spread = depth.get("spread_percent", 0)

            # Si el spread supera el umbral, crear alerta
            if spread >= settings.SPREAD_THRESHOLD:
                alert = Alert(
                    alert_type=AlertType.SPREAD_OPPORTUNITY,
                    priority=AlertPriority.HIGH if spread >= 1.0 else AlertPriority.MEDIUM,
                    title=f"Oportunidad de spread en {fiat}",
                    message=f"Spread de {spread}% detectado en USDT/{fiat}. "
                            f"Compra: {depth['best_buy']['price']}, Venta: {depth['best_sell']['price']}",
                    asset="USDT",
                    fiat=fiat,
                    percentage=spread
                )
                db.add(alert)

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
    try:
        from app.services.arbitrage_service import ArbitrageService
        from app.services.notification_service import NotificationService

        arb_service = ArbitrageService()
        notif_service = NotificationService()

        # Analizar arbitraje Spot -> P2P para ambas monedas
        for fiat in ["COP", "VES"]:
            opportunity = asyncio.run(
                arb_service.analyze_spot_to_p2p_arbitrage("USDT", fiat)
            )

            # Si es profitable, enviar notificación
            if opportunity.get('is_profitable'):
                asyncio.run(notif_service.send_arbitrage_alert(opportunity))

                logger.info(
                    "Arbitrage opportunity found",
                    fiat=fiat,
                    profit=opportunity.get('net_profit_percentage')
                )

        logger.info("Arbitrage analysis completed")
        return {"status": "success"}

    except Exception as e:
        logger.error("Error analyzing arbitrage", error=str(e))
        return {"status": "error", "error": str(e)}
